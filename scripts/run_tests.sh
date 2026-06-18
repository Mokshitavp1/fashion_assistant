#!/usr/bin/env bash
set -euo pipefail
TESTS_PATH=${1:-backend/tests}

# Export env var expected by tests
export EMAIL_VERIFICATION_REQUIRED=true
echo "EMAIL_VERIFICATION_REQUIRED=$EMAIL_VERIFICATION_REQUIRED"

python -m pytest "$TESTS_PATH" -q
