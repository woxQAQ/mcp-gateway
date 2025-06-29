# API Template DSL

一个专为API配置和模板设计的领域特定语言(DSL)，支持复杂的数据转换、类型安全和良好的错误处理。

## 特性

- **简洁易读的语法** - 类似JavaScript的表达式语法
- **类型安全** - 内置类型系统和类型检查  
- **丰富的内置函数** - 支持数组、对象、字符串等常用操作
- **管道操作** - 支持数据流式处理
- **条件表达式** - 支持三元运算符和复杂逻辑
- **错误处理** - 友好的错误信息和异常处理

## 语法概览

### 基本表达式

```javascript
// 变量访问
user.name
config.baseUrl
args.userId

// 字面量
"hello world"
123
true
null

// 数组和对象
[1, 2, 3]
{name: "Alice", age: 30}
```

### 运算符

```javascript
// 算术运算
1 + 2
"hello" + " world"
[1, 2] + [3, 4]

// 比较运算  
user.age > 18
user.role == "admin"

// 逻辑运算
user.active && user.verified
user.role == "admin" || user.role == "moderator"
```

### 条件表达式

```javascript
// 三元运算符
user.role == "admin" ? "allowed" : "denied"

// 复杂条件
user.age >= 18 ? 
  (user.verified ? "full_access" : "limited_access") : 
  "restricted"
```

### 管道操作

```javascript
// 数据流处理
users | filter(data, u => u.active) | map(data, u => u.name)

// 链式操作
data | sort(data) | slice(data, 0, 10) | join(data, ", ")
```

### 函数调用

```javascript
// 内置函数
length(users)
toString(user.id)
toJSON({name: user.name})

// 数组操作
map(users, user => user.name)
filter(users, user => user.active)
sort(users, user => user.age)
```

## 内置函数

### 类型转换
- `toString(value)` - 转换为字符串
- `toNumber(value)` - 转换为数字
- `toJSON(value)` - 转换为JSON字符串
- `fromJSON(value)` - 从JSON字符串解析

### 数组操作
- `length(array)` - 获取长度
- `map(array, func)` - 映射
- `filter(array, func)` - 过滤
- `find(array, func)` - 查找
- `sort(array, keyFunc?)` - 排序
- `slice(array, start, end?)` - 切片
- `concat(...arrays)` - 连接
- `join(array, separator)` - 连接成字符串

### 对象操作
- `keys(object)` - 获取键
- `values(object)` - 获取值
- `merge(...objects)` - 合并对象
- `pick(object, ...keys)` - 选择字段
- `omit(object, ...keys)` - 排除字段

### 字符串操作
- `split(string, separator)` - 分割
- `replace(string, search, replacement)` - 替换
- `match(string, pattern)` - 正则匹配
- `extract(string, pattern)` - 正则提取

### 工具函数
- `default(value, defaultValue)` - 默认值

## 使用示例

### API URL构建

```javascript
// 基本URL构建
config.baseUrl + "/users/" + toString(args.userId)

// 带查询参数
config.baseUrl + "/users?page=" + toString(args.page) + "&limit=" + toString(args.limit)

// 条件URL
args.includeDetails ? 
  config.baseUrl + "/users/" + toString(args.userId) + "/details" :
  config.baseUrl + "/users/" + toString(args.userId)
```

### 请求头构建

```javascript
// 基本请求头
{
  "Authorization": "Bearer " + config.token,
  "Content-Type": "application/json",
  "User-Agent": config.userAgent
}

// 条件请求头
merge(
  {"Content-Type": "application/json"},
  config.token ? {"Authorization": "Bearer " + config.token} : {},
  args.correlationId ? {"X-Correlation-ID": args.correlationId} : {}
)
```

### 请求体构建

```javascript
// 简单请求体
{
  "name": args.name,
  "email": args.email,
  "age": toNumber(args.age)
}

// 条件字段
merge(
  {"name": args.name, "email": args.email},
  args.age ? {"age": toNumber(args.age)} : {},
  args.phone ? {"phone": args.phone} : {}
)
```

### 数据转换

```javascript
// 用户列表转换
users | 
  filter(data, user => user.active) |
  map(data, user => {
    id: user.id,
    name: user.firstName + " " + user.lastName,
    email: user.email
  }) |
  sort(data, user => user.name)

// 分页处理
users | 
  slice(data, args.page * args.limit, (args.page + 1) * args.limit)
```

### 响应处理

```javascript
// 提取特定字段
response.data | map(data, item => pick(item, "id", "name", "status"))

// 错误处理
response.success ? 
  response.data : 
  {error: response.message, code: response.errorCode}
```

## Python集成

```python
from mcp_gateway.dsl import parse_and_execute, validate_expression

# 执行DSL表达式
context = {
    "user": {"name": "Alice", "id": 123},
    "config": {"baseUrl": "https://api.example.com"}
}

result = parse_and_execute('config.baseUrl + "/users/" + toString(user.id)', context)
if result.success:
    print(result.value)  # "https://api.example.com/users/123"
else:
    print(f"Error: {result.error.message}")

# 验证表达式
result = validate_expression("user.name")
print(f"Valid: {result.success}")
```

## 错误处理

DSL提供了友好的错误信息：

```python
# 语法错误
result = parse_and_execute("user.name +", context)
# Error: Unexpected end of input

# 运行时错误
result = parse_and_execute("1 / 0", context)  
# Error: Division by zero

# 类型错误
result = parse_and_execute('length("not an array")', context)
# 返回 0 (graceful degradation)
```

## 扩展性

可以注册自定义函数：

```python
from mcp_gateway.dsl.functions import register_function
from mcp_gateway.dsl.types import DSLValue

def custom_hash(value: DSLValue) -> DSLValue:
    import hashlib
    content = str(value.to_python())
    hash_value = hashlib.md5(content.encode()).hexdigest()
    return DSLValue.from_python(hash_value)

register_function("hash", custom_hash)

# 使用自定义函数
result = parse_and_execute('hash(user.email)', context)
```

## 性能特点

- 词法分析和语法分析使用高效的算法
- 访问者模式确保良好的可扩展性
- 内置函数经过优化
- 支持复杂表达式的快速执行

这个DSL专门为OpenAPI到MCP的配置转换而设计，提供了比传统模板引擎更强大和灵活的能力。 