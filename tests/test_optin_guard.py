import hashlib
import pytest

from atlas.rpc.server import OptInGuard, AuthError


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def test_optin_guard_allows_when_not_required():
    g = OptInGuard(opt_in_required=False, opt_in_token_sha256="")
    g.check([])


def test_optin_guard_denies_without_token_when_required():
    g = OptInGuard(opt_in_required=True, opt_in_token_sha256=sha("secret"))
    with pytest.raises(AuthError):
        g.check([])


def test_optin_guard_accepts_correct_token():
    g = OptInGuard(opt_in_required=True, opt_in_token_sha256=sha("secret"))
    g.check([("x-opt-in-token", "secret")])


def test_optin_guard_rejects_wrong_token():
    g = OptInGuard(opt_in_required=True, opt_in_token_sha256=sha("secret"))
    with pytest.raises(AuthError):
        g.check([("x-opt-in-token", "nope")])
