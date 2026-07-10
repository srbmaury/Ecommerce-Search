"""Tests for backend/utils/config.py — URL normalization and database URL resolution."""

import os
import pytest
from unittest.mock import patch

from backend.utils.config import _normalize_database_url, get_database_url


class TestNormalizeDatabaseUrl:
    def test_postgres_scheme_rewritten_to_postgresql(self):
        url = "postgres://user:pass@host:5432/db"
        result = _normalize_database_url(url)
        assert result.startswith("postgresql://")

    def test_postgresql_scheme_unchanged(self):
        url = "postgresql://user:pass@host:5432/db"
        assert _normalize_database_url(url) == url

    def test_sqlite_url_unchanged(self):
        url = "sqlite:////tmp/dev.db"
        assert _normalize_database_url(url) == url

    def test_credentials_preserved(self):
        url = "postgres://alice:secret@db.example.com:5432/mydb"
        result = _normalize_database_url(url)
        assert "alice:secret" in result
        assert "db.example.com" in result
        assert "/mydb" in result

    def test_query_params_preserved(self):
        url = "postgres://user:pw@host/db?sslmode=require"
        result = _normalize_database_url(url)
        assert "sslmode=require" in result

    def test_port_preserved(self):
        url = "postgres://user:pw@host:5433/db"
        result = _normalize_database_url(url)
        assert "5433" in result

    def test_path_only_sqlite_unchanged(self):
        url = "sqlite:///relative/path.db"
        assert _normalize_database_url(url) == url


class TestGetDatabaseUrl:
    def test_returns_env_var_when_set(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://u:p@host/db"}):
            url = get_database_url()
        assert url == "postgresql://u:p@host/db"

    def test_normalizes_postgres_scheme_from_env(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgres://u:p@host/db"}):
            url = get_database_url()
        assert url.startswith("postgresql://")

    def test_falls_back_to_sqlite_when_no_env(self):
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            url = get_database_url()
        assert url.startswith("sqlite:///")

    def test_sqlite_fallback_points_to_data_dir(self):
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            url = get_database_url()
        assert "ecommerce.db" in url

    def test_returns_string(self):
        url = get_database_url()
        assert isinstance(url, str)
        assert len(url) > 0
