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


## KF-002: WCAG 2.1 AA Critical Accessibility Violation (meta-viewport user-scalable=no)

- **Discovered by**: Axe-Core Accessibility Audit in Playwright Suite (`qa/tests/web/test_playwright_chat.py::test_accessibility_scan_with_axe`)
- **Location**: `app/frontend/index.html` line 6
- **Error / Axe Violation Output**:
  ```text
  AssertionError: Found critical a11y violations: [{
    'id': 'meta-viewport',
    'impact': 'critical',
    'description': 'Ensures <meta name="viewport"> does not disable text scaling and zooming',
    'help': 'Zooming and scaling should not be disabled',
    'helpUrl': 'https://dequeuniversity.com/rules/axe/4.4/meta-viewport?application=axeAPI',
    'nodes': [{
      'any': [{'id': 'meta-viewport', 'data': 'user-scalable=no', 'message': 'user-scalable=no on <meta> tag disables zooming on mobile devices'}],
      'html': '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">'
    }]
  }]
  ```
- **Expected Behaviour**: Mobile viewport allows pinch-to-zoom and text resizing for visually impaired users per WCAG 2.1 Success Criterion 1.4.4 (Resize Text).
- **Actual Behaviour**: Viewport prevented zooming via `maximum-scale=1.0, user-scalable=no`.
- **Root Cause**: Default boilerplate mobile meta tag included aggressive scaling lockdown.
- **Resolution**: Updated `app/frontend/index.html` viewport to `<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />` and recompiled frontend assets (`npm run build`).



