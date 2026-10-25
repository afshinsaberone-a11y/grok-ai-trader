from __future__ import annotations

from copy import deepcopy

import pytest

from tools.audit_capital_firewall_github_environment_v1 import (
    SCHEMA,
    audit_configuration,
    run_audit,
)

REPO = "afshinsaberone-a11y/grok-ai-trader"
OWNER = "afshinsaberone-a11y"
ACTOR = OWNER
REVIEWER = "independent-reviewer"


def _environment():
    return {
        "name": "capital-firewall-production",
        "can_admins_bypass": False,
        "protection_rules": [
            {
                "type": "required_reviewers",
                "prevent_self_review": True,
                "reviewers": [
                    {
                        "type": "User",
                        "reviewer": {"login": REVIEWER, "id": 24680},
                    }
                ],
            }
        ],
        "deployment_branch_policy": {
            "protected_branches": False,
            "custom_branch_policies": True,
        },
    }


def _branch_policies():
    return {"total_count": 1, "branch_policies": [{"id": 1, "name": "main", "type": "branch"}]}


def _audit(environment=None, branches=None, **overrides):
    args = {
        "repo": REPO,
        "actor": ACTOR,
        "expected_reviewer": REVIEWER,
        "environment": "capital-firewall-production",
    }
    args.update(overrides)
    return audit_configuration(
        deepcopy(_environment() if environment is None else environment),
        deepcopy(_branch_policies() if branches is None else branches),
        **args,
    )


def test_valid_configuration_passes_but_does_not_assert_source_or_trading_authority():
    report = _audit()
    assert report["schema"] == SCHEMA
    assert report["status"] == "PASS_CONFIGURATION_ONLY"
    assert report["prevent_self_review"] is True
    assert report["can_admins_bypass"] is False
    assert report["deployment_branches"] == ["main"]
    assert report["source_authorities_verified"] is False
    assert report["private_key_or_secret_inspected"] is False
    assert report["grant_issued"] is False
    assert report["orders_submitted"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("can_admins_bypass", True, "ADMIN_BYPASS_NOT_EXPLICITLY_DISABLED"),
        ("can_admins_bypass", None, "ADMIN_BYPASS_NOT_EXPLICITLY_DISABLED"),
        ("name", "other-environment", "ENVIRONMENT_NAME_MISMATCH"),
    ],
)
def test_missing_or_unsafe_environment_fields_fail_closed(field, value, reason):
    environment = _environment()
    environment[field] = value
    report = _audit(environment=environment)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == reason
    assert report["grant_issued"] is False


def test_self_review_must_be_explicitly_prevented():
    environment = _environment()
    environment["protection_rules"][0]["prevent_self_review"] = False
    report = _audit(environment=environment)
    assert report["reason"] == "SELF_REVIEW_NOT_EXPLICITLY_PREVENTED"


def test_required_reviewer_must_be_known_external_user():
    environment = _environment()
    environment["protection_rules"][0]["reviewers"][0]["reviewer"]["login"] = OWNER
    report = _audit(environment=environment)
    assert report["reason"] == "OWNER_OR_WORKFLOW_ACTOR_IS_CONFIGURED_AS_REVIEWER"


def test_teams_are_rejected_because_membership_is_not_verified_by_this_audit():
    environment = _environment()
    environment["protection_rules"][0]["reviewers"] = [
        {"type": "Team", "reviewer": {"slug": "security-reviewers", "id": 99}}
    ]
    report = _audit(environment=environment)
    assert report["reason"] == "ONLY_EXPLICIT_USER_REVIEWERS_ARE_AUDITABLE"


def test_expected_reviewer_must_be_configured_and_not_owner_or_triggering_actor():
    report = _audit(expected_reviewer="another-reviewer")
    assert report["reason"] == "EXPECTED_REVIEWER_NOT_CONFIGURED"

    report = _audit(expected_reviewer=OWNER)
    assert report["reason"] == "EXPECTED_REVIEWER_MUST_BE_DISTINCT_FROM_OWNER_AND_ACTOR"


@pytest.mark.parametrize(
    ("branches", "reason"),
    [
        ({"total_count": 0, "branch_policies": []}, "EXACTLY_MAIN_DEPLOYMENT_BRANCH_REQUIRED"),
        ({"total_count": 2, "branch_policies": [{"name": "main"}, {"name": "release/*"}]}, "EXACTLY_MAIN_DEPLOYMENT_BRANCH_REQUIRED"),
        ({"total_count": 1, "branch_policies": [{"name": "release/*"}]}, "DEPLOYMENT_BRANCH_MUST_BE_MAIN_ONLY"),
    ],
)
def test_deployment_branch_policy_allows_only_main(branches, reason):
    report = _audit(branches=branches)
    assert report["reason"] == reason


def test_branch_policy_without_documented_type_is_partial_not_full_pass():
    branches = _branch_policies()
    del branches["branch_policies"][0]["type"]
    report = _audit(branches=branches)
    assert report["status"] == "PARTIAL_CONFIGURATION_REVIEW_REQUIRED"
    assert report["reason"] == "DEPLOYMENT_BRANCH_TAG_TYPE_NOT_EXPOSED_BY_DOCUMENTED_READ_API"
    assert report["deployment_branch_policy_type_status"] == "NOT_EXPOSED_BY_DOCUMENTED_READ_API"
    assert "DEPLOYMENT_BRANCH_TAG_TYPE_NOT_EXPOSED_BY_DOCUMENTED_READ_API" in report["verification_gaps"]
    assert report["grant_issued"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False


def test_tag_deployment_policy_is_rejected():
    branches = _branch_policies()
    branches["branch_policies"][0]["type"] = "tag"
    report = _audit(branches=branches)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "DEPLOYMENT_POLICY_IS_NOT_BRANCH"


def test_documented_github_environment_response_without_admin_bypass_field_is_partial():
    environment = _environment()
    del environment["can_admins_bypass"]
    report = _audit(environment=environment)
    assert report["status"] == "PARTIAL_CONFIGURATION_REVIEW_REQUIRED"
    assert report["reason"] == "ADMIN_BYPASS_NOT_EXPOSED_BY_DOCUMENTED_READ_API"
    assert report["admin_bypass_status"] == "NOT_EXPOSED_BY_DOCUMENTED_READ_API"
    assert report["can_admins_bypass"] is None
    assert report["grant_issued"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False


def test_api_token_is_required_and_never_reported():
    report = run_audit(
        repo=REPO,
        actor=ACTOR,
        expected_reviewer=REVIEWER,
        token="",
    )
    assert report["reason"] == "READ_ONLY_GITHUB_TOKEN_MISSING"
    assert "token" not in report


def test_invalid_repo_is_rejected_before_network_access():
    report = run_audit(
        repo="https://github.com/owner/repo",
        actor=ACTOR,
        expected_reviewer=REVIEWER,
        token="not-a-real-token",
    )
    assert report["reason"] == "REPOSITORY_NAME_INVALID"
