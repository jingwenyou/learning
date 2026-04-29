# 02 HTTP协议深入 —— Web安全的核心战场

> **HTTP是安全测试中你接触最多的协议，没有之一。**
> SQL注入、XSS、CSRF、越权……所有Web漏洞的载体都是HTTP请求和响应。
> 把HTTP吃透，后面学任何漏洞都事半功倍。

---

## 一、HTTP到底是什么

HTTP = HyperText Transfer Protocol（超文本传输协议）

**一句话理解：** 浏览器和服务器之间"对话"的规则。

```
浏览器（客户端）说："我要看 /index.html 这个页面"   ← 请求（Request）
服务器说："好的，给你，内容如下……"                 ← 响应（Response）
```

HTTP是**无状态的** —— 服务器不会记住"你是谁"。每次请求都是独立的。
这个特性直接导致了Cookie/Session/Token的诞生，也导致了一大类安全问题。

---

## 二、HTTP请求：你发出去的每一个动作

### 2.1 请求的完整结构

```http
POST /api/login HTTP/1.1              ← 请求行：方法 + 路径 + 协议版本
Host: www.example.com                  ← 请求头开始
Content-Type: application/json
Cookie: session=abc123
User-Agent: Mozilla/5.0 ...
Authorization: Bearer eyJhbGci...
Content-Length: 51
                                       ← 空行（分隔头和体）
{"username":"admin","password":"123"}  ← 请求体（Body）
```

### 2.2 请求方法：不只是GET和POST

| 方法 | 用途 | 有请求体 | 安全测试关注点 |
|------|------|---------|--------------|
| GET | 获取资源 | 无 | 参数在URL中，容易被日志记录、缓存、泄露 |
| POST | 提交数据 | 有 | 登录、表单提交、文件上传 |
| PUT | 更新资源（整体替换） | 有 | 未授权的PUT可能覆盖资源 |
| PATCH | 更新资源（部分修改） | 有 | 同PUT |
| DELETE | 删除资源 | 可选 | 未授权的DELETE = 直接删数据 |
| OPTIONS | 查询支持的方法 | 无 | CORS预检请求，配置不当会泄露信息 |
| HEAD | 同GET但只返回头 | 无 | 探测资源是否存在 |
| TRACE | 回显请求 | 无 | 可能导致XST攻击，应该禁用 |

**安全测试要做的事：**
```
1. 一个只应该接受GET的接口，试试POST、PUT、DELETE
2. 试试OPTIONS请求，看服务器支持哪些方法
3. 试试TRACE请求，看是否被禁用
```

### 2.3 请求头：信息量最大的部分

**必须深入理解的请求头：**

```http
Host: www.example.com
```
- 指定请求的目标域名
- 一台服务器可能托管多个网站，靠Host区分
- **安全相关：** Host头注入 —— 篡改Host头可能导致密码重置链接指向攻击者的域名

```http
Cookie: session=abc123; user_id=42
```
- 浏览器自动携带的身份信息
- **安全相关：** 这是身份认证的核心，偷到Cookie = 偷到身份
- **安全相关：** 观察Cookie的值——是明文？可预测的数字？还是加密的Token？

```http
Content-Type: application/json
Content-Type: application/x-www-form-urlencoded
Content-Type: multipart/form-data
```
- 告诉服务器请求体的格式
- **安全相关：** 改Content-Type可能绕过服务端验证
  - 例：服务端只过滤了form-urlencoded格式的SQL注入，换成json就绕过了

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
```
- 标识客户端类型
- **安全相关：** 可以随意伪造，不能作为安全判断依据
- **安全相关：** 有些WAF规则基于UA，改UA可能绕过

```http
Referer: https://www.example.com/dashboard
```
- 告诉服务器"我是从哪个页面跳过来的"
- **安全相关：** 有些CSRF防护依赖Referer检查，可以被绕过
- **安全相关：** Referer可能泄露敏感URL中的信息

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```
- API认证常用方式，携带JWT或其他Token
- **安全相关：** JWT的安全性（后面认证模块详细讲）

---

## 三、HTTP响应：服务器告诉你的一切

### 3.1 响应的完整结构

```http
HTTP/1.1 200 OK                       ← 状态行：协议版本 + 状态码 + 原因短语
Content-Type: text/html; charset=utf-8 ← 响应头开始
Set-Cookie: session=xyz789; HttpOnly; Secure; SameSite=Strict
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
                                       ← 空行
<html>页面内容</html>                  ← 响应体
```

### 3.2 状态码：服务器的"表情"

```
2xx 成功
  200 OK              ← 正常返回
  201 Created         ← 资源创建成功（POST后常见）
  204 No Content      ← 成功但没有返回内容

3xx 重定向
  301 Moved Permanently  ← 永久重定向
  302 Found              ← 临时重定向
  304 Not Modified       ← 缓存可用，不需要重新传输

  安全相关：重定向到哪？如果重定向的URL可控 → 开放重定向漏洞
  例：https://example.com/redirect?url=https://evil.com

4xx 客户端错误
  400 Bad Request     ← 请求格式错误
  401 Unauthorized    ← 未认证（没登录）
  403 Forbidden       ← 无权限（登录了但没权限）
  404 Not Found       ← 资源不存在
  405 Method Not Allowed ← 方法不允许

  安全相关：
  - 401 vs 403 的区别很重要——有些系统对不存在的资源返回403而不是404，
    这就泄露了"资源存在"的信息
  - 通过观察不同ID的响应码差异，可以枚举有效资源

5xx 服务器错误
  500 Internal Server Error  ← 服务端代码出错
  502 Bad Gateway            ← 网关错误
  503 Service Unavailable    ← 服务不可用

  安全相关：
  - 500错误的详细信息可能泄露代码路径、数据库类型、框架版本
  - 故意触发500错误是安全测试的常用手法
```

### 3.3 安全相关的响应头（重点）

这些响应头是服务器的"安全防线"，安全测试要检查它们是否存在且配置正确：

```http
Set-Cookie: session=xxx; HttpOnly; Secure; SameSite=Strict
```
- `HttpOnly` → JavaScript无法读取此Cookie → 防XSS偷Cookie
- `Secure` → 只在HTTPS时发送 → 防中间人窃取
- `SameSite=Strict` → 跨站请求不携带 → 防CSRF
- **测试：** 检查登录后的Set-Cookie是否包含这三个属性

```http
X-Frame-Options: DENY
```
- 禁止页面被嵌入iframe
- **缺失风险：** 点击劫持（Clickjacking）—— 透明iframe覆盖在诱导页面上

```http
Content-Security-Policy: default-src 'self'; script-src 'self'
```
- 限制页面能加载的资源来源
- **作用：** 即使有XSS漏洞，CSP也能阻止恶意脚本执行
- **测试：** 检查CSP策略是否过于宽松（比如允许 'unsafe-inline'）

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```
- 强制浏览器只用HTTPS访问
- **缺失风险：** SSL剥离攻击——中间人把HTTPS降级为HTTP

```http
X-Content-Type-Options: nosniff
```
- 禁止浏览器猜测Content-Type
- **缺失风险：** MIME类型混淆，上传的txt被当成html执行

---

## 四、HTTP的"记忆"：Cookie、Session、Token

HTTP本身无状态，但用户需要"登录状态"。三种实现方式：

### 4.1 Cookie + Session（传统方式）

```
[登录流程]
1. 用户提交用户名/密码
2. 服务器验证通过，在服务端创建Session（内存/数据库中保存）
   Session: { id: "abc123", user: "zhangsan", role: "admin" }
3. 服务器返回 Set-Cookie: session_id=abc123
4. 之后每次请求，浏览器自动带上 Cookie: session_id=abc123
5. 服务器根据session_id找到对应Session，知道你是谁

[安全问题]
- Session ID可预测 → 攻击者猜出别人的Session ID → 冒充身份
- Session ID泄露（URL中、日志中、Referer中）→ 身份被盗
- Session不过期 → 偷一次永久有效
- Cookie没设HttpOnly → XSS可以偷走Cookie
```

### 4.2 Token（现代方式，JWT为例）

```
[登录流程]
1. 用户提交用户名/密码
2. 服务器验证通过，生成JWT Token：
   Header.Payload.Signature
   eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiemhhbmdzYW4iLCJyb2xlIjoiYWRtaW4ifQ.签名
3. 返回给客户端，客户端保存在localStorage或Cookie中
4. 之后每次请求带上 Authorization: Bearer eyJhbGci...
5. 服务器验证签名，从Token中直接读取用户信息

[安全问题]
- 算法设置为none → 不验证签名 → 任意伪造Token
- 密钥太简单 → 可以爆破
- Token不过期 → 和Session同样的问题
- 存在localStorage → XSS可以偷走
- 存在Cookie → 要注意CSRF

[一个关键区别]
Session：身份信息在服务端，客户端只有一个ID
Token：身份信息在客户端（Token本身包含用户信息），服务端无状态

这意味着：Token一旦签发，服务端无法主动让它失效（除非额外维护黑名单）
```

### 4.3 安全测试的检查点

```
□ Session ID/Token 是否足够随机（不可预测）
□ 是否设置了合理的过期时间
□ 登出后Session/Token是否真的失效了
□ 是否能同时存在多个有效Session（多设备登录控制）
□ Cookie是否设置了HttpOnly、Secure、SameSite
□ JWT的算法是否安全（不是none，不是弱密钥）
□ Token是否包含敏感信息（解码JWT的Payload看看）
```

---

## 五、HTTPS：加密的HTTP

### 5.1 为什么需要HTTPS

HTTP是**明文传输**的。这意味着：
- 同一个WiFi下的人可以看到你的所有请求
- 运营商可以看到你访问的内容（甚至注入广告）
- 任何经过的网络设备都可以偷看

HTTPS = HTTP + TLS（传输层安全协议）

### 5.2 TLS握手简化过程

```
客户端                              服务端
  |                                  |
  |-- ClientHello ------------------>|  "我支持这些加密算法：A, B, C"
  |                                  |
  |<-- ServerHello + 证书 -----------|  "用算法B吧，这是我的证书"
  |                                  |
  |  [验证证书是否可信]               |
  |  [用证书中的公钥加密一个随机数]    |
  |                                  |
  |-- 加密的随机数 ------------------>|
  |                                  |
  |  [双方根据随机数生成相同的对称密钥]|
  |                                  |
  |<========= 加密通信 =============>|  用对称密钥加密所有数据
```

**核心：** 非对称加密交换密钥 → 对称加密传输数据

### 5.3 安全测试的关注点

```
□ 是否全站HTTPS（不要HTTP和HTTPS混用）
□ 是否有HTTP到HTTPS的重定向
□ TLS版本是否安全（TLS 1.2+，禁用SSL 3.0、TLS 1.0、TLS 1.1）
□ 证书是否有效、未过期、域名匹配
□ 是否配置了HSTS头
□ 是否存在混合内容（HTTPS页面加载HTTP资源）
```

---

## 六、动手实践

### 实践1：用浏览器F12分析HTTP

```
1. 打开浏览器 → F12 → Network标签
2. 访问任意网站（如 www.baidu.com）
3. 观察：
   - 请求方法、URL、状态码
   - 请求头中的Cookie、User-Agent、Referer
   - 响应头中的Set-Cookie、安全相关头
   - 响应体的内容
4. 找一个需要登录的网站：
   - 观察登录请求的Content-Type和Body
   - 密码是明文还是加密的？
   - 登录后Set-Cookie返回了什么？
```

### 实践2：用curl手工发请求

```bash
# 基本GET请求，显示响应头
curl -I https://www.baidu.com

# 完整请求和响应（包括头）
curl -v https://www.example.com

# 发送POST请求（模拟表单提交）
curl -X POST https://httpbin.org/post \
  -d "username=admin&password=123456"

# 发送JSON数据
curl -X POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'

# 自定义Cookie
curl -b "session=abc123" https://httpbin.org/cookies

# 自定义User-Agent
curl -A "MyCustomAgent/1.0" https://httpbin.org/user-agent

# 测试不同HTTP方法
curl -X PUT https://httpbin.org/put -d "data=test"
curl -X DELETE https://httpbin.org/delete
curl -X OPTIONS -I https://httpbin.org/get
```

### 实践3：解码JWT

```bash
# 安装jwt-cli或者用Python
# Python方式：
python3 -c "
import base64, json, sys

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
parts = token.split('.')

for i, part in enumerate(parts[:2]):
    # 补齐base64填充
    padded = part + '=' * (4 - len(part) % 4)
    decoded = base64.urlsafe_b64decode(padded)
    name = 'Header' if i == 0 else 'Payload'
    print(f'{name}: {json.dumps(json.loads(decoded), indent=2)}')
"

# 观察：Payload里有什么信息？role字段能不能改？
```

### 实践4：检查安全响应头

```bash
# 检查目标网站的安全头
curl -s -I https://www.example.com | grep -iE "(strict-transport|content-security|x-frame|x-content-type|set-cookie)"

# 对比几个网站，看哪些安全头缺失
# 尝试：你们公司的测试环境、大厂网站、小网站
# 你会发现差异很大
```

---

## 七、自测清单

- [ ] HTTP请求由哪几部分组成？每部分的作用？
- [ ] GET和POST的本质区别是什么？（不是"GET获取POST提交"这种表面回答）
- [ ] Cookie、Session、Token的区别和各自的安全风险？
- [ ] HttpOnly、Secure、SameSite分别防御什么攻击？
- [ ] 301和302的区别？开放重定向漏洞怎么产生的？
- [ ] 401和403的区别？为什么这对安全测试有意义？
- [ ] HTTPS的TLS握手大致过程？为什么能防中间人？
- [ ] Content-Type在安全测试中为什么重要？
- [ ] 看到一个HTTP响应，你能列出哪些安全问题的检查点？

---

> **下一模块：** [03 Linux基础](../03-linux-essentials/README.md) —— 安全工具的运行环境
