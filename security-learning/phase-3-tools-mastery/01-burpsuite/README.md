# 01 Burp Suite —— 安全测试的瑞士军刀

> Burp Suite是Web安全测试的**标准工具**，几乎所有安全测试人员每天都在用。
> 它本质上是一个HTTP代理——拦截浏览器和服务器之间的所有通信，
> 让你能**看到、修改、重放**每一个请求。

---

## 一、安装和配置

### 1.1 下载

```
Burp Suite Community Edition（免费版）足够学习使用：
https://portswigger.net/burp/communitydownload

需要Java运行环境（安装包通常自带）
```

### 1.2 配置浏览器代理

```
Burp启动后默认监听 127.0.0.1:8080

方法1：浏览器手动配置代理
  Firefox → 设置 → 网络设置 → 手动配置代理
  HTTP代理：127.0.0.1  端口：8080
  勾选"所有协议使用此代理"

方法2：使用FoxyProxy扩展（推荐）
  安装Firefox的FoxyProxy插件
  添加代理：127.0.0.1:8080
  一键切换代理开关

HTTPS配置：
  1. 浏览器访问 http://burpsuite（代理开启状态）
  2. 下载Burp的CA证书
  3. Firefox → 设置 → 证书 → 导入 → 信任此证书
  → 这样Burp才能拦截HTTPS流量
```

---

## 二、核心功能详解

### 2.1 Proxy（代理）—— 基础中的基础

```
作用：拦截浏览器发出的每个HTTP请求

[Intercept标签]
  Intercept is on  → 请求会被拦截，等你操作
  Intercept is off → 请求自动放行（但仍被记录）

  拦截到请求后你可以：
  Forward  → 放行（可以先修改再放行）
  Drop     → 丢弃（请求不会到达服务器）
  Action   → 发送到其他工具（Repeater、Intruder等）

[HTTP History标签]（最常看的地方）
  记录了所有经过代理的请求和响应
  可以按URL、状态码、长度等筛选和排序
  双击查看请求/响应的详细内容

工作流程：
  1. 开启代理，Intercept设为off
  2. 浏览器正常浏览目标网站的所有功能
  3. 回到Burp的HTTP History
  4. 浏览所有请求，找到感兴趣的接口
  5. 右键 → Send to Repeater/Intruder
```

### 2.2 Repeater（重放器）—— 最常用的功能

```
作用：手动修改和重发HTTP请求

从Proxy History中右键 → Send to Repeater

Repeater中：
  左边：请求（可以自由修改任何部分）
  右边：响应（点Send后显示）

使用场景：

[1] SQL注入手工测试
  原始：GET /search?id=1
  修改：GET /search?id=1' OR 1=1 --
  点Send → 观察响应

[2] 越权测试
  请求中替换Cookie/Token为另一个用户的
  点Send → 观察响应

[3] 参数篡改
  修改价格：price=1 → price=0.01
  修改角色：role=user → role=admin
  修改数量：quantity=1 → quantity=-1

[4] 快速验证
  在发现可能的漏洞后，用Repeater反复修改payload验证

技巧：
  - Ctrl+R 快速发送请求
  - 可以开多个Tab对比不同请求的响应
  - 底部的搜索框可以在响应中搜索关键词
```

### 2.3 Intruder（入侵者）—— 自动化攻击

```
作用：自动化地发送大量变形请求

使用流程：
  1. 从Proxy/Repeater右键 → Send to Intruder
  2. Positions标签：标记要变化的参数位置
     用§符号包围变量：username=§admin§&password=§123§
  3. Payloads标签：设置每个位置的值列表
  4. 点Start Attack

四种攻击模式：

[Sniper] 单点狙击
  一次只改一个位置，其他保持原值
  适用：测试单个参数的注入

[Battering Ram] 冲撞
  所有位置使用相同的值
  适用：同一个payload测试多个参数

[Pitchfork] 叉子
  位置1用列表1的第N个，位置2用列表2的第N个
  适用：已知的用户名/密码配对（撞库）

[Cluster Bomb] 集束炸弹
  所有列表的完全组合
  适用：暴力破解（用户名×密码的所有组合）

实战示例——暴力破解登录：
  1. 拦截登录请求
  2. Send to Intruder
  3. Positions：标记password参数
  4. Payloads：加载密码字典
  5. Start Attack
  6. 按响应长度排序——长度不同的可能是成功登录
```

### 2.4 Decoder（编解码器）

```
作用：各种编码/解码/哈希计算

支持的编码：
  - URL编码/解码
  - HTML编码/解码
  - Base64编码/解码
  - Hex编码/解码
  - 各种哈希（MD5, SHA1, SHA256）

使用场景：
  - 解码Base64的Cookie值
  - 对payload进行URL编码
  - 解码JWT的各个部分
  - 识别和解码响应中的编码数据
```

### 2.5 Comparer（对比器）

```
作用：对比两个请求或响应的差异

使用场景：
  - 对比"正确密码"和"错误密码"的响应差异
  - 对比"有权限"和"无权限"的响应差异
  - 对比"正常请求"和"注入请求"的响应差异
  - 发现细微的差异（用于盲注判断）

操作：
  从任何地方右键 → Send to Comparer
  在Comparer中选择两个项目 → 点Words或Bytes对比
```

---

## 三、实战工作流

### 3.1 标准安全测试流程（Burp视角）

```
[阶段1] 信息收集
  1. 配置代理，Intercept off
  2. 浏览器遍历目标网站所有功能
  3. 包括：登录、注册、搜索、个人设置、所有按钮
  4. 回到Burp查看HTTP History
  5. 按Host排序，过滤目标域名
  6. 记录所有API接口和参数

[阶段2] 被动分析
  7. 查看所有响应的安全头
  8. 查看Cookie属性
  9. 查看是否有信息泄露（注释、错误信息、版本号）
  10. 查看是否有敏感数据在响应中

[阶段3] 主动测试
  11. 对每个参数：Send to Repeater → 测试注入
  12. 对认证功能：Send to Intruder → 暴力破解测试
  13. 对资源接口：替换Token → 越权测试
  14. 对上传功能：修改文件名和内容 → 文件上传测试
  15. 对表单操作：检查CSRF Token → CSRF测试
```

### 3.2 用Burp测试SQL注入

```
1. 找到带参数的请求（如 /search?q=test）
2. Send to Repeater
3. 在Repeater中逐步测试：

   原始：q=test
   测试：q=test'                → 观察是否报错
   测试：q=test' AND '1'='1    → 观察响应
   测试：q=test' AND '1'='2    → 对比响应差异
   测试：q=test' ORDER BY 1--  → 确定列数
   测试：q=test' UNION SELECT 1,2,3-- → 回显位置

4. 关键是对比：正常响应 vs 注入后的响应
   用Comparer辅助对比
```

### 3.3 用Burp测试越权

```
准备：
  浏览器1用用户A登录 → 记录Cookie A
  浏览器2用用户B登录 → 记录Cookie B

测试：
  1. 用浏览器A操作，Burp记录所有请求
  2. 在HTTP History中找到用户A的资源请求
  3. Send to Repeater
  4. 替换Cookie为用户B的Cookie
  5. Send → 如果返回用户A的数据 → 越权

批量测试（用Intruder）：
  1. 找到 GET /api/user/profile/101（用户A的ID是101）
  2. Send to Intruder
  3. 标记101为变量
  4. Payload：101, 102, 103, ... 200
  5. 使用用户A的Cookie
  6. Start Attack
  7. 观察哪些ID返回了200（不该看到的数据）
```

---

## 四、常用插件

```
Burp Suite支持通过BApp Store安装扩展插件：

[Autorize] — 自动化越权测试（强烈推荐）
  设置低权限用户的Cookie
  用高权限用户正常浏览
  自动重放每个请求并对比

[Logger++] — 增强版日志
  更强大的请求过滤和搜索

[JSON Beautifier] — JSON格式化
  自动美化JSON请求和响应

[Turbo Intruder] — 高速暴力测试
  比内置Intruder快得多（Python脚本驱动）

[Param Miner] — 参数发现
  自动发现隐藏的HTTP参数

安装方法：
  Extender标签 → BApp Store → 搜索 → Install
```

---

## 五、动手实践

### 实践1：Burp基础操作

```
1. 启动Burp Suite，配置浏览器代理
2. 访问DVWA，Intercept设为off
3. 遍历DVWA所有页面
4. 回到HTTP History，找到：
   - 登录请求
   - SQL注入页面的请求
   - 文件上传的请求
5. 把登录请求Send to Repeater
6. 修改密码为错误的值 → Send → 观察响应
7. 修改密码为正确的值 → Send → 对比响应差异
```

### 实践2：用Intruder暴力破解

```
1. 拦截DVWA的登录请求
2. Send to Intruder
3. Clear所有默认标记
4. 标记password参数的值
5. Payloads → 简单列表，手动添加：
   123456, password, admin, test, letmein, dragon
6. Start Attack
7. 按Length排序，找到响应长度不同的那个→正确密码
```

### 实践3：用Repeater测试SQL注入

```
1. 访问DVWA SQL Injection页面
2. 输入1，提交
3. 在HTTP History找到这个请求
4. Send to Repeater
5. 逐步修改id参数测试注入（参考Phase 2模块02的步骤）
6. 最终目标：用UNION SELECT提取users表数据
```

---

## 六、自测清单

- [ ] 能配置浏览器使用Burp代理（包括HTTPS证书）？
- [ ] 知道Proxy的Intercept开关和HTTP History的区别？
- [ ] 能用Repeater手动修改和重发请求？
- [ ] 能用Intruder做简单的暴力破解？
- [ ] 知道Intruder四种攻击模式的区别？
- [ ] 能用Decoder做Base64/URL编解码？
- [ ] 能用Comparer对比两个响应？
- [ ] 知道安全测试的标准Burp工作流程？

---

> **下一模块：** [02 sqlmap/Nmap](../02-sqlmap-nmap/README.md) —— 自动化检测利器
