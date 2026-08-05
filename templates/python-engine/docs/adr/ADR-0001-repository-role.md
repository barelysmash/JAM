# ADR-0001: Repository Role

Status: Accepted

## Context

{{PROJECT_NAME}} is part of the BarelySmash Intelligence Platform and conforms
to JAM.

The repository requires an explicit domain boundary so its responsibilities do
not drift into orchestration, unrelated engines, applications, or shared
infrastructure.

## Decision

{{PROJECT_NAME}} serves as:

> {{PLATFORM_ROLE}}

The repository remains independently deployable and independently testable.

It owns its domain reasoning and state while communicating across repository
boundaries through explicit, versioned contracts.

## Consequences

Positive:

- domain ownership remains local;
- runtime coupling to JARVIS is not required;
- repository releases remain independent;
- cross-repository integration uses stable contracts.

Negative:

- shared behavior must be promoted into JAM or Foundation deliberately;
- duplicated domain reasoning across repositories is prohibited;
- contract evolution requires explicit versioning.
