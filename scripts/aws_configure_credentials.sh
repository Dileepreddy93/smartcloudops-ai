#!/usr/bin/env bash

set -euo pipefail

# Non-interactive AWS credentials configurator
# Priority for inputs:
# 1) CLI args
# 2) Environment variables
# 3) .env file at repo root (if present)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROFILE_NAME="${1:-${AWS_PROFILE:-smartcloudops}}"
AWS_REGION_INPUT="${2:-${AWS_DEFAULT_REGION:-us-east-1}}"

load_env_file() {
  local env_file="$REPO_ROOT/.env"
  if [[ -f "$env_file" ]]; then
    # shellcheck disable=SC2046
    export $(grep -E '^(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|AWS_DEFAULT_REGION)=' "$env_file" | xargs -d '\n') || true
  fi
}

ensure_aws_cli() {
  if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI not found. Installing locally via pip..."
    python3 -m pip install --user awscli >/dev/null
    export PATH="$HOME/.local/bin:$PATH"
  fi
  aws --version | cat
}

write_aws_files() {
  local credentials_dir="$HOME/.aws"
  mkdir -p "$credentials_dir"
  chmod 700 "$credentials_dir"

  local credentials_file="$credentials_dir/credentials"
  local config_file="$credentials_dir/config"

  # Write credentials
  if grep -q "^\[$PROFILE_NAME\]" "$credentials_file" 2>/dev/null; then
    # Remove existing profile block
    awk -v p="[$PROFILE_NAME]" 'BEGIN{skip=0} {if($0==p){print; getline; while($0!~/^\[/ && length($0)>0){getline} if(length($0)>0){print $0} skip=1; next} if(skip==1 && $0!~/^\[/){next} print}' "$credentials_file" >"$credentials_file.tmp" || true
    mv "$credentials_file.tmp" "$credentials_file"
  fi

  {
    echo "[$PROFILE_NAME]"
    echo "aws_access_key_id=$AWS_ACCESS_KEY_ID"
    echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"
    if [[ -n "${AWS_SESSION_TOKEN:-}" ]]; then
      echo "aws_session_token=$AWS_SESSION_TOKEN"
    fi
  } >> "$credentials_file"

  # Write config
  if ! grep -q "^\[profile $PROFILE_NAME\]" "$config_file" 2>/dev/null; then
    {
      echo "[profile $PROFILE_NAME]"
      echo "region = $AWS_REGION_INPUT"
      echo "output = json"
    } >> "$config_file"
  else
    # Update region/output if the profile exists
    awk -v p="[profile $PROFILE_NAME]" -v r="$AWS_REGION_INPUT" 'BEGIN{inblk=0} {
      if($0==p){print; inblk=1; next}
      if(inblk==1 && $0 ~ /^\[/){inblk=0}
      if(inblk==1 && $0 ~ /^region[[:space:]]*=/){print "region = " r; next}
      if(inblk==1 && $0 ~ /^output[[:space:]]*=/){print "output = json"; next}
      print
    }' "$config_file" > "$config_file.tmp" && mv "$config_file.tmp" "$config_file"
  fi

  chmod 600 "$credentials_file" "$config_file"
}

verify_identity() {
  echo "Verifying AWS identity for profile '$PROFILE_NAME'..."
  local ident
  if ! ident=$(aws sts get-caller-identity --profile "$PROFILE_NAME" --output json 2>/dev/null); then
    echo "ERROR: Failed to verify identity. Check your credentials and permissions." >&2
    exit 1
  fi
  echo "$ident" | jq -r '.Account + " " + .Arn' 2>/dev/null || echo "$ident"
}

main() {
  load_env_file

  : "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required (env or .env)}"
  : "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required (env or .env)}"
  export AWS_DEFAULT_REGION="$AWS_REGION_INPUT"

  ensure_aws_cli
  write_aws_files
  verify_identity

  echo "Configured AWS profile '$PROFILE_NAME' with region '$AWS_REGION_INPUT'."
}

main "$@"


