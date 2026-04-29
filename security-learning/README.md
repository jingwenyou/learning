# 安全测试系统学习路线

> 面向测试工程师的安全测试学习体系，从零基础到实战落地。

## 学习理念

```
理解原理 → 动手验证 → 深入本质 → 融入工作
```

每个知识点遵循：**是什么 → 为什么 → 怎么做 → 动手练 → 深入想**

## 学习路线总览

```
Phase 1: 基础筑基（6-8周）
  ├── 01 网络基础 ──── 数据在网络中怎么走的
  ├── 02 HTTP协议 ──── Web世界的通信语言（重点）
  ├── 03 Linux基础 ─── 安全工具的运行环境
  ├── 04 Python脚本 ── 你的自动化武器
  └── 05 Web基础 ──── 前后端交互全貌

Phase 2: 安全核心（8-12周）
  ├── 01 安全思维 ──── 从测试思维到攻击者思维
  ├── 02 注入攻击 ──── SQL注入/命令注入
  │   └── appendix: 路径遍历 ── 穿越目录的黑客之路
  ├── 03 XSS攻击 ──── 跨站脚本的前世今生
  ├── 04 CSRF攻击 ─── 借刀杀人的艺术
  ├── 05 认证缺陷 ──── 登录/Session/Token
  ├── 06 越权访问 ──── 测试工程师的天然优势
  ├── 07 文件上传 ──── 上传一个"炸弹"
  └── 08 SSRF/XXE ─── 服务端请求伪造/XML外部实体

Phase 3: 工具精通（4-6周）
  ├── 01 Burp Suite ── 安全测试的瑞士军刀
  ├── 02 sqlmap/Nmap ─ 自动化检测利器
  └── 03 浏览器DevTools ─ 被低估的安全工具

Phase 4: 进阶提升（持续）
  ├── 01 业务逻辑漏洞 ── 最难自动化检测的漏洞
  ├── 02 API安全测试 ─── 现代Web的主战场
  ├── 03 自动化安全扫描 ── DAST/SAST/SCA工具
  ├── 04 CVSS漏洞评级 ── 给漏洞一个客观分数 ★新增
  ├── 05 GraphQL安全测试 ── 现代API的专属攻击面 ★新增
  └── 06 OAuth 2.0安全 ── 现代认证的标配漏洞 ★新增

Phase 5: 实战落地（持续）
  ├── 01 融入日常测试 ── 安全左移
  ├── 02 安全测试用例 ── 21个可直接使用的用例模板
  └── 03 漏洞报告撰写 ── 专业输出

附录:
  └── PortSwigger Academy ── 每个漏洞类型的配套Lab ★推荐
```

## 每个模块的结构

每个模块包含：
- `README.md` — 知识讲解（原理→深入→本质）
- `practice.md` — **动手实践指南**（靶场练习 + 逐步验证步骤）★核心模块已补充
- `exercises/` — 练习代码和脚本（如有）
- 自测清单 — 学完能回答这些问题就过关

## 推荐练习路径

```
靶场难度递增（按这个顺序练习）：

[第1步] DVWA + Pikachu（本地部署，入门）
  → bash labs/setup-labs.sh
  → 先Low级别，理解每个漏洞的基本形态

[第2步] PortSwigger Web Security Academy（在线，免费，质量最高）
  → https://portswigger.net/web-security
  → 每个漏洞类型有5-10个Lab，循序渐进
  → 做完DVWA对应模块后，去PortSwigger找同类Lab

[第3步] CTF入门（BUUCTF/CTFHub Web题）
  → 综合运用多个漏洞解题
  → 锻炼漏洞串联能力

[第4步] 挖真实src（当有一定积累后）
  → hackerone、bugcrowd、看云SRC
  → 从低危漏洞开始积累实战经验
```

## 重点补充内容（评审后新增）

基于专业评审，以下关键内容已补充：

| 模块 | 内容 | 重要性 |
|------|------|--------|
| CVSS评级 | 漏洞严重程度量化评估方法 | 致命 |
| GraphQL安全 | 现代API的专属攻击面 | 高 |
| 路径遍历 | 独立漏洞类，高频出现 | 高 |
| OAuth 2.0 | 第三方认证的安全问题 | 高 |

## 学习节奏建议

| 阶段 | 每天投入 | 周期 | 节奏 |
|------|---------|------|------|
| Phase 1 | 1-1.5h | 6-8周 | 周一到四学理论，周五到日动手练 |
| Phase 2 | 1-1.5h | 8-12周 | 每个漏洞类型1-2周，必须打靶场 |
| Phase 3 | 1h | 4-6周 | 跟着教程边用边学 |
| Phase 4 | 按需 | 持续 | 结合工作实践 |

## 自学路径建议

```
[第1个月]  Phase 1 基础全部完成
           每学完一个模块 → 做对应的靶场练习
           重点：HTTP协议（Phase 1.2）是最核心的

[第2-3个月] Phase 2 安全核心
           优先级顺序：
           注入(2) → XSS(3) → 越权(6) → CSRF(4) → 认证(5) → 上传(7) → SSRF(8)
           建议从SQL注入开始，这是最经典也是最能触类旁通的

[第4个月]  Phase 3 工具 + Phase 4 新增模块
           Burp Suite必须用熟
           GraphQL和OAuth是新技术的安全测试标配

[第5个月起] Phase 5 实战落地
           把安全测试融入日常工作
           开始写自己的安全测试用例库
```

## 自学检验标准

```
学完一个模块的标志：
  1. 能用自己的话向别人解释这个漏洞
  2. 能在靶场成功复现
  3. 知道防御方法
  4. 能给漏洞打出CVSS分数
  5. 能写出规范的漏洞报告

全部通过 → 进入下一个模块
有任何一条卡住 → 回头复习
```

## 快速开始

```bash
# 1. 部署靶场（一键安装DVWA + WebGoat + Pikachu）
bash labs/setup-labs.sh

# 2. 开始学习
# Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

# 3. 每个模块末尾都有自测清单，通过后再继续
```

## 参考资源

```
靶场：
  PortSwigger Academy — https://portswigger.net/web-security （免费，推荐）
  DVWA — labs/setup-labs.sh 部署
  WebGoat — labs/setup-labs.sh 部署
  Pikachu — labs/setup-labs.sh 部署

工具：
  Burp Suite — https://portswigger.net/burp （社区版免费）
  OWASP ZAP — https://www.zaproxy.org （免费开源）
  sqlmap — pip install sqlmap
  Nmap — apt install nmap

标准：
  OWASP Top 10 — https://owasp.org/Top10
  CVSS 3.1 — https://www.first.org/cvss/calculator
  ASVS — https://owasp.org/www-project-application-security-verification-standard
```

## 当前进度

```
Phase 1: 5/5 个模块 ✓
Phase 2: 8/8 个模块 + 1个附录 ✓
Phase 3: 3/3 个模块 ✓
Phase 4: 6/6 个模块 ✓
Phase 5: 3/3 个模块 ✓
  ★ 新增: CVSS评级, GraphQL安全, 路径遍历附录, OAuth安全
```

---

开始学习： [Phase 1 - 01 网络基础](phase-1-foundations/01-network-basics/README.md)
