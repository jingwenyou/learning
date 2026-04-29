# 05 认证缺陷 —— 登录/Session/Token的安全问题

> 认证回答的是一个问题：**"你是谁？"**
> 如果认证环节有漏洞，攻击者可以冒充任何人。
> 这是OWASP Top 10中长期排名靠前的高危漏洞类别。

---

## 一、认证的全貌

```
完整的认证流程：

[1] 注册 → 创建账号
[2] 登录 → 验证身份，获得凭证（Session/Token）
[3] 保持状态 → 后续请求携带凭证
[4] 登出 → 销毁凭证
[5] 密码重置 → 忘记密码时的恢复流程
[6] 多因素认证 → 额外的安全层

每一步都可能出问题。逐个分析：
```

---

## 二、登录环节的漏洞

### 2.1 暴力破解（Brute Force）

```
攻击：自动化地尝试大量密码组合

类型1：固定用户名，遍历密码
  admin / 123456
  admin / password
  admin / admin123
  admin / qwerty
  ...（用密码字典，常见密码有几千到几百万条）

类型2：密码喷洒（Password Spraying）
  user1 / 123456
  user2 / 123456
  user3 / 123456
  ...（用一个常见密码遍历所有用户名，每个用户只试一次，避免触发锁定）

类型3：撞库（Credential Stuffing）
  用从其他网站泄露的用户名/密码组合直接尝试
  （因为很多人在不同网站用相同密码）

测试方法：
  1. 连续错误登录10次、50次、100次
  2. 观察是否有：
     □ 账户锁定机制
     □ 请求频率限制（Rate Limiting）
     □ 验证码出现
     □ 响应延迟增加
  3. 如果什么防护都没有 → 严重漏洞
```

### 2.2 用户名枚举

```
问题：登录失败的提示信息泄露了用户名是否存在

不安全的提示：
  输入不存在的用户 → "用户名不存在"
  输入存在的用户但密码错 → "密码错误"
  → 攻击者可以确认哪些用户名是有效的

安全的提示：
  统一返回 → "用户名或密码错误"

更隐蔽的枚举方式（高级测试）：
  - 响应时间差异：存在的用户需要验证密码（耗时更长）
  - 响应长度差异：不同情况下HTML内容不同
  - 注册时提示"用户名已被使用"
  - 密码重置时提示"该邮箱未注册"

测试方法：
  1. 用一个确认存在的用户名和一个随机用户名分别登录
  2. 对比：错误提示、响应时间、响应长度、HTTP状态码
  3. 任何差异都可以被利用来枚举用户名
```

### 2.3 弱密码策略

```
检查点：
  □ 是否允许"123456"、"password"等弱密码？
  □ 最短密码长度要求？（至少8位）
  □ 是否要求包含大小写、数字、特殊字符？
  □ 是否检查常见密码黑名单？
  □ 是否允许密码与用户名相同？
```

---

## 三、Session管理漏洞

### 3.1 Session ID安全

```
Session ID是你登录后的"身份证"，它的安全性至关重要。

[Session ID可预测]
  坏的实现：session_id = 用户ID + 时间戳
    user1_1704067200
    user2_1704067201
  攻击者可以猜出其他用户的Session ID

  好的实现：128位以上的随机数
    a7b3c9d2e1f08765432198abcdef1234

测试方法：
  1. 收集多个Session ID
  2. 观察是否有规律（递增？包含用户名？时间戳？）
  3. 用Burp Suite的Sequencer分析随机性

[Session固定攻击（Session Fixation）]
  1. 攻击者获取一个未认证的Session ID：abc123
  2. 攻击者把这个Session ID "种"给受害者
     （通过URL参数、XSS等方式）
  3. 受害者用这个Session ID登录
  4. 登录后，Session ID没有变化，还是abc123
  5. 攻击者用abc123访问 → 直接获得受害者身份

测试方法：
  1. 记录登录前的Session ID
  2. 登录
  3. 记录登录后的Session ID
  4. 两个ID一样？→ Session固定漏洞！
     登录后应该重新生成Session ID

[Session不过期]
  测试：
  1. 登录获取Session ID
  2. 等待一段时间（或手动修改服务端Session过期时间）
  3. 用旧Session ID访问 → 还能用？
  4. 点击"登出"后 → 用Session ID访问 → 还能用？

  问题：
  □ Session有没有过期时间？
  □ 登出后Session是否在服务端销毁？
  □ 闲置超时（30分钟无操作自动过期）？
  □ 绝对超时（无论是否活跃，8小时后过期）？
```

### 3.2 Cookie安全属性

```
登录后查看Set-Cookie头：

Set-Cookie: session=abc123; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=3600

逐项检查：
  □ HttpOnly  → 防止JavaScript读取（防XSS偷Cookie）
  □ Secure    → 只在HTTPS时发送（防中间人截获）
  □ SameSite  → 限制跨站发送（防CSRF）
  □ Path=/    → Cookie的作用范围
  □ Max-Age   → 过期时间（不要太长）
  □ Domain    → 不要设置得过于宽泛（如 .example.com）

任何一项缺失都是安全发现。
```

---

## 四、Token（JWT）安全

### 4.1 JWT结构回顾

```
JWT由三部分组成，用.分隔：
  Header.Payload.Signature

Header（头部）：
  {"alg": "HS256", "typ": "JWT"}
  → Base64编码 → eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

Payload（载荷）：
  {"user_id": 1, "username": "admin", "role": "admin", "exp": 1704067200}
  → Base64编码 → eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIn0

Signature（签名）：
  HMACSHA256(Base64(header) + "." + Base64(payload), secret_key)
  → 防止篡改

关键理解：
  Header和Payload只是Base64编码，不是加密！
  任何人都可以解码查看内容
  安全性完全依赖于Signature
```

### 4.2 JWT常见漏洞

```
[漏洞1] 算法设为none
  攻击者修改Header：{"alg": "none", "typ": "JWT"}
  然后去掉Signature部分
  如果服务端接受alg=none → 不验证签名 → 可以伪造任意Token

  测试：
  1. 解码JWT
  2. 修改Header的alg为"none"或"None"或"NONE"
  3. 修改Payload（如改role为admin）
  4. 重新编码，去掉签名部分（保留末尾的.）
  5. 用新Token发请求

[漏洞2] 弱密钥
  如果密钥是"secret"、"password"、"123456"等
  可以用工具暴力破解：

  # 用hashcat破解JWT密钥
  hashcat -m 16500 jwt.txt wordlist.txt

  # 或用john
  john jwt.txt --wordlist=wordlist.txt

[漏洞3] 算法混淆（RS256→HS256）
  正常：服务端用RSA私钥签名，公钥验签
  攻击：把alg从RS256改成HS256
       用公钥（公开的）作为HMAC密钥签名
       如果服务端按alg字段选择算法 → 用公钥做HMAC验签 → 通过

[漏洞4] Payload中的敏感信息
  JWT Payload是Base64编码不是加密
  如果里面放了密码、手机号等敏感信息 → 信息泄露

  测试：解码每个JWT的Payload，检查有无敏感数据

[漏洞5] Token不过期
  没设exp字段，或exp设得太远
  一旦泄露，永久有效
```

### 4.3 JWT测试工具

```python
"""JWT安全检测脚本"""
import base64
import json
import hmac
import hashlib

def decode_jwt(token):
    """解码JWT的Header和Payload"""
    parts = token.split(".")
    if len(parts) != 3:
        print("不是有效的JWT格式")
        return None, None

    result = {}
    for i, name in enumerate(["Header", "Payload"]):
        part = parts[i]
        # 补齐Base64填充
        padded = part + "=" * (4 - len(part) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        data = json.loads(decoded)
        result[name] = data
        print(f"\n{name}:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # 检查安全问题
    header = result["Header"]
    payload = result["Payload"]

    print("\n===  安全检查 ===")

    # 检查算法
    alg = header.get("alg", "未设置")
    if alg.lower() == "none":
        print("[严重!] 算法为none，不验证签名")
    elif alg == "HS256":
        print("[注意] 使用HS256，检查密钥是否足够强")
    else:
        print(f"[信息] 算法: {alg}")

    # 检查过期时间
    import time
    exp = payload.get("exp")
    if not exp:
        print("[警告!] 没有设置过期时间(exp)")
    else:
        if exp < time.time():
            print(f"[信息] Token已过期: {time.ctime(exp)}")
        else:
            remaining = (exp - time.time()) / 3600
            print(f"[信息] Token过期时间: {time.ctime(exp)} (还剩{remaining:.1f}小时)")
            if remaining > 24 * 7:
                print("[警告] Token有效期超过7天，建议缩短")

    # 检查敏感信息
    sensitive_keys = ["password", "pwd", "secret", "phone", "mobile",
                      "email", "ssn", "credit_card", "token"]
    for key in payload:
        if any(s in key.lower() for s in sensitive_keys):
            print(f"[警告!] Payload包含可能的敏感字段: {key}")

    return result["Header"], result["Payload"]

def test_none_alg(token):
    """测试none算法攻击"""
    parts = token.split(".")
    # 修改Header为alg:none
    new_header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    # 保持原Payload
    forged = f"{new_header}.{parts[1]}."
    print(f"\n伪造的Token（alg=none）:\n{forged}")
    print("用这个Token发请求，如果服务端接受 → 存在none算法漏洞")
    return forged

def test_weak_secret(token, wordlist):
    """尝试常见弱密钥"""
    parts = token.split(".")
    sign_input = f"{parts[0]}.{parts[1]}".encode()

    # 恢复原始签名
    sig_padded = parts[2] + "=" * (4 - len(parts[2]) % 4)
    original_sig = base64.urlsafe_b64decode(sig_padded)

    print(f"\n尝试破解JWT密钥（共{len(wordlist)}个候选）...")
    for secret in wordlist:
        test_sig = hmac.new(secret.encode(), sign_input, hashlib.sha256).digest()
        if test_sig == original_sig:
            print(f"[成功!] 密钥是: {secret}")
            return secret

    print("未找到匹配的密钥")
    return None

# 使用示例
sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

decode_jwt(sample_jwt)

common_secrets = ["secret", "password", "123456", "key", "admin",
                  "jwt_secret", "changeme", "test", "your-256-bit-secret"]
test_weak_secret(sample_jwt, common_secrets)
```

---

## 五、密码重置漏洞

```
密码重置流程是认证环节中最容易出问题的地方：

[漏洞1] 重置Token可预测
  重置链接：https://target.com/reset?token=123456
  token如果是递增数字或时间戳 → 可以猜出其他人的重置Token

[漏洞2] 重置Token不过期
  收到重置邮件后不立即使用
  过了几天Token还能用 → 攻击窗口太大

[漏洞3] Host头攻击
  POST /forgot-password
  Host: attacker.com       ← 篡改Host头
  Body: email=victim@example.com

  如果服务端用Host头构造重置链接：
  https://attacker.com/reset?token=abc123
  → 重置链接指向攻击者网站 → 攻击者获取到Token

[漏洞4] 重置后旧Session不失效
  改了密码但旧Session还能用
  → 如果攻击者之前偷了Session，改密码也没用

测试清单：
  □ 重置Token是否随机不可预测？
  □ 重置Token是否有过期时间（建议<1小时）？
  □ 重置Token使用后是否失效（一次性）？
  □ 修改Host头后重置链接是否改变？
  □ 密码重置后旧Session是否全部失效？
  □ 能否通过枚举发现有效的重置Token？
```

---

## 六、多因素认证（MFA）绕过

```
即使有2FA/MFA，也可能被绕过：

[绕过1] 直接跳过2FA步骤
  正常流程：登录 → /verify-2fa → /dashboard
  测试：登录后直接访问 /dashboard，跳过/verify-2fa
  如果成功 → 2FA形同虚设

[绕2] 2FA码暴力破解
  6位数字验证码 = 100万种可能
  如果没有频率限制和尝试次数限制 → 可以暴力破解

[绕过3] 2FA码重复使用
  用一个验证码验证后，再用一次 → 还能通过？
  应该是一次性的

[绕过4] 备用码泄露
  很多系统提供备用恢复码
  如果保存在前端或容易泄露的地方 → 绕过2FA
```

---

## 七、动手实践

### 实践1：DVWA暴力破解

```
1. DVWA → Brute Force 页面（Low级别）
2. 用Burp Suite拦截登录请求
3. 发送到Intruder：
   - 标记password参数为变量
   - 载入密码字典
   - 开始攻击
   - 观察响应长度差异（成功和失败的长度不同）
4. 找到正确密码
5. 思考：这个系统有什么防护措施？（答案是：什么都没有）
```

### 实践2：Session安全检查

```
1. 登录DVWA
2. F12 → Application → Cookies
3. 记录Session ID：PHPSESSID=xxx
4. 检查Cookie属性：
   □ HttpOnly？
   □ Secure？
   □ SameSite？
5. 点击登出
6. 手动设置Cookie为旧的Session ID
7. 刷新页面 → 还能访问吗？（Session是否被销毁）
```

### 实践3：JWT解码和分析

```bash
# 如果你手头有JWT Token（从你测试的系统中获取）

# 用Python解码
python3 -c "
import base64, json
token = '你的JWT'
for i, part in enumerate(token.split('.')[:2]):
    padded = part + '=' * (4 - len(part) % 4)
    print(json.dumps(json.loads(base64.urlsafe_b64decode(padded)), indent=2))
"

# 在线工具：jwt.io（注意不要贴生产环境的真实Token）
```

---

## 八、认证安全检查总清单

```
登录：
  □ 暴力破解防护（锁定/限频/验证码）
  □ 用户名枚举（错误提示是否统一）
  □ 密码策略（复杂度、长度、黑名单）
  □ 密码传输（是否HTTPS）
  □ 登录日志和异常通知

Session/Token：
  □ Session ID随机性
  □ 登录后Session ID是否更新（防固定攻击）
  □ Session/Token过期机制
  □ 登出后Session/Token是否失效
  □ Cookie安全属性（HttpOnly, Secure, SameSite）
  □ JWT算法安全（非none，非弱密钥）
  □ JWT Payload无敏感信息

密码重置：
  □ 重置Token随机且有时效
  □ 重置Token一次性使用
  □ Host头攻击
  □ 重置后旧Session失效

高级：
  □ MFA是否可绕过
  □ 并发登录控制
  □ 账户锁定后是否可以枚举（响应差异）
```

---

## 九、自测清单

- [ ] 暴力破解有哪些类型？密码喷洒和传统暴力破解有什么区别？
- [ ] 什么是用户名枚举？除了错误提示，还有哪些方式可以枚举？
- [ ] Session固定攻击的原理和测试方法？
- [ ] JWT的三个部分分别是什么？Payload是加密的吗？
- [ ] JWT的none算法攻击是怎么回事？
- [ ] 密码重置功能可能有哪些安全问题？
- [ ] Cookie的HttpOnly、Secure、SameSite分别防什么？
- [ ] 能完成DVWA的暴力破解挑战？

---

> **下一模块：** [06 越权访问](../06-access-control/README.md) —— 测试工程师的天然优势
