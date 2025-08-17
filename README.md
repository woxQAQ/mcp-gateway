# MyUnla MCP Gateway

A secure, observable gateway for converting RESTful APIs to MCP (Model Context Protocol) format.

## Features

- **REST to MCP Conversion**: Automatically convert RESTful API endpoints to MCP tools and resources
- **Security**: Multiple authentication methods (API Key, JWT, OAuth 2.0)
- **Observability**: Built-in OpenTelemetry support for distributed tracing
- **Configuration Management**: YAML/JSON configuration with hot reload
- **Rate Limiting**: Built-in rate limiting and abuse protection
- **Health Monitoring**: Service health checks and monitoring

## Quick Start

1. Install dependencies:
```bash
pip install -e .
```

2. Configure your services in `config.yaml`

3. Run the gateway:
```bash
python main.py
```

4. The gateway will be available at `http://localhost:8000`

## Configuration

See `config.yaml` for configuration examples and `myunla/models/config.py` for schema details.

## API Endpoints

- `GET /` - Gateway information
- `GET /health` - Health status
- `GET /tools` - List available tools
- `GET /resources` - List available resources
- `POST /mcp` - MCP JSON-RPC endpoint

## MCP Protocol

The gateway implements the MCP protocol with support for:
- `tools/list` - List available tools
- `tools/call` - Execute a tool
- `resources/list` - List available resources
- `resources/read` - Read a resource
- `initialize` - Initialize connection

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

## License

MIT License
