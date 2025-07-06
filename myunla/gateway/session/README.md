# Session Management

这个模块提供了网关的会话管理功能，支持内存存储和Redis存储两种方式。

## 功能特性

- **抽象接口**: 提供统一的Store和Connection接口
- **内存存储**: 基于内存的会话存储，适合单实例部署
- **Redis存储**: 基于Redis的分布式会话存储，支持多实例部署
- **发布订阅**: Redis存储支持跨实例的事件分发
- **异步支持**: 全异步设计，性能优异
- **类型安全**: 完整的类型注解

## 核心组件

### 数据模型

- `Message`: 消息模型，包含事件名和数据
- `RequestInfo`: 请求信息，包含headers、queries、cookies
- `Meta`: 会话元数据，包含ID、创建时间、前缀、类型等

### 接口定义

- `Store`: 会话存储抽象接口
- `Connection`: 会话连接抽象接口

### 实现类

- `MemoryStore/MemoryConnection`: 内存存储实现
- `RedisStore/RedisConnection`: Redis存储实现

## 使用方法

### 内存存储

```python
from myunla.gateway.session import MemoryStore, Meta, RequestInfo, Message
from datetime import datetime

# 创建存储
store = MemoryStore()

# 创建会话元数据
meta = Meta(
    id="session_001",
    created_at=datetime.now(),
    prefix="/api/v1",
    type="sse",
    request=RequestInfo(
        headers={"User-Agent": "browser"},
        queries={"token": "abc123"},
        cookies={"session": "xyz789"}
    )
)

# 注册连接
conn = await store.register(meta)

# 发送消息
message = Message(event="data", data=b"Hello World!")
await conn.send(message)

# 获取连接
retrieved_conn = await store.get("session_001")

# 注销连接
await store.unregister("session_001")
```

### Redis存储

```python
from myunla.gateway.session import create_redis_store
from myunla.config.redis_config import SessionRedisConfig

# 创建Redis配置
config = SessionRedisConfig(
    addr="localhost:6379",
    db=0,
    prefix="session",
    topic="session_updates"
)

# 创建存储
store = await create_redis_store(config)

# 其他操作与内存存储相同...

# 记得关闭存储
await store.close()
```

## Redis配置说明

Redis存储支持多种部署模式：

### 单机模式
```python
SessionRedisConfig(
    addr="localhost:6379",
    cluster_type="single",
    db=0
)
```

### 集群模式
```python
SessionRedisConfig(
    addr="node1:6379,node2:6379,node3:6379",
    cluster_type="cluster"
)
```

### 哨兵模式
```python
SessionRedisConfig(
    addr="sentinel1:26379,sentinel2:26379,sentinel3:26379",
    cluster_type="sentinel",
    master_name="mymaster"
)
```

## 配置参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| addr | Redis地址，支持多地址 | localhost:6379 |
| username | 用户名 | "" |
| password | 密码 | "" |
| db | 数据库编号 | 0 |
| cluster_type | 集群类型 | single |
| master_name | 哨兵主节点名 | "" |
| prefix | 键前缀 | session |
| topic | 发布订阅主题 | session_updates |
| ttl | 会话过期时间 | 24小时 |

## 错误处理

```python
from myunla.gateway.session import SessionNotFoundError

try:
    conn = await store.get("nonexistent_session")
except SessionNotFoundError as e:
    print(f"会话不存在: {e.session_id}")
```

## 运行示例

```bash
# 运行示例代码
python myunla/gateway/session/example.py
```

## 依赖要求

- Python 3.9+
- redis[hiredis] >= 5.2.0 (用于Redis存储)
- aiorwlock >= 1.5.0 (用于读写锁)

## 注意事项

1. Redis存储需要Redis服务器支持
2. 内存存储数据不持久化，重启后丢失
3. Redis存储支持分布式部署和事件分发
4. 所有操作都是异步的，需要使用await
5. 记得在应用关闭时调用`store.close()`清理资源 