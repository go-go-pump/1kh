#!/bin/bash
# fix-codecommit-creds.sh
# Fixes the recurring 403 error with AWS CodeCommit HTTPS credentials.
#
# Root cause: macOS system git configures osxkeychain as a credential helper.
# This caches stale passwords and prevents the AWS credential-helper from running.
#
# This script:
#   1. Removes ALL codecommit entries from macOS Keychain
#   2. Reconfigures ~/.gitconfig so the AWS helper is used (not osxkeychain)

set -euo pipefail

SERVER="git-codecommit.us-east-1.amazonaws.com"
KEYCHAIN="$HOME/Library/Keychains/login.keychain-db"

echo "=== Step 1: Remove all CodeCommit entries from Keychain ==="
while security find-internet-password -s "$SERVER" "$KEYCHAIN" &>/dev/null; do
  security delete-internet-password -s "$SERVER" "$KEYCHAIN" 2>/dev/null && \
    echo "  Deleted one entry" || break
done
echo "  Done — no more entries for $SERVER"

echo ""
echo "=== Step 2: Fix ~/.gitconfig ==="
# The correct config is:
#   [credential]
#       helper =                              <-- clears system osxkeychain
#       UseHttpPath = true
#       helper = !aws codecommit credential-helper $@
#
# The blank "helper =" MUST come first to override the system-level osxkeychain.

cat > "$HOME/.gitconfig" << 'GITCONFIG'
[credential]
	helper =
	UseHttpPath = true
	helper = !aws codecommit credential-helper $@
GITCONFIG
echo "  Updated ~/.gitconfig"

echo ""
echo "=== Step 3: Verify ==="
echo "  Credential helpers (should show blank line then aws helper):"
git config --get-all credential.helper
echo ""
echo "  Testing AWS credentials..."
if aws sts get-caller-identity &>/dev/null; then
  echo "  AWS CLI session is valid"
else
  echo "  WARNING: AWS CLI session may be expired. Run: aws sso login"
fi

echo ""
echo "=== Done ==="
echo "Try: git push"
