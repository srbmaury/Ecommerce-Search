"""Tests for auth helper functions — experiment assignment and timing-safe password check."""

import pytest
from collections import Counter

from backend.controllers.auth_controller import (
    assign_experiment_group,
    constant_time_password_check,
    EXPERIMENT_GROUPS,
)
from backend.services.security import hash_password


class TestAssignExperimentGroup:
    def test_returns_valid_group(self):
        group = assign_experiment_group("u123abc")
        assert group in EXPERIMENT_GROUPS

    def test_same_user_always_same_group(self):
        uid = "u_deterministic_user"
        groups = {assign_experiment_group(uid) for _ in range(10)}
        assert len(groups) == 1

    def test_different_users_can_get_different_groups(self):
        results = {assign_experiment_group(f"u{i:06d}") for i in range(100)}
        assert len(results) > 1

    def test_distribution_is_roughly_equal(self):
        # With 1000 users, each group should have between 40% and 60% of assignments
        counts = Counter(assign_experiment_group(f"u{i:06d}") for i in range(1000))
        for g in EXPERIMENT_GROUPS:
            ratio = counts[g] / 1000
            assert 0.40 <= ratio <= 0.60, f"Group {g} has unbalanced ratio {ratio:.2%}"

    def test_handles_empty_string_user_id(self):
        # Should not raise
        group = assign_experiment_group("")
        assert group in EXPERIMENT_GROUPS


class TestConstantTimePasswordCheck:
    def test_correct_password_returns_true(self):
        pw = "SecurePass1@"
        h = hash_password(pw)
        assert constant_time_password_check(pw, h) is True

    def test_wrong_password_returns_false(self):
        h = hash_password("SecurePass1@")
        assert constant_time_password_check("WrongPass1@", h) is False

    def test_none_hash_returns_false(self):
        # user not found path: no hash, but we still run bcrypt to avoid timing leak
        assert constant_time_password_check("anypassword", None) is False

    def test_empty_password_returns_false(self):
        h = hash_password("SecurePass1@")
        assert constant_time_password_check("", h) is False
