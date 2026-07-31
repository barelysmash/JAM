# Testing Standards

Version: 1.0

## Purpose

This standard defines what must be tested across the BarelySmash platform, and
to what depth.

It is built around one observation: the failure most likely to hurt this
platform is not a bug inside a repository. It is a contract breaking between
them — Atlas shipping a reasoning change that quietly alters the shape of what
it emits, and JARVIS discovering it in production.

Most of what follows is ordinary practice. The contract test is the part that
matters.

---

## Framework

pytest. Not `unittest`.

Fixtures and `parametrize` are the reason. Most of what needs testing here is
table-driven — a contract with many valid and invalid shapes — and pytest
expresses that in a fraction of the code.

```
tests/                          Mirrors the src/ structure.
tests/conftest.py               Shared fixtures.
tests/test_<module>.py          Unit tests.
tests/contracts/                Contract tests and pinned schemas.
```

Test functions are named `test_<what>_<condition>_<expectation>`. A failing test
name should tell you what broke without opening the file.

---

## The Contract Test

**Every repository that emits or consumes Decision objects carries a contract
test.** This is not optional and is not waived for early-stage repositories.

The test takes representative output the repository actually produces — not
handwritten fixtures — and validates it against the Decision schema.

```python
def test_emitted_decisions_satisfy_the_contract(validator, sample_decisions):
    for decision in sample_decisions:
        errors = list(validator.iter_errors(decision))
        assert not errors, format_errors(decision, errors)
```

The samples must come from the real emission path. A test that validates a
fixture someone wrote by hand proves the fixture is well-formed and nothing
about the engine.

Consumers test the other direction: given a valid Decision at the schema version
they claim to support, the consumer handles it — including the parts of the
contract that are easy to forget. Unknown enum values degrade gracefully.
Unknown fields are ignored. Both are required by the specification and neither
happens by accident.

### Pinning the schema

Repositories vendor the schema they validate against, under
`tests/contracts/`, alongside a note recording which version of JAM it came
from.

Vendoring rather than fetching is deliberate. A test that reaches the network is
a test that fails when the network does, and a schema that updates silently
turns an unrelated CI run red for reasons nobody asked for. Refreshing the
vendored copy is a deliberate act with its own commit.

> **Open:** JAM does not publish tagged releases yet. When it does, the
> vendored copy should become a pinned dependency and this section should be
> revised.

---

## What Must Be Tested

**Contracts.** Covered above. Mandatory.

**Business logic.** Anything that decides, calculates, or transforms. If it
could be wrong in a way that matters, it has a test.

**Error paths.** The branch that handles a malformed response or a missing field
is the branch least likely to be exercised in development and most likely to run
at three in the morning.

**Boundaries.** Empty collections, single elements, the confidence floor exactly
at 0.30, `expires_at` exactly equal to `created_at`. Off-by-one lives here.

**Regressions.** Every bug that reaches `main` gets a test reproducing it,
committed alongside the fix. This is the cheapest test to justify and the one
most often skipped.

## What Need Not Be Tested

Third-party libraries. Trivial accessors. Generated code. Configuration with no
logic in it.

Testing these inflates coverage while proving nothing, which is exactly the
failure the next section is about.

---

## Coverage

The floor is **70%**, enforced in CI.

An honest statement of what that number is worth: not much. Coverage measures
which lines executed, not whether anything was asserted about them. It passes
for a test suite that calls every function and checks nothing, and it drops when
dead code is deleted, which is an improvement.

It is kept because it detects rot. A repository drifting from 85% to 60% is
telling you something, even if the absolute number means little.

So the floor is set low enough to be a floor rather than a target. Do not chase
it upward by testing accessors. If coverage is low in a module that matters, the
problem is the missing tests, and the number is a symptom rather than the thing
to fix.

**The contract test is the real gate.** A repository at 95% coverage without one
is less safe than a repository at 70% with one.

---

## Determinism

A test that fails once a week is worse than no test, because it teaches everyone
to re-run CI instead of reading it.

**Freeze time.** Never assert against `datetime.now()`. Inject a clock or use
`freezegun`.

**Seed randomness.** ULID generation and any sampling get a fixed seed, or the
identifier is injected.

**No network.** Unit tests do not make network calls. Integration tests that do
are marked and excluded from the default run:

```python
@pytest.mark.integration
def test_against_the_live_broker_sandbox(): ...
```

```
pytest -m "not integration"        # default, runs in CI
pytest -m integration              # run deliberately
```

**No shared mutable state between tests.** Order dependence is discovered at the
worst possible time, usually when a single test is run in isolation to debug
something else.

---

## Running Them

The command CI runs is the command a developer runs. If reproducing a CI failure
requires a different invocation, someone will debug by pushing commits.

```
pytest -m "not integration" --cov --cov-fail-under=70
```

The repository README documents this command.

---

## Core Principle

> Coverage tells you what ran.
>
> The contract test tells you whether the platform still fits together.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
