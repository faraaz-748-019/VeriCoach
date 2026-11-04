# Known Failures

This document records test failures that reveal real defects in the app.
Each entry contains: failing test, expected vs actual behaviour, root cause (if known),
and whether a fix is in progress.

## KF-001: 500 Internal Server Error on GET /api/v1/synthetic-user

- **Discovered by**: Schemathesis Property-Based Fuzz Testing (`qa/tests/api/test_schemathesis.py`)
- **Endpoint**: `GET /api/v1/synthetic-user?seed=0`
- **Failing Command**:
  ```bash
  pytest qa/tests/api/test_schemathesis.py
  # Reproduce curl:
  curl -X GET 'http://127.0.0.1:8000/api/v1/synthetic-user?seed=0'
  ```
- **Error / Traceback**:
  ```text
  AttributeError: 'SyntheticUser' object has no attribute 'model_dump'
    File "app/backend/main.py", line 434, in legacy_synthetic_user
      return user.model_dump()
  ```
- **Expected Behaviour**: HTTP 200 with JSON serialization of the synthetic user data.
- **Actual Behaviour**: HTTP 500 Internal Server Error unhandled exception.
- **Root Cause**: `generate_user()` in `app.data.synthetic` returns a Python dataclass instance (`SyntheticUser`), not a Pydantic `BaseModel`. Calling `.model_dump()` fails with `AttributeError`.
- **Resolution**: Updated `app/backend/main.py` `legacy_synthetic_user` to support both dataclass (`dataclasses.asdict(user)`) and Pydantic (`user.model_dump()`).


