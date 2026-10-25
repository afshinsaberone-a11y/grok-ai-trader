"""Read-only GitHub Actions environment guard for the Capital Firewall release path.

This checks GitHub-hosted deployment-environment configuration only. It does not
inspect secrets, validate upstream source authorities, sign packets, create a
registry, issue a Grant, or authorize trading.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

SCHEMA = "forexai.capital_firewall.github_environment_audit.v1"
DEFAULT_ENVIRONMENT = "capital-firewall-production"
API_VERSION = "2022-11-28"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class EnvironmentAuditError(RuntimeError):
    """Sanitized configuration or API failure."""


def _blocked(code: str, *, environment: str, repo: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "BLOCKED",
        "reason": code,
        "repository": repo,
        "environment": environment,
        "scope": "GITHUB_ENVIRONMENT_CONFIGURATION_ONLY",
        "source_authorities_verified": False,
        "private_key_or_secret_inspected": False,
        "grant_issued": False,
        "orders_submitted": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
    }


def audit_configuration(
    environment_data: Mapping[str, Any],
    branch_policy_data: Mapping[str, Any],
    *,
    repo: str,
    actor: str,
    expected_reviewer: str,
    environment: str = DEFAULT_ENVIRONMENT,
) -> dict[str, Any]:
    """Validate only observable environment controls; fail closed on ambiguity."""
    def fail(reason: str) -> dict[str, Any]:
        return _blocked(reason, environment=environment, repo=repo)

    if not REPO_RE.fullmatch(repo):
        return fail("REPOSITORY_NAME_INVALID")
    owner = repo.split("/", 1)[0]
    if not LOGIN_RE.fullmatch(actor or ""):
        return fail("WORKFLOW_ACTOR_INVALID")
    if not LOGIN_RE.fullmatch(expected_reviewer or ""):
        return fail("EXPECTED_REVIEWER_INVALID")
    if expected_reviewer.casefold() in {owner.casefold(), actor.casefold()}:
        return fail("EXPECTED_REVIEWER_MUST_BE_DISTINCT_FROM_OWNER_AND_ACTOR")

    if environment_data.get("name") != environment:
        return fail("ENVIRONMENT_NAME_MISMATCH")

    # GitHub's environment API exposes this field even though not all API docs
    # list it. Missing is not interpreted as safe.
    if environment_data.get("can_admins_bypass") is not False:
        return fail("ADMIN_BYPASS_NOT_EXPLICITLY_DISABLED")

    protection_rules = environment_data.get("protection_rules")
    if not isinstance(protection_rules, list):
        return fail("PROTECTION_RULES_MISSING_OR_INVALID")
    reviewer_rules = [
        item for item in protection_rules
        if isinstance(item, Mapping) and item.get("type") == "required_reviewers"
    ]
    if len(reviewer_rules) != 1:
        return fail("EXACTLY_ONE_REQUIRED_REVIEWER_RULE_REQUIRED")
    reviewer_rule = reviewer_rules[0]
    if reviewer_rule.get("prevent_self_review") is not True:
        return fail("SELF_REVIEW_NOT_EXPLICITLY_PREVENTED")

    reviewers = reviewer_rule.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        return fail("REQUIRED_REVIEWER_LIST_EMPTY_OR_INVALID")

    configured_user_logins: list[str] = []
    for entry in reviewers:
        if not isinstance(entry, Mapping) or entry.get("type") != "User":
            # Team membership cannot be verified by this narrow read-only audit.
            return fail("ONLY_EXPLICIT_USER_REVIEWERS_ARE_AUDITABLE")
        user = entry.get("reviewer")
        login = user.get("login") if isinstance(user, Mapping) else None
        if not isinstance(login, str) or not LOGIN_RE.fullmatch(login):
            return fail("REVIEWER_IDENTITY_INVALID")
        if login.casefold() in {owner.casefold(), actor.casefold()}:
            return fail("OWNER_OR_WORKFLOW_ACTOR_IS_CONFIGURED_AS_REVIEWER")
        configured_user_logins.append(login)

    if expected_reviewer.casefold() not in {login.casefold() for login in configured_user_logins}:
        return fail("EXPECTED_REVIEWER_NOT_CONFIGURED")

    deployment_policy = environment_data.get("deployment_branch_policy")
    if not isinstance(deployment_policy, Mapping):
        return fail("DEPLOYMENT_BRANCH_POLICY_MISSING_OR_INVALID")
    if deployment_policy.get("protected_branches") is not False:
        return fail("DEPLOYMENT_BRANCH_POLICY_MUST_NOT_RELY_ON_UNVERIFIED_PROTECTION")
    if deployment_policy.get("custom_branch_policies") is not True:
        return fail("CUSTOM_DEPLOYMENT_BRANCH_POLICY_NOT_ENABLED")

    policies = branch_policy_data.get("branch_policies")
    if not isinstance(policies, list) or len(policies) != 1:
        return fail("EXACTLY_MAIN_DEPLOYMENT_BRANCH_REQUIRED")
    policy = policies[0]
    if not isinstance(policy, Mapping) or policy.get("name") != "main":
        return fail("DEPLOYMENT_BRANCH_MUST_BE_MAIN_ONLY")

    return {
        "schema": SCHEMA,
        "status": "PASS_CONFIGURATION_ONLY",
        "reason": None,
        "repository": repo,
        "environment": environment,
        "required_reviewer": expected_reviewer,
        "required_reviewer_count": len(configured_user_logins),
        "prevent_self_review": True,
        "can_admins_bypass": False,
        "deployment_branches": ["main"],
        "scope": "GITHUB_ENVIRONMENT_CONFIGURATION_ONLY",
        "source_authorities_verified": False,
        "private_key_or_secret_inspected": False,
        "grant_issued": False,
        "orders_submitted": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "note": "PASS verifies GitHub environment settings only; it does not prove independent custody or source readiness.",
    }


def _get_json(url: str, token: str) -> Mapping[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "ForexAI-Capital-Firewall-ReadOnly-Audit",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise EnvironmentAuditError("GITHUB_API_UNEXPECTED_STATUS")
            value = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        reasons = {401: "GITHUB_API_AUTHENTICATION_FAILED", 403: "GITHUB_API_ACCESS_DENIED", 404: "GITHUB_ENVIRONMENT_OR_BRANCH_POLICY_NOT_FOUND"}
        raise EnvironmentAuditError(reasons.get(exc.code, "GITHUB_API_REQUEST_FAILED")) from None
    except (URLError, TimeoutError, OSError):
        raise EnvironmentAuditError("GITHUB_API_UNAVAILABLE") from None
    except (UnicodeError, json.JSONDecodeError):
        raise EnvironmentAuditError("GITHUB_API_RESPONSE_INVALID") from None
    if not isinstance(value, Mapping):
        raise EnvironmentAuditError("GITHUB_API_RESPONSE_NOT_OBJECT")
    return value


def run_audit(
    *,
    repo: str,
    actor: str,
    expected_reviewer: str,
    token: str,
    environment: str = DEFAULT_ENVIRONMENT,
    api_base: str = "https://api.github.com",
) -> dict[str, Any]:
    if not REPO_RE.fullmatch(repo):
        return _blocked("REPOSITORY_NAME_INVALID", environment=environment, repo=repo)
    if not token or not token.strip():
        return _blocked("READ_ONLY_GITHUB_TOKEN_MISSING", environment=environment, repo=repo)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,99}", environment):
        return _blocked("ENVIRONMENT_NAME_INVALID", environment=DEFAULT_ENVIRONMENT, repo=repo)
    root = f"{api_base.rstrip('/')}/repos/{repo}"
    environment_url = f"{root}/environments/{quote(environment, safe='')}"
    branch_policy_url = f"{environment_url}/deployment-branch-policies"
    try:
        environment_data = _get_json(environment_url, token)
        branch_policy_data = _get_json(branch_policy_url, token)
    except EnvironmentAuditError as exc:
        return _blocked(str(exc), environment=environment, repo=repo)
    return audit_configuration(
        environment_data,
        branch_policy_data,
        repo=repo,
        actor=actor,
        expected_reviewer=expected_reviewer,
        environment=environment,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--actor", default=os.environ.get("GITHUB_ACTOR", ""))
    parser.add_argument("--expected-reviewer", default=os.environ.get("EXPECTED_REVIEWER", ""))
    parser.add_argument("--environment", default=DEFAULT_ENVIRONMENT)
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")
    report = run_audit(
        repo=args.repo,
        actor=args.actor,
        expected_reviewer=args.expected_reviewer,
        token=token,
        environment=args.environment,
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS_CONFIGURATION_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
