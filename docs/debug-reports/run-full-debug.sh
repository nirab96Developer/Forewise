#!/bin/bash
# Forewise Full Debug Script
# Runs all checks and saves results to debug report

REPORT_DIR="/root/kkl-forest/docs/debug-reports"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT="$REPORT_DIR/debug-$TIMESTAMP.md"

echo "# Forewise Debug Report — $TIMESTAMP" > "$REPORT"
echo "" >> "$REPORT"
echo "---" >> "$REPORT"

# 1. Backend Health
echo "" >> "$REPORT"
echo "## 1. Backend Health" >> "$REPORT"
echo '```' >> "$REPORT"
HEALTH=$(curl -s http://localhost:8000/health 2>&1)
echo "$HEALTH" >> "$REPORT"
echo '```' >> "$REPORT"
if echo "$HEALTH" | grep -q '"ok"'; then
  echo "✅ Backend is running" >> "$REPORT"
else
  echo "❌ Backend is DOWN" >> "$REPORT"
fi

# 2. Port 8000 Status
echo "" >> "$REPORT"
echo "## 2. Port 8000" >> "$REPORT"
echo '```' >> "$REPORT"
fuser 8000/tcp 2>&1 >> "$REPORT"
echo '```' >> "$REPORT"

# 3. Nginx Status
echo "" >> "$REPORT"
echo "## 3. Nginx" >> "$REPORT"
echo '```' >> "$REPORT"
systemctl status nginx --no-pager -l 2>&1 | head -15 >> "$REPORT"
echo '```' >> "$REPORT"

# 4. Frontend Build Check
echo "" >> "$REPORT"
echo "## 4. Frontend dist/" >> "$REPORT"
echo '```' >> "$REPORT"
ls -lh /root/kkl-forest/app_frontend/dist/index.html 2>&1 >> "$REPORT"
ls /root/kkl-forest/app_frontend/dist/assets/*.js 2>/dev/null | wc -l | xargs -I{} echo "JS files: {}" >> "$REPORT"
echo '```' >> "$REPORT"

# 5. API Endpoints Quick Test
echo "" >> "$REPORT"
echo "## 5. API Endpoints Test" >> "$REPORT"
echo "| Endpoint | Status |" >> "$REPORT"
echo "|----------|--------|" >> "$REPORT"
for ep in "/health" "/api/v1/health" "/api/v1/auth/login" "/api/v1/projects" "/api/v1/work-orders" "/api/v1/worklogs" "/api/v1/suppliers" "/api/v1/equipment" "/api/v1/invoices" "/api/v1/budgets" "/api/v1/notifications" "/api/v1/dashboard/statistics" "/api/v1/supplier-rotations" "/api/v1/geo/layers/all" "/api/v1/support-tickets"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -L "http://localhost:8000$ep" 2>/dev/null)
  if [ "$CODE" = "200" ] || [ "$CODE" = "401" ] || [ "$CODE" = "422" ] || [ "$CODE" = "307" ]; then
    echo "| $ep | ✅ $CODE |" >> "$REPORT"
  elif [ "$CODE" = "405" ]; then
    echo "| $ep | ✅ $CODE (POST only) |" >> "$REPORT"
  else
    echo "| $ep | ❌ $CODE |" >> "$REPORT"
  fi
done

# 6. Database Connection
echo "" >> "$REPORT"
echo "## 6. Database" >> "$REPORT"
echo '```' >> "$REPORT"
DB_CHECK=$(curl -s http://localhost:8000/api/v1/health/db 2>&1)
echo "$DB_CHECK" >> "$REPORT"
echo '```' >> "$REPORT"

# 7. Recent Backend Errors (last 50 lines of log)
echo "" >> "$REPORT"
echo "## 7. Recent Backend Errors" >> "$REPORT"
echo '```' >> "$REPORT"
if [ -f /root/kkl-forest/app_backend/logs/development.log ]; then
  grep -i "error\|exception\|traceback\|failed" /root/kkl-forest/app_backend/logs/development.log 2>/dev/null | tail -20 >> "$REPORT"
else
  echo "No log file found" >> "$REPORT"
fi
# Also check uvicorn output
if [ -f /tmp/uvicorn.log ]; then
  echo "" >> "$REPORT"
  echo "--- uvicorn.log (last 20 errors) ---" >> "$REPORT"
  grep -i "error\|exception\|traceback\|failed\|500" /tmp/uvicorn.log 2>/dev/null | tail -20 >> "$REPORT"
fi
echo '```' >> "$REPORT"

# 8. Service Worker & PWA
echo "" >> "$REPORT"
echo "## 8. PWA / Service Worker" >> "$REPORT"
echo '```' >> "$REPORT"
echo "manifest:" >> "$REPORT"
cat /root/kkl-forest/app_frontend/public/manifest.webmanifest | head -5 >> "$REPORT"
echo "sw.js cache:" >> "$REPORT"
head -4 /root/kkl-forest/app_frontend/public/sw.js >> "$REPORT"
echo '```' >> "$REPORT"

# 9. Disk Space
echo "" >> "$REPORT"
echo "## 9. Disk Space" >> "$REPORT"
echo '```' >> "$REPORT"
df -h / | tail -1 >> "$REPORT"
echo '```' >> "$REPORT"

# 10. Memory & CPU
echo "" >> "$REPORT"
echo "## 10. Memory & CPU" >> "$REPORT"
echo '```' >> "$REPORT"
free -h | head -2 >> "$REPORT"
echo "Uvicorn processes:" >> "$REPORT"
ps aux | grep uvicorn | grep -v grep >> "$REPORT" 2>/dev/null
echo '```' >> "$REPORT"

# Summary
echo "" >> "$REPORT"
echo "---" >> "$REPORT"
echo "## Summary" >> "$REPORT"
ERRORS=$(grep -c "❌" "$REPORT")
OKS=$(grep -c "✅" "$REPORT")
echo "- ✅ Passed: $OKS" >> "$REPORT"
echo "- ❌ Failed: $ERRORS" >> "$REPORT"
echo "- Report saved: $REPORT" >> "$REPORT"

echo "✅ Debug report saved to: $REPORT"
echo "Passed: $OKS | Failed: $ERRORS"
