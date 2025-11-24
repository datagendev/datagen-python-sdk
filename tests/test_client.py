import os
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
        assert client.base_url == "http://localhost:3001"
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
            base_url="http://localhost:3001/",
        )
        assert client.base_url == "http://localhost:3001"


class TestExecuteTool:
    """Tests for the execute_tool method."""

    @responses.activate
    def test_execute_tool_success(self):
        """Test successful tool execution."""
        responses.add(
            responses.POST,
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
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
            "http://localhost:3001/api/tools/execute",
            body="Server Error",
            status=500,
        )
        responses.add(
            responses.POST,
            "http://localhost:3001/api/tools/execute",
            body="Server Error",
            status=500,
        )
        responses.add(
            responses.POST,
            "http://localhost:3001/api/tools/execute",
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
                "http://localhost:3001/api/tools/execute",
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
