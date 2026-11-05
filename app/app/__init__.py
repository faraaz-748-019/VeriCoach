"""VeriCoach App - personal-finance assistant package."""

import sys

try:
    import backend

    sys.modules["app.backend"] = backend
except ImportError:
    pass
