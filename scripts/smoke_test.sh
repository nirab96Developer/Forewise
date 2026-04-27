#!/usr/bin/env bash
# Phase 3 Wave 2.6 — post-deploy smoke test.
#
# Run after every deploy to verify the basic surface is alive:
#   1. /health           returns 200 ok
#   2. /version          returns the expected version + a real git SHA
#   3. /health/deep      returns 200 with database=ok + alembic_head
#   4. /api/v1/auth/login responds (401 expected with no creds — proves
#                                  the auth router is mounted)
#   5. /api/v1/dashboard/summary returns 401 with no auth header
#                                (proves the auth middleware is wired)
#
# Usage:
#   scripts/smoke_test.sh                          # http://localhost:8000
#   BASE=https://forewise.co scripts/smoke_test.sh # production
#
# Exits 0 on full pass, 1 on any failure. Designed to be CI-friendly.

set -uo pipefail

BASE="${BASE:-http://localhost:8000}"
EXPECTED_VERSION="${EXPECTED_VERSION:-1.1.0}"
PASS=0
FAIL=0

color() { tput setaf "$1" 2>/dev/null || true; }
reset() { tput sgr0 2>/dev/null || true; }

check() {
  local name="$1"; shift
  printf "  %-55s" "$name"
  if "$@"; then
    color 2; printf "PASS\n"; reset
    PASS=$((PASS + 1))
  else
    color 1; printf "FAIL\n"; reset
    FAIL=$((FAIL + 1))
  fi
}

assert_status() {
  local url="$1"; local expected="$2"
  local actual
  actual="$(curl -sS -o /dev/null -w "%{http_code}" "$url" || echo "000")"
  [[ "$actual" == "$expected" ]] || {
    echo "      url=$url expected=$expected actual=$actual" >&2
    return 1
  }
}

assert_body_contains() {
  local url="$1"; local needle="$2"
  local body
  body="$(curl -sS "$url" || echo "")"
  [[ "$body" == *"$needle"* ]] || {
    echo "      url=$url missing needle=$needle body=$body" >&2
    return 1
  }
}

echo
echo "Forewise smoke test against: $BASE"
echo "Expected version: $EXPECTED_VERSION"
echo

# 1. /health — light, anonymous
check "/health returns 200" \
  assert_status "$BASE/health" "200"
check "/health body has status=ok" \
  assert_body_contains "$BASE/health" '"status":"ok"'
check "/health body has expected version" \
  assert_body_contains "$BASE/health" "\"version\":\"$EXPECTED_VERSION\""

# 2. /version — anonymous, build metadata
check "/version returns 200" \
  assert_status "$BASE/version" "200"
check "/version body has expected version" \
  assert_body_contains "$BASE/version" "\"version\":\"$EXPECTED_VERSION\""
check "/version body has git_sha field" \
  assert_body_contains "$BASE/version" '"git_sha"'
check "/version body has build_time field" \
  assert_body_contains "$BASE/version" '"build_time"'
check "/version body has environment field" \
  assert_body_contains "$BASE/version" '"environment"'
# Defense — no secret-shaped fields
check "/version body has no 'password' field" \
  bash -c "! curl -sS '$BASE/version' | grep -qi 'password'"
check "/version body has no 'postgresql://' string" \
  bash -c "! curl -sS '$BASE/version' | grep -q 'postgresql://'"

# 3. /health/deep — ops health probe
check "/health/deep returns 200 (DB up)" \
  assert_status "$BASE/health/deep" "200"
check "/health/deep body has database=ok" \
  assert_body_contains "$BASE/health/deep" '"database":"ok"'
check "/health/deep body has alembic_head" \
  assert_body_contains "$BASE/health/deep" '"alembic_head"'
check "/health/deep body has app=ok" \
  assert_body_contains "$BASE/health/deep" '"app":"ok"'

# 4. /api/v1/auth/login — auth router mounted
# 422 = validation error on empty body; 401 = wrong creds; either proves
# the route is reachable and handles input correctly.
check "/api/v1/auth/login responds (422 on empty body)" \
  assert_status "$BASE/api/v1/auth/login" "405"  # GET on a POST route
# Try POST with empty body — expect 422 from FastAPI validation
post_status="$(curl -sS -o /dev/null -w '%{http_code}' \
                -X POST -H 'Content-Type: application/json' \
                -d '{}' "$BASE/api/v1/auth/login" || echo '000')"
check "/api/v1/auth/login POST empty → 422" \
  bash -c "[[ '$post_status' == '422' ]]"

# 5. /api/v1/dashboard/summary — auth middleware wired
check "/api/v1/dashboard/summary returns 401 (no auth)" \
  assert_status "$BASE/api/v1/dashboard/summary" "401"

# Summary
echo
total=$((PASS + FAIL))
if [[ "$FAIL" == "0" ]]; then
  color 2; echo "Smoke test PASSED ($PASS/$total checks)"; reset
  exit 0
else
  color 1; echo "Smoke test FAILED ($FAIL/$total checks failed, $PASS/$total passed)"; reset
  exit 1
fi
