from enum import StrEnum


class Policy(StrEnum):
    ON_START = "on_start"
    ON_DEMAND = "on_demand"


class McpServerType(StrEnum):
    SSE = "sse"
    STDIO = "stdio"
