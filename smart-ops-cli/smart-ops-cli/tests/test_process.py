"""
进程监控模块测试
"""
import pytest
from src.core import process_monitor


class TestProcessMonitor:
    """进程监控测试"""

    def test_get_top_processes_cpu(self):
        """测试获取TOP CPU进程"""
        processes = process_monitor.get_top_processes(n=10, sort_by="cpu")
        assert isinstance(processes, list)
        assert len(processes) <= 10

        for proc in processes:
            assert "pid" in proc
            assert "name" in proc
            assert "cpu_percent" in proc
            assert "memory_percent" in proc

    def test_get_top_processes_mem(self):
        """测试获取TOP 内存进程"""
        processes = process_monitor.get_top_processes(n=10, sort_by="mem")
        assert isinstance(processes, list)
        assert len(processes) <= 10

        # 验证按内存排序
        if len(processes) >= 2:
            for i in range(len(processes) - 1):
                assert processes[i]["memory_percent"] >= processes[i+1]["memory_percent"]

    def test_find_process_by_name(self):
        """测试按名称查找进程"""
        results = process_monitor.find_process_by_name("python")
        assert isinstance(results, list)

    def test_get_process_info(self):
        """测试获取单个进程信息"""
        import psutil
        current_proc = psutil.Process()
        info = process_monitor.get_process_info(current_proc)

        assert info is not None
        assert info["pid"] == current_proc.pid
        assert info["name"] == current_proc.name()

    @pytest.mark.slow
    def test_get_top_io_processes(self):
        """测试I/O TOP进程（iotop风格）《性能之巅》I/O分析
        注意：此测试需要1秒采样时间，标记为slow"""
        # 采样1秒获取I/O进程
        io_processes = process_monitor.get_top_io_processes(n=10, interval=1)
        assert isinstance(io_processes, list)
        assert len(io_processes) <= 10

        for proc in io_processes:
            assert "pid" in proc
            assert "name" in proc
            assert "read_kb_per_sec" in proc
            assert "write_kb_per_sec" in proc
            assert "total_kb_per_sec" in proc
            assert proc["total_kb_per_sec"] >= 0

        # 验证排序（应该按total_kb_per_sec降序）
        if len(io_processes) >= 2:
            for i in range(len(io_processes) - 1):
                assert io_processes[i]["total_kb_per_sec"] >= io_processes[i+1]["total_kb_per_sec"]
