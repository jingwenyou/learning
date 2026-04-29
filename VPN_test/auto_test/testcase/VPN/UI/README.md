# VPN安全网关UI自动化测试 - 使用手册

## 一、环境准备

### 1.1 安装依赖
```bash
pip3 install -r doc/requirements.txt
pip3 install playwright
playwright install chromium
```

### 1.2 目标设备配置
修改 `config/devs.py` 中的 vpn_dev 配置：
```python
'vpn_dev': {
    "ip_port": "192.168.110.247:8443",  # 修改为实际IP
    'sec_user': '安全管理员',
    'sec_pwd': 'QzPm@a2*',
    'sys_user': '系统管理员',
    'sys_pwd': 'QzPm@a1*',
    'audit_user': '审计管理员',
    'audit_pwd': 'QzPm@a3*',
}
```

---

## 二、执行测试

### 2.1 基本命令
```bash
cd auto_test

# 运行全部UI测试（39个用例）
python3 -m pytest testcase/VPN/UI/ -v

# 运行Bug回归测试
python3 -m pytest testcase/VPN/UI/test_bug_regression.py -v

# 运行单个测试
python3 -m pytest testcase/VPN/UI/test_bug_regression.py::TestSSLService::test_ssl_resource_edit -v

# 过滤执行
python3 -m pytest testcase/VPN/UI/ -k "ssl" -v
```

### 2.2 常用选项
| 选项 | 说明 |
|------|------|
| `-v` | 详细输出 |
| `-s` | 显示print输出 |
| `-k "关键字"` | 按名称筛选 |
| `--tb=short` | 简化报错 |
| `-x` | 遇失败即停 |

---

## 三、测试用例概览

| 测试文件 | 用例数 | 说明 |
|----------|--------|------|
| test_vpn_login.py | 5 | 登录功能 |
| test_vpn_permission.py | 4 | 菜单权限 |
| test_ssl_service.py | 5 | SSL服务 |
| test_ipsec_service.py | 6 | IPSec服务 |
| test_audit_log.py | 6 | 审计日志 |
| test_bug_regression.py | 13 | Bug回归验证 |
| **总计** | **39** | 全部通过 |

---

## 四、Bug回归测试详情

| 测试类 | Bug ID | 描述 |
|--------|--------|------|
| TestCertificateManagement | [32083] | 设备证书分页展示 |
| | [31955] | 证书有效期显示到日 |
| TestSSLService | [31767] | SSL资源配置编辑资源名错误 |
| | [31572] | 密码算法勾选显示+6 |
| | [31569] | 重置按钮未清空配置 |
| | [31320] | 关闭隧道后重置按钮未取消 |
| TestQuantumService | [31436] | 抗量子服务页面502 |
| | [31442] | 抗量子服务增加重置功能 |
| TestLoginAndSession | [32084] | 页面过期上传证书返502 |
| | [31728] | 直接URL访问行为 |
| | [30786] | 页面超时未退出 |
| | [30265] | 退出后history访问安全 |
| TestIPSecService | [32013] | IPSec策略允许/拒绝切换 |

---

## 五、禅道Bug数据

685个Bug原始数据在 `bugs_list.json`

```bash
# 查看高优先级UI bug
cat bugs_list.json | python3 -c "
import json,sys
bugs=json.load(sys.stdin)
ui_kw=['界面','页面','按钮','显示','弹窗','菜单','输入','表单']
for b in bugs:
    if b['severity'] in ['1-高','2-中'] and any(k in b['title'] for k in ui_kw):
        print(f\"[{b['id']}] [{b['severity']}] {b['title'][:70]}\")
"
```

---

## 六、页面对象方法

`VpnHomePage` 类：

| 方法 | 说明 |
|------|------|
| `login(username, password)` | 登录（自动绕过验证码） |
| `click_ssl(sub_menu)` | SSL服务菜单 |
| `click_ipsec(sub_menu)` | IPSec服务菜单 |
| `click_maintenance(sub_menu)` | 系统维护菜单 |
| `click_log(sub_menu)` | 日志管理菜单 |
| `logout()` | 退出登录 |
| `get_menu_items()` | 获取可见菜单 |

---

## 七、验证码绕过

`conftest.py` 已配置Playwright route自动绕过canvas验证码。

---

## 八、截图输出

测试截图保存在：`output/UI/vpn_respng/`

---

## 九、禅道信息

- 地址：http://106.37.95.242:48080
- 用户：jingwen.you / a.123456
- 项目：《IPSec/SSL 综合网关 新》