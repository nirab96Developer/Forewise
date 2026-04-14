#!/bin/bash
# ============================================================
# check_api_gaps.sh — Frontend↔Backend API Gap Detector
# ============================================================
# Scans frontend for all API calls and checks if each endpoint
# exists in the backend routers.
#
# Usage:  bash scripts/check_api_gaps.sh
# ============================================================

set -uo pipefail

FRONTEND="app_frontend/src"
BACKEND="app_backend/app/routers"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

echo ""
echo -e "${BOLD}=========================================${NC}"
echo -e "${BOLD}  Frontend ↔ Backend API Gap Detector${NC}"
echo -e "${BOLD}=========================================${NC}"
echo ""

# -----------------------------------------------------------
# STEP 1: Extract all backend endpoint paths
# -----------------------------------------------------------
echo -e "${CYAN}[1/4] Scanning backend routers...${NC}"

BACKEND_ENDPOINTS=$(mktemp)

# Extract router prefixes and endpoint paths
for f in "$BACKEND"/*.py; do
  # Get prefix from APIRouter(prefix="...")
  prefix=$(grep -oP 'prefix\s*=\s*"([^"]*)"' "$f" 2>/dev/null | head -1 | grep -oP '"[^"]*"' | tr -d '"' || true)
  [ -z "$prefix" ] && continue

  # Get all route decorators
  grep -nP '@router\.(get|post|put|patch|delete)\(' "$f" 2>/dev/null | while IFS= read -r line; do
    method=$(echo "$line" | grep -oP '\.(get|post|put|patch|delete)' | tr -d '.')
    path=$(echo "$line" | grep -oP '"([^"]*)"' | head -1 | tr -d '"' || echo "")
    full="${prefix}${path}"
    # Normalize path params: {xxx} → {*}
    normalized=$(echo "$full" | sed -E 's/\{[^}]+\}/{*}/g')
    echo "${method^^} $normalized"
  done
done | sort -u > "$BACKEND_ENDPOINTS"

backend_count=$(wc -l < "$BACKEND_ENDPOINTS")
echo -e "   Found ${GREEN}${backend_count}${NC} backend endpoints"

# -----------------------------------------------------------
# STEP 2: Extract all frontend API calls
# -----------------------------------------------------------
echo -e "${CYAN}[2/4] Scanning frontend API calls...${NC}"

FRONTEND_CALLS=$(mktemp)

# Find all api.get/post/put/patch/delete calls
grep -rnP "api\.(get|post|put|patch|delete)\s*\(" "$FRONTEND" --include="*.ts" --include="*.tsx" 2>/dev/null | \
  grep -v node_modules | \
  grep -v '.d.ts' | \
  while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    lineno=$(echo "$line" | cut -d: -f2)
    method=$(echo "$line" | grep -oP 'api\.(get|post|put|patch|delete)' | head -1 | cut -d. -f2)
    # Extract endpoint path from the call — handle both 'path' and `template`
    path=$(echo "$line" | grep -oP "api\.\w+\s*\(\s*['\`\"]([^'\`\"]*)" | grep -oP "['\`\"].*" | head -1 | tr -d "'\`\"" || true)
    [ -z "$path" ] && continue
    # Normalize: remove template expressions like ${xxx}
    normalized=$(echo "$path" | sed -E 's/\$\{[^}]+\}/{*}/g')
    echo "${method^^}|${normalized}|${file}|${lineno}"
  done | sort -u > "$FRONTEND_CALLS"

frontend_count=$(wc -l < "$FRONTEND_CALLS")
echo -e "   Found ${GREEN}${frontend_count}${NC} frontend API calls"

# -----------------------------------------------------------
# STEP 3: Cross-reference — find gaps
# -----------------------------------------------------------
echo -e "${CYAN}[3/4] Cross-referencing...${NC}"
echo ""

MISSING=$(mktemp)
MATCHED=0
MISSING_COUNT=0

while IFS='|' read -r method path file lineno; do
  [ -z "$method" ] && continue
  # Normalize the path for matching
  norm_path=$(echo "$path" | sed -E 's/\{[^}]+\}/{*}/g')

  # Try exact match
  if grep -q "^${method} ${norm_path}$" "$BACKEND_ENDPOINTS" 2>/dev/null; then
    MATCHED=$((MATCHED + 1))
    continue
  fi

  # Try match with trailing slash variations
  alt_path="${norm_path%/}"
  [ "$alt_path" = "$norm_path" ] && alt_path="${norm_path}/"
  if grep -q "^${method} ${alt_path}$" "$BACKEND_ENDPOINTS" 2>/dev/null; then
    MATCHED=$((MATCHED + 1))
    continue
  fi

  # Check if it's a sub-path of an existing endpoint (e.g. /invoices/{*}/items under /invoices)
  # Only flag if no prefix match at all
  base=$(echo "$norm_path" | sed -E 's|/\{?\*?\}?$||; s|/[^/]+$||')
  if grep -q "^${method} ${norm_path}" "$BACKEND_ENDPOINTS" 2>/dev/null; then
    MATCHED=$((MATCHED + 1))
    continue
  fi

  # This is a gap
  MISSING_COUNT=$((MISSING_COUNT + 1))
  rel_file=$(echo "$file" | sed "s|^$FRONTEND/||")
  echo "${method}|${path}|${rel_file}|${lineno}" >> "$MISSING"
done < "$FRONTEND_CALLS"

# -----------------------------------------------------------
# STEP 4: Report
# -----------------------------------------------------------
echo -e "${BOLD}─────────────────────────────────────────${NC}"
echo -e "${BOLD}  RESULTS${NC}"
echo -e "${BOLD}─────────────────────────────────────────${NC}"
echo ""
echo -e "  Backend endpoints:   ${BOLD}${backend_count}${NC}"
echo -e "  Frontend API calls:  ${BOLD}${frontend_count}${NC}"
echo -e "  Matched:             ${GREEN}${BOLD}${MATCHED}${NC}"
echo -e "  Missing in backend:  ${RED}${BOLD}${MISSING_COUNT}${NC}"
echo ""

if [ "$MISSING_COUNT" -gt 0 ]; then
  echo -e "${RED}${BOLD}  MISSING ENDPOINTS:${NC}"
  echo -e "${BOLD}─────────────────────────────────────────${NC}"
  printf "  ${BOLD}%-7s %-42s %s${NC}\n" "METHOD" "ENDPOINT" "FILE:LINE"
  echo -e "  ─────────────────────────────────────────────────────────────────────────"

  sort -t'|' -k2 "$MISSING" | while IFS='|' read -r method path file lineno; do
    printf "  ${RED}%-7s${NC} %-42s ${YELLOW}%s:%s${NC}\n" "$method" "$path" "$file" "$lineno"
  done

  echo ""
  echo -e "${BOLD}─────────────────────────────────────────${NC}"

  # Check which ones are actually used (called from pages/components)
  echo ""
  echo -e "${CYAN}[4/4] Checking usage (dead code vs active)...${NC}"
  echo ""

  sort -t'|' -k2 "$MISSING" | while IFS='|' read -r method path file lineno; do
    # Check if this is in a service file
    if echo "$file" | grep -q "services/"; then
      # Extract function name around this line
      func_name=$(sed -n "${lineno}p" "$FRONTEND/$file" 2>/dev/null | grep -oP '\w+' | head -3 | tail -1 || true)
      # Search for callers in pages/components
      callers=$(grep -rl "$func_name" "$FRONTEND/pages" "$FRONTEND/components" 2>/dev/null | wc -l || echo 0)
      if [ "$callers" -eq 0 ]; then
        printf "  ${YELLOW}DEAD CODE${NC}  %-7s %-35s (0 callers)\n" "$method" "$path"
      else
        printf "  ${RED}ACTIVE${NC}     %-7s %-35s (%s callers)\n" "$method" "$path" "$callers"
      fi
    else
      printf "  ${RED}ACTIVE${NC}     %-7s %-35s (in page/component)\n" "$method" "$path"
    fi
  done
fi

echo ""

# Cleanup
rm -f "$BACKEND_ENDPOINTS" "$FRONTEND_CALLS" "$MISSING"

echo -e "${GREEN}Done.${NC}"
