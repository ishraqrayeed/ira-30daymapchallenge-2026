#!/usr/bin/env bash
# Run in an internet-connected terminal. No tokens are stored by this script.
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
account="ishraqrayeed"
repository="$account/ira-30daymapchallenge-2026"

command -v gh >/dev/null || { echo "Install GitHub CLI first: brew install gh"; exit 1; }
if ! login="$(gh api user --jq .login)"; then
  echo "GitHub authentication could not be verified. Run: gh auth login --hostname github.com --web --git-protocol https --scopes repo,workflow"
  exit 1
fi
if [[ "$login" != "$account" ]]; then
  echo "Expected $account, but GitHub CLI is using $login."
  echo "Run: gh auth switch --hostname github.com --user $account"
  exit 1
fi

python3 scripts/build_pages.py
python3 -m unittest discover -s tests -q
if command -v node >/dev/null; then node tests/test_map_controls.js; fi

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  [[ "$git_root" == "$project_root" ]] || { echo "Project is inside a different Git repository; stopping."; exit 1; }
else
  git init -b main
fi

if ! git config user.name >/dev/null; then git config user.name "$account"; fi
if ! git config user.email >/dev/null; then
  user_id="$(gh api user --jq .id)"
  git config user.email "$user_id+$account@users.noreply.github.com"
fi

if origin="$(git remote get-url origin 2>/dev/null)"; then
  case "$origin" in
    "https://github.com/$repository"|"https://github.com/$repository.git"|"git@github.com:$repository.git") ;;
    *) echo "Origin points to $origin rather than $repository; stopping."; exit 1 ;;
  esac
fi

# Stage only the intended project paths; source caches and local settings stay out.
git add -- .gitignore .github README.md PLAN.md \
  LICENSE requirements.txt environment.yml src scripts templates assets tests maps docs flagship \
  data/raw/.gitkeep data/interim/.gitkeep data/processed/.gitkeep
# Retire the tracked setup plan while keeping its local archive ignored.
if git ls-files --error-unmatch -- 30DayMapChallenge_2026_CODEX_PLAN.md >/dev/null 2>&1; then
  git add -u -- 30DayMapChallenge_2026_CODEX_PLAN.md
fi
if ! git diff --cached --quiet; then
  git commit -m "Publish Someone Was Walking Here and update project documentation"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  if gh repo view "$repository" --json name >/dev/null 2>&1; then
    git remote add origin "https://github.com/$repository.git"
  else
    gh repo create "$repository" --public --source . --remote origin \
      --description "30DayMapChallenge 2026: reproducible transportation and geospatial portfolio"
  fi
fi
branch="$(git branch --show-current)"
[[ "$branch" == main ]] || { echo "Expected the main branch, found $branch; stopping before push."; exit 1; }
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push -u origin main

if gh api "repos/$repository/pages" --silent 2>/dev/null; then
  gh api --method PUT "repos/$repository/pages" -f build_type=workflow --silent
else
  gh api --method POST "repos/$repository/pages" -f build_type=workflow --silent
fi
gh workflow run pages.yml --repo "$repository" --ref main
head_commit="$(git rev-parse HEAD)"
run_id=""
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  run_id="$(gh run list --repo "$repository" --workflow pages.yml --event workflow_dispatch \
    --commit "$head_commit" --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
  [[ -n "$run_id" ]] && break
  sleep 2
done
if [[ -z "$run_id" ]]; then
  echo "Deployment dispatched. Track it at https://github.com/$repository/actions"
  exit 0
fi
gh run watch "$run_id" --repo "$repository" --exit-status
site_url="$(gh api "repos/$repository/pages" --jq .html_url)"
echo "Published: $site_url"
