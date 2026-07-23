#!/bin/bash
set -euo pipefail

# Hermes Verification Script
# Usage: sudo bash scripts/verify.sh

SOURCE_DIR="/opt/hermes/sembako-dashboard"
PASS=0
FAIL=0

pass() { echo "✓ $1"; ((PASS++)); }
fail() { echo "✗ $1"; ((FAIL++)); }

echo "=== Hermes Acceptance Tests ==="
echo ""

# AT-01: Git
echo "AT-01: Git"
cd "$SOURCE_DIR"
if git rev-parse HEAD &>/dev/null; then
    pass "Git repository valid"
    COMMIT=$(git rev-parse HEAD)
    echo "  Commit: $COMMIT"
else
    fail "Git repository not valid"
fi
echo ""

# AT-02: Dependency
echo "AT-02: Dependency"
if [[ -f "$SOURCE_DIR/.venv/bin/python" ]]; then
    PYTHON_VERSION=$("$SOURCE_DIR/.venv/bin/python" --version 2>&1)
    pass "Virtual environment exists ($PYTHON_VERSION)"
    if "$SOURCE_DIR/.venv/bin/pip" check &>/dev/null; then
        pass "No broken dependencies"
    else
        fail "Broken dependencies detected"
    fi
else
    fail "Virtual environment not found"
fi
echo ""

# AT-03: Service
echo "AT-03: Service"
if systemctl is-enabled hermes-dashboard &>/dev/null; then
    pass "hermes-dashboard service enabled"
else
    fail "hermes-dashboard service not enabled"
fi

if systemctl is-active hermes-dashboard &>/dev/null; then
    pass "hermes-dashboard service active"
else
    fail "hermes-dashboard service not active"
fi
echo ""

# AT-04: Local Health Check
echo "AT-04: Local Health Check"
if curl -fsS http://127.0.0.1:5000/api/health 2>/dev/null | grep -q "healthy"; then
    pass "Health endpoint returns healthy"
else
    fail "Health endpoint not responding"
fi
echo ""

# AT-05: Nginx
echo "AT-05: Nginx"
if nginx -t 2>&1 | grep -q "syntax is okay"; then
    pass "Nginx configuration valid"
else
    fail "Nginx configuration invalid"
fi
echo ""

# AT-06: Endpoint Data
echo "AT-06: Endpoint Data"
ENDPOINTS=("sembako" "crypto" "emas" "pertanian" "summary")
for endpoint in "${ENDPOINTS[@]}"; do
    if curl -fsS "http://127.0.0.1/api/$endpoint" 2>/dev/null | grep -q .; then
        pass "Endpoint /$endpoint responds"
    else
        fail "Endpoint /$endpoint not responding"
    fi
done
echo ""

# AT-07: Timer
echo "AT-07: Timer"
if systemctl list-timers --all | grep -q hermes-update; then
    pass "hermes-update timer exists"
else
    fail "hermes-update timer not found"
fi

if systemctl list-timers --all | grep -q hermes-backup; then
    pass "hermes-backup timer exists"
else
    fail "hermes-backup timer not found"
fi
echo ""

# Summary
echo "=== Summary ==="
echo "PASSED: $PASS"
echo "FAILED: $FAIL"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi

echo "All tests passed!"
