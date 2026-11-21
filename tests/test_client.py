import pytest
import responses
from datagen_sdk import (
    DatagenClient,
    DatagenError,
    DatagenAuthError,
    DatagenHttpError,
    DatagenToolError,
)


class TestDatagenClient:
    """Tests for DatagenClient initialization and configuration."""

    def test_init_with_api_key(self):
        """Test client initialization with API key provided."""
        client = DatagenClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.datagen.dev"
        assert client.timeout == 30
        assert client.retries == 0
        assert client.backoff_seconds == 0.5

    def test_init_with_env_variable(self, monkeypatch):
        """Test client initialization with API key from environment."""
        monkeypatch.setenv("DATAGEN_API_KEY", "env_test_key")
        client = DatagenClient()
        assert client.api_key == "env_test_key"

    def test_init_without_api_key(self, monkeypatch):
        """Test client initialization fails without API key."""
        monkeypatch.delenv("DATAGEN_API_KEY", raising=False)
        with pytest.raises(DatagenAuthError, match="API key missing"):
            DatagenClient()

    def test_init_with_custom_config(self):
        """Test client initialization with custom configuration."""
        client = DatagenClient(
            api_key="test_key",
            base_url="https://api.datagen.dev",
            timeout=60,
            retries=3,
            backoff_seconds=1.0,
        )
        assert client.base_url == "https://api.datagen.dev"
        assert client.timeout == 60
        assert client.retries == 3
        assert client.backoff_seconds == 1.0

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        client = DatagenClient(
            api_key="test_key",
            base_url="https://api.datagen.dev/",
        )
        assert client.base_url == "https://api.datagen.dev"


class TestExecuteTool:
    """Tests for the execute_tool method."""

    @responses.activate
    def test_execute_tool_success(self):
        """Test successful tool execution."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            json={
                "success": True,
                "data": {
                    "success": True,
                    "result": [{"id": 1, "name": "Test Project"}],
                },
            },
            status=200,
        )

        client = DatagenClient(api_key="test_key")
        result = client.execute_tool("test_tool", {"param": "value"})

        assert result == [{"id": 1, "name": "Test Project"}]
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["X-API-Key"] == "test_key"
        assert responses.calls[0].request.headers["Content-Type"] == "application/json"

    @responses.activate
    def test_execute_tool_with_empty_parameters(self):
        """Test tool execution with no parameters."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            json={"success": True, "data": {"success": True, "result": {"status": "ok"}}},
            status=200,
        )

        client = DatagenClient(api_key="test_key")
        result = client.execute_tool("test_tool")

        assert result == {"status": "ok"}

    def test_execute_tool_empty_name(self):
        """Test that empty tool name raises ValueError."""
        client = DatagenClient(api_key="test_key")
        with pytest.raises(ValueError, match="tool_alias_name is required"):
            client.execute_tool("")

    @responses.activate
    def test_execute_tool_auth_error_401(self):
        """Test authentication error with 401 status."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            body="Unauthorized",
            status=401,
        )

        client = DatagenClient(api_key="test_key")
        with pytest.raises(DatagenAuthError, match="Auth failed"):
            client.execute_tool("test_tool")

    @responses.activate
    def test_execute_tool_auth_error_403(self):
        """Test authentication error with 403 status."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            body="Forbidden",
            status=403,
        )

        client = DatagenClient(api_key="test_key")
        with pytest.raises(DatagenAuthError, match="Auth failed"):
            client.execute_tool("test_tool")

    @responses.activate
    def test_execute_tool_http_error(self):
        """Test HTTP error handling."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            body="Internal Server Error",
            status=500,
        )

        client = DatagenClient(api_key="test_key")
        with pytest.raises(DatagenHttpError, match="HTTP 500"):
            client.execute_tool("test_tool")

    @responses.activate
    def test_execute_tool_unsuccessful_response(self):
        """Test handling of unsuccessful API response."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            json={"success": False, "error": "Something went wrong"},
            status=200,
        )

        client = DatagenClient(api_key="test_key")
        with pytest.raises(DatagenHttpError, match="Unexpected response"):
            client.execute_tool("test_tool")

    @responses.activate
    def test_execute_tool_tool_failure(self):
        """Test handling of tool execution failure."""
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            json={
                "success": True,
                "data": {
                    "success": False,
                    "error": "Tool execution failed",
                },
            },
            status=200,
        )

        client = DatagenClient(api_key="test_key")
        with pytest.raises(DatagenToolError, match="Tool execution failed"):
            client.execute_tool("test_tool")

    @responses.activate
    def test_execute_tool_with_retries(self):
        """Test retry logic with exponential backoff."""
        # First two calls fail, third succeeds
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            body="Server Error",
            status=500,
        )
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            body="Server Error",
            status=500,
        )
        responses.add(
            responses.POST,
            "https://api.datagen.dev/api/tools/execute",
            json={
                "success": True,
                "data": {"success": True, "result": {"status": "ok"}},
            },
            status=200,
        )

        client = DatagenClient(api_key="test_key", retries=2, backoff_seconds=0.01)
        result = client.execute_tool("test_tool")

        assert result == {"status": "ok"}
        assert len(responses.calls) == 3

    @responses.activate
    def test_execute_tool_retries_exhausted(self):
        """Test that exception is raised when retries are exhausted."""
        # All calls fail
        for _ in range(4):
            responses.add(
                responses.POST,
                "https://api.datagen.dev/api/tools/execute",
                body="Server Error",
                status=500,
            )

        client = DatagenClient(api_key="test_key", retries=3, backoff_seconds=0.01)
        with pytest.raises(DatagenHttpError, match="HTTP 500"):
            client.execute_tool("test_tool")

        assert len(responses.calls) == 4  # Initial + 3 retries


class TestExceptions:
    """Tests for custom exception types."""

    def test_datagen_error_hierarchy(self):
        """Test that all custom exceptions inherit from DatagenError."""
        assert issubclass(DatagenAuthError, DatagenError)
        assert issubclass(DatagenHttpError, DatagenError)
        assert issubclass(DatagenToolError, DatagenError)

    def test_exception_messages(self):
        """Test that exceptions can carry custom messages."""
        auth_error = DatagenAuthError("Auth failed")
        assert str(auth_error) == "Auth failed"

        http_error = DatagenHttpError("HTTP 500")
        assert str(http_error) == "HTTP 500"

        tool_error = DatagenToolError("Tool failed")
        assert str(tool_error) == "Tool failed"


class TestDecide:
    """Tests for the decide method (POST /api/tools/decide)."""

    URL = "https://api.datagen.dev/api/tools/decide"
    QUESTIONS = {"urgent": {"type": "noul", "instructions": "Needs an answer today?"}}

    @responses.activate
    def test_decide_success(self):
        result = {
            "provider": {"key": "jev", "model": "jev-1.14.0"},
            "answers": {"urgent": {"type": "noul", "answer": "yes", "confidence": 0.9}},
            "usage": {"input_tokens": 100, "output_tokens": 10},
            "latency_ms": 150,
        }
        responses.add(responses.POST, self.URL, json={"ok": True, "result": result}, status=200)
        client = DatagenClient(api_key="test_key")
        out = client.decide("Please refund invoice 4471", self.QUESTIONS, provider="jev", vault_id="v-1")
        assert out == result
        sent = responses.calls[0].request
        assert sent.headers["X-API-Key"] == "test_key"
        import json as _json

        assert _json.loads(sent.body) == {
            "state": "Please refund invoice 4471",
            "questions": self.QUESTIONS,
            "provider": "jev",
            "vault_id": "v-1",
        }

    @responses.activate
    def test_decide_refusal_carries_the_code(self):
        from datagen_sdk import DatagenDecisionError

        responses.add(
            responses.POST,
            self.URL,
            json={"ok": False, "error": {"code": "no_decision_provider", "message": "none", "status": 409}},
            status=409,
        )
        client = DatagenClient(api_key="test_key")
        with pytest.raises(DatagenDecisionError) as exc:
            client.decide("text", self.QUESTIONS)
        assert exc.value.code == "no_decision_provider"
        assert exc.value.status == 409
        assert isinstance(exc.value, DatagenToolError)

    @responses.activate
    def test_decide_does_not_retry_a_provider_error(self):
        from datagen_sdk import DatagenDecisionError

        responses.add(
            responses.POST,
            self.URL,
            json={"ok": False, "error": {"code": "decision_provider_error", "message": "HTTP 503", "status": 502}},
            status=502,
        )
        client = DatagenClient(api_key="test_key", retries=2, backoff_seconds=0)
        with pytest.raises(DatagenDecisionError):
            client.decide("text", self.QUESTIONS)
        assert len(responses.calls) == 1

    @responses.activate
    def test_decide_retries_a_rate_limit(self):
        responses.add(responses.POST, self.URL, json={"success": False, "error": "Rate limit"}, status=429)
        responses.add(responses.POST, self.URL, json={"ok": True, "result": {"answers": {}}}, status=200)
        client = DatagenClient(api_key="test_key", retries=1, backoff_seconds=0)
        assert client.decide("text", self.QUESTIONS) == {"answers": {}}
        assert len(responses.calls) == 2

    def test_decide_validates_input(self):
        client = DatagenClient(api_key="test_key")
        with pytest.raises(ValueError):
            client.decide("", self.QUESTIONS)
        with pytest.raises(ValueError):
            client.decide("text", {})
