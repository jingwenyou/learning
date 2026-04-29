# 健康检查模块提示词

## 任务描述
请为 `smart-ops-cli` 项目实现 `src/core/health.py` 模块，实现健康检查与诊断建议功能。

## 功能要求

### 1. HealthChecker 类
```
属性:
- cpu_threshold: CPU 使用率阈值 (默认 80%)
- memory_threshold: 内存使用率阈值 (默认 85%)
- disk_threshold: 磁盘使用率阈值 (默认 90%)

方法:
- check(): 执行全面健康检查
- check_cpu(): 检查 CPU
- check_memory(): 检查内存
- check_disk(): 检查磁盘
- check_network(): 检查网络
- get_diagnostic_advice(status): 根据状态返回诊断建议
```

### 2. 阈值配置化
- 支持从配置文件加载阈值
- 支持环境变量覆盖
- 默认阈值可通过构造函数传入

### 3. 诊断建议
根据检查结果返回中文诊断建议：
- 正常: "系统运行正常"
- 告警: 具体问题描述 + 建议处理方式
- 危险: 紧急问题 + 立即处理建议

### 4. 输出格式
```json
{
  "status": "normal|warning|critical",
  "timestamp": "ISO8601",
  "checks": {
    "cpu": {"status": "...", "value": 45.2, "threshold": 80},
    "memory": {"status": "...", "value": 72.1, "threshold": 85},
    "disk": {"status": "...", "value": 65.0, "threshold": 90}
  },
  "advice": ["建议1", "建议2"]
}
```

## 异常处理
- 系统信息获取失败时返回 unknown 状态
- 配置文件不存在时使用默认阈值
- 所有异常需要捕获并记录日志

请生成完整的代码实现。
