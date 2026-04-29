# 03 Linux基础 —— 安全工具的运行环境

> 绝大多数安全工具跑在Linux上，靶场跑在Linux上，真实的服务器也跑在Linux上。
> 你不需要成为Linux专家，但必须能**在Linux上自如地操作**。

---

## 一、为什么安全测试离不开Linux

1. **安全工具的主场**：Burp Suite、Nmap、sqlmap、Metasploit……原生支持最好的平台是Linux
2. **靶场环境**：DVWA、WebGoat等靶场通常用Docker部署在Linux上
3. **目标服务器**：互联网上超过70%的服务器跑Linux，你测试的目标大概率是Linux
4. **Kali Linux**：专门为安全测试打造的发行版，预装了几百个安全工具

---

## 二、环境准备

### 推荐方案：虚拟机 + Ubuntu

```bash
# 方案1：VirtualBox + Ubuntu 22.04（免费，适合入门）
# 方案2：VMware + Ubuntu（更流畅）
# 方案3：WSL2（Windows用户最方便，Windows 10/11自带）

# WSL2安装（Windows用户推荐）
wsl --install -d Ubuntu-22.04

# 后期可以再装Kali Linux
# wsl --install -d kali-linux
```

### 或者：直接用Docker（如果你的机器已经有Docker）

```bash
# 拉一个Ubuntu容器练习
docker run -it ubuntu:22.04 /bin/bash
```

---

## 三、文件系统：Linux的"地图"

### 3.1 目录结构

```
/                    ← 根目录，一切的起点
├── /home/username/  ← 你的主目录（类似Windows的"我的文档"）
├── /root/           ← root用户的主目录
├── /etc/            ← 系统配置文件（极其重要）
│   ├── passwd       ← 用户信息
│   ├── shadow       ← 密码哈希（需要root权限读取）
│   ├── hosts        ← 本地DNS映射
│   └── nginx/       ← Nginx配置
├── /var/            ← 可变数据
│   ├── log/         ← 系统日志（安全排查常看）
│   └── www/         ← Web服务器默认网站目录
├── /tmp/            ← 临时文件（所有人可写，安全隐患点）
├── /usr/            ← 用户程序
├── /bin/            ← 基本命令
├── /sbin/           ← 系统管理命令
└── /proc/           ← 虚拟文件系统（进程信息，实时内核数据）
```

**安全相关的关键路径：**
```
/etc/passwd      → 可以看到系统有哪些用户（所有人可读）
/etc/shadow      → 密码哈希（只有root可读，拿到就能离线爆破）
/var/log/         → 日志文件，安全事件排查必看
/tmp/             → 所有人可写，常被利用作临时中转
/proc/self/       → 当前进程信息，SSRF/LFI中常用来读取环境变量
```

### 3.2 文件操作基础

```bash
# === 导航 ===
pwd                    # 当前目录
ls -la                 # 列出所有文件（含隐藏文件），显示详细信息
cd /etc                # 进入目录
cd ~                   # 回到主目录
cd -                   # 回到上一个目录

# === 查看文件 ===
cat filename           # 查看整个文件
head -20 filename      # 查看前20行
tail -20 filename      # 查看后20行
tail -f /var/log/syslog  # 实时跟踪日志（重要技能）
less filename          # 分页查看（大文件用这个，q退出）

# === 创建和编辑 ===
touch newfile          # 创建空文件
mkdir -p dir1/dir2     # 创建多级目录
nano filename          # 简单编辑器（推荐新手用）
vim filename           # 强大但有学习曲线（i进入编辑，Esc后:wq保存退出）

# === 复制、移动、删除 ===
cp file1 file2         # 复制
cp -r dir1 dir2        # 复制目录
mv file1 /tmp/         # 移动
mv old_name new_name   # 重命名
rm file                # 删除文件
rm -r dir              # 删除目录（小心使用！）

# === 查找文件 ===
find / -name "*.conf"  # 全盘搜索.conf文件
find /var/log -name "*.log" -mtime -1  # 找到最近1天修改的日志
which nmap             # 查找命令的路径
locate filename        # 快速搜索（需要先updatedb）
```

---

## 四、权限系统：Linux安全的基石

### 4.1 理解权限表示

```bash
ls -la
# 输出示例：
# -rwxr-xr-- 1 root www-data 4096 Jan 1 00:00 script.sh
#  ↑↑↑↑↑↑↑↑↑↑  ↑    ↑
#  ||||||||||  所有者 所属组
#  |├─┤├─┤├─┤
#  | u  g  o
#  |用户 组 其他人
#  文件类型（- 普通文件, d 目录, l 链接）

# rwx 含义：
# r (read)    = 4  → 可读
# w (write)   = 2  → 可写
# x (execute) = 1  → 可执行

# rwxr-xr-- 翻译：
# 所有者(root)：rwx = 可读+可写+可执行 = 7
# 所属组(www-data)：r-x = 可读+可执行 = 5
# 其他人：r-- = 只可读 = 4
# 数字表示：754
```

### 4.2 修改权限

```bash
chmod 755 script.sh    # 所有者rwx，组和其他人rx
chmod 644 config.txt   # 所有者rw，其他人只读
chmod +x script.sh     # 给所有人添加执行权限
chmod u+w file         # 只给所有者添加写权限

chown user:group file  # 改变文件所有者和组
chown -R www-data:www-data /var/www/  # 递归修改目录
```

### 4.3 权限与安全（重点）

```
安全问题1：配置文件权限过宽
  /etc/shadow 如果被设为 644（所有人可读）
  → 任何用户都能读到密码哈希 → 离线暴力破解

安全问题2：Web目录可写
  /var/www/html/ 如果被设为 777（所有人可写可执行）
  → 攻击者上传webshell后可以直接执行

安全问题3：SUID位
  chmod u+s program    # 设置SUID位
  # SUID意味着：任何人运行这个程序时，都以程序所有者的权限运行
  # 如果一个root拥有的程序有SUID位 → 普通用户执行它就有root权限
  # 这是Linux提权的经典方式

  # 查找所有SUID程序：
  find / -perm -u=s -type f 2>/dev/null
  # 安全测试中发现异常的SUID程序 = 潜在提权路径

安全问题4：/tmp目录
  所有人可写，但有sticky bit（只能删自己的文件）
  仍然是攻击者常用的临时文件存放地
```

---

## 五、用户与进程管理

### 5.1 用户相关

```bash
whoami                 # 当前用户
id                     # 当前用户的详细信息（uid, gid, 所属组）
cat /etc/passwd        # 查看所有用户
  # 格式：用户名:x:uid:gid:描述:主目录:默认shell
  # root:x:0:0:root:/root:/bin/bash
  # www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
  #                                     ↑ nologin = 不能登录，但服务用这个用户运行

sudo command           # 以root权限执行命令
su - username          # 切换到其他用户
```

### 5.2 进程管理

```bash
ps aux                 # 查看所有进程
ps aux | grep nginx    # 查找特定进程

top                    # 实时进程监控（q退出）
htop                   # 更好看的版本（需要安装）

kill PID               # 终止进程
kill -9 PID            # 强制终止

# 安全相关：
# 查看哪些进程在监听网络端口
ss -tunlp
# 或
netstat -tunlp

# 输出示例：
# tcp  LISTEN  0.0.0.0:3306  users:(("mysqld",pid=1234))
# 意味着：MySQL在所有网络接口上监听3306端口
# 如果这是公网服务器 → MySQL暴露在公网 → 严重安全风险
```

---

## 六、网络命令（安全测试高频使用）

```bash
# === 网络状态 ===
ip addr                # 查看网络接口和IP
ip route               # 查看路由表
ss -tunlp              # 查看监听端口（最常用）

# === 连通性测试 ===
ping 8.8.8.8           # 测试网络连通
ping -c 4 target       # 只发4个包

traceroute target      # 追踪路由路径
# 或
tracepath target

# === DNS ===
nslookup domain        # DNS查询
dig domain             # 更详细的DNS查询
dig +short domain      # 只显示IP
host domain            # 简洁的DNS查询

# === HTTP请求 ===
curl -v url            # 发请求并显示详细过程
curl -I url            # 只看响应头
curl -X POST url -d "data"  # POST请求
wget url               # 下载文件

# === 端口探测 ===
# 不用nmap也能简单测试端口
nc -zv target 80       # 测试80端口是否开放（netcat）
# 或
timeout 3 bash -c "echo > /dev/tcp/target/80" && echo "open" || echo "closed"

# === 抓包 ===
sudo tcpdump -i any port 80   # 抓HTTP流量
sudo tcpdump -i any -w capture.pcap  # 保存抓包文件（用Wireshark打开分析）
```

---

## 七、文本处理（日志分析利器）

安全测试中经常需要分析大量日志和输出，文本处理是核心技能：

```bash
# === grep：搜索文本 ===
grep "error" /var/log/syslog         # 搜索包含error的行
grep -i "error" file                  # 不区分大小写
grep -r "password" /etc/              # 递归搜索目录
grep -n "login" file                  # 显示行号
grep -v "info" file                   # 排除包含info的行
grep -E "error|warning|fail" file     # 正则匹配多个关键词
grep -c "404" access.log              # 统计匹配行数

# === 管道：组合命令的力量 ===
# 管道 | 把前一个命令的输出，作为后一个命令的输入

cat access.log | grep "404" | wc -l   # 统计404错误数量
ps aux | grep python                   # 找Python进程
ss -tunlp | grep LISTEN                # 只看监听的端口

# === 常用组合 ===
# 查看访问最多的IP（Web日志分析）
cat access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# 查看被扫描的迹象（大量404）
grep " 404 " access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# 查找文件中的敏感信息
grep -rn "password\|secret\|token\|api_key" /path/to/project/

# 实时监控日志中的异常
tail -f /var/log/auth.log | grep --color "Failed"
```

---

## 八、软件安装与服务管理

```bash
# === Ubuntu/Debian ===
apt update                    # 更新软件源
apt install nmap              # 安装软件
apt search keyword            # 搜索软件
apt remove package            # 卸载

# === CentOS/RHEL ===
yum install nmap
# 或
dnf install nmap

# === 通用：用pip安装Python工具 ===
pip3 install sqlmap

# === 服务管理（systemd） ===
systemctl status nginx        # 查看服务状态
systemctl start nginx         # 启动
systemctl stop nginx          # 停止
systemctl restart nginx       # 重启
systemctl enable nginx        # 开机自启
systemctl list-units --type=service  # 查看所有服务
journalctl -u nginx -f        # 查看服务日志

# === Docker（靶场环境必备） ===
# 安装Docker
curl -fsSL https://get.docker.com | sh

# 基本操作
docker ps                     # 查看运行中的容器
docker ps -a                  # 查看所有容器
docker images                 # 查看已有镜像
docker run -d -p 8080:80 image  # 后台运行，端口映射
docker exec -it container_id bash  # 进入容器
docker logs container_id      # 查看容器日志
docker stop container_id      # 停止容器
docker-compose up -d          # 用docker-compose启动多容器环境
```

---

## 九、动手实践

### 实践1：文件权限实验

```bash
# 创建测试文件
echo "secret data" > /tmp/secret.txt

# 观察默认权限
ls -la /tmp/secret.txt

# 设为只有自己可读
chmod 600 /tmp/secret.txt

# 如果有其他用户，切换过去试试能不能读
# su - testuser
# cat /tmp/secret.txt   → 应该被拒绝

# 查找系统中的SUID程序
find / -perm -u=s -type f 2>/dev/null
# 记录下来，后面学提权时会用到
```

### 实践2：网络探测

```bash
# 查看本机监听了哪些端口
ss -tunlp

# 用netcat探测一个远程端口
nc -zv scanme.nmap.org 22
nc -zv scanme.nmap.org 80

# 查看某个域名的DNS记录
dig scanme.nmap.org
```

### 实践3：日志分析模拟

```bash
# 创建一个模拟的访问日志
cat > /tmp/access.log << 'EOF'
192.168.1.100 - - [01/Jan/2024:10:00:01] "GET /index.html HTTP/1.1" 200 1234
192.168.1.100 - - [01/Jan/2024:10:00:02] "GET /style.css HTTP/1.1" 200 567
10.0.0.5 - - [01/Jan/2024:10:00:03] "GET /admin HTTP/1.1" 403 189
10.0.0.5 - - [01/Jan/2024:10:00:04] "GET /../../etc/passwd HTTP/1.1" 400 0
10.0.0.5 - - [01/Jan/2024:10:00:05] "GET /shell.php HTTP/1.1" 404 0
10.0.0.5 - - [01/Jan/2024:10:00:06] "POST /login HTTP/1.1" 200 45
10.0.0.5 - - [01/Jan/2024:10:00:07] "POST /login HTTP/1.1" 401 23
10.0.0.5 - - [01/Jan/2024:10:00:08] "POST /login HTTP/1.1" 401 23
10.0.0.5 - - [01/Jan/2024:10:00:09] "POST /login HTTP/1.1" 401 23
192.168.1.200 - - [01/Jan/2024:10:00:10] "GET /index.html HTTP/1.1" 200 1234
EOF

# 练习：
# 1. 找出所有404请求
grep " 404 " /tmp/access.log

# 2. 统计每个IP的请求次数
awk '{print $1}' /tmp/access.log | sort | uniq -c | sort -rn

# 3. 找出可疑行为（路径遍历尝试）
grep "\.\." /tmp/access.log

# 4. 找出暴力破解迹象（同一IP多次401）
grep " 401 " /tmp/access.log | awk '{print $1}' | sort | uniq -c

# 5. 找出试图访问webshell的请求
grep -E "\.(php|jsp|asp)" /tmp/access.log
```

### 实践4：Docker部署靶场（为Phase 2做准备）

```bash
# 确保Docker已安装
docker --version

# 部署DVWA靶场
docker run -d -p 8081:80 --name dvwa vulnerables/web-dvwa

# 部署WebGoat
docker run -d -p 8082:8080 --name webgoat webgoat/webgoat

# 验证
curl -I http://localhost:8081
curl -I http://localhost:8082/WebGoat

# 浏览器访问：
# DVWA: http://你的IP:8081
# WebGoat: http://你的IP:8082/WebGoat
```

---

## 十、自测清单

- [ ] 能说出Linux主要目录的用途（/etc, /var, /tmp, /proc）？
- [ ] 看到 `-rwxr-x---` 能说出具体权限？对应的数字是什么？
- [ ] 什么是SUID？为什么它是安全风险？
- [ ] 怎么查看系统监听了哪些端口？
- [ ] 怎么从日志中找到暴力破解的迹象？
- [ ] 能用grep + 管道组合做简单的日志分析？
- [ ] Docker的基本操作（run, ps, exec, logs）？
- [ ] 怎么安装和管理系统服务？

---

> **下一模块：** [04 Python安全脚本](../04-python-for-security/README.md) —— 你的自动化武器
