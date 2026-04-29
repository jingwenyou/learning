# 05 Web基础 —— 前后端交互全貌

> 安全漏洞发生在前后端交互的**每一个环节**。
> 你不需要会写Web应用，但必须理解**数据是怎么在前端和后端之间流动的**。
> 理解了这个过程，你就知道在哪里插入测试，在哪里找漏洞。

---

## 一、前端三件套：浏览器看到的一切

### 1.1 HTML —— 页面的骨架

```html
<!DOCTYPE html>
<html>
<head>
    <title>登录页面</title>
</head>
<body>
    <!-- 这是一个登录表单 -->
    <form action="/api/login" method="POST">
        <input type="text" name="username" placeholder="用户名">
        <input type="password" name="password" placeholder="密码">
        <input type="hidden" name="user_role" value="normal">  <!-- 隐藏字段！ -->
        <button type="submit">登录</button>
    </form>
</body>
</html>
```

**安全测试视角：**
```
1. 查看页面源码（右键→查看源代码，或Ctrl+U）
   - 隐藏字段（hidden input）→ 值能不能改？上面的user_role改成admin呢？
   - HTML注释 → 可能泄露内部信息、测试账号、API路径
   - 硬编码的API地址 → 更多攻击面

2. 表单的action和method
   - action="/api/login" → 这就是后端接口地址
   - method="POST" → 换成GET会怎样？

3. input的type
   - type="password" 只是不显示明文，不代表传输加密
   - type="hidden" 对用户隐藏，但F12里一览无余
```

### 1.2 CSS —— 页面的样式

CSS本身安全风险很小，但有两个关注点：
```
1. CSS可以隐藏元素：display:none 的元素可能包含敏感信息
2. CSS注入（罕见）：在某些场景下可以通过CSS泄露数据
```

### 1.3 JavaScript —— 页面的行为（安全重灾区）

```javascript
// 前端验证 —— 看起来安全，实际不安全
function validateForm() {
    var username = document.getElementById("username").value;
    if (username.length < 3) {
        alert("用户名太短");
        return false;  // 阻止提交
    }
    // 这个验证完全可以绕过（禁用JS、直接发请求、改前端代码）
    return true;
}

// 前端存储 —— 安全隐患
localStorage.setItem("token", "eyJhbGci...");  // XSS可以偷走
sessionStorage.setItem("user", "admin");

// AJAX请求 —— 真正的数据交互
fetch("/api/user/profile", {
    method: "GET",
    headers: {
        "Authorization": "Bearer " + localStorage.getItem("token")
    }
})
.then(response => response.json())
.then(data => {
    document.getElementById("name").innerText = data.name;
    // 如果data.name包含恶意脚本，这里可能触发XSS
    // 安全方式应该用 textContent 而不是 innerHTML
});
```

**安全测试视角：**
```
1. 前端验证 ≠ 安全
   所有前端验证都可以绕过。安全验证必须在后端。
   测试方法：用Burp Suite拦截请求，修改数据后放行

2. JavaScript源码是公开的
   F12 → Sources标签 → 所有JS代码一览无余
   可能发现：API密钥、内部API路径、业务逻辑、调试信息

3. 敏感数据存储
   F12 → Application标签 → 查看localStorage、sessionStorage、Cookie
   Token存在localStorage = XSS能偷走
```

---

## 二、后端：看不见但真正做事的地方

### 2.1 后端做什么

```
前端（浏览器）                        后端（服务器）
    |                                    |
    |--- HTTP请求 ---------------------->|
    |    POST /api/login                 |
    |    {"user":"admin","pass":"123"}   |
    |                                    |  1. 接收请求
    |                                    |  2. 解析参数
    |                                    |  3. 验证输入 ← 安全的关键！
    |                                    |  4. 查询数据库
    |                                    |  5. 处理业务逻辑
    |                                    |  6. 构造响应
    |                                    |
    |<--- HTTP响应 ----------------------|
    |    {"status":"ok","token":"xxx"}   |
```

### 2.2 后端处理请求的关键环节

**路由（Routing）** —— 请求到了后端，怎么知道该交给哪个函数处理？

```python
# Python Flask示例
@app.route("/api/login", methods=["POST"])    # 路由规则
def login():
    username = request.form["username"]        # 获取参数
    password = request.form["password"]
    # ... 处理逻辑

@app.route("/api/user/<int:user_id>")          # URL中的参数
def get_user(user_id):
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")  # SQL注入！
    return jsonify(user)
```

**安全问题就出在后端处理数据的过程中：**
```
获取参数 → 如果不验证 → 注入攻击
查询数据库 → 如果拼接SQL → SQL注入
返回数据 → 如果不过滤 → XSS
检查权限 → 如果不检查 → 越权
处理文件 → 如果不限制 → 文件上传漏洞
```

### 2.3 数据库：数据的最终归宿

```sql
-- 用户表（几乎所有Web应用都有）
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(255),   -- 应该存哈希，不是明文
    role VARCHAR(20)
);

-- 正常的查询
SELECT * FROM users WHERE username = 'admin' AND password = 'hashed_pwd';

-- SQL注入后的查询（输入 username = admin' OR 1=1 --)
SELECT * FROM users WHERE username = 'admin' OR 1=1 --' AND password = 'anything';
-- OR 1=1 永远为真 → 返回所有用户
-- -- 后面是注释 → 密码检查被跳过
```

**你需要理解的SQL（够用即可）：**
```sql
SELECT * FROM users;                           -- 查询所有用户
SELECT * FROM users WHERE id = 1;              -- 条件查询
INSERT INTO users (username, password) VALUES ('a', 'b');  -- 插入
UPDATE users SET password = 'new' WHERE id = 1;            -- 更新
DELETE FROM users WHERE id = 1;                             -- 删除

-- 这些就够理解SQL注入了
-- 更复杂的SQL（UNION, 子查询）在学SQL注入时会深入
```

---

## 三、前后端交互的方式

### 3.1 传统表单提交

```
浏览器                                     服务器
  |                                         |
  | POST /login                             |
  | Content-Type: application/x-www-form-urlencoded
  | Body: username=admin&password=123       |
  |---------------------------------------->|
  |                                         |
  |<--- 302 Redirect to /dashboard ---------|
  |                                         |
  | GET /dashboard                          |
  | Cookie: session=abc123                  |
  |---------------------------------------->|
  |                                         |
  |<--- 200 OK (HTML页面) ------------------|

特点：每次交互都是整个页面刷新
安全测试：重点看POST数据和Cookie
```

### 3.2 AJAX/Fetch（现代方式）

```
浏览器                                     服务器
  |                                         |
  | POST /api/login                         |
  | Content-Type: application/json          |
  | Body: {"username":"admin","password":"123"}
  |---------------------------------------->|
  |                                         |
  |<--- 200 OK ----------------------------|
  | Body: {"token":"eyJhbGci...","user":{...}}
  |                                         |
  | GET /api/user/profile                   |
  | Authorization: Bearer eyJhbGci...       |
  |---------------------------------------->|
  |                                         |
  |<--- 200 OK ----------------------------|
  | Body: {"name":"张三","role":"user"}      |

特点：不刷新页面，只交换数据（JSON）
安全测试：F12的Network标签可以看到所有AJAX请求
```

### 3.3 RESTful API（当前主流）

```
REST是一种设计风格，用HTTP方法表示操作：

GET    /api/users        → 获取用户列表
GET    /api/users/42     → 获取ID为42的用户
POST   /api/users        → 创建新用户
PUT    /api/users/42     → 更新用户42的全部信息
PATCH  /api/users/42     → 更新用户42的部分信息
DELETE /api/users/42     → 删除用户42

安全测试要做的事：
1. 列表接口 → 能不能看到不该看的数据？
2. 详情接口 → 改ID能不能看到别人的数据？（IDOR）
3. 创建接口 → 能不能创建管理员角色？
4. 更新接口 → 能不能改别人的数据？能不能改自己的角色？
5. 删除接口 → 能不能删别人的数据？
6. 每个接口 → 不带Token能不能访问？用普通用户的Token能不能访问管理接口？
```

---

## 四、同源策略与跨域（理解XSS和CSRF的前提）

### 4.1 同源策略（Same-Origin Policy）

```
"同源"的定义：协议 + 域名 + 端口 完全相同

https://www.example.com:443/page1
https://www.example.com:443/page2    ← 同源 ✓（路径不同没关系）
http://www.example.com:443/page1     ← 不同源 ✗（协议不同）
https://api.example.com:443/page1    ← 不同源 ✗（域名不同）
https://www.example.com:8080/page1   ← 不同源 ✗（端口不同）

同源策略的作用：
  浏览器禁止一个源的页面读取另一个源的数据。
  这样 evil.com 的JavaScript就不能读取 bank.com 的页面内容。

为什么重要：
  没有同源策略 → 你访问恶意网站时，它的JS可以读你银行页面的余额
  有同源策略 → 恶意网站的JS只能在自己的"沙盒"里玩
```

### 4.2 CORS（跨源资源共享）

```
有时候前后端不在同一个源（比如前端在 localhost:3000，后端在 localhost:8080）。
这时需要后端明确允许跨域请求。

响应头：
Access-Control-Allow-Origin: https://www.example.com   ← 只允许这个源
Access-Control-Allow-Origin: *                          ← 允许所有源（危险！）
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Allow-Credentials: true                  ← 允许携带Cookie

安全问题：
  Allow-Origin: * 且 Allow-Credentials: true
  → 任何网站都可以带着用户的Cookie请求你的API
  → 等于同源策略被废掉了
```

---

## 五、浏览器开发者工具（安全测试随身武器）

### 5.1 各面板的安全用途

```
[Elements面板]
  - 查看/修改HTML：找hidden字段、注释、硬编码信息
  - 修改前端验证：把disabled按钮改成enabled，maxlength改大

[Console面板]
  - 执行JavaScript：document.cookie 查看Cookie
  - 测试XSS payload是否会执行
  - 查看JS报错信息（可能泄露内部信息）

[Network面板]（最重要）
  - 查看所有HTTP请求/响应
  - 分析请求参数和响应数据
  - 观察登录流程、Token传递
  - Copy as cURL → 在终端重放请求

[Application面板]
  - Cookies：查看/修改/删除Cookie
  - LocalStorage/SessionStorage：查看存储的数据
  - 可以直接修改Cookie值测试越权

[Sources面板]
  - 查看所有JS源码
  - 搜索关键词：password、secret、api_key、token、admin
  - 设置断点调试前端逻辑
```

### 5.2 实战技巧

```
技巧1：修改请求（不用Burp也能做简单测试）
  Network面板 → 右键某个请求 → Copy as fetch
  → Console面板粘贴 → 修改参数 → 回车执行

技巧2：发现隐藏API
  Network面板 → 在页面上进行各种操作
  → 观察发出了哪些请求
  → 这些API地址就是你的测试目标

技巧3：查看WebSocket通信
  Network面板 → WS标签
  → 实时聊天、通知等功能常用WebSocket
  → 查看通信内容是否包含敏感信息
```

---

## 六、动手实践

### 实践1：分析一个真实网站的前后端交互

```
1. 打开一个需要登录的网站（最好用靶场）
2. 打开F12 → Network面板 → 勾选"Preserve log"
3. 执行登录操作
4. 在Network面板中找到登录请求，记录：
   - 请求方法和URL
   - Content-Type
   - 请求体（密码是明文还是加密？）
   - 响应中的Set-Cookie或Token
5. 登录后访问几个页面，观察：
   - 每个请求带了什么身份凭证
   - 有没有请求泄露了敏感信息
```

### 实践2：查看JavaScript中的敏感信息

```
1. 打开F12 → Sources面板
2. 按 Ctrl+Shift+F 全局搜索
3. 搜索以下关键词：
   - password
   - secret
   - api_key
   - token
   - admin
   - TODO
   - FIXME
   - debug
   - test
4. 检查搜到的内容是否包含真实的敏感信息
```

### 实践3：修改前端验证

```
1. 找一个有前端验证的表单（如"密码长度至少8位"）
2. F12 → Elements面板
3. 找到对应的input元素
4. 删除 minlength 属性，或修改 type="password" 为 type="text"
5. 提交一个不符合前端验证规则的值
6. 观察后端是否也做了验证
   - 后端也拒绝了 → 有双重验证（正确）
   - 后端接受了 → 只有前端验证（漏洞）
```

### 实践4：用Python模拟前后端交互

```python
"""模拟完整的Web交互流程"""
import requests

session = requests.Session()
base_url = "http://localhost:8081"  # DVWA靶场

# 1. 获取登录页面（观察是否有CSRF Token）
resp = session.get(f"{base_url}/login.php")
print("登录页面的Cookie:", session.cookies.get_dict())

# 2. 从HTML中提取CSRF Token（如果有的话）
# 简单方式：用正则或BeautifulSoup
from bs4 import BeautifulSoup
soup = BeautifulSoup(resp.text, "html.parser")
csrf_input = soup.find("input", {"name": "user_token"})
csrf_token = csrf_input["value"] if csrf_input else ""
print(f"CSRF Token: {csrf_token}")

# 3. 登录
login_data = {
    "username": "admin",
    "password": "password",
    "Login": "Login",
    "user_token": csrf_token,
}
resp = session.post(f"{base_url}/login.php", data=login_data)
print(f"登录结果: {resp.status_code}")
print(f"登录后Cookie: {session.cookies.get_dict()}")

# 4. 访问需要登录的页面
resp = session.get(f"{base_url}/vulnerabilities/sqli/")
print(f"受保护页面状态码: {resp.status_code}")
print(f"页面包含'Welcome': {'Welcome' in resp.text}")
```

---

## 七、安全测试的核心思维模型

学完Phase 1的所有基础，你应该建立这个思维模型：

```
用户输入
    ↓
[前端] ──── 验证？→ 能绕过吗？
    ↓
HTTP请求 ──── 能拦截和修改吗？（Burp Suite）
    ↓
[后端路由] ── 有没有未授权的接口？
    ↓
[后端处理] ── 对输入做了什么？过滤了吗？够不够？
    ↓
[数据库/文件系统] ── 数据怎么存的？怎么读的？
    ↓
HTTP响应 ──── 返回了什么？有没有泄露信息？
    ↓
[前端渲染] ── 数据怎么展示的？会不会执行恶意代码？
```

**安全测试就是在这个数据流的每一个环节找问题。**

---

## 八、自测清单

- [ ] HTML中的hidden字段安全吗？为什么？
- [ ] 前端验证能替代后端验证吗？
- [ ] 同源策略保护了什么？CORS是怎么"打开"这个保护的？
- [ ] RESTful API的增删改查分别对应什么HTTP方法？
- [ ] 用F12能发现哪些安全相关的信息？
- [ ] 一个HTTP请求从前端到数据库，经过哪些环节？每个环节可能有什么安全问题？
- [ ] `Access-Control-Allow-Origin: *` 为什么危险？
- [ ] 能用Python的requests模拟一个完整的登录+访问流程？

**Phase 1 完成标志：** 以上所有清单全部通过，且DVWA靶场已成功部署并能登录。

---

> **下一阶段：** [Phase 2 - 安全核心](../../phase-2-security-core/01-security-mindset/README.md) —— 从测试思维到攻击者思维
