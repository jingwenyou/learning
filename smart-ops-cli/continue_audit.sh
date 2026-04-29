#!/bin/bash
# 《性能之巅》审计续跑脚本 — 由 systemd-run 调度
# 创建时间: 2026-04-20

cd /root/AI/smart-ops-cli

PROMPT='继续执行《性能之巅》审计。

读取 /root/AI/smart-ops-cli/smart-ops-cli/AUDIT_PROGRESS.md 确认哪些Round未完成。

对于每个未完成的Round，读取对应的报告文件（如已存在则跳过，否则执行审计）：
- Round 1报告: .omc/scientist/reports/round1_vol1_chapter_audit.md
- Round 2报告: .omc/scientist/reports/round2_vol2_bpf_audit.md
- Round 3报告: .omc/scientist/reports/round3_methodology_toolchain_audit.md

如果报告已存在，直接读取并将该Round标记为完成。
如果报告不存在，执行对应的审计并写入报告。

所有Round完成后：
1. 更新 /root/AI/smart-ops-cli/smart-ops-cli/AUDIT_PROGRESS.md，将完成的Round标记为[x]
2. 在 AUDIT_PROGRESS.md 末尾追加综合结论（总体覆盖率、TOP5改进建议）'

claude -p "$PROMPT" --output-format text >> /root/AI/smart-ops-cli/continue_audit.log 2>&1
echo "[$(date)] 续跑完成，退出码: $?" >> /root/AI/smart-ops-cli/continue_audit.log
