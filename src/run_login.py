import json
import os
import sys

from fintech_oauth import InfraiClient, SocialLoginRequest, begin_social_login, InfraiError


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python src/run_login.py <google|github>")
        return 2
    try:
        result = begin_social_login(SocialLoginRequest(
            provider=sys.argv[1],
            return_to=os.environ.get("RETURN_TO", "https://localhost:8000/complete"),
            redirect_uri=os.environ.get("REDIRECT_URI", "https://localhost:8000/oauth/callback"),
            captcha_token=os.environ.get("CAPTCHA_TOKEN", ""),
            ip=os.environ.get("CLIENT_IP", ""),
            widget_record_id=os.environ.get("WIDGET_RECORD_ID", ""),
        ), InfraiClient())
    except InfraiError as exc:
        print(json.dumps({"accepted": False, "error": exc.code}))
        return 1
    print(json.dumps({"accepted": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
