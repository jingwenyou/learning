# 06 OAuth 2.0安全测试 —— 现代认证的标配

> 如果你测试的应用使用微信登录、Google登录、GitHub登录……
> 这些都是OAuth 2.0。OAuth的安全问题有自己独特的攻击面。
> 认证缺陷不只是"密码对不对"，还有"认证流程被没有被劫持"。

---

## 一、OAuth 2.0 快速入门

### 1.1 为什么需要OAuth

```
不用OAuth：
  用户在第三方App注册账号
  App直接问用户要用户名密码
  → App存储了用户的密码 → 极大安全风险

用OAuth：
  用户在第三方App点击"用微信登录"
  App跳转到微信授权页面
  用户在微信授权页确认
  微信返回一个临时凭证给App
  App用凭证换取用户信息
  → App永远不知道用户的微信密码
```

### 1.2 四种授权模式

```
OAuth 2.0定义了4种授权方式：

[1] 授权码模式（Authorization Code）— 最安全，推荐使用
    用于：有后端服务器的Web应用
    流程：用户授权 → 返回授权码 → 后端用授权码换Token

[2] 隐式模式（Implicit）— 不安全，已不推荐
    用于：无后端的前端SPA
    流程：用户授权 → 直接返回Access Token（通过URL fragment）
    问题：Token暴露在浏览器地址栏，容易被窃取

[3] 密码凭证模式（Resource Owner Password Credentials）— 不推荐
    用于：极度可信的第一方应用
    流程：用户把用户名密码直接给App
    问题：App仍然持有用户密码

[4] 客户端凭证模式（Client Credentials）
    用于：机器对机器的认证
    流程：客户端用自己的凭证换Token
    例：微服务之间的认证
```

### 1.3 授权码模式的完整流程

```
授权码模式流程图：

[用户]          [第三方App]         [认证服务器]         [资源服务器]
  |                  |                    |                   |
  |-- 点击登录 ---->|                    |                   |
  |                  |-- 重定向到 ------>|                   |
  |<-- 授权页面 ---|                    |                   |
  |-- 输入账号密码 ->|                   |                   |
  |                  |-- 用户确认 ------>|                   |
  |<-- 授权码 -----|<-------------------|                   |
  |                  |-- 用授权码换Token ->                  |
  |                  |<-- Access Token ---|<------------------|
  |                  |-- 用Token获取用户信息 ->              |
  |                  |<-- 用户数据 ------|<------------------|
  |                  |                    |                   |
  |-- 登录成功 ---->|                    |                   |

具体URL例子：
Step 1: App发起授权请求
  GET /authorize?
    response_type=code&        ← 要求返回授权码
    client_id=app123&           ← App的ID
    redirect_uri=https://app.com/callback&
    scope=profile,email&
    state=random_string_abc123& ← 防止CSRF
    code_challenge=xxx&         ← PKCE可选
    code_challenge_method=S256

Step 2: 用户在认证服务器登录并授权
  (用户在微信/Google的页面输入密码)

Step 3: 认证服务器重定向回App
  GET https://app.com/callback?
    code=auth_code_xyz789&     ← 授权码（短期有效）
    state=random_string_abc123 ← 验证是否一致

Step 4: App用授权码换Token（服务端到服务端）
  POST /token
  Body:
    grant_type=authorization_code
    code=auth_code_xyz789
    redirect_uri=https://app.com/callback
    client_id=app123
    client_secret=xxx          ← App的密钥（不在浏览器中）

Step 5: 获取Token
  Response:
  {
    "access_token": "eyJhbGci...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "abc123...",
    "scope": "profile email"
  }

Step 6: 用Token获取用户信息
  GET /userinfo
  Authorization: Bearer eyJhbGci...

Step 7: 创建本地会话，登录完成
```

---

## 二、OAuth常见安全漏洞

### 2.1 CSRF攻击 —— 绑定劫持

```
最常见的OAuth漏洞！

场景：用户A在app.com上绑定第三方账号（微信）
攻击者：先用自己账号在app.com登录，绑定攻击者的微信

攻击步骤：

1. 攻击者在自己的app.com账号中点击"绑定微信"
   App重定向到微信授权页
   但攻击者在这一步停止

2. 攻击者构造恶意链接，发给受害者：
   https://auth.weixin.qq.com/authorize?
     response_type=code&
     client_id=attacker_wechat_id&    ← 攻击者的微信App ID
     redirect_uri=https://app.com/callback& ← 攻击者的callback
     state=abc123

3. 受害者（已经在app.com登录了）点击这个链接
   在攻击者的微信账号上授权
   微信把授权码发给攻击者的callback URL

4. 攻击者拿到授权码
   用授权码换Token → 获得受害者在微信的账号访问权限

5. 攻击者回到自己的app.com账号
   绑定受害者的微信账号 → 绑定成功！
   → 现在攻击者的账号和受害者的微信关联了

关键：state参数！
  如果App在授权请求时正确使用了state参数，
  攻击者的callback URL会带上正确的state，
  App会验证state是否匹配 → CSRF攻击失败

如果没有state参数 → CSRF攻击成功！
```

### 2.2 redirect_uri验证不严

```
OAuth要求App注册一个或一组允许的回调URL。
认证服务器必须验证回调URL是否在注册的白名单中。

漏洞类型：

[漏洞1] redirect_uri完全验证缺失
  App注册: https://app.com
  攻击者利用: https://app.com.evil.com
  → evil.com结尾，但认证服务器可能只检查了包含关系

[漏洞2] 子目录验证不严
  App注册: https://app.com/callback
  攻击者利用: https://app.com/callback/evil
  或: https://app.com/callback?redirect=https://evil.com

[漏洞3] path参数注入
  App注册: https://app.com/oauth/callback
  攻击者利用: https://app.com/oauth/callback/..%2f..%2fevil

修复方式：
  认证服务器必须精确匹配redirect_uri（不是包含关系）
  或使用path + hash的组合验证
```

### 2.3 授权码泄露

```
授权码在URL中通过重定向传递：
  https://app.com/callback?code=auth_code

风险点：
1. 授权码出现在浏览器历史记录中
2. 授权码出现在Referer头中（如果用户从一个页面跳到另一个）
3. 授权码被记录在日志中

对策：
  - 授权码有效期应极短（<60秒）
  - 授权码只能使用一次
  - 授权码必须和client_id、redirect_uri绑定

攻击场景：
  攻击者窃听到授权码（通过Referer、日志等）
  → 立即用授权码换Token
  → 在授权码过期前抢先把受害者账号绑定到攻击者的第三方账号
```

### 2.4 Token泄露

```
Access Token在URL中传递（Implicit模式）：
  https://app.com/callback#access_token=xxx&token_type=bearer

问题：
  - URL在浏览器历史记录中
  - URL在Referer头中
  - URL可能被分享

修复：
  - 使用授权码模式而非Implicit模式
  - 使用PKCE扩展（即使授权码模式也需要）
  - Token存储在HttpOnly Cookie中，而非localStorage
```

### 2.5 PKCE缺失

```
PKCE（Proof Key for Code Exchange）= 动态密钥对

为什么需要PKCE：
  即使没有client_secret（如移动App、SPA），
  PKCE也能防止授权码被窃取后换Token。

PKCE流程：

1. App端生成随机字符串code_verifier
2. 计算code_challenge = BASE64URL(SHA256(code_verifier))
3. 授权请求带上code_challenge和method

4. 换取Token时，必须带上code_verifier
5. 服务端重新计算code_challenge，对比是否匹配

如果攻击者窃取授权码，但没有code_verifier → 无法换Token

测试：检查OAuth流程是否使用了PKCE
  - 授权请求中是否有 code_challenge 参数？
  - Token请求中是否有 code_verifier 参数？
  - 如果没有，且App没有client_secret → 高危
```

### 2.6 Scope权限过大

```
OAuth的scope定义了Token能访问哪些数据：
  scope=profile          → 只能访问公开资料
  scope=profile,email   → 访问资料和邮箱
  scope=profile,email,contacts,friends → 访问所有信息

问题：
  App请求了远超实际需要的权限
  例：一个简单的小程序要求读取"所有联系人"
  → 这些权限被攻击者拿到后危害巨大

测试：
  1. 检查App请求的scope是否合理
  2. 尝试减少scope：去掉某个scope重新授权，看功能是否受影响
  3. 如果功能不受影响，说明App多要了不必要的权限
```

---

## 三、OAuth安全测试检查清单

### 授权请求阶段

```
□ 授权请求是否包含 state 参数？
□ state 是否随机且不可预测（至少32字节熵）？
□ state 在授权前后是否经过验证？
□ 是否使用 PKCE（code_challenge + code_verifier）？
□ redirect_uri 是否被验证？
□ 是否验证 redirect_uri 精确匹配（而非前缀匹配）？
□ scope 是否最小化（只请求必要的权限）？
□ 是否明确告知用户将被授予哪些权限？
```

### Token交换阶段

```
□ client_secret 是否安全存储（不在前端代码中）？
□ 授权码是否短期有效（<60秒）？
□ 授权码是否一次性使用？
□ 授权码是否和 redirect_uri 绑定？
□ 是否验证 code_verifier（如果使用PKCE）？
□ Token响应是否通过HTTPS传输？
```

### Token使用阶段

```
□ Access Token 是否安全存储（不在URL中）？
□ Refresh Token 是否安全存储？
□ 是否支持Token撤销（Logout后Token是否失效）？
□ Token过期后是否正确拒绝请求？
□ Token是否关联了正确的scope？
□ 是否验证Token来自可信的发行者？
```

### CSRF防护

```
□ 绑定/解绑第三方账号操作是否需要CSRF Token？
□ state参数是否贯穿整个OAuth流程？
□ 绑定操作前是否验证用户当前登录状态？
□ 绑定成功/失败后是否有通知？
```

---

## 四、动手实践

### 实践1：OAuth授权请求抓包分析

```
1. 找一个使用OAuth登录的网站（如用微信/Google/GitHub登录）
2. F12 → Network面板 → 找到OAuth的authorize请求
3. 完整记录以下参数：
   - response_type (应该是code)
   - client_id
   - redirect_uri
   - scope
   - state
   - code_challenge (如果有)
4. 检查每个参数是否存在和正确
5. 找一个不使用OAuth的网站做对比
```

### 实践2：模拟OAuth CSRF攻击

```python
"""
OAuth CSRF攻击演示（仅用于学习靶场）
"""
import hashlib
import base64
import secrets
import requests

def generate_pkce_pair():
    """生成PKCE密钥对"""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return code_verifier, code_challenge

def build_auth_url():
    """构造OAuth授权URL"""
    client_id = "your_client_id"
    redirect_uri = "https://your-app.com/callback"
    scope = "profile email"
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_pair()

    auth_url = (
        f"https://auth.example.com/authorize"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    return auth_url, code_verifier

def test_oauth_security(base_url):
    """OAuth安全测试"""
    print("=== OAuth安全测试 ===\n")

    # 检查1：state参数
    print("检查1: state参数")
    resp = requests.get(f"{base_url}/authorize?client_id=test")
    if "state=" not in resp.text:
        print("  [警告] 授权请求中没有state参数 — 可能存在CSRF风险")

    # 检查2：PKCE支持
    print("\n检查2: PKCE支持")
    if "code_challenge" not in resp.text:
        print("  [信息] 不支持PKCE — 在无client_secret场景下风险增加")

    # 检查3：scope最小化
    print("\n检查3: scope范围")
    # 实际测试中需要解析授权页面
    print("  [操作] 人工检查请求的权限范围是否合理")

    # 检查4：redirect_uri验证
    print("\n检查4: redirect_uri验证")
    malicious_redirect = "https://evil.com/callback"
    resp = requests.get(
        f"{base_url}/authorize",
        params={"redirect_uri": malicious_redirect, "client_id": "test"}
    )
    final_url = resp.url
    if "evil.com" in final_url or resp.status_code == 200:
        print(f"  [严重] redirect_uri验证不严 — 重定向到了 {final_url}")
    else:
        print("  [安全] redirect_uri验证正常")

# 使用
# test_oauth_security("https://oauth-provider.example.com")
```

### 实践3：PortSwigger OAuth Labs

```
PortSwigger OAuth Labs（免费）：
https://portswigger.net/web-security/oauth

必做Lab：
1. Authentication bypass via OAuth implicit flow
2. Forced OAuth profile linking
3. OAuth account hijacking via redirect_uri
4. Stealing OAuth access tokens via open redirect
5. OAuth token hijacking via CSRF

每个Lab对应一个真实攻击场景，全部完成对OAuth安全有深入理解。
```

---

## 五、自测清单

- [ ] OAuth 2.0的四种授权模式是什么？各自用在什么场景？
- [ ] 授权码模式的完整流程是什么？
- [ ] OAuth中的CSRF攻击是怎么进行的？state参数的作用是什么？
- [ ] redirect_uri验证不严会导致什么问题？
- [ ] PKCE是什么？为什么重要？
- [ ] Implicit模式为什么被废弃？
- [ ] Scope权限过大的风险是什么？
- [ ] 能在PortSwigger完成至少2个OAuth Lab？

---

> **相关模块：**
> - [05 认证缺陷](../05-broken-auth/README.md) —— OAuth只是认证方式的一种
> - [04 CSRF攻击](../04-csrf/README.md) —— OAuth CSRF是CSRF的特例
> - [04 CVSS评级](../04-cvss-severity/README.md) —— 给OAuth漏洞打分
