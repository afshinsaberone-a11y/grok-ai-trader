#!/usr/bin/env bash
# One-time, fail-closed filesystem/account bootstrap for a newly provisioned
# Ubuntu LTS Capital Firewall signer host. This does not install or activate a signer.
set -Eeuo pipefail
umask 077

readonly RUNTIME_USER="capital-firewall"
readonly DATA_ROOT="/var/lib/capital-firewall"
readonly HOST_CONFIRM_PHRASE=""

fail() {
  printf 'CAPITAL_FIREWALL_HOST_BOOTSTRAP=BLOCKED reason=%s\n' "$1" >&2
  exit 2
}

[[ "${EUID}" -eq 0 ]] || fail "MUST_RUN_AS_ROOT"
[[ -r /etc/os-release ]] || fail "OS_RELEASE_NOT_FOUND"
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == "ubuntu" ]] || fail "UNSUPPORTED_OS"
case "${VERSION_ID:-}" in
  "22.04"|"24.04") ;;
  *) fail "UNSUPPORTED_UBUNTU_VERSION" ;;
esac
[[ -t 0 ]] || fail "INTERACTIVE_TTY_REQUIRED"

# Deliberately refuse to adopt pre-existing identities or data. Review them
# manually instead of recursively changing ownership or permissions in place.
if getent passwd "$RUNTIME_USER" >/dev/null 2>&1; then
  fail "RUNTIME_IDENTITY_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED"
fi
if [[ -e "$DATA_ROOT" || -L "$DATA_ROOT" ]]; then
  fail "DATA_ROOT_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED"
fi

hostname_value="$(hostname --fqdn 2>/dev/null || hostname)"
[[ -n "$hostname_value" ]] || fail "HOSTNAME_UNAVAILABLE"
printf 'Target host: %s\n' "$hostname_value"
printf 'This creates one locked runtime identity and empty protected directories only.\n'
printf 'It does NOT create keys, registry/database, source packet, Grant, service, or trading permission.\n'
printf 'Type the exact target hostname to confirm: '
IFS= read -r typed_hostname
[[ "$typed_hostname" == "$hostname_value" ]] || fail "HOSTNAME_CONFIRMATION_MISMATCH"

# No SSH, firewall, package, cloud, key, database, or trading configuration is
# changed here. Those changes require reviewed, provider-specific operations.
useradd --system --user-group --home-dir "$DATA_ROOT" --no-create-home \
  --shell /usr/sbin/nologin "$RUNTIME_USER"

install -d -o "$RUNTIME_USER" -g "$RUNTIME_USER" -m 0700 "$DATA_ROOT"
for child in keys in out state; do
  install -d -o "$RUNTIME_USER" -g "$RUNTIME_USER" -m 0700 "$DATA_ROOT/$child"
done

# Verify the effective identity and filesystem controls without displaying secrets.
passwd_record="$(getent passwd "$RUNTIME_USER")" || fail "RUNTIME_IDENTITY_VERIFICATION_FAILED"
IFS=: read -r found_user _ found_uid found_gid _ found_home found_shell <<< "$passwd_record"
[[ "$found_user" == "$RUNTIME_USER" ]] || fail "RUNTIME_USERNAME_MISMATCH"
[[ "$found_uid" =~ ^[0-9]+$ && "$found_uid" -ge 1 ]] || fail "RUNTIME_UID_INVALID"
[[ "$found_home" == "$DATA_ROOT" ]] || fail "RUNTIME_HOME_MISMATCH"
[[ "$found_shell" == "/usr/sbin/nologin" ]] || fail "RUNTIME_SHELL_NOT_LOCKED"

for path in "$DATA_ROOT" "$DATA_ROOT/keys" "$DATA_ROOT/in" "$DATA_ROOT/out" "$DATA_ROOT/state"; do
  [[ ! -L "$path" && -d "$path" ]] || fail "PROTECTED_PATH_INVALID"
  owner="$(stat -c '%U' -- "$path")"
  group="$(stat -c '%G' -- "$path")"
  mode="$(stat -c '%a' -- "$path")"
  [[ "$owner" == "$RUNTIME_USER" && "$group" == "$RUNTIME_USER" ]] || fail "PROTECTED_PATH_OWNER_MISMATCH"
  [[ "$mode" == "700" ]] || fail "PROTECTED_PATH_MODE_MISMATCH"
  [[ -z "$(find "$path" -mindepth 1 -maxdepth 1 -print -quit)" ]] || fail "UNEXPECTED_PREEXISTING_CONTENT"
done

printf 'CAPITAL_FIREWALL_HOST_BOOTSTRAP=PASS_EMPTY_LAYOUT_ONLY\n'
printf 'HOSTNAME=%s\n' "$hostname_value"
printf 'RUNTIME_USER=%s\n' "$RUNTIME_USER"
printf 'DATA_ROOT=%s\n' "$DATA_ROOT"
printf 'KEYS_CREATED=0\nREGISTRY_CREATED=0\nSOURCE_PACKET_CREATED=0\nGRANT_ISSUED=0\n'
printf 'SERVICE_INSTALLED=0\nORDERS_SUBMITTED=0\nDEMO_AUTHORIZED=0\nLIVE_ENABLED=0\n'
