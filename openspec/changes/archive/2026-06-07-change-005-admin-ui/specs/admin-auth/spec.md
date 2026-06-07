# Capability: admin-auth

## Purpose
Authentication for the admin panel. Single password (`wero123` for MVP), validated against a plain text constant. Session is a signed cookie via `itsdangerous.TimestampSigner` — no DB session table needed. Auth is enforced via a FastAPI `Depends(get_current_admin)` dependency on every admin route.

## Requirements

### Requirement: ADMIN_PASSWORD constant
The system MUST define `ADMIN_PASSWORD = "wero123"` as a module-level constant in `app/auth.py`. The value is the plain-text password (acceptable trade-off for a single-admin local MVP; documented as a known limitation).

#### Scenario: constant is accessible
- **GIVEN** `app/auth.py` is imported
- **WHEN** `from app.auth import ADMIN_PASSWORD` is run
- **THEN** `ADMIN_PASSWORD` is `"wero123"`

#### Scenario: constant is documented
- **GIVEN** the codebase
- **WHEN** a developer reads `app/auth.py`
- **THEN** there is a comment near `ADMIN_PASSWORD` explaining: "Plain text for MVP. Replace with bcrypt + user table for production."

### Requirement: SECRET_KEY constant
The system MUST define `SECRET_KEY = "wero-dev-secret-change-me-in-production"` as a module-level constant in `app/auth.py`. This is used to sign the session cookies.

#### Scenario: SECRET_KEY is overridable via env
- **GIVEN** the environment variable `WERO_SECRET_KEY` is set
- **WHEN** `app/auth.py` is imported
- **THEN** `SECRET_KEY` is the value of the env var (or the default if not set)

### Requirement: password verification
The system MUST provide `check_password(submitted: str) -> bool` in `app/auth.py` that returns `True` if `submitted == ADMIN_PASSWORD`, `False` otherwise. Uses `secrets.compare_digest` to prevent timing attacks.

#### Scenario: correct password
- **GIVEN** `ADMIN_PASSWORD = "wero123"`
- **WHEN** `check_password("wero123")` is called
- **THEN** the result is `True`

#### Scenario: wrong password
- **GIVEN** `ADMIN_PASSWORD = "wero123"`
- **WHEN** `check_password("wrong")` is called
- **THEN** the result is `False`

#### Scenario: empty password
- **GIVEN** `ADMIN_PASSWORD = "wero123"`
- **WHEN** `check_password("")` is called
- **THEN** the result is `False`

### Requirement: session token creation
The system MUST provide `create_session_token() -> str` in `app/auth.py` that returns a signed, timestamped string using `itsdangerous.TimestampSigner(SECRET_KEY).sign("admin")`. The returned string is base64url-encoded and safe to use as a cookie value.

#### Scenario: token is created
- **GIVEN** `SECRET_KEY` is set
- **WHEN** `create_session_token()` is called
- **THEN** the result is a non-empty string

#### Scenario: token is verifiable
- **GIVEN** a token from `create_session_token()`
- **WHEN** `verify_session_token(token)` is called
- **THEN** the result is `True`

### Requirement: session token verification
The system MUST provide `verify_session_token(token: str) -> bool` in `app/auth.py` that:
- Returns `True` if the token was signed with the current `SECRET_KEY` AND is less than 7 days old
- Returns `False` if the token is invalid, tampered, or expired

#### Scenario: valid token
- **GIVEN** a fresh token from `create_session_token()`
- **WHEN** `verify_session_token(token)` is called
- **THEN** the result is `True`

#### Scenario: tampered token
- **GIVEN** a token from `create_session_token()` with one character changed
- **WHEN** `verify_session_token(tampered)` is called
- **THEN** the result is `False`

#### Scenario: empty token
- **GIVEN** an empty string
- **WHEN** `verify_session_token("")` is called
- **THEN** the result is `False`

#### Scenario: expired token
- **GIVEN** a token signed more than 7 days ago (mocked via time travel or manually crafted)
- **WHEN** `verify_session_token(expired_token)` is called
- **THEN** the result is `False`

### Requirement: get_current_admin dependency
The system MUST provide `async def get_current_admin(request: Request) -> str` in `app/auth.py` that:
- Reads the `wero_admin` cookie
- If valid, returns the username string `"admin"` (the dependency caller can use this)
- If invalid or missing, raises `HTTPException(status_code=303, headers={"Location": "/admin/login"})` (redirect to login)

Wait — FastAPI's `HTTPException` is 4xx/5xx, not 3xx. For a redirect, the dependency should return a `Response` or use a different mechanism. The correct pattern is: raise `HTTPException(status_code=401, detail="Not authenticated")` for API endpoints, but for HTML endpoints, return a `RedirectResponse` directly OR raise a custom exception handled by middleware.

The cleanest implementation: `get_current_admin` returns either the username (str) or a `RedirectResponse`. FastAPI's `Depends` supports returning a `Response` from a dependency, which short-circuits the endpoint and returns that response directly. So:

```python
def get_current_admin(request: Request) -> str:
    token = request.cookies.get("wero_admin")
    if not token or not verify_session_token(token):
        return RedirectResponse(url="/admin/login", status_code=303)
    return "admin"
```

And the route signature becomes:
```python
@router.get("/")
def dashboard(admin: str = Depends(get_current_admin)):
    # If we reach here, the user is authenticated
    ...
```

If `get_current_admin` returns a `RedirectResponse`, FastAPI returns it directly (status 303), bypassing the endpoint function.

#### Scenario: valid cookie
- **GIVEN** the request has a valid `wero_admin` cookie
- **WHEN** the endpoint is called with `Depends(get_current_admin)`
- **THEN** the endpoint function runs normally (no redirect)

#### Scenario: missing cookie
- **GIVEN** the request has no `wero_admin` cookie
- **WHEN** the endpoint is called with `Depends(get_current_admin)`
- **THEN** the response is HTTP 303 with `Location: /admin/login` (and the endpoint function does NOT run)

#### Scenario: invalid cookie
- **GIVEN** the request has a tampered or expired `wero_admin` cookie
- **WHEN** the endpoint is called with `Depends(get_current_admin)`
- **THEN** the response is HTTP 303 with `Location: /admin/login`

### Requirement: login route behavior
The system MUST expose `GET /admin/login` that returns the login form (or redirects to `/admin/` if already authenticated) and `POST /admin/login` that validates the password and sets the cookie.

#### Scenario: GET /admin/login (unauthenticated)
- **GIVEN** no `wero_admin` cookie
- **WHEN** `GET /admin/login` is requested
- **THEN** the response is HTTP 200 with the login form HTML

#### Scenario: GET /admin/login (already authenticated)
- **GIVEN** a valid `wero_admin` cookie
- **WHEN** `GET /admin/login` is requested
- **THEN** the response is HTTP 303 with `Location: /admin/`

#### Scenario: POST /admin/login (correct password)
- **GIVEN** no `wero_admin` cookie
- **WHEN** `POST /admin/login` with `password=wero123` is submitted
- **THEN** the response is HTTP 303 with `Location: /admin/`
- **AND** the response has `Set-Cookie: wero_admin=<token>; HttpOnly; Max-Age=604800; Path=/; SameSite=Lax`

#### Scenario: POST /admin/login (wrong password)
- **GIVEN** no `wero_admin` cookie
- **WHEN** `POST /admin/login` with `password=wrong` is submitted
- **THEN** the response is HTTP 200 with the login form re-rendered, showing an error message ("Contraseña incorrecta")
- **AND** NO `Set-Cookie` header is sent

#### Scenario: POST /admin/login (empty password)
- **GIVEN** no `wero_admin` cookie
- **WHEN** `POST /admin/login` with `password=` is submitted
- **THEN** the response is HTTP 200 with the login form re-rendered, showing an error message

### Requirement: logout route behavior
The system MUST expose `GET /admin/logout` that clears the `wero_admin` cookie and redirects to `/admin/login`. (Note: GET, not POST, for simplicity in this MVP.)

#### Scenario: logout clears cookie
- **GIVEN** a valid `wero_admin` cookie
- **WHEN** `GET /admin/logout` is requested
- **THEN** the response is HTTP 303 with `Location: /admin/login`
- **AND** the response has `Set-Cookie: wero_admin=; Max-Age=0; Path=/` (clears the cookie)

### Requirement: cookie attributes
The `wero_admin` cookie MUST be set with:
- `HttpOnly=True` (prevents JS access, mitigates XSS)
- `Max-Age=604800` (7 days)
- `Path=/`
- `SameSite=Lax` (mitigates CSRF for cross-origin POST)

For local development (HTTP), `Secure=False`. In production with HTTPS, the app should be configured to set `Secure=True`.

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
