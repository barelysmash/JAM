# Deployment

Version: 1.0

## Purpose

This standard defines how a BarelySmash service reaches its host and how it
is taken back off again. It is written from the two deployments that exist —
JARVIS and Atlas on Guildenstern — and binds the next one to the same shape,
so that an operator who knows one knows all of them.

---

## Host model

One host, one unprivileged service account, no sudo in the loop.

- Services run as a dedicated user (`ocelia` on Guildenstern) under
  `systemctl --user`. Linger is enabled once, by an admin
  (`loginctl enable-linger`), so services survive logout and start at boot.
- Everything a deploy does afterwards runs as that user. A deploy that needs
  `sudo` is a one-time host setup step, documented in the repository's
  `deploy/README.md`, not part of the deploy.
- Hosts are reached over the private network (Tailscale). Nothing listens on a
  public interface.

---

## Layout on the host

Every service owns four paths, named after its repository:

```
~/<repo>-releases/<repo>-YYYYMMDD-HHMMSS/   immutable release directories
~/<repo>                                   symlink to the current release
~/<repo>-previous                          symlink to the rollback release
~/<repo>-data/                             persistent state; never part of a release
```

- **A release is a `git archive HEAD` of the repository.** Only tracked files
  can enter it; untracked and ignored local files are excluded by
  construction. Build artifacts a release requires (a compiled HUD) are
  produced and verified before the release is installed, and the install
  refuses a release that lacks them.
- **State lives outside the release**, under `~/<repo>-data/`: databases,
  logs, tokens, routine state, event logs. Deploys and rollbacks never touch
  it. Where code expects state at a relative path, the install symlinks into
  `~/<repo>-data/` rather than copying.
- **The private environment lives there too**: `~/<repo>-data/env/<repo>.env`,
  mode 600, referenced by every unit as `EnvironmentFile=`. See
  [Secrets](secrets.md).
- **The interpreter**: a release owns its own virtual environment where it
  can (`~/atlas/.venv`), so a rollback reverts code and dependencies
  together. A repository that shares one interpreter across releases
  (`~/jarvis-venv`) records that in its `deploy/README.md`, because its
  rollback does not revert dependencies.

---

## Install, swap, verify

An install is:

1. unpack the release into `~/<repo>-releases/`;
2. create or update the interpreter and install dependencies;
3. create the persistent data directories if absent, symlink them in;
4. **atomically swap** `~/<repo>` to the new release, moving the old target
   to `~/<repo>-previous`;
5. install the release's `deploy/systemd/*.service` and `*.timer` into
   `~/.config/systemd/user/`, `daemon-reload`, then reconcile: restart
   running services, enable and start new ones, enable or disable timers
   per the registry, and retire units the registry no longer names;
6. verify — a health endpoint or a `systemctl --user is-active` — and report.

A running install is never modified in place. The symlink swap is the only
moment the host changes what it runs.

**Rollback** is the same swap in reverse — `~/<repo>` and `~/<repo>-previous`
exchange targets, services restart — and it must work without network
access to GitHub. The last five releases are kept for it.

---

## Units are generated or registered, never hand-written on the host

What runs on the host is declared in the repository and installed from the
release:

- JARVIS: `config/routines.yaml` renders `deploy/systemd/jarvis-routine-*`
  (CI checks the rendering is current); `scripts/install_routine_units.sh`
  installs, enables, disables and retires them.
- Atlas: `deploy/workloads.toml` declares each workload's data directories,
  required private files, services and timers; deploy and rollback both
  reconcile systemd from the active release's registry.

A unit file edited directly in `~/.config/systemd/user/` is a drift the next
deploy erases. That is intended.

---

## The deploy command

Each repository has **one** deploy entry point, run from a developer machine
on an up-to-date `main`:

- it refuses to run with uncommitted changes;
- it pushes, so the host pulls what GitHub has, never what the developer's
  tree has;
- it installs, swaps, reconciles units and verifies, in that order;
- it prints the one command to check when verification fails.

JARVIS additionally has a fast path (`./deploy.sh`) for a host that keeps a
git checkout: push → `git pull --ff-only` → install routine units → restart →
health check. It is the path used day to day; the release-directory path is
what rollback is built on. A repository offering both says which is which.

Deploy from `main` only. A branch is deployed by merging it.

---

## What a repository must document

`deploy/README.md` in every deployed repository states: the host layout above
with the repository's own names; the one-time admin steps; the deploy and
rollback commands; the units installed and what each is for; where the
private environment file lives and which template it is filled from.

---

## Enforcement

| Rule | Kind |
| --- | --- |
| Release = `git archive HEAD`; state outside the release; symlink swap | Tooling — the install scripts |
| Units generated from a registry and current in the tree | CI (JARVIS) / Tooling (Atlas) |
| No uncommitted work deployed; deploy from `main` | Tooling — the deploy script's preflight |
| `deploy/README.md` contents | Convention |
