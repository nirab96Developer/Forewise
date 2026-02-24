@echo off
echo ========================================
echo    יצירת תעודת חתימה זמנית לבדיקה
echo ========================================
echo.

echo יצירת תעודה זמנית...
powershell -Command "& {New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=KKL Time Report, O=KKL, C=IL' -KeyUsage DigitalSignature -FriendlyName 'KKL Time Report Code Signing' -CertStoreLocation Cert:\CurrentUser\My -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3')}"

echo.
echo ייצוא התעודה לקובץ P12...
powershell -Command "& {$cert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object {$_.Subject -eq 'CN=KKL Time Report, O=KKL, C=IL'}; $pwd = ConvertTo-SecureString -String 'kkl123' -Force -AsPlainText; Export-PfxCertificate -Cert $cert -FilePath 'certificates/kkl-certificate.p12' -Password $pwd}"

echo.
echo ========================================
echo    התעודה נוצרה בהצלחה!
echo ========================================
echo.
echo קובץ התעודה: certificates/kkl-certificate.p12
echo סיסמת התעודה: kkl123
echo.
echo הערה: זו תעודה זמנית לבדיקה בלבד
echo לפרודקשן צריך תעודה מ-CA מוכר
echo.
pause



