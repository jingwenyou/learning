# OAuth 2.0安全测试 — 实战练习指南

> 本练习主要使用 PortSwigger Web Security Academy 的免费 OAuth Labs，
> 以及浏览器 DevTools 分析真实 OAuth 流程。

---

## 环境准备

```
[必备] PortSwigger 账号（免费注册）
  https://portswigger.net/web-security/oauth

[必备] Burp Suite 社区版（用于拦截 OAuth 重定向请求）
  下载：https://portswigger.net/burp/communitydownload

[可选] 浏览器 DevTools
  Network 面板用于抓取 OAuth 授权请求参数
```

---

## 练习1：观察真实 OAuth 流程（理解机制）

```
找一个使用第三方登录的网站（如 GitHub 登录），观察完整 OAuth 流程。

1.1 打开浏览器 DevTools → Network 面板
  点击 GitHub 登录按钮

1.2 找到第一个授权请求（跳转到 GitHub 的请求）
  URL 形如：
  https://github.com/login/oauth/authorize?
    client_id=Iv1.xxxx&
    redirect_uri=https://app.com/callback&
    scope=user:email&
    state=xxxxxxxx

1.3 记录并检查每个参数：

  client_id    → 是否存在？（必须有）
  redirect_uri → 是什么？能否被修改为其他域名？
  scope        → 请求了哪些权限？是否超出必要范围？
  state        → 是否存在？长度是否足够（建议 ≥ 16 字符）？
  code_challenge → 是否使用了 PKCE？

1.4 完成登录，找到回调请求
  URL 形如：
  https://app.com/callback?
    code=xxxxxxxxxxxx&
    state=xxxxxxxx

  检查：
  - state 值是否和授权请求中的一致？（应该一致）
  - code 是否只出现一次就失效？（可以尝试刷新回调URL）

记录你的观察结果：
  □ 存在 state 参数
  □ state 值 ≥ 16 字符
  □ 使用了 PKCE
  □ scope 合理
```

---

## 练习2：PortSwigger OAuth Lab 1 — 通过 implicit flow 绕过认证

```
Lab 地址：
  https://portswigger.net/web-security/oauth/lab-oauth-authentication-bypass-via-oauth-implicit-flow

目标：理解 Implicit 模式的安全问题，通过修改 Token 响应登录其他账号

背景：
  Implicit 模式下，Access Token 直接通过 URL fragment 返回给前端：
  https://app.com/callback#access_token=xxx&token_type=bearer
  前端 JS 读取 Token 后提交给后端验证。

步骤：

2.1 在 Burp 中拦截所有请求，启动 Lab
  完成一次正常的 OAuth 登录（使用 wiener:peter 账号）

2.2 找到前端提交 Token 的请求
  登录完成后，前端会发送一个 POST 请求，包含 Token 和用户信息
  形如：
  POST /authenticate
  {
    "email": "wiener@normal-user.net",
    "token": "eyJhbGci...",
    "username": "wiener"
  }

2.3 在 Burp Repeater 中修改请求
  把 email 改为 carlos@carlos-montoya.net（Lab 的目标账号）
  把 username 改为 carlos

2.4 发送修改后的请求

Expected 结果：
  如果后端没有验证 Token 中的用户信息和提交的 email/username 是否匹配
  → 直接登录为 carlos 账号

漏洞原理：
  Token 验证只检查签名有效性，没有检查 Token 内的用户 ≠ 提交的用户
  → 可以用自己的 Token 声称是任何人的身份
```

---

## 练习3：PortSwigger OAuth Lab 2 — 强制账号绑定（CSRF攻击）

```
Lab 地址：
  https://portswigger.net/web-security/oauth/lab-oauth-forced-oauth-profile-linking

目标：利用 OAuth 绑定流程中缺少 state 参数，劫持受害者账号

步骤：

3.1 理解攻击流程
  你（攻击者）已在 Blog 上有账号
  受害者（carlos）也有 Blog 账号
  Blog 支持"用社交账号绑定登录"

3.2 开始绑定流程，但不完成
  用你的攻击者账号登录 Blog
  点击"绑定社交账号"
  Burp 拦截跳转到 OAuth 服务器的授权请求
  在 Burp 中拦截到：
  GET /auth?client_id=...&redirect_uri=.../oauth-linking&response_type=code

  注意：有没有 state 参数？（此 Lab 中没有！）

3.3 复制回调 URL
  完成授权，得到带 code 的回调：
  https://blog.com/oauth-linking?code=xxxxxx

  把这个 URL 复制出来，但不要让自己访问（否则就绑定到你自己了）

3.4 构造 CSRF 攻击
  把上面的 URL 嵌入 img 或 a 标签：
  <img src="https://blog.com/oauth-linking?code=xxxxxx">

  通过博客的存储型 XSS 或其他方式让 carlos 访问这个页面

3.5 观察结果
  carlos 在不知情的情况下访问了这个 URL
  → code 被绑定到 carlos 的账号上（而不是你的）
  → 你可以用自己的社交账号登录为 carlos

漏洞原理：
  state 参数的作用是把授权码和当前会话绑定
  没有 state → 任何人访问回调 URL 都会触发绑定
```

---

## 练习4：检查 redirect_uri 验证

```
测试认证服务器是否严格验证 redirect_uri。

步骤：

4.1 找到 OAuth 授权 URL
  形如：
  GET /authorize?client_id=xxx&redirect_uri=https://app.com/callback&...

4.2 修改 redirect_uri，尝试以下变种：

  [测试1] 添加路径
  redirect_uri=https://app.com/callback/../evil

  [测试2] 子路径
  redirect_uri=https://app.com/callback/extra

  [测试3] 域名欺骗（注意：仅在授权范围内的测试环境进行）
  redirect_uri=https://app.com.evil-test.com/callback

  [测试4] 参数注入
  redirect_uri=https://app.com/callback?extra=https://evil.com

4.3 观察认证服务器的反应
  正确的实现：
    返回错误，拒绝修改后的 redirect_uri

  有漏洞的实现：
    接受修改后的 URL，并把授权码发送到新地址

4.4 PortSwigger 专用 Lab
  https://portswigger.net/web-security/oauth/lab-oauth-account-hijacking-via-redirect-uri

  按 Lab 说明，将 redirect_uri 改为 Burp Collaborator 地址
  → 如果收到带有 code 的请求，说明验证有漏洞
```

---

## 练习5：检查 OAuth 安全参数清单（实际工作中使用）

```
对一个使用 OAuth 登录的功能进行完整安全检查。

工具：Burp Suite + 浏览器 DevTools

5.1 拦截授权请求，检查每一项：

参数检查：
  □ 存在 state 参数？
  □ state 长度 ≥ 16 字符（熵足够）？
  □ state 是随机的（每次登录都不同）？
  □ 存在 code_challenge（PKCE）？
  □ redirect_uri 是精确匹配的 URL？
  □ scope 是最小化的（不含不必要权限）？

5.2 拦截回调请求，检查：

  □ state 值和授权请求中的一致？
  □ code 只能使用一次（重放回调 URL 是否报错）？

  重放测试：
  在 Burp 中右键回调请求 → Send to Repeater
  再次发送这个请求（使用已经用过的 code）
  Expected：返回错误（code already used）
  有漏洞：再次成功登录

5.3 检查 Token 存储：

  F12 → Application → Local Storage / Session Storage / Cookies
  - Access Token 是否存在 localStorage？（安全风险，XSS 可读取）
  - 是否存在 HttpOnly Cookie？（更安全）
  - Refresh Token 是否在前端可见？

5.4 记录检查结果，给每个问题打 CVSS 分数：

  例：state 参数缺失导致 CSRF
  AV:N / AC:H / PR:N / UI:R / S:U / C:H / I:H / A:N
  → 约 7.1（高危）
```

---

## 练习6：PortSwigger 推荐 Lab 列表

```
按难度递增完成以下 Lab（全部免费）：

[入门] Authentication bypass via OAuth implicit flow
  理解 Implicit 模式的缺陷
  https://portswigger.net/web-security/oauth/lab-oauth-authentication-bypass-via-oauth-implicit-flow

[入门] Forced OAuth profile linking
  理解 state 参数的重要性
  https://portswigger.net/web-security/oauth/lab-oauth-forced-oauth-profile-linking

[中级] OAuth account hijacking via redirect_uri
  测试 redirect_uri 验证
  https://portswigger.net/web-security/oauth/lab-oauth-account-hijacking-via-redirect-uri

[中级] Stealing OAuth access tokens via open redirect
  结合 Open Redirect 漏洞窃取 Token
  https://portswigger.net/web-security/oauth/lab-oauth-stealing-oauth-access-tokens-via-an-open-redirect

[进阶] SSRF via OpenID dynamic client registration
  通过 OpenID 动态注册触发 SSRF
  https://portswigger.net/web-security/oauth/openid/lab-oauth-ssrf-via-openid-dynamic-client-registration

建议顺序：先做入门2个，再做中级，进阶留到有一定基础再做。
每个 Lab 完成后，给发现的漏洞打 CVSS 分数，练习评级能力。
```

---

## 自测验收

完成以上练习后，检查自己能否：

- [ ] 用 DevTools 捕获 OAuth 授权请求，找到所有关键参数
- [ ] 判断一个 OAuth 实现是否有 state 参数，并解释缺失的后果
- [ ] 完成 PortSwigger OAuth Lab 1（implicit flow 绕过）
- [ ] 完成 PortSwigger OAuth Lab 2（强制绑定 CSRF）
- [ ] 说出 PKCE 的作用以及什么场景下必须使用
- [ ] 对照安全检查清单（5.1-5.3），对一个真实 OAuth 流程进行完整检查

---

> **相关模块：**
> - [05 认证缺陷](../../phase-2-security-core/05-broken-auth/README.md) — OAuth 是认证方式的一种
> - [04 CSRF攻击](../../phase-2-security-core/04-csrf/README.md) — OAuth CSRF 是 CSRF 的特例
> - [04 CVSS评级](../04-cvss-severity/practice.md) — 给 OAuth 漏洞打分
