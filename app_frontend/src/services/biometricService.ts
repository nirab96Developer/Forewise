// src/services/biometricService.ts
// WebAuthn biometric service — register + authenticate via server

const REGISTERED_KEY = 'biometric_registered';

// ── Helpers ────────────────────────────────────────────────────────────────

/** base64url → ArrayBuffer (handles missing padding) */
function b64urlToBuffer(b64url: string): ArrayBuffer {
  const b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
  const padded = b64.padEnd(b64.length + (4 - b64.length % 4) % 4, '=');
  const bin = atob(padded);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}

/** ArrayBuffer → base64url */
function bufToB64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let bin = '';
  bytes.forEach(b => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}


/** Serialise a PublicKeyCredential to plain JSON for sending to server */
function credentialToJSON(cred: PublicKeyCredential): Record<string, unknown> {
  const r = cred.response;

  const base: Record<string, unknown> = {
    id:     cred.id,
    rawId:  bufToB64url(cred.rawId),
    type:   cred.type,
  };

  if ('attestationObject' in r) {
    // Registration response
    const attResp = r as AuthenticatorAttestationResponse;
    base.response = {
      clientDataJSON:    bufToB64url(attResp.clientDataJSON),
      attestationObject: bufToB64url(attResp.attestationObject),
    };
  } else {
    // Authentication response
    const assResp = r as AuthenticatorAssertionResponse;
    base.response = {
      clientDataJSON:  bufToB64url(assResp.clientDataJSON),
      authenticatorData: bufToB64url(assResp.authenticatorData),
      signature:       bufToB64url(assResp.signature),
      userHandle:      assResp.userHandle ? bufToB64url(assResp.userHandle) : null,
    };
  }

  return base;
}

// ── Public API ─────────────────────────────────────────────────────────────

class BiometricService {
  /** True when WebAuthn platform authenticator is available on this device */
  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'PublicKeyCredential' in window &&
      typeof (PublicKeyCredential as any).isUserVerifyingPlatformAuthenticatorAvailable === 'function'
    );
  }

  async isAvailable(): Promise<boolean> {
    if (!this.isSupported()) return false;
    try {
      return await (PublicKeyCredential as any).isUserVerifyingPlatformAuthenticatorAvailable();
    } catch {
      return false;
    }
  }

  /** Has the user completed registration on this device? */
  isRegistered(): boolean {
    return localStorage.getItem(REGISTERED_KEY) === 'true';
  }

  /**
   * Full registration flow:
   * 1. GET challenge from server (requires valid auth token)
   * 2. navigator.credentials.create() → shows platform authenticator dialog
   * 3. POST result to server
   */
  async register(): Promise<void> {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('יש להתחבר תחילה');

    // Step 1 — get options from server
    const beginRes = await fetch('/api/v1/auth/webauthn/register/begin', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!beginRes.ok) {
      const err = await beginRes.json().catch(() => ({}));
      throw new Error(err.detail || 'שגיאה בהתחלת רישום');
    }
    const options = await beginRes.json();

    // Explicit conversion: only the fields WebAuthn requires as ArrayBuffer.
    // rp.id must remain a plain string — do NOT convert it.
    const publicKey: PublicKeyCredentialCreationOptions = {
      ...options,
      challenge: b64urlToBuffer(options.challenge),
      user: {
        ...options.user,
        id: b64urlToBuffer(options.user.id),
      },
      excludeCredentials: (options.excludeCredentials ?? []).map((c: any) => ({
        ...c,
        id: b64urlToBuffer(c.id),
      })),
    };

    // Step 2 — platform authenticator dialog
    let credential: PublicKeyCredential;
    try {
      credential = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential;
    } catch (e: any) {
      if (e.name === 'NotAllowedError') throw new Error('הפעולה בוטלה על ידי המשתמש');
      throw e;
    }
    if (!credential) throw new Error('יצירת credential נכשלה');

    // Step 3 — send to server
    const completeRes = await fetch('/api/v1/auth/webauthn/register/complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(credentialToJSON(credential)),
    });
    if (!completeRes.ok) {
      const err = await completeRes.json().catch(() => ({}));
      throw new Error(err.detail || 'שגיאה בשמירת הרישום');
    }

    localStorage.setItem(REGISTERED_KEY, 'true');
  }

  /**
   * Full authentication flow:
   * 1. POST username → server returns challenge + allowCredentials
   * 2. navigator.credentials.get() → shows platform authenticator dialog
   * 3. POST assertion → server returns access_token + user
   */
  async authenticate(username: string): Promise<{ access_token: string; refresh_token?: string; user: any }> {
    if (!this.isRegistered()) {
      throw new Error('יש להפעיל תחילה התחברות ביומטרית מדף הברוכים הבאים');
    }

    // Step 1 — get options from server
    const beginRes = await fetch('/api/v1/auth/webauthn/login/begin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    });
    if (!beginRes.ok) {
      const err = await beginRes.json().catch(() => ({}));
      // Credential not registered on server — clear local flag
      if (beginRes.status === 404) {
        localStorage.removeItem(REGISTERED_KEY);
        throw new Error('לא נמצא credential במערכת. אנא הפעל מחדש את ההתחברות הביומטרית');
      }
      throw new Error(err.detail || 'שגיאה בהתחלת אימות');
    }
    const options = await beginRes.json();

    // Explicit conversion — same rule: rp.id stays string, only binary fields become ArrayBuffer.
    const publicKey: PublicKeyCredentialRequestOptions = {
      ...options,
      challenge: b64urlToBuffer(options.challenge),
      allowCredentials: (options.allowCredentials ?? []).map((c: any) => ({
        ...c,
        id: b64urlToBuffer(c.id),
      })),
    };

    // Step 2 — platform authenticator dialog
    let assertion: PublicKeyCredential;
    try {
      assertion = (await navigator.credentials.get({ publicKey })) as PublicKeyCredential;
    } catch (e: any) {
      if (e.name === 'NotAllowedError') throw new Error('הפעולה בוטלה על ידי המשתמש');
      throw e;
    }
    if (!assertion) throw new Error('אימות נכשל');

    // Step 3 — verify on server
    const completeRes = await fetch('/api/v1/auth/webauthn/login/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        ...credentialToJSON(assertion),
      }),
    });
    if (!completeRes.ok) {
      const err = await completeRes.json().catch(() => ({}));
      throw new Error(err.detail || 'אימות ביומטרי נכשל');
    }
    return completeRes.json();
  }

  /** Remove local registration flag (e.g. after user signs out) */
  clearRegistration(): void {
    localStorage.removeItem(REGISTERED_KEY);
  }

  // ── Legacy compat ───────────────────────────────────────────────────────
  hasSavedCredentials(): boolean { return this.isRegistered(); }
  getSavedCredentials() { return this.isRegistered() ? { registered: true } : null; }
  clearCredentials(): void { this.clearRegistration(); }
}

const biometricService = new BiometricService();
export default biometricService;
