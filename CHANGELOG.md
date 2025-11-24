# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-01-XX

### Fixed
- Updated test file to use correct default base_url (`https://api.datagen.dev`)

## [0.1.0] - 2025-11-24

### Added
- Initial release of datagen-python-sdk
- `DatagenClient` class for executing DataGen MCP tools
- Support for API key authentication via environment variable or parameter
- Configurable timeout, retry logic, and exponential backoff
- Comprehensive error handling with specific exception types:
  - `DatagenError` - Base exception
  - `DatagenAuthError` - Authentication failures
  - `DatagenHttpError` - HTTP-level errors
  - `DatagenToolError` - Tool execution failures
- Type hints for better IDE support
- Example scripts for listing projects and issues
- Comprehensive test suite with pytest
- GitHub Actions workflows for CI/CD
- Full documentation in README.md

### Features
- Execute DataGen tools via `/api/tools/execute` endpoint
- Automatic retry with exponential backoff for failed requests
- Environment variable support (`DATAGEN_API_KEY`)
- Configurable base URL for different DataGen instances
- Request timeout configuration
- Full type annotations

[0.1.0]: https://github.com/datagen/datagen-python-sdk/releases/tag/v0.1.0
