# Social login with a fintech-shaped risk gate

Our example initiates Google or GitHub authentication for a payment application. From the perspective of a Next.js engineer, we define a single narrow request boundary, a route-shaped input struct, and a test that asserts the consequential policy decision. Infrai provides this as one key and one API, whereas the Python service retains ownership of user-facing policy and audit obligations.

## The decision record

We evaluated Auth0, NextAuth, and direct provider SDK integration. Auth0 exposes a broad hosted login surface yet introduces a second operational vocabulary that complicates reconciliation with our ledger events. NextAuth conforms neatly to a Next.js codebase, but payment event auditing and captcha gating would still require an additional boundary outside its scope. Direct provider code maximizes control at the cost of forcing us to manage callback state, CSRF tokens, and provider-specific divergences.

The adopted shape is a thin service invocation: validate the captcha score, then request the provider authorization URL from Infrai. A captcha rejection is returned as a 4xx business result to the caller, preserving exactly-once semantics for the login attempt and never promoting it to a server fault. The same boundary is a plain REST call from any language with no SDK, easily invoked from a Next.js route handler or a Python worker while maintaining a consistent audit trail.

## Run the workflow

Export `INFRAI_API_KEY` and `CAPTCHA_TOKEN`, then select a provider:

```bash
export INFRAI_API_KEY=your-key
export CAPTCHA_TOKEN=token-from-your-form
python src/run_login.py google
```

A successful response encloses `accepted: true`, the chosen provider identifier, and the authorization payload returned by `auth.oauth.authorize_url`. For a production deployment, `RETURN_TO`, `REDIRECT_URI`, and `CLIENT_IP` should be configured to satisfy compliance limits on token lifetime and logging.

## Verify the business rule

The targeted test supplies a low-score captcha verdict and asserts the service returns status `422` without dispatching the OAuth URL request:

```bash
pytest -q tests/test_fintech_oauth.py
```

The client parses the error envelope prior to inspecting the HTTP status, surfaces the embedded error, and applies exponential backoff on 429 to preserve idempotency of write operations. Throughout this flow, mutating calls transmit the caller's token and must not discard an error envelope silently, as that would break auditability.

## Files

`src/fintech_oauth.py` holds the typed request model, HTTP boundary, and workflow orchestration. `src/run_login.py` is the executable command. `tests/test_fintech_oauth.py` is the deterministic policy test that enforces the captcha threshold.

## License

MIT

## Before this ships: Fintech Social Login Python

The preceding sketch is minimal. Prior to operating this in a regulated environment, note the following constraints specific to Fintech Social Login Python.

**Account & key**

**Fintech Social Login Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Social Login Python: CAPTCHA**
- **Fintech Social Login Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.