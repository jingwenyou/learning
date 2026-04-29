# 04 Python安全脚本 —— 你的自动化武器

> 安全测试工具很多，但总有工具覆盖不到的场景。
> 会写Python脚本，你就能**自己造工具**——批量测试、自动化验证、数据处理。
> 不需要精通，够用就行。

---

## 一、为什么选Python

- 安全社区的主力语言（sqlmap、Burp插件、PoC脚本……大部分用Python写）
- 语法简单，上手快
- `requests` 库让HTTP操作极其方便
- 大量安全相关的第三方库

**目标：** 能写脚本发HTTP请求、处理响应、批量操作。不需要学算法和设计模式。

---

## 二、环境准备

```bash
# 确认Python3已安装
python3 --version

# 安装pip（Python包管理器）
apt install python3-pip    # Ubuntu
# 或
yum install python3-pip    # CentOS

# 安装核心库
pip3 install requests      # HTTP请求
pip3 install beautifulsoup4  # HTML解析
pip3 install pyjwt         # JWT处理
```

---

## 三、Python速成（只学安全测试用得到的）

### 3.1 基础语法

```python
# 变量和类型
url = "https://example.com"       # 字符串
port = 8080                        # 整数
is_vulnerable = True               # 布尔
targets = ["192.168.1.1", "192.168.1.2"]  # 列表
headers = {"Cookie": "session=abc", "User-Agent": "test"}  # 字典

# 字符串操作（安全测试中非常频繁）
payload = "' OR 1=1 --"
url = f"https://target.com/search?q={payload}"  # f-string拼接
print(url)

# 字符串方法
response_text = "Login failed: invalid password"
if "failed" in response_text:
    print("登录失败")

text = "admin:password123"
username, password = text.split(":")  # 分割

# 条件判断
status_code = 200
if status_code == 200:
    print("请求成功")
elif status_code == 403:
    print("无权限")
else:
    print(f"其他状态码: {status_code}")

# 循环
# 遍历列表
for target in targets:
    print(f"扫描: {target}")

# 范围循环
for i in range(1, 101):       # 1到100
    print(f"测试ID: {i}")

# 读写文件
# 读取字典文件（暴力破解用）
with open("passwords.txt", "r") as f:
    for line in f:
        password = line.strip()  # 去掉换行符
        print(password)

# 写入结果
with open("results.txt", "w") as f:
    f.write("发现漏洞: SQL注入\n")
    f.write("URL: https://target.com/search?q='\n")
```

### 3.2 函数

```python
def check_url(url):
    """检查URL是否可访问"""
    import requests
    try:
        resp = requests.get(url, timeout=5)
        return resp.status_code
    except requests.exceptions.RequestException as e:
        return None

# 调用
status = check_url("https://example.com")
if status:
    print(f"状态码: {status}")
else:
    print("无法连接")
```

### 3.3 异常处理

```python
import requests

try:
    resp = requests.get("https://target.com", timeout=5)
    resp.raise_for_status()
except requests.exceptions.Timeout:
    print("请求超时")
except requests.exceptions.ConnectionError:
    print("连接失败")
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
```

---

## 四、requests库：安全测试的核心武器

### 4.1 基本请求

```python
import requests

# GET请求
resp = requests.get("https://httpbin.org/get")
print(resp.status_code)        # 状态码
print(resp.headers)            # 响应头（字典）
print(resp.text)               # 响应体（字符串）
print(resp.json())             # 响应体（解析为JSON字典）

# POST请求 - 表单数据
resp = requests.post("https://httpbin.org/post",
    data={"username": "admin", "password": "123456"})

# POST请求 - JSON数据
resp = requests.post("https://httpbin.org/post",
    json={"username": "admin", "password": "123456"})
```

### 4.2 自定义Headers和Cookies

```python
# 自定义请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Authorization": "Bearer eyJhbGci...",
    "X-Forwarded-For": "127.0.0.1",      # 伪造IP（有些服务端信任这个头）
}
resp = requests.get("https://target.com/api/user", headers=headers)

# 自定义Cookie
cookies = {"session": "abc123", "role": "admin"}
resp = requests.get("https://target.com/dashboard", cookies=cookies)
```

### 4.3 Session保持（重要）

```python
# 使用Session对象，自动处理Cookie
session = requests.Session()

# 第1步：登录
login_data = {"username": "admin", "password": "admin"}
session.post("http://target.com/login", data=login_data)
# Session自动保存了服务器返回的Cookie

# 第2步：访问需要登录的页面（自动带上Cookie）
resp = session.get("http://target.com/admin/dashboard")
print(resp.text)

# 第3步：继续操作（Cookie自动携带）
resp = session.get("http://target.com/admin/users")
```

### 4.4 处理重定向和SSL

```python
# 禁止自动重定向（观察302跳转）
resp = requests.get("http://target.com/admin", allow_redirects=False)
print(resp.status_code)         # 302
print(resp.headers["Location"]) # 跳转目标

# 忽略SSL证书错误（测试环境常用）
resp = requests.get("https://self-signed.target.com", verify=False)
# 生产环境永远不要用 verify=False
```

---

## 五、实战脚本：从简单到进阶

### 脚本1：批量检查安全响应头

```python
"""检查目标网站的安全响应头配置"""
import requests

def check_security_headers(url):
    """检查一个URL的安全头"""
    security_headers = {
        "Strict-Transport-Security": "缺失 → 可能遭受SSL剥离攻击",
        "X-Frame-Options": "缺失 → 可能遭受点击劫持",
        "X-Content-Type-Options": "缺失 → 可能遭受MIME类型混淆",
        "Content-Security-Policy": "缺失 → XSS防护减弱",
        "X-XSS-Protection": "缺失 → 旧浏览器XSS防护缺失",
    }

    try:
        resp = requests.get(url, timeout=10, verify=False)
        print(f"\n{'='*60}")
        print(f"目标: {url}")
        print(f"状态码: {resp.status_code}")
        print(f"{'='*60}")

        for header, risk in security_headers.items():
            value = resp.headers.get(header)
            if value:
                print(f"  [✓] {header}: {value}")
            else:
                print(f"  [✗] {header} — {risk}")

        # 检查Cookie安全属性
        for cookie_header in resp.headers.get("Set-Cookie", "").split(","):
            if cookie_header.strip():
                print(f"\n  Cookie: {cookie_header.strip()}")
                if "HttpOnly" not in cookie_header:
                    print(f"    [!] 缺少HttpOnly")
                if "Secure" not in cookie_header:
                    print(f"    [!] 缺少Secure")
                if "SameSite" not in cookie_header:
                    print(f"    [!] 缺少SameSite")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {url}: {e}")


# 使用
urls = [
    "https://www.baidu.com",
    "https://www.github.com",
    "https://www.example.com",
]

for url in urls:
    check_security_headers(url)
```

### 脚本2：简单的目录枚举

```python
"""探测目标网站的常见敏感路径"""
import requests

def dir_scan(base_url, wordlist):
    """目录枚举扫描"""
    found = []

    for path in wordlist:
        url = f"{base_url.rstrip('/')}/{path}"
        try:
            resp = requests.get(url, timeout=5, allow_redirects=False)
            if resp.status_code != 404:
                status = resp.status_code
                length = len(resp.text)
                print(f"  [{status}] {url} (长度: {length})")
                found.append({"url": url, "status": status})
        except requests.exceptions.RequestException:
            pass

    return found


# 常见敏感路径
common_paths = [
    "robots.txt",          # 爬虫规则，可能暴露隐藏路径
    ".git/config",         # Git配置泄露
    ".env",                # 环境变量泄露
    "admin",               # 管理后台
    "admin/login",
    "wp-admin",            # WordPress后台
    "phpinfo.php",         # PHP信息泄露
    "swagger-ui.html",     # API文档泄露
    "api/docs",
    ".DS_Store",           # macOS文件泄露
    "backup.sql",          # 数据库备份
    "test",
    "debug",
]

print("目录枚举开始...")
results = dir_scan("http://target.com", common_paths)
print(f"\n发现 {len(results)} 个非404路径")
```

### 脚本3：越权检测（IDOR）

```python
"""
越权检测：用用户A的Token访问用户B的资源
这是测试工程师最容易上手的安全测试
"""
import requests

# 模拟两个用户的Session
user_a_token = "Bearer token_of_user_a"
user_b_token = "Bearer token_of_user_b"

base_url = "http://target.com/api"

# 用户A的资源ID
user_a_resources = [101, 102, 103]
# 用户B的资源ID
user_b_resources = [201, 202, 203]

print("=== 越权测试：用户A尝试访问用户B的资源 ===\n")

for resource_id in user_b_resources:
    url = f"{base_url}/orders/{resource_id}"
    resp = requests.get(url, headers={"Authorization": user_a_token})

    if resp.status_code == 200:
        print(f"  [漏洞!] {url} → 用户A能访问用户B的数据！")
        print(f"         响应: {resp.text[:100]}...")
    elif resp.status_code == 403:
        print(f"  [安全] {url} → 正确拒绝了越权访问")
    else:
        print(f"  [?]    {url} → 状态码: {resp.status_code}")
```

### 脚本4：登录暴力破解检测

```python
"""
测试登录接口是否有暴力破解防护
注意：只在授权的测试环境中使用！
"""
import requests
import time

def test_brute_force_protection(login_url, username, passwords):
    """测试登录是否有频率限制/账户锁定"""

    session = requests.Session()
    results = {"success": None, "locked": False, "rate_limited": False}

    for i, password in enumerate(passwords, 1):
        resp = session.post(login_url, data={
            "username": username,
            "password": password
        }, allow_redirects=False)

        status = resp.status_code

        # 检测是否被锁定
        if status == 429:
            print(f"  [第{i}次] 被限频(429) — 有暴力破解防护 ✓")
            results["rate_limited"] = True
            break

        if "locked" in resp.text.lower() or "too many" in resp.text.lower():
            print(f"  [第{i}次] 账户被锁定 — 有暴力破解防护 ✓")
            results["locked"] = True
            break

        # 检测是否登录成功
        if status in (200, 302) and "error" not in resp.text.lower():
            print(f"  [第{i}次] 密码 '{password}' 登录成功！")
            results["success"] = password
            break

        print(f"  [第{i}次] 密码 '{password}' 失败 (状态码:{status})")

    if not results["rate_limited"] and not results["locked"] and not results["success"]:
        print(f"\n  [!] 尝试了{len(passwords)}次，没有任何防护措施 → 存在暴力破解风险")

    return results

# 使用示例（只在靶场中使用！）
passwords = ["123456", "password", "admin", "admin123", "test", "root",
             "letmein", "welcome", "monkey", "dragon"]

test_brute_force_protection(
    "http://localhost:8081/login.php",
    "admin",
    passwords
)
```

---

## 六、Python安全测试常用技巧

### Base64编解码

```python
import base64

# 编码
encoded = base64.b64encode(b"admin:password").decode()
print(encoded)  # YWRtaW46cGFzc3dvcmQ=

# 解码
decoded = base64.b64decode("YWRtaW46cGFzc3dvcmQ=").decode()
print(decoded)  # admin:password

# URL安全的Base64（JWT用的就是这个）
encoded = base64.urlsafe_b64encode(b'{"user":"admin"}').decode()
```

### URL编码

```python
from urllib.parse import quote, unquote, urlencode

# 编码特殊字符
encoded = quote("' OR 1=1 --")
print(encoded)  # %27%20OR%201%3D1%20--

# 解码
decoded = unquote("%27%20OR%201%3D1%20--")
print(decoded)  # ' OR 1=1 --

# 构造查询参数
params = urlencode({"q": "' OR 1=1 --", "page": "1"})
print(params)  # q=%27+OR+1%3D1+--&page=1
```

### 哈希计算

```python
import hashlib

text = "password123"

# MD5（不安全，但很多系统还在用）
print(hashlib.md5(text.encode()).hexdigest())
# 482c811da5d5b4bc6d497ffa98491e38

# SHA256
print(hashlib.sha256(text.encode()).hexdigest())

# 安全测试用途：
# - 比对密码哈希
# - 验证文件完整性
# - 识别哈希类型（MD5是32位hex，SHA256是64位hex）
```

---

## 七、自测清单

- [ ] 能用requests发GET/POST请求？
- [ ] 能自定义Headers和Cookies？
- [ ] 能用Session保持登录状态？
- [ ] 能读写文件？
- [ ] 能写一个简单的批量检测脚本（比如批量检查安全头）？
- [ ] 知道Base64编解码、URL编码怎么用？
- [ ] 能处理JSON响应数据？

**验证方式：** 把上面5个脚本都跑一遍（用httpbin.org或靶场），能看懂输出结果。

---

> **下一模块：** [05 Web基础](../05-web-fundamentals/README.md) —— 前后端交互全貌
