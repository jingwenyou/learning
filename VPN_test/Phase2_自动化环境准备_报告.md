# Phase 2: 自动化环境准备 - 报告

**测试日期**: 2026-04-17
**目标设备**: 海泰方圆综合安全网关 (192.168.110.243:8443)
**方法论**: AI驱动Web系统测试最佳实践方法论 - Phase 2

---

## 2.1 工具链确认

| 工具 | 用途 | 状态 | 命令 |
|------|------|------|------|
| Playwright | Web自动化、截图 | ✓ 已安装 | `pip install playwright` |
| Anthropic SDK | 验证码识别 | ✓ 已安装 | `pip install anthropic` |
| requests | HTTP接口测试 | ✓ 已安装 | `pip install requests` |
| Python 3 | 运行环境 | ✓ 可用 | `python3 --version` |

---

## 2.2 目录结构

```
/root/AI/VPN_test/script/
├── __init__.py
├── base_login.py          # 基础登录框架 (Phase 2核心产出)
├── permission_matrix.py   # 权限矩阵测试 (Phase 3)
├── captcha_solver.py      # 验证码识别模块
├── pages/                 # 页面对象模型 (POM)
│   ├── __init__.py
│   └── login_page.py      # 登录页面对象
├── data/                  # 测试数据
│   ├── __init__.py
│   └── test_data.py       # 账号矩阵、API端点、Payload
├── tests/                 # 测试用例
│   └── __init__.py
└── utils/                 # 工具模块
    ├── __init__.py
    └── captcha_solver.py  # 验证码识别
```

---

## 2.3 测试数据清单

### 账号矩阵

| 角色键名 | 显示名称 | 密码 | 索引 |
|----------|----------|------|------|
| system_admin | 系统管理员 | 1111aaa* | 0 |
| security_admin | 安全管理员 | 1111aac* | 1 |
| audit_admin | 审计管理员 | 1111aab* | 2 |

### API端点矩阵 (15+个关键接口)

| API路径 | 方法 | 所属角色 | 说明 |
|---------|------|----------|------|
| /system/user | GET | 系统管理员 | 用户列表 |
| /system/role | GET | 系统管理员 | 角色列表 |
| /sys/reboot | POST | 系统管理员 | 重启设备 |
| /vpn/ipsec | GET | 安全管理员 | IPSec配置 |
| /vpn/ssl | GET | 安全管理员 | SSL VPN |
| /network/firewall | GET | 安全管理员 | 防火墙规则 |
| /log/operation | GET | 审计管理员 | 操作日志 |
| /log/communication | GET | 审计管理员 | 通信日志 |
| /log/exception | GET | 审计管理员 | 异常日志 |

### 安全测试Payload

| 类型 | 数量 | 示例 |
|------|------|------|
| 命令注入 | 5 | `; id`, `&& whoami` |
| SQL注入 | 4 | `' OR 1=1 --` |
| XSS | 4 | `<script>alert(1)</script>` |
| 路径遍历 | 4 | `../../etc/passwd` |

---

## 2.4 页面对象模型 (POM)

### LoginPage 类

| 方法 | 说明 |
|------|------|
| `goto_login_page(url)` | 访问登录页 |
| `select_role(index)` | 选择角色 |
| `select_role_by_name(name)` | 按名称选择角色 |
| `fill_password(pwd)` | 填写密码 |
| `fill_captcha(code)` | 填写验证码 |
| `click_login()` | 点击登录 |
| `screenshot_captcha(path)` | 截取验证码 |
| `login(index, pwd, code)` | 组合登录 |
| `is_login_page()` | 检查是否在登录页 |

---

## 2.5 核心脚本

### 1. base_login.py - 基础登录冒烟测试

```bash
python3 /root/AI/VPN_test/script/base_login.py
```

**功能**:
- 三角色登录冒烟测试
- 自动识别验证码 (Claude Vision)
- 保存登录状态到 `screenshots/states/*.json`
- 生成登录结果报告

**输出**:
- `screenshots/login_*.png` - 各阶段截图
- `screenshots/states/*.json` - 登录状态
- `screenshots/login_results.json` - 测试结果

### 2. captcha_solver.py - 验证码识别

```python
from script.utils.captcha_solver import solve_captcha

captcha = solve_captcha("/path/to/captcha.png")
```

**功能**:
- Canvas验证码截取
- Claude Vision API识别
- 自动过滤非字母数字字符

### 3. permission_matrix.py - 权限矩阵测试

```bash
python3 /root/AI/VPN_test/script/permission_matrix.py
```

**功能**:
- 加载已保存的登录状态
- 3×3越权矩阵测试
- 三权分立验证
- 生成详细报告

---

## 2.6 执行流程

```
Phase 2 执行顺序:

1. base_login.py          # 三角色登录冒烟
   ├── 截图验证码
   ├── Claude Vision识别
   ├── 自动填表登录
   └── 保存状态文件

2. (后续Phase 3)
   permission_matrix.py    # 权限矩阵测试
   ├── 加载状态文件
   ├── 越权API调用
   └── 生成报告
```

---

## 2.7 前置条件检查

| 检查项 | 命令 | 预期输出 |
|--------|------|----------|
| Python版本 | `python3 --version` | Python 3.x |
| Playwright | `python3 -c "from playwright"` | 无错误 |
| Anthropic | `python3 -c "from anthropic"` | 无错误 |
| requests | `python3 -c "import requests"` | 无错误 |
| 屏幕截图目录 | `ls /root/AI/VPN_test/screenshots/` | 目录存在 |

---

## 2.8 已知限制

1. **验证码识别**: 依赖Claude Vision API，需有效API Key
2. **登录状态**: 需要成功登录后才能保存状态文件
3. **网络**: 需要能访问192.168.110.243:8443

---

## 下一步行动

### 必须先执行

```bash
# 1. 运行基础登录冒烟测试
python3 /root/AI/VPN_test/script/base_login.py

# 2. 验证状态文件生成
ls -la /root/AI/VPN_test/screenshots/states/
```

### Phase 3 执行

```bash
# 3. 运行权限矩阵测试
python3 /root/AI/VPN_test/script/permission_matrix.py
```

---

## Phase 2 产出汇总

| 产出物 | 文件 | 状态 |
|--------|------|------|
| 测试脚本框架 | `script/` | ✓ 完成 |
| 页面对象模型 | `script/pages/login_page.py` | ✓ 完成 |
| 测试数据 | `script/data/test_data.py` | ✓ 完成 |
| 验证码识别 | `script/utils/captcha_solver.py` | ✓ 完成 |
| 基础登录脚本 | `script/base_login.py` | ✓ 完成 |
| 权限矩阵脚本 | `script/permission_matrix.py` | ✓ 完成 |
| Phase 2报告 | `Phase2_自动化环境准备_报告.md` | ✓ 完成 |

---

*本文档为Phase 2自动化环境准备完整产出。*
