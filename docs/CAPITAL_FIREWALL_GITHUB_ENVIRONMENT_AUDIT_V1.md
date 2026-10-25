# Capital Firewall GitHub Environment Audit v1

**Status:** proposed read-only gate; not production authorization. It does not create or modify any GitHub environment, reviewer, secret, key, registry, source packet, Grant, or trading permission.

## Why this gate exists

A GitHub environment is not trusted merely because a workflow references its name. A missing environment can be auto-created with no protection rules. This audit calls GitHub's read-only environment APIs and fails closed unless the named environment exists and the observable controls are exact.

It checks:
- `capital-firewall-production` exists;
- if `can_admins_bypass` is returned, it must be explicitly `false`; the documented GitHub GET-environment response currently omits this field, so the audit reports a partial result instead of inventing a full pass;
- exactly one required-reviewer rule is configured;
- `prevent_self_review=true`;
- the selected expected reviewer is an explicitly named GitHub user and is not the repository owner or person who started the audit;
- the environment does not list the repository owner or current actor as reviewers;
- custom deployment branch policy is enabled and its sole pattern is exactly `main`.

It deliberately rejects teams because this small audit does not establish team membership. The user dispatching the workflow must supply the expected independent reviewer's login; the script verifies configuration against that input but does **not** prove the human's identity, account custody, employment/independence, or administrative access.

## Run it

After this proposed change has been reviewed and merged, open **Actions → ForexAI Capital Firewall GitHub Environment Audit v1 → Run workflow** on `main`. Enter the login of the independently appointed reviewer (not `afshinsaberone-a11y` and not your own login). The workflow uses a read-only `GITHUB_TOKEN` limited to `actions: read` and `contents: read`. It performs HTTP GET only.

Expected result with the documented GitHub API shape is `PARTIAL_CONFIGURATION_REVIEW_REQUIRED`: reviewer/self-review/branch controls may pass, but administrator-bypass prevention is not exposed by the documented GET response and must be verified manually in repository Settings. The workflow deliberately exits nonzero rather than treating this unknown as safe. `PASS_CONFIGURATION_ONLY` is possible only if an API response explicitly provides `can_admins_bypass=false`. Even that result does **not** inspect environment-secret values or verify that a Grant key is absent; it does not inspect repository rulesets/branch protection, host administration, the Grant private key, source authorities, current G13 evidence, or the durable anti-replay registry.

## Keep the secret boundary intact

- Never place the Grant private key or passphrase in GitHub Actions secrets or on the self-hosted MT5 runner.
- The audit's workflow token is read-only; no workflow input can change the environment, secret values, branch policy, or repository protection.
- If required observable environment controls are missing or ambiguous, the script returns `BLOCKED` and exits nonzero. If administrator-bypass prevention is not exposed by the API, it returns `PARTIAL_CONFIGURATION_REVIEW_REQUIRED` and exits nonzero. Only explicit API evidence of `can_admins_bypass=false` can clear that programmatic check.
- A second account under the same unrestricted administrator is not proof of independent custody. A passing configuration audit is not a substitute for a genuinely independent administrator/reviewer.
- The existing real Promotion fingerprint mismatch and the non-provisioned Signal, Risk + durable Reservation, and Operator sources remain separate blockers. Do not issue a Grant or authorize a trade based on this audit.

## Relevant GitHub API contracts

The implementation uses the documented read-only [deployment environment endpoint](https://docs.github.com/en/rest/deployments/environments) and [deployment branch policy endpoint](https://docs.github.com/en/rest/deployments/branch-policies). Required reviewers, self-review prevention, and administrator-bypass settings must be configured manually by an authorized repository administrator; this patch intentionally contains no write call for these settings.
