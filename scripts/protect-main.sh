#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo '用法：scripts/protect-main.sh gycrosskit/<仓库名> [...]' >&2
  exit 2
fi

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for repo in "$@"; do
  if [ "$(gh repo view "$repo" --json defaultBranchRef --jq '.defaultBranchRef.name')" != main ]; then
    echo "$repo 的默认分支不是 main，请先核对目标分支" >&2
    exit 1
  fi
  endpoint="repos/$repo/branches/main/protection"
  if current=$(gh api "$endpoint" --jq '[.required_pull_request_reviews != null, .enforce_admins.enabled, (.allow_force_pushes.enabled | not), (.allow_deletions.enabled | not)] | all' 2>/dev/null); then
    if [ "$current" != true ]; then
      echo "$repo 已有不同的保护规则，请人工检查，避免覆盖" >&2
      exit 1
    fi
    echo "$repo/main 已受保护"
  else
    result=$(gh api --method PUT "$endpoint" --input "$script_dir/../templates/main-protection.json" \
      --jq '"已保护 main：PR=" + (.required_pull_request_reviews != null | tostring) + ", admins=" + (.enforce_admins.enabled | tostring)')
    echo "$repo: $result"
  fi
done
