# 02 API安全测试 —— 现代Web的主战场

> 现代Web应用几乎都是前后端分离架构：前端SPA + 后端API。
> 安全测试的重心从"页面"转向"接口"。
> API安全测试的核心思路和前面学的一样，只是载体变了。

---

## 一、API安全测试要点

### 1.1 信息发现

```
API文档泄露：
  /swagger-ui.html, /swagger.json
  /api/docs, /api/v1/docs
  /openapi.json, /openapi.yaml
  /graphql（GraphQL自带内省查询）

  发现API文档 = 获得完整攻击面地图

隐藏接口发现：
  - 前端JS代码中搜索 /api/ 路径
  - 从v1推测v2（/api/v1/users → /api/v2/users）
  - HTTP方法探测（GET改POST/PUT/DELETE）
  - 参数名猜测（id, user_id, admin, debug, test）
```

### 1.2 认证测试

```
□ 无Token访问API → 应该被拒绝（401）
□ 过期Token → 应该被拒绝
□ 伪造Token → 应该被拒绝
□ Token中修改用户信息 → 应该被检测到
□ 不同接口的认证是否一致（有些接口忘了加认证）
```

### 1.3 授权测试

```
□ 普通用户Token访问管理API
□ 用户A的Token访问用户B的资源
□ 修改请求中的用户ID参数
□ 批量接口是否验证每个ID的权限
□ GraphQL查询是否限制了可查询的字段
```

### 1.4 输入验证

```
□ 每个参数都测试注入（SQL、XSS、命令注入）
□ 类型混淆（期望数字的地方传字符串、数组、对象）
□ 超长输入
□ 特殊字符
□ Content-Type混淆（JSON→XML→form-urlencoded）
```

### 1.5 速率限制

```
□ 登录接口有没有限频
□ 短信/邮件发送有没有限频
□ 敏感操作有没有限频
□ 通过换IP、换User-Agent能否绕过限频
```

### 1.6 数据暴露

```
□ 响应是否返回了多余字段（如password_hash、internal_id）
□ 列表接口是否分页（不分页可能一次返回所有数据）
□ 错误响应是否泄露内部信息（堆栈跟踪、SQL语句、文件路径）
□ 是否有调试接口暴露在生产环境
```

---

## 二、API安全测试清单

```
认证：
  □ 未认证访问
  □ Token有效性验证
  □ Token过期处理

授权：
  □ 水平越权（IDOR）
  □ 垂直越权
  □ 功能级授权

输入：
  □ 注入测试（SQL/XSS/命令）
  □ 类型/长度/格式验证
  □ 批量操作安全

限制：
  □ 速率限制
  □ 分页限制
  □ 文件大小限制

泄露：
  □ 响应数据最小化
  □ 错误信息安全
  □ API文档泄露
  □ 版本信息泄露

传输：
  □ HTTPS强制
  □ CORS配置
  □ 敏感数据加密
```

---

## 三、自测清单

- [ ] 现代API安全和传统Web安全的区别？
- [ ] 怎么发现未公开的API接口？
- [ ] API越权测试的方法？
- [ ] 什么是BOLA（Broken Object Level Authorization）？和IDOR什么关系？
- [ ] API的速率限制怎么测试？

---

> **下一模块：** [03 自动化安全扫描](../03-automated-scanning/README.md)
