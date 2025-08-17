"""Configuration models for MCP Gateway."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class MCPType(str, Enum):
    """MCP component types."""

    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class AuthType(str, Enum):
    """Authentication types."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


class ParameterLocation(str, Enum):
    """Parameter locations."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    BODY = "body"


class ParameterDefinition(BaseModel):
    """Parameter definition for REST to MCP mapping."""

    name: str
    type: str = "string"
    description: str | None = None
    required: bool = True
    location: ParameterLocation = ParameterLocation.QUERY
    default: Any | None = None


class AuthenticationConfig(BaseModel):
    """Authentication configuration."""

    type: AuthType = AuthType.NONE
    api_key: str | None = None
    api_key_header: str = "X-API-Key"
    bearer_token: str | None = None
    basic_auth_username: str | None = None
    basic_auth_password: str | None = None
    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oauth2_token_url: str | None = None
    oauth2_scopes: list[str] = []


class EndpointConfig(BaseModel):
    """Single endpoint configuration."""

    path: str
    method: HTTPMethod
    mcp_type: MCPType
    mcp_name: str
    description: str
    parameters: list[ParameterDefinition] = []
    response_mapping: dict[str, Any] | None = None
    auth: AuthenticationConfig | None = None

    @validator("mcp_name")
    def validate_mcp_name(cls, v: str) -> str:
        """Validate MCP name follows naming conventions."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "MCP name must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v


class ServiceConfig(BaseModel):
    """Service configuration."""

    name: str
    description: str
    base_url: str
    auth: AuthenticationConfig | None = None
    endpoints: list[EndpointConfig] = []

    @validator("base_url")
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = False
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    burst_size: int = 10


class ObservabilityConfig(BaseModel):
    """Observability configuration."""

    enabled: bool = True
    tracing_enabled: bool = True
    metrics_enabled: bool = True
    logging_enabled: bool = True
    service_name: str = "mcp-gateway"
    jaeger_endpoint: str | None = None
    otlp_endpoint: str | None = None
    log_level: str = "INFO"


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    access_log: bool = True


class GatewayConfig(BaseModel):
    """Main gateway configuration."""

    version: str = "1.0"
    services: list[ServiceConfig] = []
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    observability: ObservabilityConfig = Field(
        default_factory=ObservabilityConfig
    )
    server: ServerConfig = Field(default_factory=ServerConfig)

    @validator("services")
    def validate_services(cls, v: list[ServiceConfig]) -> list[ServiceConfig]:
        """Validate service names are unique."""
        names = [service.name for service in v]
        if len(names) != len(set(names)):
            raise ValueError("Service names must be unique")
        return v


class Settings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"
    log_level: str = "INFO"
    debug: bool = False

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False
