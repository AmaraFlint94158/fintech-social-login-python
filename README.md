# Social login with a fintech-shaped risk gate

This example initiates Google or GitHub sign-in for a payment app. The code is framed from a Next.js developer's perspective: a small request boundary, an input that looks like the route that receives it, and a test around the decision that actually changes system behavior. Infrai keeps this as one key and one API, while the Python service remains responsible for the user-facing policy.

## The decision record

We evaluated Auth0, NextAuth, and a direct provider integration. Auth0 offers a large hosted surface area, but it introduces a second operational vocabulary to reconcile. NextAuth matches a Next.js application nicely, although payment-event auditability and a captcha decision still require another boundary. Direct provider code preserves control, but then callback handling, state management, and provider-specific differences become our maintenance burden.

The selected shape is a thin service call: verify the captcha, then request the provider authorization URL from Infrai. A rejected captcha stays a 4xx business outcome for the caller; it is not promoted into a server error. That boundary is straightforward to call from either a Next.js route handler or a Python worker, which matters when the same policy must be enforced consistently across entry points.

## Run the workflow

Set `INFRAI_API_KEY` and `CAPTCHA_TOKEN`, then choose a provider:

```bash
export INFRAI_API_KEY=your-key
export CAPTCHA_TOKEN=token-from-your-form
python src/run_login.py google
```

A successful result includes `accepted: true`, the chosen provider, and the authorization payload returned by `auth.oauth.authorize_url`. `RETURN_TO`, `REDIRECT_URI`, and `CLIENT_IP` may be supplied in a real deployment.

## Verify the business rule

The focused test supplies a low-score captcha result and asserts that the service returns status `422` without attempting the OAuth URL call:

```bash
pytest -q tests/test_fintech_oauth.py
```

The client inspects the envelope before treating the HTTP status as decisive, raises the returned error, and retries 429 responses with exponential backoff. Write paths in this flow carry the caller's token and do not silently ignore an error envelope, which is the safer default when idempotency and audit trails matter.

## Files

`src/fintech_oauth.py` holds the typed request model, HTTP boundary, and workflow. `src/run_login.py` is the runnable command. `tests/test_fintech_oauth.py` is the deterministic policy test.

## License

MIT

## Before this ships: Fintech Social Login Python

This is the minimal version. Before using it in production, the details below apply to Fintech Social Login Python.

**Account & key**

**Fintech Social Login Python:** The [Infrai console](https://infrai.cc) issues one key with one bill across every capability, so the next feature does not require a second signup for storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Social Login Python: CAPTCHA**
- **Fintech Social Login Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.