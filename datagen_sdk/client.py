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


class DatagenDecisionError(DatagenToolError):
    """A decide call the server refused or could not answer.

    ``code`` is the server's error code, e.g. ``no_decision_provider`` (the
    vault has no decision model), ``decide_tool_disabled`` (a sandbox key whose
    agent has the decide switch off), ``invalid_decision_request`` or
    ``decision_provider_error``; ``status`` is the HTTP status.
    """

    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status


class DatagenClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.datagen.dev",
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

    def decide(
        self,
        state: str,
        questions: Dict[str, Any],
        provider: Optional[str] = None,
        vault_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ask the vault's decision model fixed-option questions about ``state``.

        ``questions`` maps a question name (lowercase letters, digits and
        underscores) to ``{"type": "choice" | "noul" | "score",
        "instructions": ..., "criteria": ...}``. ``provider`` names a decision
        model in the vault (default: the vault's default one); ``vault_id``
        picks the vault, as on ``execute_tool``.

        Returns ``{"provider": {"key", "model"}, "answers": {name: {"type",
        "answer", "confidence", "probabilities"}}, "usage": {...},
        "latency_ms": ...}``. Raises :class:`DatagenDecisionError` with the
        server's code when the call is refused or fails.

        Each call is billed by the decision model's provider. ``retries``
        apply only to a 429 or a connection that never reached the server,
        never to a call the provider may already have answered.
        """
        if not isinstance(state, str) or not state:
            raise ValueError("state must be a non-empty string")
        if not isinstance(questions, dict) or not questions:
            raise ValueError("questions must be a non-empty dict")

        body: Dict[str, Any] = {"state": state, "questions": questions}
        if provider:
            body["provider"] = provider
        if vault_id:
            body["vault_id"] = vault_id
        url = f"{self.base_url}/api/tools/decide"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        for attempt in range(self.retries + 1):
            try:
                resp = requests.post(url, json=body, headers=headers, timeout=self.timeout)
            except requests.ConnectionError:
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
                    continue
                raise
            if resp.status_code == 429 and attempt < self.retries:
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue
            try:
                payload = resp.json()
            except ValueError:
                raise DatagenHttpError(f"HTTP {resp.status_code}: {resp.text}")
            if resp.status_code < 400 and isinstance(payload, dict) and payload.get("ok") is True:
                return payload.get("result") or {}
            error = payload.get("error") if isinstance(payload, dict) else None
            if isinstance(error, dict) and error.get("code"):
                raise DatagenDecisionError(
                    str(error["code"]), str(error.get("message") or ""), resp.status_code
                )
            if resp.status_code == 401:
                raise DatagenAuthError(f"Auth failed: {resp.text}")
            raise DatagenHttpError(f"HTTP {resp.status_code}: {resp.text}")
        raise DatagenError("Unknown error during decide")
