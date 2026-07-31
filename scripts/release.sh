#!/usr/bin/env bash
#
# release.sh
#
# Cuts a JAM release: verifies the tree and CI, creates an annotated tag,
# pushes it, and publishes a GitHub release.
#
# Usage
#   ./scripts/release.sh 1.0.0
#   ./scripts/release.sh 1.1.0 --notes "Adds the DecisionState contract."
#
# Options
#   --notes TEXT     Prepend a summary to the generated release notes
#   --draft          Create the release as a draft
#   --no-ci-check    Skip verifying that checks passed on the commit
#   --dry-run        Show what would happen without doing it
#   -h, --help       Show this message
#
# Releases exist so that other repositories can pin to a schema version rather
# than a commit. See standards/testing.md.

set -euo pipefail

VERSION=""
NOTES=""
DRAFT=0
CI_CHECK=1
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --notes)       NOTES="${2:-}"; [ -n "$NOTES" ] || { echo "error: --notes needs text" >&2; exit 2; }; shift 2 ;;
    --draft)       DRAFT=1; shift ;;
    --no-ci-check) CI_CHECK=0; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)            echo "error: unknown option $1" >&2; exit 2 ;;
    *)             [ -z "$VERSION" ] || { echo "error: give one version" >&2; exit 2; }; VERSION="$1"; shift ;;
  esac
done

say()  { printf '%s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }
sub()  { printf '    %s\n' "$*"; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
run()  { if [ "$DRY_RUN" -eq 1 ]; then say "    would run: $*"; else "$@"; fi; }

[ -n "$VERSION" ] || die "give a version, for example: ./scripts/release.sh 1.0.0"

VERSION="${VERSION#v}"
printf '%s' "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$' \
  || die "version must be MAJOR.MINOR.PATCH, for example 1.0.0"
TAG="v$VERSION"

# ---------------------------------------------------------------- preflight

step "Preflight"

command -v git >/dev/null 2>&1 || die "git is not installed"
command -v gh  >/dev/null 2>&1 || die "the GitHub CLI is not installed; see https://cli.github.com"
gh auth status >/dev/null 2>&1 || die "the GitHub CLI is not authenticated; run: gh auth login"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
cd "$REPO_ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "main" ] || die "releases are cut from main; you are on $BRANCH"

[ -z "$(git status --porcelain | grep -v -E '(apply-[^/]*|ship|release)\.sh$' || true)" ] \
  || die "working tree has uncommitted changes"

git fetch --quiet --tags origin || die "could not fetch from origin"

if [ -n "$(git log origin/main..main --oneline)" ]; then
  die "main has unpushed commits; push them first"
fi
if [ -n "$(git log main..origin/main --oneline)" ]; then
  die "main is behind origin; pull first"
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  die "$TAG already exists; tags are not reused"
fi

COMMIT="$(git rev-parse HEAD)"
sub "tag:    $TAG"
sub "commit: $(git rev-parse --short HEAD)"

# ------------------------------------------------------- version consistency

step "Checking version consistency"

SCHEMA="schemas/decision.schema.json"
if [ -f "$SCHEMA" ]; then
  SCHEMA_VERSION="$(grep -o '/decision/[0-9]\+\.[0-9]\+\.[0-9]\+/' "$SCHEMA" \
    | head -1 | tr -d '/' | sed 's/^decision//')"
  if [ -z "$SCHEMA_VERSION" ]; then
    sub "could not read a version from the schema \$id; skipping"
  elif [ "$SCHEMA_VERSION" = "$VERSION" ]; then
    sub "schema \$id declares $SCHEMA_VERSION, matching the tag"
  else
    die "the schema \$id declares $SCHEMA_VERSION but you are tagging $VERSION;
       update schemas/decision.schema.json and architecture/decision-object.md,
       or tag $SCHEMA_VERSION instead"
  fi
else
  sub "no Decision schema found; skipping"
fi

# --------------------------------------------------------------------- ci

step "Checking CI"

if [ "$CI_CHECK" -eq 0 ]; then
  sub "skipped (--no-ci-check)"
else
  WAITED=0
  CI_TIMEOUT="${CI_TIMEOUT:-300}"

  while :; do
    set +e
    RUNS="$(gh run list --commit "$COMMIT" --json status,conclusion,name \
      --jq '.[] | "\(.status)|\(.conclusion)|\(.name)"' 2>/dev/null)"
    rc=$?
    set -e

    if [ "$rc" -ne 0 ] || [ -z "$RUNS" ]; then
      sub "no runs found for this commit; releasing without that assurance"
      break
    fi

    PENDING="$(printf '%s\n' "$RUNS" | grep -vc '^completed|' || true)"

    if [ "$PENDING" -eq 0 ]; then
      printf '%s\n' "$RUNS" | awk -F'|' '{printf "      %-10s %s\n", $2, $3}'

      FAILED="$(printf '%s\n' "$RUNS" \
        | awk -F'|' '$2 != "success" && $2 != "skipped" && $2 != "neutral"' || true)"

      if [ -n "$FAILED" ]; then
        die "not every check succeeded on $COMMIT; fix them or pass --no-ci-check"
      fi

      sub "all runs succeeded"
      break
    fi

    if [ "$WAITED" -ge "$CI_TIMEOUT" ]; then
      die "$PENDING run(s) still going after ${WAITED}s; wait and retry, or pass --no-ci-check"
    fi

    sub "$PENDING run(s) still going (${WAITED}s)"
    sleep 10
    WAITED=$((WAITED + 10))
  done
fi

# -------------------------------------------------------------------- tag

step "Tagging"

TAG_MESSAGE="JAM $TAG

The architectural contracts in this release are stable. Repositories vendoring
schemas from JAM should record this tag as their pinned version."

if [ -n "$NOTES" ]; then
  TAG_MESSAGE="JAM $TAG

$NOTES"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  sub "would create annotated tag $TAG"
  sub "would push it to origin"
else
  git tag -a "$TAG" -m "$TAG_MESSAGE"
  sub "created $TAG"
  git push origin "$TAG"
  sub "pushed"
fi

# ---------------------------------------------------------------- release

step "Publishing"

RELEASE_ARGS=("$TAG" --title "JAM $TAG" --generate-notes)
[ "$DRAFT" -eq 1 ] && RELEASE_ARGS+=(--draft)
[ -n "$NOTES" ] && RELEASE_ARGS+=(--notes-start-tag "$TAG")

if [ "$DRY_RUN" -eq 1 ]; then
  sub "would publish a GitHub release for $TAG"
else
  gh release create "${RELEASE_ARGS[@]}" || die "the release was not created; the tag is pushed and can be reused with: gh release create $TAG --generate-notes"
  sub "published"
  gh release view "$TAG" --json url --jq .url | sed 's/^/      /'
fi

step "Done"
if [ "$DRY_RUN" -eq 1 ]; then
  sub "dry run only; nothing was tagged or published"
else
  sub "other repositories can now pin to $TAG"
fi
