#!/usr/bin/env bash
#
# ship.sh
#
# Takes one or more branches from local commits to merged: pushes, opens a
# pull request, waits for checks to finish, merges, and cleans up.
#
# Usage
#   ./ship.sh                        Ship the current branch
#   ./ship.sh feat/adr               Ship one named branch
#   ./ship.sh feat/adr chore/x       Ship several, in order
#
# Options
#   --base NAME        Base branch to merge into (default: main)
#   --strategy NAME    merge, squash, or rebase (default: merge)
#   --no-wait          Merge without waiting for checks
#   --keep-branch      Do not delete the branch after merging
#   --grace SECONDS    How long to wait for checks to appear (default: 90)
#   --dry-run          Show what would happen without doing it
#   -h, --help         Show this message
#
# Requires the GitHub CLI, authenticated. Install from https://cli.github.com
# then run: gh auth login
#
# Safe to re-run. If a pull request already exists it is reused, and a branch
# that is already merged is skipped rather than failing.

set -euo pipefail

BASE="main"
STRATEGY="merge"
WAIT=1
DELETE_BRANCH=1
GRACE=90
DRY_RUN=0
BRANCHES=()

while [ $# -gt 0 ]; do
  case "$1" in
    --base)        BASE="${2:-}";     [ -n "$BASE" ]     || { echo "error: --base needs a name" >&2; exit 2; }; shift 2 ;;
    --strategy)    STRATEGY="${2:-}"; [ -n "$STRATEGY" ] || { echo "error: --strategy needs a value" >&2; exit 2; }; shift 2 ;;
    --grace)       GRACE="${2:-}";    [ -n "$GRACE" ]    || { echo "error: --grace needs a number" >&2; exit 2; }; shift 2 ;;
    --no-wait)     WAIT=0; shift ;;
    --keep-branch) DELETE_BRANCH=0; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)            echo "error: unknown option $1" >&2; exit 2 ;;
    *)             BRANCHES+=("$1"); shift ;;
  esac
done

case "$STRATEGY" in
  merge|squash|rebase) ;;
  *) echo "error: --strategy must be merge, squash, or rebase" >&2; exit 2 ;;
esac

say()  { printf '%s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }
sub()  { printf '    %s\n' "$*"; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    say "    would run: $*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------- preflight

command -v git >/dev/null 2>&1 || die "git is not installed"
command -v gh  >/dev/null 2>&1 || die "the GitHub CLI is not installed; see https://cli.github.com"

gh auth status >/dev/null 2>&1 || die "the GitHub CLI is not authenticated; run: gh auth login"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die "not inside a git repository"
cd "$REPO_ROOT"

if [ ${#BRANCHES[@]} -eq 0 ]; then
  CURRENT="$(git rev-parse --abbrev-ref HEAD)"
  [ "$CURRENT" != "$BASE" ] || die "you are on $BASE; name a branch to ship, or check one out"
  BRANCHES=("$CURRENT")
fi

step "Plan"
sub "repository: $(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || echo "$REPO_ROOT")"
sub "base:       $BASE"
sub "strategy:   $STRATEGY"
sub "branches:   ${BRANCHES[*]}"
[ "$DRY_RUN" -eq 1 ] && sub "mode:       dry run"

git fetch --quiet --prune origin || die "could not fetch from origin"

# ------------------------------------------------------------------ helpers

branch_exists() {
  git show-ref --verify --quiet "refs/heads/$1"
}

already_merged() {
  git merge-base --is-ancestor "$1" "origin/$BASE" 2>/dev/null
}

pr_number_for() {
  gh pr list --head "$1" --state open --json number --jq '.[0].number' 2>/dev/null
}

# Wait for checks to be registered, then watch them to completion.
wait_for_checks() {
  local branch="$1"
  local waited=0
  local out rc

  while :; do
    set +e
    out="$(gh pr checks "$branch" 2>&1)"
    rc=$?
    set -e

    if printf '%s' "$out" | grep -qi "no checks reported"; then
      if [ "$waited" -ge "$GRACE" ]; then
        sub "no checks reported after ${waited}s; merging without them"
        return 0
      fi
      sub "waiting for checks to start (${waited}s)"
      sleep 5
      waited=$((waited + 5))
      continue
    fi
    break
  done

  sub "watching checks"
  set +e
  gh pr checks "$branch" --watch
  rc=$?
  set -e

  if [ "$rc" -ne 0 ]; then
    say ""
    gh pr checks "$branch" || true
    die "checks did not pass on $branch; nothing was merged"
  fi

  sub "checks passed"
}

# --------------------------------------------------------------------- ship

SHIPPED=()
SKIPPED=()

for BRANCH in "${BRANCHES[@]}"; do
  step "Shipping $BRANCH"

  if [ "$BRANCH" = "$BASE" ]; then
    sub "this is the base branch; skipping"
    SKIPPED+=("$BRANCH")
    continue
  fi

  if ! branch_exists "$BRANCH" && ! git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
    die "branch $BRANCH does not exist locally or on origin"
  fi

  if already_merged "$BRANCH"; then
    sub "already merged into $BASE; nothing to do"
    SKIPPED+=("$BRANCH")
    continue
  fi

  # Push, and set upstream if it is missing.
  if branch_exists "$BRANCH"; then
    if git rev-parse --abbrev-ref "$BRANCH@{upstream}" >/dev/null 2>&1; then
      if [ -n "$(git log "origin/$BRANCH..$BRANCH" --oneline 2>/dev/null)" ]; then
        sub "pushing new commits"
        run git push origin "$BRANCH"
      else
        sub "already up to date on origin"
      fi
    else
      sub "pushing and setting upstream"
      run git push -u origin "$BRANCH"
    fi
  fi

  # Open a pull request, or reuse the open one.
  PR="$(pr_number_for "$BRANCH" || true)"
  if [ -n "${PR:-}" ] && [ "$PR" != "null" ]; then
    sub "reusing open pull request #$PR"
  elif [ "$DRY_RUN" -eq 1 ]; then
    sub "would open a pull request against $BASE"
    PR="(dry run)"
  else
    sub "opening a pull request against $BASE"
    gh pr create --base "$BASE" --head "$BRANCH" --fill >/dev/null
    PR="$(pr_number_for "$BRANCH" || true)"
    [ -n "${PR:-}" ] && [ "$PR" != "null" ] || die "the pull request was not created"
    sub "opened #$PR"
  fi

  # Checks.
  if [ "$WAIT" -eq 0 ]; then
    sub "not waiting for checks (--no-wait)"
  elif [ "$DRY_RUN" -eq 1 ]; then
    sub "would wait for checks"
  else
    wait_for_checks "$BRANCH"
  fi

  # Merge. Move off the branch first so the local delete succeeds.
  if [ "$DRY_RUN" -eq 1 ]; then
    sub "would merge #$PR with --$STRATEGY"
  else
    if [ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ]; then
      git checkout --quiet "$BASE"
    fi

    MERGE_ARGS=("--$STRATEGY")
    [ "$DELETE_BRANCH" -eq 1 ] && MERGE_ARGS+=("--delete-branch")

    gh pr merge "$PR" "${MERGE_ARGS[@]}" || die "merging #$PR failed"
    sub "merged #$PR"
  fi

  SHIPPED+=("$BRANCH")
done

# ------------------------------------------------------------------ cleanup

step "Cleaning up"

if [ "$DRY_RUN" -eq 1 ]; then
  sub "would return to $BASE and pull"
else
  git checkout --quiet "$BASE"
  git pull --quiet --ff-only origin "$BASE" || sub "could not fast-forward $BASE; pull by hand"
  git fetch --quiet --prune origin
  sub "on $BASE at $(git rev-parse --short HEAD)"
fi

step "Summary"
[ ${#SHIPPED[@]} -gt 0 ] && sub "shipped: ${SHIPPED[*]}"
[ ${#SKIPPED[@]} -gt 0 ] && sub "skipped: ${SKIPPED[*]}"

REMAINING="$(git branch -r --format='%(refname:short)' \
  | grep -v -E "^origin\$|origin/(HEAD|$BASE)\$" || true)"
if [ -n "$REMAINING" ]; then
  sub "branches still open on origin:"
  printf '%s\n' "$REMAINING" | sed 's/^/      /'
else
  sub "no other branches on origin"
fi
