import os
import time
from typing import Any, Dict, Optional

import requests


class DatagenError(Exception):
    """Base Datagen SDK exception."""


class DatagenAuthError(DatagenError):
    """Authentication or API-key related errors."""


class DatagenToolError(DatagenError):
    """Returned when a tool executes but signals failure."""


class DatagenHttpError(DatagenError):
    """HTTP-level errors (network/4xx/5xx)."""


class DatagenClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:3001",
        timeout: int = 30,
        retries: int = 0,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.api_key = api_key or os.getenv("DATAGEN_API_KEY")
        if not self.api_key:
            raise DatagenAuthError("API key missing. Set DATAGEN_API_KEY or pass api_key.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff_seconds = backoff_seconds

    def execute_tool(self, tool_alias_name: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        if not tool_alias_name:
            raise ValueError("tool_alias_name is required")

        body = {
            "tool_alias_name": tool_alias_name,
            "parameters": parameters or {},
        }
        url = f"{self.base_url}/api/tools/execute"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = requests.post(url, json=body, headers=headers, timeout=self.timeout)
                if resp.status_code == 401 or resp.status_code == 403:
                    raise DatagenAuthError(f"Auth failed: {resp.text}")
                if resp.status_code >= 400:
                    raise DatagenHttpError(f"HTTP {resp.status_code}: {resp.text}")

                payload = resp.json()
                if not payload.get("success", False):
                    raise DatagenHttpError(f"Unexpected response: {payload}")

                tool_payload = payload.get("data", {})
                if not tool_payload.get("success", False):
                    raise DatagenToolError(tool_payload.get("error") or "Tool reported failure")

                return tool_payload.get("result")
            except (requests.RequestException, DatagenHttpError) as exc:
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
                    continue
                raise
        if last_exc:
            raise last_exc
        raise DatagenError("Unknown error during tool execution")
