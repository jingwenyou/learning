# Smart Ops CLI 部署与使用指南

> 本文档面向运维工程师、Python学习者和性能监控新手，涵盖从快速部署到生产环境完整方案。

---

## 概述

Smart Ops CLI 是一款 Linux 服务器性能监控工具，基于《性能之巅》方法论设计。

**核心功能：**
- **本机检查** - CPU、内存、磁盘、网络状态检查
- **远程巡检** - 通过 SSH 批量检查多台机器
- **历史记录** - SQLite 存储历史数据，支持趋势分析
- **可解释输出** - 显示每项判断的理论依据（《性能之巅》阈值）

**适用场景：**
- 运维日常巡检
- 故障定位分析
- 性能基线建立
- 批量机器监控

---

## 一、环境对应表与选择决策

### 选择决策树

```
你的环境？
├── 有 Python 3.8+ 环境
│   └── → 方式一：源码运行（最简单）
├── 无 Python，需要最小依赖
│   ├── x86_64 架构 → 方式二：二进制运行
│   └── ARM64 架构 → 方式二：ARM64二进制
└── 需要快速部署/迁移
    └── → 方式三：Docker部署
```

### 环境对应表

| 目标环境 | Python版本 | 二进制文件 | 推荐方案 |
|---------|-----------|-----------|---------|
| 完整Linux (x86_64) | Python 3.8+ | `smart-ops-x86_64` | 源码运行 |
| 完整Linux (ARM64) | Python 3.8+ | `smart-ops-arm64` | 源码运行 |
| 裁减版Linux (x86_64) | 无Python | `smart-ops-x86_64` | 二进制运行 |
| 裁减版Linux (ARM64) | 无Python | `smart-ops-arm64` | 二进制运行 |

### 获取二进制文件

如果还没有二进制文件，有两种方式获取：

**方式A：从项目构建（需要Python环境）**
```bash
# 1. 克隆项目
git clone <repo-url>
cd smart-ops-cli

# 2. 构建二进制
pip install pyinstaller
pyinstaller --onefile --name smart-ops-x86_64 src/cli/main.py

# 3. 二进制位于 dist/smart-ops-x86_64
```

**方式B：联系开发者获取预编译版本**
```
如果目标机器无法安装Python和构建工具，请联系项目维护者获取预编译二进制。
```

### 硬件资源要求

| 配置级别 | CPU | 内存 | 磁盘 | 说明 |
|---------|-----|------|------|------|
| **最低配置** | 1核 | 128MB | 100MB | 巡检 1-5 台 |
| **推荐配置** | 2核+ | 256MB+ | 500MB+ | 巡检 10+ 台 |

**注意**：历史数据每 30 天约占用 500MB-1GB，建议配置 SSD 存储。

### 运行时资源消耗（参考值）

| 场景 | 内存占用 | CPU占用 | 执行时间 | 说明 |
|------|---------|---------|---------|------|
| `check`（单次） | ~50MB | <5% | 1-3秒 | 采集系统信息 |
| `monitor`（4主机并发） | ~80MB | <10% | 视网络 | SSH连接期间 |
| `history --hours 720`（30天） | ~100MB | <10% | 5-30秒 | SQLite全表扫描 |

**注意**：
- 上述数值为参考值，实际可能因数据量和系统状态不同
- `history` 查询大数据量时响应较慢，建议添加索引或定期VACUUM
- 并发SSH连接数受 `max_workers` 限制（默认4）

---

## 二、快速开始

### 前置检查

```bash
# 检查 Python 版本（需要 >= 3.8）
python3 --version

# 检查系统架构
uname -m
```

### 方式一：源码运行（完整Linux，有Python）

```bash
# 1. 安装依赖
pip install click psutil paramiko schedule

# 验证依赖安装成功
python3 -c "import click, psutil, paramiko, schedule; print('依赖验证成功')"

# 2. 运行检查
python3 -m src.cli.main check

# 3. 查看帮助
python3 -m src.cli.main --help
```

**验证成功标志：**
```
✅ 检查完成！你的服务器状态：
- CPU使用率正常（< 70%）
- 内存使用率正常（< 80%）
- 磁盘空间充足（> 20%可用）
- 网络连通性正常
```

### 方式二：二进制运行（裁减版Linux，无Python）

```bash
# 1. 获取二进制（从构建机器scp或下载）
scp user@构建机器:/path/to/smart-ops-x86_64 /tmp/smart-ops

# 2. 拷贝到目标机器（网络不通时用U盘）
scp /tmp/smart-ops root@目标机器:/usr/local/bin/smart-ops

# 3. 赋予执行权限（文件属主为运维用户）
chown ops:ops /usr/local/bin/smart-ops
chmod 755 /usr/local/bin/smart-ops

# 4. 验证部署
file /usr/local/bin/smart-ops                    # 确认架构匹配
/usr/local/bin/smart-ops --help                 # 确认可执行

# 5. 直接运行
smart-ops check
```

---

## 三、可用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `check` | 本机性能检查 | `python3 -m src.cli.main check` |
| `monitor` | 远程多机巡检 | `python3 -m src.cli.main monitor -H "root@192.168.1.10"` |
| `history` | 查看历史数据 | `python3 -m src.cli.main history --hours 24` |
| `baseline` | 性能基线 | `python3 -m src.cli.main baseline` |
| `tool` | 工具集 | `python3 -m src.cli.main tool ps` |

### 命令参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-H` | 远程主机地址（格式：用户@主机） | `-H "root@192.168.1.100"` |
| `-k` | SSH密钥文件路径 | `-k ~/.ssh/id_rsa` |
| `-o` | SSH端口（非默认22） | `-o 2222` |
| `-p` | 使用密码认证 | `-p`（仅测试环境） |
| `--interval` | 巡检间隔（秒） | `--interval 300` |

### 详细命令用法

```bash
# ========== check 命令 ==========
# 本机性能检查（CPU、内存、磁盘、网络）
python3 -m src.cli.main check

# 带可解释性输出（学习用，显示判断依据）
python3 -m src.cli.main check --explain

# ========== monitor 命令 ==========
# 远程单台主机（推荐使用SSH密钥）
python3 -m src.cli.main monitor -H "root@192.168.1.100" -k ~/.ssh/id_rsa

# 远程多台主机
python3 -m src.cli.main monitor -H "root@192.168.1.100,root@192.168.1.101" -k ~/.ssh/id_rsa

# 定期巡检（每5分钟）
python3 -m src.cli.main monitor -H "root@192.168.1.100" -k ~/.ssh/id_rsa --interval 300

# 指定非默认SSH端口
python3 -m src.cli.main monitor -H "root@192.168.1.100" -o 2222 -k ~/.ssh/id_rsa

# ========== history 命令 ==========
# 查看最近24小时
python3 -m src.cli.main history --hours 24

# ========== baseline 命令 ==========
# 查看性能基线
python3 -m src.cli.main baseline

# ========== tool 命令 ==========
python3 -m src.cli.main tool port localhost 22
python3 -m src.cli.main tool ps
```

---

## 四、SSH安全连接

### 关键术语说明

| 术语 | 解释 |
|------|------|
| **SSH** | 安全外壳协议，用于远程连接服务器（类比：远程桌面的安全版） |
| **SSH密钥认证** | 用加密钥匙代替密码登录，更安全 |
| **ssh-agent** | SSH密钥管理器，帮你管理私钥无需每次输入密码 |

### 推荐：SSH密钥认证（生产环境）

```bash
# 1. 生成SSH密钥（如果已有可跳过）
ssh-keygen -t ed25519 -C "smart-ops-cli"
# 验证：密钥已生成
ls -la ~/.ssh/id_ed25519*

# 2. 复制公钥到远程主机（建立信任关系，无需每次输入密码）
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@192.168.1.100

# 3. 验证免密登录成功
ssh root@192.168.1.100 "echo OK"
# 预期：无须输入密码，直接输出 OK

# 4. 使用密钥连接
python3 -m src.cli.main monitor -H "root@192.168.1.100" -k ~/.ssh/id_ed25519
```

### 安全：SSH Agent转发

```bash
# 1. 启动ssh-agent
eval "$(ssh-agent -s)"

# 2. 添加密钥
ssh-add ~/.ssh/id_rsa

# 3. 验证 agent 已启动
ssh-add -l
echo $SSH_AUTH_SOCK

# 4. 连接（密钥由agent提供，不暴露密码）
python3 -m src.cli.main monitor -H "root@192.168.1.100"
```

### 环境变量注入密码（不推荐，仅测试用）

```bash
# 密码通过环境变量传递，不在命令参数中
export SSH_PASSWORD="your_password"
python3 -m src.cli.main monitor -H "root@192.168.1.100" -p

# 使用后清除（防止通过history泄露）
unset SSH_PASSWORD
```

**⚠️ 安全警告**：
- 环境变量可以通过 `/proc/[pid]/environ` 被同用户其他进程读取
- 建议生产环境使用 SSH Agent 或密钥认证
- 如果必须使用密码，请使用 `ssh-agent` 方案（见上方推荐）

**⚠️ SSH 已知主机安全警告**：
- 使用 `ssh-keyscan` 自动接受主机密钥存在中间人（MITM）攻击风险
- 生产环境建议：预先在 known_hosts 中配置目标主机指纹，或使用 `StrictHostKeyChecking=yes` 首次连接时手动确认
- paramiko 的 `AutoAddPolicy` 也会自动接受新主机，生产环境建议使用 `RejectPolicy` 并预先配置主机密钥

**⚠️ 重要：paramiko 线程安全**
paramiko **不是线程安全**的，每个线程需要独立的SSH连接。本工具的 monitor 命令在多主机巡检时使用 ThreadPoolExecutor，每个任务线程创建独立连接，避免共享SSH客户端导致的连接问题。详见 ARCHITECTURE.md 第4.6.1节。

### SSH安全加固建议（生产环境）

```bash
# /etc/ssh/sshd_config 配置
PasswordAuthentication no           # 禁用密码认证
PermitRootLogin no                  # 禁用root直接登录
MaxAuthTries 3                      # 最大重试次数
ClientAliveInterval 300             # SSH心跳（防断连）

# 访问控制（建议添加）
AllowUsers ops@192.168.1.0/24      # 只允许特定网段
AllowGroups sshusers                # 只允许特定用户组
```

---

## 五、systemd服务配置（生产环境推荐）

### 关键术语说明

| 术语 | 解释 |
|------|------|
| **systemd** | Linux系统服务管理器，让程序开机自启、受控运行 |
| **service** | systemd的服务单元，定义如何运行一个程序 |

### 安装服务

```bash
# 1. 创建专用用户（如果不存在）
useradd -r -s /bin/false ops || true

# 2. 拷贝二进制
cp dist/smart-ops-x86_64 /usr/local/bin/smart-ops
chown ops:ops /usr/local/bin/smart-ops
chmod 755 /usr/local/bin/smart-ops

# 3. 创建数据目录
mkdir -p /var/lib/smart-ops
chown ops:ops /var/lib/smart-ops

# 4. 安装service文件
cp deployment/smart-ops.service /etc/systemd/system/
systemctl daemon-reload

# 5. 验证配置
systemd-analyze verify /etc/systemd/system/smart-ops.service
systemctl list-unit-files | grep smart-ops
```

### smart-ops.service 配置示例

```ini
[Unit]
Description=Smart Ops CLI Performance Monitor
Documentation=https://github.com/your-org/smart-ops-cli
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ops
Group=ops
WorkingDirectory=/var/lib/smart-ops

# 环境变量
Environment="HOME=/var/lib/smart-ops"
Environment="TZ=Asia/Shanghai"

# 启动命令
ExecStart=/usr/local/bin/smart-ops monitor \
    -H "root@192.168.1.100" \
    -k /home/ops/.ssh/id_rsa \
    --interval 300

# 资源限制（防止耗尽系统资源）
MemoryMax=200M
CPUQuota=20%
TasksMax=10
LimitNOFILE=1024

# 重启策略
Restart=on-failure
RestartSec=10

# 启动超时（防止启动命令挂起）
TimeoutStartSec=60

# 日志配置（使用journald）
StandardOutput=journal
StandardError=journal
SyslogIdentifier=smart-ops

# 安全限制
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/smart-ops
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 服务管理命令

```bash
# 启动服务
systemctl start smart-ops

# 停止服务
systemctl stop smart-ops

# 查看状态（验证服务是否正常运行）
systemctl status smart-ops
# 判断方法：Active: active (running) 表示正常运行

# 查看日志
journalctl -u smart-ops -f

# 验证服务状态
if systemctl is-active --quiet smart-ops; then
    echo "服务运行正常"
else
    echo "服务异常"
    systemctl status smart-ops --no-pager
fi

# 开机自启
systemctl enable smart-ops

# 禁用开机自启
systemctl disable smart-ops
```

---

## 六、Docker部署（现代化场景）

### 关键术语说明

| 术语 | 解释 |
|------|------|
| **Docker** | 容器化平台，将应用及其依赖打包成容器运行 |
| **network_mode: host** | 容器与宿主机共享网络命名空间，直接访问宿主机的/proc |

### Dockerfile

```dockerfile
FROM python:3.12-slim

LABEL maintainer="ops@example.com"
LABEL description="Smart Ops CLI Performance Monitor"

# 安装必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -s /bin/bash ops

# 复制应用
COPY dist/smart-ops-x86_64 /usr/local/bin/smart-ops

# 权限设置
RUN chown ops:ops /usr/local/bin/smart-ops && \
    chmod 500 /usr/local/bin/smart-ops

# 切换到非root用户
USER ops
WORKDIR /home/ops

# 默认命令
ENTRYPOINT ["/usr/local/bin/smart-ops"]
CMD ["--help"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  smart-ops:
    build: .
    container_name: smart-ops
    image: smart-ops:latest

    # 主机网络模式（访问宿主机/proc）
    network_mode: host

    # 资源限制
    mem_limit: 200m
    cpus: 0.2
    pids_limit: 10

    # 挂载必要路径
    volumes:
      - ./data:/home/ops/data
      - /etc/ssh/ssh_config:/etc/ssh/ssh_config:ro

    # 环境变量
    environment:
      - TZ=Asia/Shanghai
      - HOME=/home/ops

    user: "1000:1000"

    # 定期巡检示例
    command: >
      monitor
      -H "root@192.168.1.100"
      -k /home/ops/.ssh/id_rsa
      --interval 300

    restart: unless-stopped

    healthcheck:
      test: ["CMD", "/usr/local/bin/smart-ops", "check"]
      interval: 60s
      timeout: 30s
      retries: 3
```

### Docker使用

```bash
# 构建镜像并验证
docker build -t smart-ops:latest .
docker images | grep smart-ops

# 运行一次性检查
docker run --rm --network host \
  -v $(pwd)/data:/home/ops/data \
  smart-ops check

# 后台运行巡检
docker run -d --network host \
  --name smart-ops \
  -v $(pwd)/data:/home/ops/data \
  smart-ops

# 查看日志
docker logs -f smart-ops

# 查看资源使用
docker stats smart-ops --no-stream

# 停止
docker stop smart-ops

# 检查OOM情况
docker inspect smart-ops | grep -i oom
```

---

## 七、logrotate配置（日志管理）

### 关键术语说明

| 术语 | 解释 |
|------|------|
| **日志轮转** | 自动切分、压缩、清理日志文件，防止磁盘占满 |
| **journald** | systemd的日志系统，由systemd管理 |

### 配置说明

**注意**：由于 systemd service 配置了 `StandardOutput=journal`，日志默认写入 journal，不写入文件。如果需要 logrotate 管理日志文件，需要修改 service 配置。

### /etc/logrotate.d/smart-ops

```
# 日志文件路径（如果service配置使用文件日志）
/var/log/smart-ops.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ops ops
    sharedscripts
    postrotate
        systemctl reload smart-ops > /dev/null 2>&1 || true
    endscript
}
```

### journal 日志管理

```bash
# 查看日志
journalctl -u smart-ops -f

# 按时间范围查看
journalctl -u smart-ops --since "1 hour ago"

# 查看错误日志
journalctl -u smart-ops -p err

# 日志持久化（如果需要）
journalctl --flush && systemctl restart systemd-journald
```

---

## 八、历史数据存储

### 数据位置

```bash
# 默认SQLite数据库路径
/var/lib/smart-ops/history.db

# 可通过环境变量自定义
export SMART_OPS_DB_PATH=/data/history.db
python3 -m src.cli.main history --hours 24
```

### 数据管理

```bash
# 查看数据库大小
ls -lh /var/lib/smart-ops/history.db

# 检查磁盘空间
df -h /var/lib/smart-ops

# 数据保留策略（默认保留30天）
# 查看当前数据量
python3 -m src.cli.main history --hours 720

# 手动清理旧数据
sqlite3 /var/lib/smart-ops/history.db "DELETE FROM health_records WHERE timestamp < datetime('now', '-30 days');"
sqlite3 /var/lib/smart-ops/history.db "VACUUM;"

# 定期VACUUM（建议每周执行）
0 3 * * 0 sqlite3 /var/lib/smart-ops/history.db "VACUUM;"

# 备份数据库
cp /var/lib/smart-ops/history.db /backup/history-$(date +%Y%m%d).db

# 验证数据库可写
python3 -c "import sqlite3; conn = sqlite3.connect('/var/lib/smart-ops/history.db'); conn.close(); print('数据库可写')"

# 数据库完整性检查
sqlite3 /var/lib/smart-ops/history.db "PRAGMA integrity_check;"
```

### SQLite 性能优化（WAL模式）

```bash
# 启用WAL模式（支持并发读写，防止写操作阻塞读）
sqlite3 /var/lib/smart-ops/history.db "PRAGMA journal_mode=WAL;"

# 设置同步级别（平衡性能和数据安全）
sqlite3 /var/lib/smart-ops/history.db "PRAGMA synchronous=NORMAL;"

# 设置忙等待超时（避免并发写入时立即失败）
sqlite3 /var/lib/smart-ops/history.db "PRAGMA busy_timeout=5000;"

# 验证当前模式
sqlite3 /var/lib/smart-ops/history.db "PRAGMA journal_mode;"
sqlite3 /var/lib/smart-ops/history.db "PRAGMA busy_timeout;"
```

**注意**：首次创建数据库时需要执行这些PRAGMA命令。SQLite默认是DELETE模式，高并发下可能出现 "database is locked" 错误。

### 自动备份策略

```bash
# 添加到 crontab（每天凌晨3点备份，保留7天）
0 3 * * * cp /var/lib/smart-ops/history.db /backup/history-$(date +\%Y\%m\%d).db && find /backup -name "history-*.db" -mtime +7 -delete

# 异地备份（如果有多台机器）
0 4 * * * scp /backup/history-$(date +\%Y\%m\%d).db ops@备份机器:/backup/
```

### 备份验证

```bash
# 验证备份文件完整性
sqlite3 /backup/history-$(date +\%Y\%m\%d).db "PRAGMA integrity_check;"

# 验证备份可读（不实际恢复，只检查数据库完整性）
sqlite3 /backup/history-$(date +\%Y\%m\%d).db "SELECT COUNT(*) FROM health_records LIMIT 1;"
```

---

## 九、交叉编译ARM64二进制（可选章节）

> 仅当你需要在 x86_64 机器上构建 ARM64 二进制时才阅读此章节。

### 关键术语说明

| 术语 | 解释 |
|------|------|
| **交叉编译** | 在x86_64机器上编译出ARM64可执行文件 |
| **crossenv** | Python交叉编译工具 |

### 交叉编译步骤

```bash
# 1. 安装交叉编译环境
apt-get install -y python3-venv gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# 验证交叉编译器已安装
aarch64-linux-gnu-gcc --version

# 2. 安装crossenv
pip install crossenv

# 3. 创建ARM64虚拟环境
python3 -m venv build_env
source build_env/bin/activate

# 4. 安装依赖
pip install pyinstaller click psutil paramiko schedule

# 5. 创建ARM64 Python环境
# 注意：根据你的系统，路径可能不同
crossenv /usr/bin/python3-aarch64-linux-gnu python3-aarch64
source pyenv-aarch64/bin/activate

# 6. 安装ARM64依赖
pip install pyinstaller click psutil paramiko schedule

# 7. 编译
pyinstaller --onefile --name smart-ops-arm64 src/cli/main.py

# 8. 验证
ls -la dist/smart-ops-arm64
file dist/smart-ops-arm64
```

### 简化方案：如果有ARM64机器

```bash
# 直接在ARM64机器上编译
python3 -m venv build_env
source build_env/bin/activate
pip install pyinstaller click psutil paramiko schedule
pyinstaller --onefile --name smart-ops-arm64 src/cli/main.py
```

### 通俗解释：什么是交叉编译？

正常编译是在你自己的电脑上编译，编译出来的程序只能在你自己的电脑架构上运行。

**通俗理解**：
- 你在美国度假，想给国内的朋友带一份礼物
- 礼物需要在中国才能买到
- 交叉编译就像你在美国的中国超市买了礼物打包好，直接寄回中国
- 你不需要亲自去中国，但礼物是按中国人的需求准备的

**为什么需要crossenv？**：
- 普通Python包编译出来的只有当前机器的架构
- crossenv 创建一个"模拟ARM64环境"，让Python以为它在ARM64机器上
- 这样编译出来的包才能在ARM64上运行

---

## 十、故障排查

### 分类一：权限问题

```bash
# Q: 提示权限不足
chmod +x smart-ops-x86_64

# 如果需要访问/proc等系统资源，可能需要sudo
sudo smart-ops check

# 检查文件权限
ls -la /usr/local/bin/smart-ops
```

### 分类二：网络问题

```bash
# Q: SSH连接失败
# 1. 检查网络连通性
ping -c 3 192.168.1.100
nc -zv 192.168.1.100 22

# 2. 检查SSH连接（详细模式）
ssh -v root@目标机器 "uname -a"

# 3. 确认密钥权限正确
chmod 600 ~/.ssh/id_rsa
chmod 700 ~/.ssh

# 4. 确认远程主机已在known_hosts中
ssh-keyscan -H 192.168.1.100 >> ~/.ssh/known_hosts 2>/dev/null

# 5. 测试SSH连接超时（默认10秒）
ssh -o ConnectTimeout=10 root@192.168.1.100 "echo OK"

# 6. 验证agent是否正常
ssh-add -l
```

### 分类三：配置问题

```bash
# Q: 二进制运行报错 "cannot execute binary file"
# 检查架构是否匹配
file smart-ops-x86_64
uname -m

# Q: 服务无法启动（systemd）
systemctl status smart-ops
journalctl -u smart-ops -n 50
systemd-analyze verify /etc/systemd/system/smart-ops.service

# Q: Python版本不兼容
python3 --version  # 需要 >= 3.8
```

### 分类四：Docker问题

```bash
# Q: Docker运行失败
systemctl status docker
docker logs smart-ops
docker inspect smart-ops | grep -i oom

# 权限问题
docker run --rm --privileged --network host smart-ops check

# 验证镜像可运行
docker run --rm smart-ops --help | head -5
```

### 分类五：依赖问题

```bash
# Q: pip install 超时或失败
pip install --default-timeout=100 click psutil paramiko schedule

# Q: 权限错误（使用虚拟环境）
python3 -m venv venv && source venv/bin/activate && pip install ...
```

---

## 十一、验证安装

### 完整验证步骤

```bash
# 1. 检查 Python 版本
python3 --version | awk '{if ($2 < "3.8") exit 1}' && echo "Python版本OK"

# 2. 验证依赖安装
python3 -c "import click, psutil, paramiko, schedule; print('依赖验证成功')"

# 3. 运行健康检查
python3 -m src.cli.main check
echo "退出码: $?"

# 4. 测试可解释性输出
python3 -m src.cli.main check --explain

# 5. 检查历史功能
python3 -m src.cli.main history --hours 1

# 6. 测试远程连接（需要SSH密钥）
python3 -m src.cli.main monitor -H "root@localhost" -k ~/.ssh/id_rsa 2>/dev/null || echo "无远程目标，跳过"
```

### 预期输出示例

**成功时的输出：**
```
=== Smart Ops 健康检查 ===
[OK] CPU: 4核, 使用率 23%
[OK] 内存: 7.6G/16G (47%)
[OK] 磁盘: 根分区 45G/100G (45%)
[OK] 网络: eth0 正常
=== 检查完成 ===
```

**失败时的输出：**
```
[WARN] CPU: 使用率 91% (警告)
[ERROR] 磁盘空间不足: 95%
```

---

## 十二、性能基线与阈值

### 基线概念

性能基线是系统在正常状态下的各项指标参考值，用于判断异常。工具基于《性能之巅》方法论设计。

### 默认阈值参考

| 指标 | 警告阈值 | 严重阈值 | 依据 |
|------|---------|---------|------|
| CPU 使用率 | > 70% | > 90% | 《性能之巅》第2章 |
| 内存使用率 | > 80% | > 95% | 《性能之巅》第7章 |
| 磁盘使用率 | > 80% | > 90% | 《性能之巅》第9章 |
| 网络带宽利用率 | > 70% | > 90% | 《性能之巅》第10章 |
| 磁盘 I/O await | > 10ms | > 50ms | 《性能之巅》第9章 |
| TCP 重传率 | > 1% | > 5% | 《性能之巅》第10章 |

### 使用 baseline 命令

```bash
# 建立当前系统性能基线
python3 -m src.cli.main baseline

# 查看基线文件
cat /var/lib/smart-ops/baseline.json
```

### 阈值调优建议

- 生产环境：阈值应比测试环境更宽松
- 业务高峰期：建议临时提高阈值 10-20%
- 使用 `check --explain` 理解每条判断依据

---

## 十三、升级与回滚

### 升级流程

```bash
# 1. 备份当前版本
cp /usr/local/bin/smart-ops /usr/local/bin/smart-ops.bak

# 2. 部署新版本
cp dist/smart-ops-x86_64 /usr/local/bin/smart-ops

# 3. 重启服务
systemctl restart smart-ops

# 4. 验证
smart-ops check

# 5. 确认正常后清理备份
rm /usr/local/bin/smart-ops.bak
```

### 回滚流程

```bash
# 1. 停止服务
systemctl stop smart-ops

# 2. 恢复备份
cp /usr/local/bin/smart-ops.bak /usr/local/bin/smart-ops

# 3. 重启服务
systemctl start smart-ops

# 4. 验证
smart-ops check
```

---

## 十四、生产环境Checklist

### 部署前检查

- [ ] SSH密钥已配置，免密码登录验证通过
- [ ] 目标机器Python版本 >= 3.8（如使用源码模式）
- [ ] 运维用户已创建，权限已配置
- [ ] 防火墙端口已开放（如需远程访问）
- [ ] 系统架构确认（x86_64 或 ARM64）

### 安全配置

- [ ] SSH已禁用密码登录
```bash
# 验证命令
grep "^PasswordAuthentication" /etc/ssh/sshd_config
# 预期输出：PasswordAuthentication no
```
- [ ] SSH已禁用root直接登录
```bash
# 验证命令
grep "^PermitRootLogin" /etc/ssh/sshd_config
# 预期输出：PermitRootLogin no
```
- [ ] 二进制文件属主为运维用户，非root
- [ ] 文件权限 755，目录权限 755
- [ ] SSH密钥权限为600

### 运维配置

- [ ] systemd service已配置并测试通过
- [ ] 资源限制已配置（MemoryMax、CPUQuota）
- [ ] logrotate已配置（如果使用文件日志）
- [ ] 历史数据保留策略已配置
- [ ] 数据库定期VACUUM已配置
- [ ] 监控告警已接入（如需要）
- [ ] 定期备份策略已设置

### 监控集成（可选）

> **注意**：目前工具暂无内置的 `/metrics` HTTP端点。以下是当该功能开发完成后，建议的集成方式。

如果需要接入Prometheus/Grafana监控：

```bash
# 1. 配置健康检查HTTP端点（如果支持）
# 访问 http://localhost:8080/metrics 获取Prometheus格式指标

# 2. 或使用日志收集
# 配置journalctl输出收集到ELK/Grafana Loki
journalctl -u smart-ops -f | grep "metric" | nc logserver:514

# 3. 关键告警指标
# - smart-ops进程CPU使用率（应长期<5%）
# - /var/lib/smart-ops/ 目录磁盘空间
# - SQLite查询响应时间（应<1秒）
# - SSH连接成功率（应>99%）
```

### 验证通过

- [ ] `smart-ops check` 执行成功
- [ ] `smart-ops history --hours 24` 可查询
- [ ] systemd服务状态为active
- [ ] 日志输出正常（journalctl -u smart-ops）

---

## 十五、构建自己的二进制

```bash
# 清理旧构建
rm -rf dist/ build/ *.spec

# 创建虚拟环境
python3 -m venv build_env
source build_env/bin/activate

# 安装依赖
pip install pyinstaller click psutil paramiko schedule

# 编译
pyinstaller --onefile --name smart-ops-x86_64 src/cli/main.py

# 查看输出
ls -la dist/

# 校验（建议）
sha256sum dist/smart-ops-x86_64 > dist/smart-ops-x86_64.sha256
```

---

## 附录：术语表

| 术语 | 解释 |
|------|------|
| **SSH** | 安全外壳协议，用于远程连接服务器 |
| **systemd** | Linux系统服务管理器，让程序开机自启、受控运行 |
| **SSH密钥认证** | 用加密钥匙代替密码登录，更安全 |
| **ssh-agent** | SSH密钥管理器，帮您管理私钥 |
| **日志轮转** | 自动切分、压缩、清理日志文件，防止磁盘占满 |
| **交叉编译** | 在一种架构的机器上编译另一种架构的可执行文件 |
| **Docker** | 容器化平台，将应用及其依赖打包成容器运行 |
| **journald** | systemd的日志系统，日志存储在内存和磁盘 |
| **USE方法论** | Utilization（利用率）、Saturation（饱和度）、Errors（错误） |

---

## 恭喜完成部署！

你现在已掌握：
- ✅ 本机性能检查
- ✅ 远程多机巡检
- ✅ 历史数据查看
- ✅ 性能基线建立

**下一步建议：**
1. 用 `check --explain` 了解每个指标的判断依据
2. 配置SSH密钥实现免密登录
3. 设置定时巡检实现自动化监控
4. 阅读 ARCHITECTURE.md 深入理解工具设计