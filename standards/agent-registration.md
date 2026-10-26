# Agent Registration

Version: 1.0

## Purpose

This standard defines how an engine or a utility agent becomes something
JARVIS can route to. It is the mechanical half of the star pattern in
[Ecosystem Architecture](../architecture/ecosystem.md): JARVIS coordinates,
and nothing domain-specific is added to JARVIS itself.

---

## The registry

Every component JARVIS can reach is one entry in `config/agents.yaml` in
jarvis-v2, loaded at startup by `orchestrator/agents.py`. If it is not in the
registry, JARVIS cannot call it. If it is, nothing else in JARVIS had to
change.

An entry:

```yaml
agents:
  friday:
    description: >
      Friday — trading intelligence. Analysis-only peer service on
      127.0.0.1:8082; forecasts and scans, no brokerage execution.
    transport: adapter
    module: tools.integrations.friday
    class: FridayAdapter
    requires_env: [FRIDAY_API_TOKEN]
```

| Field | Meaning |
| --- | --- |
| `description` | One paragraph: what it is, where it runs, what it will **not** do. This is what the router and the operator read. |
| `transport` | `adapter` or `mcp-stdio` (below). |
| `requires_env` | Variable names that must be set, or the agent is skipped with that reason. Names only, never values ([Secrets](secrets.md)). |
| `enabled` | `false` parks an agent without deleting its entry. Default `true`. |

Entries are declared in the order they should be loaded and listed. The
name is the prefix every tool the agent contributes is registered under, so
it is short, lowercase and stable.

---

## Two transports

**`adapter`** — an in-process class that wraps a peer service.

```yaml
transport: adapter
module: tools.integrations.<name>
class: <Name>Adapter
```

The class has a no-argument constructor and a `register(tools)` method that
registers its tools. The adapter is thin: it holds the base URL and token
from the environment, makes HTTP calls to the peer, and shapes results. It
contains no domain reasoning — that stays in the peer service, in the peer's
own repository.

**`mcp-stdio`** — an MCP server launched as a child process.

```yaml
transport: mcp-stdio
command: /home/ocelia/jarvis-venv/bin/python
args: ["-m", "sparrow.server"]
env_file: /etc/sparrow/secrets.env       # optional; ignored if absent
tools:                                   # optional allowlist; omit = all
  - find_free_assets
  - check_license
```

JARVIS spawns the process, initializes the MCP session, discovers its tools,
and registers the allowed ones under the agent's prefix. The `tools:`
allowlist is the contract: a server may grow new tools without JARVIS
exposing them until the registry says so.

The peer code lives in the agent's own repository and is installed into the
host interpreter; the registry references it by command, not by path into
jarvis-v2.

---

## Loading

Each entry loads independently, at startup, and records a status:

| Status | When |
| --- | --- |
| `loaded` | Tools registered. |
| `skipped` | `requires_env` unmet, or an unknown transport — with the reason. |
| `disabled` | `enabled: false`. |
| `failed` | The import, spawn or handshake raised — with the exception. |

**One agent's failure never blocks the rest.** The registry snapshot (name,
description, transport, status, reason, tools) is what the cockpit draws —
one node per entry, lit only when `loaded` — so a skipped or failed agent is
visible at a glance rather than silently absent.

---

## Boundaries an entry must respect

- **Same host, loopback.** A peer service binds to `127.0.0.1` (or the
  Tailscale interface); nothing JARVIS routes to is reachable from outside
  the host network.
- **Say what it will not do.** An agent that touches money, mail or the
  outside world states its limit in `description` and enforces it in the
  peer, not in JARVIS: Friday is analysis-only with no brokerage execution;
  BarelySwing arms and disarms the engine but execution stays manual.
- **Results cross a source boundary.** What a peer returns is attributed to
  it in the executive's grounding, never presented as JARVIS's own finding.
- **No domain logic in jarvis-v2.** An adapter that starts reasoning about
  its domain is a sign the logic belongs in the peer's repository.

---

## Adding an agent

1. Build the peer in its own repository: an HTTP service (adapter) or an MCP
   stdio server (`mcp-stdio`). It conforms to JAM like any other repository.
2. Install it on the host — into the host interpreter for `mcp-stdio`, or as
   its own `systemctl --user` service for a peer HTTP service
   ([Deployment](deployment.md)).
3. Add its variables to `deploy/env.template` and the host's environment
   file, or its `secrets.env` under `/etc` ([Secrets](secrets.md)).
4. For an adapter, add the thin class under `tools/integrations/`.
5. Add the registry entry. Deploy. Check the cockpit shows it `loaded`.

Retiring one is `enabled: false` first, deletion later.

---

## Enforcement

| Rule | Kind |
| --- | --- |
| Registry is the only route in; independent loading; status recorded | Tooling — `orchestrator/agents.py` |
| `requires_env` names only; skip on unmet | Tooling — the loader |
| Allowlisted MCP tools | Tooling — the loader |
| Loopback binding; stated limits; no domain logic in adapters | Convention — reviewed in the pull request that adds the entry |
