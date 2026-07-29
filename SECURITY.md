# Security Policy

## Scope

`helios-solver` is a research codebase for trajectory optimization. It does
not run as a network service and does not handle user credentials or
personal data. That said, dependency vulnerabilities, unsafe deserialization
of data files, or arbitrary code execution issues in tooling (CI config,
notebooks, pre-commit hooks) are all in scope.

## Reporting a Vulnerability

**Please do not open a public issue for security reports.**

Instead, use GitHub's private reporting flow:
[Security Advisories → Report a vulnerability](../../security/advisories/new).
This opens a private conversation with the maintainer that isn't visible to
the public until a fix is available.

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce (a minimal script or test case is ideal).
- The affected version/commit.

## Response

This is a solo-maintained research project without a formal SLA. Expect an
initial response within a few days. Confirmed vulnerabilities will be fixed
and disclosed via a GitHub Security Advisory; credit is given unless you
request otherwise.

## Supported Versions

Pre-1.0: only the `main` branch is supported. There are no maintained release
branches yet.
