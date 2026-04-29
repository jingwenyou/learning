# 越权访问实战练习指南

> 越权（IDOR/越权）是测试工程师最容易发现的漏洞类型。
> 本练习用Python构建一个故意有漏洞的靶场，带你完整体验越权测试流程。

---

## 环境准备

### 步骤1：启动靶场

```bash
# 方式1：使用已部署的靶场
# 确保DVWA运行中：docker ps | grep dvwa

# 方式2：构建本地测试靶场（推荐自己动手）
# 创建一个有越权漏洞的Flask应用
```

### 步骤2：构建越权练习靶场

```python
# 保存为 idor_practice.py
from flask import Flask, request, jsonify, session, redirect, url_for
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 模拟用户数据库
USERS = {
    "user1": {"id": 1, "name": "张三", "email": "zhangsan@example.com", "balance": 1000, "role": "user"},
    "user2": {"id": 2, "name": "李四", "email": "lisi@example.com", "balance": 2000, "role": "user"},
    "admin": {"id": 3, "name": "管理员", "email": "admin@example.com", "balance": 99999, "role": "admin"},
}

# 模拟数据库存储
DB = {
    "orders": {
        1: {"id": 1, "user_id": 1, "item": "iPhone", "price": 9999, "status": "paid"},
        2: {"id": 2, "user_id": 2, "item": "MacBook", "price": 19999, "status": "paid"},
        3: {"id": 3, "user_id": 1, "item": "AirPods", "price": 1999, "status": "shipped"},
        4: {"id": 4, "user_id": 3, "item": "服务器", "price": 99999, "status": "paid"},
    },
    "messages": {
        1: {"id": 1, "to_user_id": 1, "content": "订单1已发货"},
        2: {"id": 2, "to_user_id": 1, "content": "订单2已发货"},
        3: {"id": 3, "to_user_id": 2, "content": "你的MacBook到了"},
        4: {"id": 4, "to_user_id": 3, "content": "管理员通知"},
    }
}

TOKENS = {}  # token -> username映射

def get_current_user():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        return TOKENS.get(token)
    return None

@app.route("/")
def index():
    return jsonify({
        "message": "越权练习靶场",
        "endpoints": {
            "登录": "POST /login {\"username\": \"...\", \"password\": \"...\"}",
            "获取用户资料": "GET /api/user/<id> (Authorization: Bearer <token>)",
            "修改用户资料": "PUT /api/user/<id> {\"name\": \"...\", \"email\": \"...\"}",
            "查看我的订单": "GET /api/orders (Authorization: Bearer <token>)",
            "查看任意订单": "GET /api/order/<id> (Authorization: Bearer <token>)",
            "管理员面板": "GET /admin/users (Authorization: Bearer <token>)",
        }
    })

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password", "password")  # 简化版，所有密码都是password

    if username in USERS:
        token = secrets.token_hex(32)
        TOKENS[token] = username
        return jsonify({
            "success": True,
            "token": token,
            "user": USERS[username]
        })
    return jsonify({"success": False, "error": "用户不存在"}), 401

# ==================== 有漏洞的接口 ====================

@app.route("/api/user/<int:user_id>")
def get_user(user_id):
    """漏洞：只检查是否登录，不检查是否是自己的数据"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "未登录"}), 401

    # 漏洞！直接用user_id查，不验证是否是当前用户的
    for username, user in USERS.items():
        if user["id"] == user_id:
            return jsonify(user)

    return jsonify({"error": "用户不存在"}), 404

@app.route("/api/user/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """漏洞：修改时不检查数据所属权"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "未登录"}), 401

    data = request.json

    # 漏洞！张三可以直接修改李四的资料
    for username, user in USERS.items():
        if user["id"] == user_id:
            if "name" in data:
                user["name"] = data["name"]
            if "email" in data:
                user["email"] = data["email"]
            return jsonify({"success": True, "user": user})

    return jsonify({"error": "用户不存在"}), 404

@app.route("/api/order/<int:order_id>")
def get_order(order_id):
    """漏洞：不验证订单是否属于当前用户"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "未登录"}), 401

    order = DB["orders"].get(order_id)
    if order:
        return jsonify(order)
    return jsonify({"error": "订单不存在"}), 404

@app.route("/admin/users")
def admin_users():
    """漏洞：只检查是否登录，不检查是否是管理员"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "未登录"}), 401

    # 漏洞！普通用户也能访问管理员接口
    return jsonify({"users": list(USERS.values()), "count": len(USERS)})

# ==================== 有防护的接口 ====================

@app.route("/api/protected/user/<int:user_id>")
def get_user_safe(user_id):
    """安全版本：验证数据所属权"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "未登录"}), 401

    user = USERS.get(current_user)
    if user and user["id"] == user_id:
        return jsonify(user)

    return jsonify({"error": "无权访问该用户数据"}), 403

if __name__ == "__main__":
    print("\n" + "="*60)
    print("越权练习靶场已启动")
    print("="*60)
    print("\n测试账号（密码都是password）：")
    print("  - user1 (张三, 普通用户)")
    print("  - user2 (李四, 普通用户)")
    print("  - admin (管理员)\n")
    print("开始练习前，先获取token：")
    print("  curl -X POST http://localhost:5000/login -H 'Content-Type: application/json' -d '{\"username\":\"user1\"}'\n")
    print("="*60 + "\n")
    app.run(port=5000, debug=True)
```

```bash
# 启动靶场
python3 idor_practice.py
```

---

## 练习1：登录并获取Token

### 步骤1.1：登录用户1（张三）

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1"}'
```

记录返回的token：
```json
{"success":true,"token":"abc123...","user":{...}}
```

### 步骤1.2：登录用户2（李四）

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user2"}'
```

### 步骤1.3：登录管理员

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin"}'
```

---

## 练习2：水平越权（IDOR）

### 步骤2.1：用张三的Token查看自己的资料

```bash
# 假设张三的token是 TOKEN_USER1
curl http://localhost:5000/api/user/1 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回张三的用户信息
```json
{"id":1,"name":"张三","email":"zhangsan@example.com","balance":1000,"role":"user"}
```

### 步骤2.2：用张三的Token查看李四的资料（越权！）

```bash
curl http://localhost:5000/api/user/2 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回李四的信息！

这就是水平越权：
- 张三（user_id=1）登录
- 用张三的token访问 user_id=2（李四）的数据
- 服务端没有验证"这个数据是不是张三的"

结论：张三可以看所有用户的信息！

### 步骤2.3：用张三的Token查看管理员的资料

```bash
curl http://localhost:5000/api/user/3 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回管理员的信息！

### 步骤2.4：用张三的Token修改李四的资料（修改越权！）

```bash
curl -X PUT http://localhost:5000/api/user/2 \
  -H "Authorization: Bearer TOKEN_USER1" \
  -H "Content-Type: application/json" \
  -d '{"name":"被张三改的名字"}'
```

验证李四的资料是否被改了：
```bash
curl http://localhost:5000/api/user/2 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 李四的名字变成了"被张三改的名字"！

---

## 练习3：垂直越权

### 步骤3.1：用普通用户张三的Token访问管理接口

```bash
curl http://localhost:5000/admin/users \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回了所有用户列表！

这就是垂直越权：
- 张三只是普通用户（role="user"）
- 但他能访问管理员才能用的 /admin/users 接口
- 服务端只检查了"是否登录"，没检查"是否是管理员"

### 步骤3.2：用没有登录的请求访问

```bash
curl http://localhost:5000/admin/users
```

Expected: 返回 `{"error":"未登录"}`

---

## 练习4：订单越权

### 步骤4.1：查看张三的订单

```bash
curl http://localhost:5000/api/order/1 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回订单1（属于张三）

### 步骤4.2：用张三的Token查看李四的订单

```bash
curl http://localhost:5000/api/order/2 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回订单2（属于李四）！

张三的Token可以看到所有人的订单！

### 步骤4.3：查看管理员的高额订单

```bash
curl http://localhost:5000/api/order/4 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 返回订单4（服务器，99999元）

---

## 练习5：对比安全版本

### 步骤5.1：访问有防护的接口

```bash
curl http://localhost:5000/api/protected/user/1 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: 成功（张三访问自己的数据）

### 步骤5.2：尝试越权访问

```bash
curl http://localhost:5000/api/protected/user/2 \
  -H "Authorization: Bearer TOKEN_USER1"
```

Expected: `{"error":"无权访问该用户数据"}` 403！

安全版本正确验证了数据所属权！

---

## 练习6：用Python脚本批量检测越权

```python
"""越权自动化检测脚本"""
import requests
import json

BASE_URL = "http://localhost:5000"

def login(username):
    resp = requests.post(f"{BASE_URL}/login", json={"username": username})
    return resp.json()["token"]

def test_idor():
    # 登录两个用户
    token1 = login("user1")  # 张三
    token2 = login("user2")  # 李四

    print("=== 水平越权测试 ===\n")

    # 张三访问自己的数据
    resp = requests.get(f"{BASE_URL}/api/user/1",
                        headers={"Authorization": f"Bearer {token1}"})
    print(f"张三访问自己的数据: {resp.status_code}")
    print(f"  内容: {resp.json()}\n")

    # 张三访问李四的数据
    resp = requests.get(f"{BASE_URL}/api/user/2",
                        headers={"Authorization": f"Bearer {token1}"})
    print(f"张三访问李四的数据: {resp.status_code}")
    print(f"  内容: {resp.json()}")
    if resp.status_code == 200:
        print(f"  [漏洞!] 水平越权存在!\n")

    print("=== 垂直越权测试 ===\n")

    # 张三访问管理员接口
    resp = requests.get(f"{BASE_URL}/admin/users",
                        headers={"Authorization": f"Bearer {token1}"})
    print(f"普通用户张三访问管理员接口: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  [漏洞!] 垂直越权存在! 看到了 {len(resp.json()['users'])} 个用户\n")

    print("=== 安全版本测试 ===\n")

    # 测试有防护的版本
    resp = requests.get(f"{BASE_URL}/api/protected/user/2",
                        headers={"Authorization": f"Bearer {token1}"})
    print(f"张三尝试访问李四(安全版本): {resp.status_code}")
    if resp.status_code == 403:
        print(f"  [安全] 正确拒绝越权访问!\n")

test_idor()
```

---

## 练习7：DVWA越权测试

### 步骤7.1：识别可能越权的功能

```
DVWA中哪些功能可能存在越权？

1. SQL Injection → 改ID参数访问其他用户数据
2. URL中有ID的参数 → 改ID值
3. 任何包含数字ID的URL和表单
```

### 步骤7.2：在DVWA中测试

```
1. DVWA → 任意一个带ID的功能（如SQL Injection）
2. 用admin账号正常操作，记录请求格式
3. 用Burp拦截请求
4. 修改ID参数为另一个值
5. 观察响应

如果是未授权访问 → 漏洞！
```

---

## 完成标志

完成以上练习后，你应该能够：
- [ ] 理解水平越权和垂直越权的区别
- [ ] 能在Python脚本中复现越权漏洞
- [ ] 知道如何用curl和Python测试越权
- [ ] 能对比有漏洞版本和安全版本的代码差异
- [ ] 能在DVWA中找到越权测试点
- [ ] 能给开发提出具体的修复建议
