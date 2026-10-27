# Provider source-signer allowlist eligibility report v1

## Purpose

The Provider Source-built Wheel Candidate workflow builds **review-only** dependencies from exact upstream source commits. This check compares the exact source-build manifest and produced wheel digests against an externally signed trust-registry bundle's approved source-signer allowlist.

The workflow writes `artifacts/provider-source-build/source-signer-eligibility-report.json` and uploads it alongside the candidate artifacts.

## Optional public review inputs

The workflow reads these public GitHub Actions repository variables:

- `FOREXAI_TRUST_REGISTRY_BUNDLE_BASE64`: base64-encoded signed public trust-registry bundle (maximum decoded size 1 MiB).
- `FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY`: raw Ed25519 root public key encoded as canonical base64.
- `FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT`: independently recorded `sha256:<64 lowercase hex>` root-key fingerprint.
- `FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256`: exact bundle digest pin.

These inputs are public verification material only. Do not put a private key or passphrase in these variables. A missing bundle, malformed bundle, missing pin, mismatched digest/signature, empty signer allowlist, unapproved signer record, source tuple mismatch, signer fingerprint mismatch, or wheel digest mismatch produces a `BLOCKED` report. It is never converted to a pass by a GitHub Actions success status.

## Meaning of outcomes

- `PASS_SOURCE_SIGNER_ALLOWLIST_MATCH`: every source tuple and wheel/bootstrap digest in this candidate matches the signed bundle's currently valid signer allowlist. **This is eligibility evidence only; it does not approve a production install.**
- `BLOCKED`: a required input or verification predicate is missing or invalid. The candidate artifacts may still be uploaded for independent review, but the report records that source-signer eligibility was not established.

Every report hard-pins `production_approved=false`, `bootstrap_approved=false`, and `trading_authorization_created=false`.

## Limits and production boundary

This GitHub-hosted report does not independently prove real-world reviewer independence or key custody. Production verification must continue to use root public-key/fingerprint and exact bundle-digest pins administered outside the source repository on the controlled Provider boundary. The source-built candidate wheelhouse remains separate from the accepted root dependency locks; this workflow does not deploy it, replace the accepted locks, issue a Grant, authorize Demo/Live, or submit orders.

A valid report therefore cannot replace independent full-source review, a clean independent Windows rebuild/hash comparison, or the separately provisioned Promotion Attestor, Signal Source, Risk Engine/reservation, Operator Approval, and Capital Firewall Grant authority.
