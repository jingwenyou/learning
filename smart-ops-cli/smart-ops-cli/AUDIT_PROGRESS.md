# 《性能之巅》覆盖审计进度

## 状态: 3轮审计进行中 (2026-04-20)
- 开始时间: 2026-04-19 14:30 GMT+8
- 上次更新: 2026-04-20
- 已完成: v1审计(63%→73.3%) + 7项Bug修复 + 新增指标
- 当前: 3个scientist agent并行执行3轮深度审计

## Bug状态 (v2审计校正)
- BUG-1: run_queue_size 累加 nr_running ✅ 已修复
- BUG-2: ctx_switches/interrupts 改速率 ⚠️ 待v2审计核实
- BUG-3: CPU时间改 psutil 双采样 ✅ 已修复
- BUG-4: 低IOPS await 最小样本保护 ⚠️ 待v2审计核实
- BUG-5: 网络错误改速率检测 ✅ 已修复
- BUG-6: 带宽 fallback 改 /sys/class/net/speed ✅ 已修复
- BUG-7: listen_drops 诊断路径修正 ✅ 已修复

## 已新增指标
- pgscand/kswapd 页面扫描 (内存早期压力)
- HugePages (total/free/size)
- disk io_errors (/proc/diskstats col 15)
- TCP高级 (ListenDrops/RcvQDrop/ZeroWindow)
- 网络错误速率 (errin_per_sec 等)
- 磁盘错误诊断建议 + Listen队列溢出诊断建议

## 覆盖率历史
| 版本 | USE覆盖率 | 第1版 | 第2版BPF |
|------|---------|-------|---------|
| v1审计 | 63% | ~45% | ~25% |
| v2审计 | 73.3% | 56.7% | 33.3% |
| v3审计 | 进行中 | 进行中 | 进行中 |

## 3轮审计计划
- [ ] Round 1: 第1版核心章节逐章对照 (Ch2-Ch12)
  - 报告: .omc/scientist/reports/round1_vol1_chapter_audit.md
- [ ] Round 2: 第2版BPF/新增章节对照
  - 报告: .omc/scientist/reports/round2_vol2_bpf_audit.md
- [ ] Round 3: 方法论完整性 + 工具链覆盖
  - 报告: .omc/scientist/reports/round3_methodology_toolchain_audit.md

## 续跑机制
- systemd timer 已设置: smart-ops-audit-continue.timer (5小时后触发)
- 续跑脚本: /root/AI/smart-ops-cli/continue_audit.sh
- 日志: /root/AI/smart-ops-cli/continue_audit.log
- 手动恢复: 读此文件 → 检查上方报告文件是否存在 → 从未完成的Round继续
