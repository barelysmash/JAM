# JAM Conformance

Version: 1.0

## Purpose

JAM is the engineering and architectural reference for every repository in the
BarelySmash Intelligence Platform.

A repository that declares JAM conformance commits to following the applicable
architecture, terminology, contracts, and engineering standards published by
JAM.

JAM is the source of truth. Individual repositories implement the standard;
they do not redefine it.

## Applicability

JAM conformance applies to:

- JARVIS
- Atlas
- Friday
- Muse
- Foundation
- RestaurantOS
- BarelyTrade
- future BarelySmash engines and applications

A standard applies when it is relevant to the repository's language, role, and
runtime.

## Required Declaration

A conforming repository must include the following statement in its README:

> Built with JAM — the JARVIS Architecture Manual.

The statement must link to the JAM repository or identify its canonical
repository location.

## Required Practices

A conforming repository must:

1. Declare its platform role.
2. Define what it owns and explicitly does not own.
3. Keep domain reasoning within the responsible engine.
4. Use versioned contracts at repository boundaries.
5. Follow the applicable JAM repository, Git, language, testing, and prompt
   standards.
6. Record justified exceptions in the repository.
7. Require human approval wherever the domain contract requires it.
8. avoid copying JAM architecture explanations into repository documentation;
   link to JAM instead.

## Independence

JAM conformance does not require repositories to:

- share a database;
- share a deployment;
- import one another's internal modules;
- release on the same schedule;
- depend on JARVIS at runtime.

Engines remain independently deployable and independently testable.

## Exceptions

A repository may deviate from a JAM standard when necessary.

The exception must be documented with:

- the applicable JAM standard;
- the reason for the deviation;
- the scope of the deviation;
- whether the deviation is temporary or permanent;
- the intended remediation, when temporary.

Material or expensive-to-reverse exceptions require an ADR.

## Verification

Conformance begins as a documented commitment.

JAM should progressively automate checks that can be enforced reliably,
including:

- required README declarations;
- repository metadata;
- schema validation;
- language and test configuration;
- contract versioning;
- prohibited architectural coupling.

Prefer tooling to CI, and CI to convention.

---

BarelySmash

Observe. Understand. Decide. Learn. Repeat.
