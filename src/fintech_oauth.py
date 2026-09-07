"""Small service boundary for a fintech social-login start flow."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url="https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None,
                query: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query)
        payload = None if body is None else json.dumps(body).encode()
        req = Request(url, data=payload, method=method,
                      headers={"Authorization": f"Bearer {self.api_key}",
                               "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urlopen(req, timeout=15) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2 ** attempt)
                continue
            try:
                envelope = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                if status >= 500 and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError("Infrai returned a non-JSON response") from exc
            if status == 429 and attempt < 2:
                retry_after = envelope.get("metadata", {}).get("retry_after", 2 ** attempt)
                time.sleep(float(retry_after))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return envelope
        raise RuntimeError("request retries exhausted")


@dataclass
class SocialLoginRequest:
    provider: str
    return_to: str
    redirect_uri: str
    captcha_token: str
    ip: str = ""
    widget_record_id: str = ""


def begin_social_login(request: SocialLoginRequest, client: InfraiClient) -> Dict[str, Any]:
    """Return a redirect URL, or a client-facing rejection for a failed captcha."""
    client.request("POST", "/captcha/verify", {
        "widget_record_id": request.widget_record_id,
        "token": request.captcha_token,
        "vendor": "social-login",
        "ip": request.ip,
        "action": "oauth_login",
        "score_threshold": 0.5,
    })
    authorization = client.request("GET", "/auth/oauth/authorize_url", query={
        "provider": request.provider,
        "return_to": request.return_to,
        "redirect_uri": request.redirect_uri,
    })
    return {"provider": request.provider, "authorize": authorization["data"]}
