export function getBiometricLabel(): { text: string; icon: 'scan-face' | 'fingerprint' | 'monitor' } {
  const ua = navigator.userAgent;

  if (/iPhone/.test(ua))
    return { text: 'התחברות עם Face ID', icon: 'scan-face' };

  if (/iPad/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1))
    return { text: 'התחברות עם Touch ID', icon: 'fingerprint' };

  if (/Samsung|SM-[A-Z]|Galaxy/.test(ua))
    return { text: 'התחברות עם טביעת אצבע', icon: 'fingerprint' };

  if (/Android/.test(ua))
    return { text: 'התחברות ביומטרית', icon: 'fingerprint' };

  if (/Windows/.test(ua) || /Win/.test(navigator.platform))
    return { text: 'התחברות עם Windows Hello', icon: 'monitor' };

  if (/Mac/.test(ua))
    return { text: 'התחברות עם Touch ID', icon: 'fingerprint' };

  return { text: 'התחברות ביומטרית (Face ID / Touch ID)', icon: 'fingerprint' };
}
