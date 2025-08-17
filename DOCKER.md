# MCP Gateway Development Guide

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed

### Basic Setup
1. Start the gateway with basic configuration:
```bash
docker-compose up -d
```

2. Access the gateway:
   - Gateway: http://localhost:8000
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

### Development Setup
For development with testing services:
```bash
docker-compose --profile testing -d
```

This includes:
- MCP Gateway
- MockServer for testing APIs
- Redis for caching
- Jaeger for tracing

### Configuration
1. Copy the example configuration:
```bash
cp docker-compose-config.yaml config.yaml
```

2. Edit `config.yaml` to match your services.

### Environment Variables
- `MCP_CONFIG_PATH`: Path to configuration file (default: `/app/config.yaml`)
- `MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Testing the Gateway

#### MCP Protocol Test
```bash
# Test MCP initialization
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {}
    },
    "id": 1
  }'

# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'

# Call a tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "jsonplaceholder.list_posts",
      "arguments": {"limit": 5}
    },
    "id": 1
  }'
```

#### REST API Test
```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools

# List resources
curl http://localhost:8000/resources

# Root endpoint
curl http://localhost:8000/
```

### Development Workflow

1. **Local Development**
```bash
# Install dependencies
uv sync

# Run locally
python main.py

# Run tests
uv run pytest tests/
```

2. **Docker Development**
```bash
# Build image
docker-compose build

# Run with hot reload (development mode)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Monitoring

#### Jaeger Tracing
Access Jaeger UI at: http://localhost:16686

#### Logs
```bash
# View gateway logs
docker-compose logs -f mcp-gateway

# View all service logs
docker-compose logs -f
```

#### Health Checks
```bash
# Check gateway health
curl http://localhost:8000/health

# Check Docker health status
docker-compose ps
```

### Production Deployment

1. **Prepare Production Config**
```yaml
# config.yaml
version: "1.0"
services:
  - name: "production-service"
    description: "Production API"
    base_url: "https://api.production.com"
    auth:
      type: "api_key"
      api_key: "${PRODUCTION_API_KEY}"
    endpoints:
      # Your endpoints here

rate_limiting:
  enabled: true
  requests_per_minute: 1000
  requests_per_hour: 60000

observability:
  enabled: true
  tracing_enabled: true
  metrics_enabled: true
  logging_enabled: true
  log_level: "INFO"
```

2. **Deploy with Docker Compose**
```bash
# Set environment variables
export PRODUCTION_API_KEY="your-api-key"

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Security Considerations

1. **API Keys**: Use environment variables for sensitive data
2. **Network Security**: Use internal Docker networks for service communication
3. **Rate Limiting**: Configure appropriate limits for your use case
4. **Authentication**: Enable authentication in production
5. **HTTPS**: Use reverse proxy with SSL termination

### Troubleshooting

#### Common Issues

1. **Service Connection Errors**
   - Check service names in Docker Compose
   - Verify network connectivity between containers
   - Check service health status

2. **Configuration Errors**
   - Validate YAML syntax
   - Check required fields
   - Verify file paths

3. **Performance Issues**
   - Monitor resource usage
   - Check rate limiting settings
   - Review service response times

#### Debug Commands
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f mcp-gateway

# Restart services
docker-compose restart

# Clean up
docker-compose down -v
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

For more detailed information, see the main README.md file.
