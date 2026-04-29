# 端口扫描模块提示词

## 任务描述
请为 `smart-ops-cli` 项目实现 `src/core/port_scanner.py` 模块，实现端口探测功能。

## 功能要求

### 1. PortScanner 类

#### scan_port(host, port, timeout=3)
- 扫描单个端口
- 返回: `{"host": "...", "port": ..., "status": "open|closed|filtered", "service": "..."}`

#### scan_ports(host, ports, timeout=3)
- 扫描多个端口
- 支持端口列表和端口范围
- 并发扫描提升效率

#### get_common_ports()
- 返回常用端口列表 (如 22, 80, 443, 3306, 6379, 8080 等)

### 2. 常见服务识别
根据端口号识别服务类型：
- 22: SSH
- 80: HTTP
- 443: HTTPS
- 3306: MySQL
- 5432: PostgreSQL
- 6379: Redis
- 8080: HTTP-Alt

### 3. 输入验证
- host: 必须是有效的 IP 或域名
- port: 必须在 1-65535 范围内
- timeout: 必须是正数

### 4. 错误处理
- 无效 host: 抛出 ValueError
- 连接超时: status 设为 "filtered"
- 权限不足: status 设为 "filtered" (非 root 用户)

请生成完整的代码实现。
