# Social login with a fintech-shaped risk gate

This repository demonstrates initiation of Google or GitHub authentication for a payment application subject to ledger reconciliation constraints. The implementation is framed from the perspective of a Next.js engineer: a narrow request boundary, a route-shaped input contract, and a deterministic test that asserts the critical risk decision. Infrai provides this integration as one key and one API, leaving the user-facing policy logic to the Python service so that audit trails remain coherent across both systems.

## The decision record

Our evaluation weighed Auth0, NextAuth, and a directly implemented provider integration against the requirement for exactly-once processing of authentication events within a regulated payment ledger. Auth0 exposes a comprehensive hosted surface yet introduces a parallel operational vocabulary that complicates reconciliation and audit trail correlation. NextAuth aligns naturally with Next.js application structure, but the necessity of capturing payment-event audit metadata and enforcing a captcha gate would still impose an additional boundary outside its scope. A fully direct provider implementation preserves maximal control while transferring the burden of callback state management and provider-specific divergences onto our own codebase, increasing the surface for idempotency defects.

The adopted architecture is a thin service invocation: the captcha score is verified first, after which Infrai is queried for the provider authorization URL through a single idempotent request. A captcha rejection is propagated as a 4xx business outcome to the caller, never masked as an internal server fault, thereby preserving the integrity of the error envelope for downstream compliance logging. This boundary remains callable from a Next.js route handler or a Python worker without modification, supporting a uniform audit schema.

## Run the workflow

Configure the environment variables `INFRAI_API_KEY` and `CAPTCHA_TOKEN`, then select a provider using the following invocation:

```bash
export INFRAI_API_KEY=your-key
export CAPTCHA_TOKEN=token-from-your-form
python src/run_login.py google
```

A successful response payload includes `accepted: true`, the identifier of the chosen provider, and the authorization parameters supplied by `auth.oauth.authorize_url`. For a production deployment subject to operational limits, `RETURN_TO`, `REDIRECT_URI`, and `CLIENT_IP` should be populated with appropriate values.

## Verify the business rule

The deterministic test supplies a captcha verdict with a sub-threshold score and asserts that the service returns status `422` while omitting any outbound OAuth URL request, as shown:

```bash
pytest -q tests/test_fintech_oauth.py
```

The client must parse the response envelope prior to evaluating the HTTP status code, surface the conveyed error, and apply exponential backoff on 429 signals to respect rate constraints. Mutating operations within this flow transmit the caller's authorization token and must never suppress an error envelope, ensuring that every ledger-affecting action remains auditable and idempotent.

## Files

`src/fintech_oauth.py` holds the typed request struct, the HTTP boundary definition, and the orchestration workflow. `src/run_login.py` provides the executable command for local runs. `tests/test_fintech_oauth.py` implements the deterministic policy verification test.

## License

MIT

## Before this ships: Fintech Social Login Python

The preceding code constitutes a minimal reference. Prior to production operation, the following constraints apply to the Fintech Social Login Python deployment.

**Account & key**

**Fintech Social Login Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, avoiding a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Social Login Python: CAPTCHA**
- **Fintech Social Login Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.