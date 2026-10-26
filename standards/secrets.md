# Secrets

Version: 1.0

## Purpose

This standard defines where credentials and private state live, and where
they may never be, across every BarelySmash repository and host.

The platform is one person's; the standard is still written as if it were
not, because the failure it prevents — a key in a commit, a token in a
release archive, Gmail content on GitHub — is the same either way and cannot
be undone.

---

## Never in the repository

- No secret value is ever committed: API keys, tokens, OAuth credentials and
  refresh tokens, bearer secrets, passwords, private URLs that embed any of
  them.
- `.gitignore` excludes `*.env`, `.env`, `env/`, `*client_secret*.json` and
  the repository's token files. A template is the one exception
  (`!*.template`).
- No private *state* is committed either: mailbox content, operating
  records, account identifiers, anything a workload accumulates about the
  business. Atlas's RestaurantOS state is the reference case.
- Release archives are `git archive HEAD` ([Deployment](deployment.md)),
  so nothing ignored can enter one. That is the construction the rule
  rests on; it is not a reason to relax the ignore list.

A secret that was committed, even briefly, is rotated. History rewriting
does not substitute for rotation.

---

## The template is committed; the file is not

Every repository that needs secrets ships a template beside where the real
file goes (`deploy/env.template`): every variable the service reads, with a
blank value or a safe default, grouped and commented — which are required,
which are optional and for what. The template is documentation; it is kept
current when a variable is added or retired.

Registries that depend on a secret name the **variable**, never the value
(`requires_env: [TAVILY_API_KEY]` in the JARVIS agent registry). A component
whose variables are unset is skipped at load with that reason, not crashed
and not given a default.

---

## On the host

Two placements, chosen by who owns the secret:

**Service-account secrets** — what one service needs to run — live in that
service's persistent state, owned by the service user:

```
~/<repo>-data/env/<repo>.env        mode 600, owner ocelia
EnvironmentFile=%h/<repo>-data/env/<repo>.env     in every unit of that service
```

They are host state, not release artifacts: a deploy verifies the file exists
and never writes it, and a rollback leaves it alone. The first install may
adopt a legacy release-local file into this place; after that, the host copy
is the only one.

**Shared or system-level secrets** — a key several services or a utility
agent use, provisioned by an admin — live under `/etc`:

```
/etc/<service>/secrets.env          mode 640, owner root:<service-group>
EnvironmentFile=/etc/<service>/secrets.env
```

The service user reads through group membership; it cannot write. A loader
that references such a file tolerates its absence (the agent loads with the
optional keys unset) so the registry entry is safe to commit before the
admin step has happened.

Private state files (OAuth tokens, synced records) live under
`~/<repo>-data/` with the same ownership, and are transferred to the host
**out of band** — streamed over SSH by a dedicated script — never through
GitHub and never inside a release.

---

## Locally

Developers keep a `.env` in the repository root, ignored, loaded by
`python-dotenv` when present. Code must run without it: a missing `.env` is
the normal state on the host, where the unit's `EnvironmentFile=` has
already set the environment.

---

## Between services

Services on the same host talk over loopback (`127.0.0.1`) and authenticate
with a shared bearer secret where the call can change state — the cockpit's
`/api/events` ingest, for example — passed as `Authorization: Bearer <token>`
and configured through the same environment files on both sides. An unset
token disables the endpoint rather than opening it.

---

## Rotation

Rotating a secret is: change the value in the host file, restart the units
that read it. Nothing is redeployed. The template does not change.

---

## Enforcement

| Rule | Kind |
| --- | --- |
| Nothing ignored enters a release | Tooling — `git archive HEAD` |
| `*.env` and token files ignored; template committed | Tooling — `.gitignore`; Convention for the template's currency |
| Registries name variables, never values; unset means skipped | Tooling — the loaders |
| Host file modes and owners | Tooling — the install scripts set them |
| Private state transferred out of band | Convention — and the ignore list, which keeps it out of the archive regardless |

A check that fails CI when a tracked file matches the ignore patterns is cheap
and worth adding to each repository; until it exists this standard is
convention at the repository boundary.
