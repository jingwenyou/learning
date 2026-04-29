# 03 浏览器DevTools —— 被低估的安全工具

> 你每天都在用F12，但可能从来没有从安全角度用过它。
> 不需要安装任何工具，浏览器自带的DevTools就能发现大量安全问题。

---

## 一、安全测试中的DevTools用法

### 1.1 Network面板——你的"简版Burp"

```
安全测试清单：

□ 登录请求
  - 密码是明文还是加密传输？
  - 是HTTP还是HTTPS？
  - 响应中Set-Cookie有没有HttpOnly/Secure/SameSite？

□ API请求
  - 右键 → Copy → Copy as cURL → 终端中修改参数重放
  - 右键 → Copy → Copy as fetch → Console中修改执行
  - 观察请求头中的认证方式（Cookie/Bearer Token/API Key）

□ 信息泄露
  - 搜索响应内容：Ctrl+F搜"password"、"token"、"secret"
  - 观察API响应是否返回了多余的字段

□ 混合内容
  - HTTPS页面是否加载了HTTP资源（图片、脚本）
  - Console中会有Mixed Content警告
```

### 1.2 Application面板——存储安全

```
Cookies：
  逐个检查每个Cookie：
  □ Value：是否明文可读？是否包含敏感信息？
  □ HttpOnly：阻止JS访问
  □ Secure：仅HTTPS发送
  □ SameSite：跨站请求控制
  □ Expires：过期时间是否合理

Local Storage / Session Storage：
  □ 是否存储了Token或敏感数据？
  □ 存在这里的数据XSS可以直接读取
  Console中验证：localStorage 回车查看所有键值

Cache Storage / IndexedDB：
  □ 是否缓存了敏感数据？
```

### 1.3 Console面板——快速验证

```javascript
// 查看所有Cookie
document.cookie
// 如果能看到session相关的Cookie → HttpOnly没设

// 查看LocalStorage
for (let i = 0; i < localStorage.length; i++) {
    let key = localStorage.key(i);
    console.log(key + ": " + localStorage.getItem(key));
}

// 快速发请求（不用Burp也能测试）
// 从Network面板复制为fetch，修改后在Console执行
fetch('/api/user/999', {
    headers: {'Authorization': 'Bearer ' + localStorage.getItem('token')}
}).then(r => r.json()).then(console.log)

// 测试DOM XSS
// 找到页面中使用innerHTML的地方
document.querySelectorAll('*').forEach(el => {
    if (el.innerHTML && el.innerHTML.includes(location.search)) {
        console.log('可能的DOM XSS:', el);
    }
});
```

### 1.4 Sources面板——前端代码审计

```
Ctrl+Shift+F 全局搜索关键词：

高优先级搜索：
  password, passwd, pwd       → 硬编码密码
  api_key, apikey, api-key    → API密钥泄露
  secret, token               → 密钥/Token
  admin                       → 管理功能/路径
  eval(                       → 危险函数
  innerHTML                   → 可能的DOM XSS
  document.write              → 可能的DOM XSS
  window.location             → 可能的重定向
  localStorage, sessionStorage → 敏感数据存储

中优先级搜索：
  TODO, FIXME, HACK, XXX      → 开发者遗留的问题
  debug, test                  → 调试代码
  http://                      → HTTP明文URL
  /api/                        → API路径发现
```

### 1.5 Security面板

```
Chrome特有的Security面板：
  - 证书信息（颁发者、有效期、域名匹配）
  - 连接安全性（TLS版本、加密套件）
  - 混合内容警告
  - 不安全的来源标记
```

---

## 二、无工具安全快速检查（5分钟检查清单）

```
只用浏览器，不装任何工具，5分钟能做的安全检查：

[1分钟] F12 → Network → 登录 → 检查密码传输和Cookie属性
[1分钟] F12 → Application → 检查Cookie/Storage中的敏感数据
[1分钟] F12 → Sources → Ctrl+Shift+F搜password/secret/api_key
[1分钟] F12 → Console → document.cookie检查HttpOnly
[1分钟] 地址栏 → 查看证书 → 检查HTTPS配置

这5个动作能发现很多低垂的果实（easy wins）。
```

---

## 三、自测清单

- [ ] 能用Network面板分析登录过程的安全性？
- [ ] 能在Application面板检查Cookie安全属性？
- [ ] 能在Sources面板搜索敏感信息？
- [ ] 能在Console中用fetch重放和修改请求？
- [ ] 能用5分钟快速检查清单做一次基本的安全检查？

---

> **Phase 3 完成！下一阶段：** [Phase 4 - 进阶提升](../../phase-4-advanced/01-business-logic/README.md)
