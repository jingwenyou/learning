# 06 越权访问 —— 测试工程师的天然优势

> 越权是**最容易被测试工程师发现**的安全漏洞。
> 不需要复杂的技术，不需要特殊工具，只需要你的**测试直觉**：
> "这个数据/操作，换一个用户试试呢？"

---

## 一、越权的本质

```
越权 = 用户做了超出其权限的事

认证（Authentication）：你是谁？→ 验证身份
授权（Authorization）：你能做什么？→ 检查权限

越权就是授权环节出了问题：
  系统知道你是张三，但没检查张三是否有权限做这件事。
```

---

## 二、越权的两种类型

### 2.1 水平越权（IDOR — Insecure Direct Object Reference）

```
同一角色等级的用户之间跨越边界

场景：
  张三（普通用户）查看自己的订单：
    GET /api/orders/1001      → 看到张三的订单 ✓

  张三把1001改成1002：
    GET /api/orders/1002      → 看到了李四的订单 ✗ 越权！

本质：服务端只检查了"你有没有登录"，没检查"这个订单是不是你的"

常见场景：
  /api/user/profile?id=123         → 改id看别人资料
  /api/orders/456                  → 改订单号看别人订单
  /api/messages/789                → 改消息ID看别人私信
  /api/files/download?file_id=100  → 改ID下载别人文件

为什么叫"水平"：
  张三和李四权限等级相同（都是普通用户）
  张三跨越到了李四的数据 → 水平移动
```

### 2.2 垂直越权（权限提升）

```
低权限用户执行了高权限用户才能做的操作

场景：
  管理后台的接口：
    GET /admin/users          → 列出所有用户
    POST /admin/user/create   → 创建用户
    DELETE /admin/user/123    → 删除用户

  普通用户直接访问这些接口：
    如果服务端没有检查角色 → 普通用户可以执行管理操作 → 垂直越权

为什么叫"垂直"：
  从普通用户跨越到管理员 → 权限等级向上移动

常见场景：
  普通用户直接访问 /admin 路径
  普通用户调用管理API
  修改请求中的role参数（role=user → role=admin）
  修改JWT中的role字段
```

---

## 三、IDOR检测方法（重点）

### 3.1 标准检测流程

```
准备两个账号：用户A 和 用户B

第1步：用用户A正常操作，记录所有包含ID的请求
  例：
    GET /api/profile/1001          ← 用户A的ID是1001
    GET /api/orders?user_id=1001
    PUT /api/profile/1001 Body: {"name": "张三"}

第2步：用用户B登录，获取B的凭证（Cookie/Token）

第3步：用用户B的凭证，请求用户A的资源
  用B的Token请求：GET /api/profile/1001
  如果返回了A的数据 → 水平越权漏洞！

第4步：用用户A的凭证，请求管理接口
  GET /admin/users
  如果返回了数据 → 垂直越权漏洞！
```

### 3.2 要关注的ID类型

```
[数字递增ID] — 最容易被利用
  /api/users/1, /api/users/2, /api/users/3
  攻击者只需要递增数字就能遍历所有用户

[UUID] — 不可预测但不代表安全
  /api/users/a7b3c9d2-e1f0-4a6b-8765-432198abcdef
  UUID猜不到，但如果在某个地方泄露了（日志、其他API响应）
  仍然可以用来越权
  UUID不是访问控制机制！

[文件名/路径]
  /api/download?file=report_zhangsan.pdf
  改成 file=report_lisi.pdf

[复合参数]
  /api/orders?user_id=1001&order_id=2001
  只验证了user_id是当前用户，没验证order_id是否属于这个user_id
```

### 3.3 容易被忽视的越权场景

```
[1] 修改操作的越权
  不只是"看"，还有"改"和"删"
  PUT /api/profile/1002  Body: {"name":"黑客"}  → 改了别人的名字
  DELETE /api/orders/1002                        → 删了别人的订单

[2] 间接引用
  POST /api/transfer
  Body: {"from_account": "A", "to_account": "B", "amount": 100}
  改from_account为C → 从C的账户转账

[3] 批量操作
  POST /api/orders/batch
  Body: {"order_ids": [1001, 1002, 1003]}
  在批量操作中混入别人的ID

[4] 搜索和过滤
  GET /api/orders?status=all
  如果服务端没有限制只返回当前用户的数据
  → 返回了所有用户的订单

[5] 导出功能
  GET /api/export/users.csv
  普通用户能导出所有用户的数据？

[6] 统计和报表
  GET /api/reports/sales?department=all
  普通员工能看到全公司的销售报表？
```

---

## 四、实战测试技巧

### 4.1 Burp Suite中的越权测试

```
方法1：手动替换Token
  1. 浏览器用用户A操作
  2. Burp拦截请求
  3. 替换Cookie/Token为用户B的
  4. 放行请求
  5. 观察响应

方法2：用Burp的"Autorize"插件（推荐）
  1. 安装Autorize插件（BApp Store）
  2. 填入低权限用户的Cookie
  3. 用高权限用户正常浏览
  4. Autorize自动用低权限Cookie重放每个请求
  5. 对比响应，标记可能的越权

方法3：Burp Repeater对比
  1. 把请求发到Repeater
  2. 复制一份到第二个Tab
  3. 第一个用A的Token，第二个用B的Token
  4. 分别发送，对比响应
```

### 4.2 Python自动化越权检测

```python
"""批量越权检测脚本"""
import requests

def test_idor(base_url, endpoints, token_a, token_b):
    """
    用用户B的Token访问用户A的资源
    如果能访问 → 可能存在越权
    """
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"

        # 用户A访问自己的资源（基准）
        resp_a = requests.get(url, headers=headers_a, timeout=10)
        # 用户B访问用户A的资源
        resp_b = requests.get(url, headers=headers_b, timeout=10)

        status_a = resp_a.status_code
        status_b = resp_b.status_code

        if status_b == 200 and status_a == 200:
            # 进一步检查返回内容是否相同
            if resp_a.text == resp_b.text:
                print(f"  [越权!] {endpoint}")
                print(f"    用户A: {status_a} ({len(resp_a.text)}字节)")
                print(f"    用户B: {status_b} ({len(resp_b.text)}字节) ← 返回了相同数据！")
            else:
                print(f"  [可疑] {endpoint} — B可以访问但内容不同，需人工确认")
        elif status_b == 403 or status_b == 401:
            print(f"  [安全] {endpoint} — 正确拒绝了越权访问 ({status_b})")
        else:
            print(f"  [检查] {endpoint} — A:{status_a} B:{status_b}")

# 使用示例
endpoints = [
    "/api/user/profile/1001",       # 用户A的资料
    "/api/orders/2001",              # 用户A的订单
    "/api/messages/inbox",           # 收件箱
    "/admin/dashboard",              # 管理后台
    "/api/users",                    # 用户列表
]

# test_idor("http://target.com", endpoints, "token_a", "token_b")
```

### 4.3 批量ID遍历

```python
"""遍历数字ID，发现可访问的资源"""
import requests

def enumerate_ids(url_template, token, start=1, end=100):
    """
    url_template: "http://target.com/api/users/{id}"
    遍历ID，找到可访问的资源
    """
    headers = {"Authorization": f"Bearer {token}"}
    found = []

    for i in range(start, end + 1):
        url = url_template.replace("{id}", str(i))
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                # 检查是否返回了有意义的数据
                try:
                    data = resp.json()
                    print(f"  [200] ID={i}: {str(data)[:80]}...")
                    found.append(i)
                except:
                    pass
        except:
            pass

    print(f"\n共发现 {len(found)} 个可访问的资源: {found}")
    return found

# enumerate_ids("http://target.com/api/users/{id}", "your_token", 1, 50)
```

---

## 五、越权防御（知道防御才能找到绕过）

```
正确的访问控制实现：

# 错误示范 —— 只检查登录，不检查权限
@app.route("/api/orders/<order_id>")
@login_required
def get_order(order_id):
    order = Order.query.get(order_id)    # 直接查询，不验证所有权
    return jsonify(order)

# 正确示范 —— 检查资源所有权
@app.route("/api/orders/<order_id>")
@login_required
def get_order(order_id):
    order = Order.query.get(order_id)
    if order.user_id != current_user.id:    # 验证这个订单是不是当前用户的
        return jsonify({"error": "forbidden"}), 403
    return jsonify(order)

# 更好的方式 —— 在查询时就限制范围
@app.route("/api/orders/<order_id>")
@login_required
def get_order(order_id):
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id      # 查询条件中包含用户ID
    ).first_or_404()
    return jsonify(order)
```

---

## 六、动手实践

### 实践1：DVWA越权测试

```
DVWA本身的越权测试有限，但你可以：

1. 用admin账号登录DVWA
2. 查看各个功能页面的URL
3. 打开一个无痕窗口（不登录）
4. 直接访问这些URL → 能访问吗？（垂直越权测试）

5. 如果DVWA支持多用户，创建第二个账号
6. 用第二个账号访问第一个账号的功能页面
```

### 实践2：构建一个越权测试场景

```python
"""用Flask构建一个有越权漏洞的练习靶场"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# 模拟用户数据
users = {
    "user1": {"id": 1, "name": "张三", "phone": "13800001111", "balance": 1000},
    "user2": {"id": 2, "name": "李四", "phone": "13800002222", "balance": 2000},
}

# 模拟Token验证（简化版）
tokens = {
    "token_user1": "user1",
    "token_user2": "user2",
    "token_admin": "admin",
}

def get_current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return tokens.get(token)

# 有漏洞的接口 —— IDOR
@app.route("/api/user/<int:user_id>")
def get_user(user_id):
    current = get_current_user()
    if not current:
        return jsonify({"error": "未登录"}), 401

    # 漏洞：只检查是否登录，不检查是否有权限查看这个用户
    for uname, udata in users.items():
        if udata["id"] == user_id:
            return jsonify(udata)
    return jsonify({"error": "用户不存在"}), 404

# 有漏洞的接口 —— 垂直越权
@app.route("/admin/users")
def admin_users():
    current = get_current_user()
    if not current:
        return jsonify({"error": "未登录"}), 401

    # 漏洞：只检查登录，不检查是否是admin
    return jsonify(list(users.values()))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

```bash
# 启动后测试：

# 正常访问自己的资料
curl -H "Authorization: Bearer token_user1" http://localhost:5000/api/user/1

# 越权访问别人的资料
curl -H "Authorization: Bearer token_user1" http://localhost:5000/api/user/2
# 如果返回了李四的数据 → IDOR漏洞！

# 普通用户访问管理接口
curl -H "Authorization: Bearer token_user1" http://localhost:5000/admin/users
# 如果返回了所有用户 → 垂直越权！
```

---

## 七、越权检查清单

```
水平越权（IDOR）：
  □ 所有包含ID的接口，用另一用户的Token测试
  □ 递增/递减ID参数
  □ GET（查看）、PUT（修改）、DELETE（删除）都要测
  □ 批量接口中混入其他用户的ID
  □ 搜索/过滤/导出功能是否限制了数据范围
  □ 文件下载是否校验文件所有者

垂直越权：
  □ 普通用户直接访问管理URL
  □ 普通用户调用管理API
  □ 修改请求中的角色参数
  □ 修改JWT中的角色字段
  □ 前端隐藏的菜单/按钮对应的接口是否做了后端验证

接口发现：
  □ API文档（Swagger/OpenAPI）中是否有未授权接口
  □ 前端JS中是否有隐藏的API路径
  □ 修改HTTP方法（GET→POST→PUT→DELETE）是否能发现新接口
```

---

## 八、自测清单

- [ ] 水平越权和垂直越权的区别？
- [ ] IDOR的全称和含义？
- [ ] 为什么说UUID不是访问控制机制？
- [ ] 越权测试至少需要几个账号？测试流程是什么？
- [ ] 除了"查看"操作，还有哪些操作需要测试越权？
- [ ] 知道Burp Suite怎么做越权测试（手动替换Token）？
- [ ] 正确的访问控制代码应该怎么写（和错误的对比）？

---

> **下一模块：** [07 文件上传漏洞](../07-file-upload/README.md) —— 上传一个"炸弹"
