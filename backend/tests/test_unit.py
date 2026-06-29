"""Dependency-light unit tests (no DB needed) for security + tier logic."""
from app.core.security import (
    hash_password, verify_password, create_access_token, decode_token,
)
from app.services.override_service import required_rank
from app.core.deps import ROLE_RANK


def test_password_roundtrip():
    h = hash_password("s3cret")
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    tok, jti = create_access_token("u1", "c1", "admin")
    payload = decode_token(tok)
    assert payload["sub"] == "u1"
    assert payload["company_id"] == "c1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
    assert payload["jti"] == jti


def test_approval_tiers():
    assert required_rank(5) == ROLE_RANK["viewer"]    # auto
    assert required_rank(20) == ROLE_RANK["planner"]  # manager
    assert required_rank(40) == ROLE_RANK["admin"]    # manager+director
    assert required_rank(80) == ROLE_RANK["admin"]    # executive
