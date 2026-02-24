// src/services/biometricService.ts
// שירות לזיהוי ביומטרי (Face ID / Touch ID) באמצעות WebAuthn API

interface BiometricCredentials {
  credentialId: string;
  publicKey: string;
  userId: number;
  username: string;
}

class BiometricService {
  private readonly STORAGE_KEY = 'biometric_credentials';

  /**
   * בדיקה אם הזיהוי הביומטרי נתמך בדפדפן
   */
  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'PublicKeyCredential' in window &&
      typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function'
    );
  }

  /**
   * בדיקה אם יש זיהוי ביומטרי זמין (Face ID / Touch ID)
   */
  async isAvailable(): Promise<boolean> {
    if (!this.isSupported()) {
      return false;
    }

    try {
      return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      return false;
    }
  }

  /**
   * רישום זיהוי ביומטרי למשתמש
   */
  async register(userId: number, username: string): Promise<BiometricCredentials | null> {
    if (!(await this.isAvailable())) {
      throw new Error('זיהוי ביומטרי לא זמין במכשיר זה');
    }

    try {
      // קבלת challenge מהשרת
      const challengeResponse = await fetch('/api/v1/auth/biometric/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, username }),
      });

      if (!challengeResponse.ok) {
        throw new Error('שגיאה בקבלת challenge מהשרת');
      }

      const { challenge, rp, user } = await challengeResponse.json();

      // יצירת credential
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge: Uint8Array.from(challenge, (c: string) => c.charCodeAt(0)),
          rp: {
            name: rp.name || 'מערכת ניהול יערות',
            id: rp.id || window.location.hostname,
          },
          user: {
            id: Uint8Array.from(user.id, (c: string) => c.charCodeAt(0)),
            name: user.name || username,
            displayName: user.displayName || username,
          },
          pubKeyCredParams: [
            { alg: -7, type: 'public-key' }, // ES256
            { alg: -257, type: 'public-key' }, // RS256
          ],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            userVerification: 'required',
          },
          timeout: 60000,
          attestation: 'direct',
        },
      }) as PublicKeyCredential;

      if (!credential) {
        throw new Error('יצירת credential נכשלה');
      }

      const response = credential.response as AuthenticatorAttestationResponse;

      // שליחה לשרת לאימות ושמירה
      const verifyResponse = await fetch('/api/v1/auth/biometric/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          credentialId: credential.id,
          attestationObject: Array.from(new Uint8Array(response.attestationObject)),
          clientDataJSON: Array.from(new Uint8Array(response.clientDataJSON)),
        }),
      });

      if (!verifyResponse.ok) {
        throw new Error('שגיאה באימות credential');
      }

      const { credentialId: savedCredentialId } = await verifyResponse.json();

      // שמירה מקומית
      const credentials: BiometricCredentials = {
        credentialId: savedCredentialId,
        publicKey: '', // לא נשמור את זה מקומית
        userId,
        username,
      };

      this.saveCredentials(credentials);

      return credentials;
    } catch (error: any) {
      console.error('Biometric registration error:', error);
      throw error;
    }
  }

  /**
   * התחברות באמצעות זיהוי ביומטרי
   */
  async authenticate(): Promise<{ access_token: string; refresh_token?: string; user: any } | null> {
    if (!(await this.isAvailable())) {
      throw new Error('זיהוי ביומטרי לא זמין במכשיר זה');
    }

    try {
      // קבלת challenge מהשרת
      const challengeResponse = await fetch('/api/v1/auth/biometric/challenge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!challengeResponse.ok) {
        throw new Error('שגיאה בקבלת challenge מהשרת');
      }

      const { challenge, allowCredentials } = await challengeResponse.json();

      // אימות
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge: Uint8Array.from(challenge, (c: string) => c.charCodeAt(0)),
          allowCredentials: allowCredentials?.map((cred: any) => ({
            id: Uint8Array.from(cred.id, (c: string) => c.charCodeAt(0)),
            type: 'public-key',
            transports: ['internal'],
          })),
          timeout: 60000,
          userVerification: 'required',
        },
      }) as PublicKeyCredential;

      if (!assertion) {
        throw new Error('אימות נכשל');
      }

      const response = assertion.response as AuthenticatorAssertionResponse;

      // שליחה לשרת לאימות
      const verifyResponse = await fetch('/api/v1/auth/biometric/authenticate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          credentialId: assertion.id,
          authenticatorData: Array.from(new Uint8Array(response.authenticatorData)),
          clientDataJSON: Array.from(new Uint8Array(response.clientDataJSON)),
          signature: Array.from(new Uint8Array(response.signature)),
        }),
      });

      if (!verifyResponse.ok) {
        throw new Error('שגיאה באימות');
      }

      return await verifyResponse.json();
    } catch (error: any) {
      console.error('Biometric authentication error:', error);
      throw error;
    }
  }

  /**
   * שמירת credentials מקומית
   */
  private saveCredentials(credentials: BiometricCredentials): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(credentials));
    } catch (error) {
      console.error('Error saving biometric credentials:', error);
    }
  }

  /**
   * קבלת credentials שמורים
   */
  getSavedCredentials(): BiometricCredentials | null {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.error('Error getting saved credentials:', error);
      return null;
    }
  }

  /**
   * מחיקת credentials שמורים
   */
  clearCredentials(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing credentials:', error);
    }
  }

  /**
   * בדיקה אם יש credentials שמורים
   */
  hasSavedCredentials(): boolean {
    return this.getSavedCredentials() !== null;
  }
}

const biometricService = new BiometricService();
export default biometricService;




