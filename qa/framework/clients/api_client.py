"""Robust HTTP/REST API client with automatic Allure telemetry and timing."""

from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi.testclient import TestClient

from qa.framework.reporting.allure_helper import attach_api_request, attach_api_response


class FrameworkAPIClient:
    """Wrapper around httpx / TestClient with integrated Allure logging and diagnostics."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        app: Any = None,
        default_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.timeout = timeout
        self.app = app

        if self.app is not None:
            self._client: TestClient | httpx.Client = TestClient(
                app=self.app,
                base_url=self.base_url,
                headers=self.default_headers,
            )
        else:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self.default_headers,
                timeout=self.timeout,
            )

    def request(
        self,
        method: str,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute HTTP request with automatic Allure instrumentation."""
        merged_headers = dict(self.default_headers)
        if headers:
            merged_headers.update(headers)

        full_url = (
            f"{self.base_url}{path}"
            if path.startswith("/")
            else f"{self.base_url}/{path}"
        )
        attach_api_request(
            method=method.upper(),
            url=full_url,
            headers=merged_headers,
            body=json or params,
        )

        start_time = time.perf_counter()
        try:
            response = self._client.request(
                method=method.upper(),
                url=path,
                json=json,
                params=params,
                headers=merged_headers,
                **kwargs,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # Parse body for logging if possible
            try:
                body_json = response.json()
            except Exception:
                body_json = response.text[:500] if response.text else None

            attach_api_response(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=body_json,
                duration_ms=elapsed_ms,
            )
            return response
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            attach_api_response(
                status_code=0,
                headers={},
                body={"error": str(exc), "type": type(exc).__name__},
                duration_ms=elapsed_ms,
            )
            raise

    def get(
        self, path: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        return self.request("GET", path, params=params, **kwargs)

    def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self.request("POST", path, json=json, params=params, **kwargs)

    def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self.request("PUT", path, json=json, params=params, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        """Close underlying client session."""
        self._client.close()

    def __enter__(self) -> FrameworkAPIClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
