# Transport 架构设计

## 概述

新的 Transport 架构采用 **一个 McpServer 对应一个 Transport** 的设计原则，提供更好的责任分离、错误隔离和扩展性。

## 架构组件

### 1. Transport (基类)
```python
class Transport(ABC):
    def __init__(self, server: McpServer):
        self.server = server  # 只管理单个服务器
```

**职责：**
- 处理单个 `McpServer` 的通信
- 提供标准的工具获取和调用接口
- 管理传输层的生命周期

### 2. SSETransport
```python
class SSETransport(Transport):
    def __init__(self, server: McpServer):
        super().__init__(server)
        self._transport: Optional[Any] = None
        self._tools_cache: list[Tool] = []
```

**职责：**
- 实现基于 SSE 的 MCP 协议通信
- 使用官方 `mcp.client.sse.sse_client`
- 管理单个服务器的工具缓存

### 3. STDIOTransport
```python
class STDIOTransport(Transport):
    def __init__(self, server: McpServer):
        super().__init__(server)
        self._transport: Optional[Any] = None
        self._tools_cache: list[Tool] = []
```

**职责：**
- 实现基于 STDIO 的 MCP 协议通信
- 使用官方 `mcp.client.stdio.stdio_client`
- 通过进程 stdin/stdout 与本地 MCP 服务器通信
- 支持复杂命令行解析和进程管理

### 4. StreamableTransport
```python
class StreamableTransport(Transport):
    def __init__(self, server: McpServer):
        super().__init__(server)
        self._active_streams: dict[str, AsyncIterator[StreamChunk]] = {}
```

**职责：**
- 实现流式工具调用和实时响应
- 支持异步迭代器接口返回数据流
- 管理多个并发流和资源清理
- 提供进度跟踪和元数据传递

### 5. TransportManager
```python
class TransportManager:
    def __init__(self, config: Mcp):
        self._transports: dict[str, Transport] = {}
```

**职责：**
- 根据 MCP 配置创建多个 Transport 实例
- 统一管理所有 Transport 的生命周期
- 提供工具查找和调用的统一接口

## 流式传输支持

### 流式数据结构

#### StreamChunk
```python
@dataclass
class StreamChunk:
    content: str          # 数据块内容
    chunk_id: int         # 块序号
    timestamp: datetime   # 时间戳
    is_final: bool       # 是否为最后一个块
    metadata: dict       # 元数据（进度、错误等）
```

#### StreamableToolResult
```python
@dataclass
class StreamableToolResult:
    tool_name: str              # 工具名称
    request_id: str             # 请求ID
    is_streaming: bool = True   # 是否流式
    total_chunks: int          # 总块数
    error: Optional[str]       # 错误信息
```

### 流式调用方式

#### 1. 直接流式调用
```python
streamable_transport = StreamableTransport(server)
async for chunk in streamable_transport.call_tools_streaming(params, req):
    process_chunk(chunk)
    if chunk.is_final:
        break
```

#### 2. 通过管理器流式调用
```python
transport_manager = TransportManager(config)
async for chunk in transport_manager.call_tool_streaming(params, req):
    update_ui(chunk.content)
    show_progress(chunk.metadata.get('progress', 0))
```

#### 3. 获取完整流式结果
```python
result = await transport_manager.get_streaming_result(params, req)
complete_result = result.to_mcp_result(all_chunks)
```

### 流式传输特性

- **🚀 实时响应**: 无需等待完整结果
- **📊 进度跟踪**: 实时显示处理进度
- **💾 内存友好**: 分块处理，降低内存占用
- **🛡️ 错误处理**: 流式错误状态和恢复
- **🔄 兼容性**: 同时支持流式和普通调用

## 架构优势

### 🔧 **更好的责任分离**
- 每个 Transport 只关注一个服务器
- TransportManager 负责整体协调
- 清晰的单一职责原则

### 🛡️ **错误隔离**
- 单个服务器故障不影响其他服务器
- 独立的错误处理和恢复机制
- 更好的系统稳定性

### 📈 **可扩展性**
- 支持不同类型的 Transport（SSE、STDIO、gRPC等）
- 动态添加/移除服务器
- 易于添加新的传输协议

### 🧪 **更好的测试性**
- 可以独立测试每个 Transport
- Mock 单个服务器更容易
- 更精确的单元测试覆盖

## 使用示例

```python
# 1. 创建配置
mcp_config = Mcp(
    servers=[
        McpServer(name="sse_server", type=McpServerType.SSE, url="http://localhost:8001"),
        McpServer(name="stdio_server", type=McpServerType.STDIO, command="python -m my_mcp_server"),
    ]
)

# 2. 创建管理器
transport_manager = TransportManager(mcp_config)

# 3. 启动所有传输
await transport_manager.start(context)

# 4. 获取所有工具
tools = await transport_manager.fetch_all_tools()

# 5. 调用工具（普通方式）
result = await transport_manager.call_tool(call_params, request)

# 6. 流式调用工具
async for chunk in transport_manager.call_tool_streaming(call_params, request):
    print(f"Chunk {chunk.chunk_id}: {chunk.content}")
    if chunk.is_final:
        break

# 7. 停止传输
await transport_manager.stop()
```

## 扩展性

### 添加新的 Transport 类型

```python
class gRPCTransport(Transport):
    def __init__(self, server: McpServer):
        super().__init__(server)
        # gRPC 特定的初始化

    async def fetch_tools(self) -> list[Tool]:
        # gRPC 特定的工具获取逻辑
        pass

    async def call_tools(self, params, req):
        # gRPC 特定的工具调用逻辑
        pass

# 在 TransportManager 中注册
def _create_transport_for_server(self, server: McpServer) -> Transport:
    if server.type.value == "sse":
        return SSETransport(server)
    elif server.type.value == "stdio":
        return STDIOTransport(server)
    elif server.type.value == "grpc":
        return gRPCTransport(server)  # 新增
    # ...
```

### 动态管理

```python
# 动态添加服务器
new_server = McpServer(name="new_server", type=McpServerType.SSE, ...)
new_transport = SSETransport(new_server)
await new_transport.start(context)
transport_manager._transports[new_server.name] = new_transport

# 动态移除服务器
old_transport = transport_manager._transports.pop("old_server")
await old_transport.stop()
```

## 文件结构

```
myunla/gateway/transports/
├── __init__.py          # TransportManager + 流式支持
├── base.py              # Transport 基类 + 装饰器
├── sse.py               # SSETransport 实现
├── stdio.py             # STDIOTransport 实现
├── streamable.py        # StreamableTransport 流式实现
└── README.md            # 本文档
```

## 下一步

- [x] 实现 STDIOTransport
- [x] 实现 StreamableTransport（流式传输）
- [ ] 添加 gRPC Transport 支持
- [ ] 添加 WebSocket Transport 支持
- [ ] 实现动态服务器管理 API
- [ ] 添加监控和健康检查
- [ ] 性能优化和连接池管理
- [ ] 实现流式传输的断点续传
- [ ] 添加流式传输的压缩支持
