// src/services/biometricService.ts
// WebAuthn biometric service — register + authenticate via server

const REGISTERED_KEY = 'biometric_registered';

// Helpers 

/** base64 or base64url string ArrayBuffer (no atob dependency) */
function b64urlToBuffer(input: string): ArrayBuffer {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let str = String(input || '').trim().replace(/-/g, '+').replace(/_/g, '/').replace(/=+$/, '');
  const bytes: number[] = [];
  for (let i = 0; i < str.length; i += 4) {
    const a = chars.indexOf(str[i] || 'A');
    const b = chars.indexOf(str[i + 1] || 'A');
    const c = chars.indexOf(str[i + 2] || 'A');
    const d = chars.indexOf(str[i + 3] || 'A');
    bytes.push((a << 2) | (b >> 4));
    if (i + 2 < str.length) bytes.push(((b & 15) << 4) | (c >> 2));
    if (i + 3 < str.length) bytes.push(((c & 3) << 6) | d);
  }
  return new Uint8Array(bytes).buffer;
}

/** ArrayBuffer base64url */
function bufToB64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let bin = '';
  bytes.forEach(b => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}


/** Serialise a PublicKeyCredential to plain JSON for sending to server */
function _credentialToJSON(cred: PublicKeyCredential): Record<string, unknown> {
  const r = cred.response;
  const base: Record<string, unknown> = {
    id:     cred.id,
    rawId:  bufToB64url(cred.rawId),
    type:   cred.type,
  };
  if ('attestationObject' in r) {
    const attResp = r as AuthenticatorAttestationResponse;
    base.response = {
      clientDataJSON:    bufToB64url(attResp.clientDataJSON),
      attestationObject: bufToB64url(attResp.attestationObject),
    };
  } else {
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
void _credentialToJSON;

// Public API 

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
* 2. navigator.credentials.create() shows platform authenticator dialog
   * 3. POST result to server
   */
  async register(): Promise<void> {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('יש להתחבר תחילה');

    // Step 1 — get challenge from server
    const beginRes = await fetch('/api/v1/auth/biometric/register', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!beginRes.ok) {
      const err = await beginRes.json().catch(() => ({}));
      throw new Error(err.detail || 'שגיאה בהתחלת רישום ביומטרי');
    }
    const options = await beginRes.json();

    if (!options.challenge || !options.user?.id) {
      throw new Error('תשובה לא תקינה מהשרת — חסר challenge או user.id');
    }

    const challengeBuf = b64urlToBuffer(String(options.challenge));
    const userIdBuf = b64urlToBuffer(String(options.user.id));

    const publicKey: PublicKeyCredentialCreationOptions = {
      challenge: challengeBuf,
      rp: options.rp || { name: 'Forewise', id: window.location.hostname },
      user: {
        id: userIdBuf,
        name: options.user.name || 'user',
        displayName: options.user.displayName || options.user.name || 'User',
      },
      pubKeyCredParams: options.pubKeyCredParams || [
        { alg: -7, type: 'public-key' },
        { alg: -257, type: 'public-key' },
      ],
      timeout: options.timeout || 60000,
      attestation: 'none',
      authenticatorSelection: {
        authenticatorAttachment: 'platform',
        userVerification: 'required',
        residentKey: 'preferred',
        requireResidentKey: false,
      },
      excludeCredentials: (options.excludeCredentials ?? []).map((c: any) => ({
        ...c,
        id: b64urlToBuffer(String(c.id)),
      })),
    };

    // Step 2 — platform authenticator dialog (Face ID / Touch ID / Windows Hello)
    let credential: PublicKeyCredential;
    try {
      credential = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential;
    } catch (e: any) {
      if (e.name === 'NotAllowedError') throw new Error('הפעולה בוטלה על ידי המשתמש');
      if (e.name === 'InvalidStateError') throw new Error('מכשיר זה כבר רשום');
      throw new Error(`שגיאת ביומטריה: ${e.message}`);
    }
    if (!credential) throw new Error('יצירת credential נכשלה');

    // Step 3 — save credential on server
    const completeRes = await fetch('/api/v1/auth/biometric/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        credentialId: credential.id,
        attestationObject: bufToB64url((credential.response as AuthenticatorAttestationResponse).attestationObject),
        clientDataJSON: bufToB64url(credential.response.clientDataJSON),
      }),
    });
    if (!completeRes.ok) {
      const err = await completeRes.json().catch(() => ({}));
      throw new Error(err.detail || 'שגיאה בשמירת הרישום');
    }

    localStorage.setItem(REGISTERED_KEY, 'true');
  }

  /**
   * Full authentication flow:
* 1. POST username server returns challenge + allowCredentials
* 2. navigator.credentials.get() shows platform authenticator dialog
* 3. POST assertion server returns access_token + user
   */
  async authenticate(username: string): Promise<{ access_token: string; refresh_token?: string; user: any }> {
    if (!this.isRegistered()) {
      throw new Error('יש להפעיל תחילה התחברות ביומטרית מדף הברוכים הבאים');
    }

    // Step 1 — get challenge from server
    const beginRes = await fetch('/api/v1/auth/biometric/challenge', {
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
    const completeRes = await fetch('/api/v1/auth/biometric/authenticate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        credentialId: assertion.id,
        username,
        authenticatorData: bufToB64url((assertion.response as AuthenticatorAssertionResponse).authenticatorData),
        signature: bufToB64url((assertion.response as AuthenticatorAssertionResponse).signature),
        clientDataJSON: bufToB64url(assertion.response.clientDataJSON),
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

// Legacy compat 
  hasSavedCredentials(): boolean { return this.isRegistered(); }
  getSavedCredentials() { return this.isRegistered() ? { registered: true } : null; }
  clearCredentials(): void { this.clearRegistration(); }
}

const biometricService = new BiometricService();
export default biometricService;
