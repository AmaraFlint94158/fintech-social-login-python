import pytest

from src.fintech_oauth import InfraiError, SocialLoginRequest, begin_social_login


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, body=None, query=None):
        self.calls.append((method, path, body, query))
        if path.endswith("captcha/verify"):
            raise InfraiError("captcha_rejected", {"code": "captcha_rejected"}, 422)
        return {"ok": True, "data": {"url": "https://accounts.example/authorize"}}


def test_rejected_captcha_is_a_client_decision():
    client = FakeClient()
    request = SocialLoginRequest("google", "/dashboard", "https://app.test/callback", "token")
    with pytest.raises(InfraiError) as error:
        begin_social_login(request, client)
    assert error.value.status == 422
    assert len(client.calls) == 1
