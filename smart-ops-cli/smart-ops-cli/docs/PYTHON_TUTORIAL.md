# Python 高级用法教程

> 本教程结合 Smart Ops CLI 源码，讲解 Python 高级用法。

---

## 目录

1. [dataclass - 数据类](#1-dataclass---数据类)
2. [类型提示 (Type Hints)](#2-类型提示-type-hints)
3. [装饰器 (Decorator)](#3-装饰器-decorator)
4. [上下文管理器 (Context Manager)](#4-上下文管理器-context-manager)
5. [生成器 (Generator)](#5-生成器-generator)
6. [并发编程 (ThreadPoolExecutor)](#6-并发编程-threadpoolexecutor)
7. [字典的高级用法](#7-字典的高级用法)
8. [异常处理最佳实践](#8-异常处理最佳实践)
9. [Lambda 和函数式编程](#9-lambda-和函数式编程)
10. [魔术方法 (Magic Methods)](#10-魔术方法-magic-methods)

---

## 1. dataclass - 数据类

### 1.1 什么是 dataclass？

dataclass 是 Python 3.7+ 引入的特性，自动生成 `__init__`, `__repr__`, `__eq__` 等方法。

### 1.2 对比：传统类 vs dataclass

```python
# ========== 传统方式 ==========
class HealthCheckResult:
    def __init__(self, name: str, status: str, value: str):
        self.name = name
        self.status = status
        self.value = value

    def __repr__(self):
        return f"HealthCheckResult(name={self.name}, status={self.status})"

    def __eq__(self, other):
        if not isinstance(other, HealthCheckResult):
            return False
        return self.name == other.name and self.status == other.status

result = HealthCheckResult("CPU", "正常", "50%")
print(result)
# HealthCheckResult(name=CPU, status=正常)
```

```python
# ========== dataclass 方式 ==========
from dataclasses import dataclass

@dataclass
class HealthCheckResult:
    name: str
    status: str
    value: str
    # 自动生成 __init__, __repr__, __eq__

result = HealthCheckResult("CPU", "正常", "50%")
print(result)
# HealthCheckResult(name='CPU', status='正常', value='50%')
```

### 1.3 实际项目中的应用

**源码位置：** `src/core/types.py`

```python
@dataclass
class CPUInfo:
    """CPU信息（《性能之巅》CPU时间分解）"""

    # 基础字段
    physical_cores: int
    logical_cores: int
    frequency_mhz: Optional[float]  # Optional[float] = float | None

    # 利用率分解（时间占比）
    user_percent: float      # 用户态时间占比
    nice_percent: float      # 优先级调整时间
    system_percent: float    # 内核态时间
    iowait_percent: float     # I/O等待时间 ← 重点！
    irq_percent: float       # 硬中断
    softirq_percent: float   # 软中断
    steal_percent: float      # 虚拟化：被宿主机抢走的时间

    # 饱和度指标
    @property
    def saturation(self) -> float:
        """饱和度（归一化负载）"""
        return self.normalized_load_1min
```

### 1.4 dataclass 进阶用法

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class HealthReport:
    """完整健康报告"""

    timestamp: str
    hostname: str

    # 嵌套 dataclass
    cpu: 'CPUInfo'
    memory: 'MemoryInfo'

    # 带默认值的字段
    status: str = "正常"

    # 列表类型用 field(default_factory)
    warnings: List[str] = field(default_factory=list)

    # 可选字段
    details: Optional[Dict] = None
```

### 1.5 为什么用 dataclass 而不是 namedtuple？

```python
# namedtuple - 不可变
from collections import namedtuple
Point = namedtuple('Point', ['x', 'y'])
p = Point(1, 2)
p.x = 3  # ❌ 错误！namedtuple不可变

# dataclass - 可变
@dataclass
class Point:
    x: int
    y: int

p = Point(1, 2)
p.x = 3  # ✅ 可以修改
```

---

## 2. 类型提示 (Type Hints)

### 2.1 基本类型提示

```python
# 变量类型提示
name: str = "CPU"
count: int = 42
ratio: float = 0.85
is_valid: bool = True

# 函数参数和返回值
def get_cpu_usage() -> float:
    return 50.0
```

### 2.2 复杂类型

```python
from typing import List, Dict, Set, Tuple, Optional

# 列表
cpu_list: List[float] = [10.0, 20.0, 30.0]

# 字典
metrics: Dict[str, float] = {"cpu": 50.0, "memory": 60.0}

# 元组（固定长度）
point: Tuple[int, int, int] = (1, 2, 3)  # 3个int

# 可选类型（可以是None）
value: Optional[str] = None
value: str | None = None  # Python 3.10+ 语法

# 联合类型
status: str | int = "正常"  # 可以是str或int
```

### 2.3 实际项目中的应用

**源码位置：** `src/core/health.py`

```python
def load_thresholds(thresholds_path: str = None) -> Dict[str, Any]:
    """
    加载阈值配置

    参数:
        thresholds_path: 阈值配置文件路径

    返回:
        Dict 包含各类阈值配置

    抛出:
        ThresholdFileError: 文件不存在或读取失败时
    """
    ...
```

### 2.4 类型提示的作用

```python
# 1. IDE代码补全
# 当IDE知道metrics是Dict[str, float]时
# 输入 metrics[' 自动提示 'cpu', 'memory'等

# 2. 文档作用
def check_cpu(thresholds, fast: bool = False) -> Dict[str, Any]:
    # 看到签名就知道返回什么

# 3. mypy类型检查
# pip install mypy
# mypy src/core/health.py
```

---

## 3. 装饰器 (Decorator)

### 3.1 装饰器是什么？

装饰器是一个**接收函数作为参数、返回新函数**的函数。

```python
# 简单装饰器
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before calling function")
        result = func(*args, **kwargs)
        print("After calling function")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

# 等价于
say_hello = my_decorator(say_hello)

say_hello()
# Output:
# Before calling function
# Hello!
# After calling function
```

### 3.2 带参数的装饰器

```python
def repeat(times: int):
    """重复执行函数指定次数"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
# ['Hello, World!', 'Hello, World!', 'Hello, World!']
```

### 3.3 实际项目中的应用 - Click 装饰器

**源码位置：** `src/cli/commands.py`

```python
# Click 装饰器链
@click.command(name="check")           # ① 定义这是一个命令
@click.option("--explain", is_flag=True)  # ② 添加 --explain 选项
@click.option("--thresholds", default=None)  # ③ 添加更多选项
def check_cmd(thresholds, explain):
    """执行健康检查"""
    ...

# 等价于（装饰器从下往上执行）：
# check_cmd = option(...)(option(...)(command(...)(check_cmd)))
```

### 3.4 functools.wraps 保留原函数信息

```python
def simple_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@simple_decorator
def hello():
    """这是hello函数的文档"""
    pass

print(hello.__name__)  # wrapper ❌ 没有保留原名
print(hello.__doc__)    # None    ❌ 没有保留文档

# ========== 使用 wraps ==========
from functools import wraps

def better_decorator(func):
    @wraps(func)  # 保留原函数的元信息
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@better_decorator
def hello():
    """这是hello函数的文档"""
    pass

print(hello.__name__)  # hello ✅
print(hello.__doc__)   # 这是hello函数的文档 ✅
```

---

## 4. 上下文管理器 (Context Manager)

### 4.1 为什么需要上下文管理器？

```python
# 传统方式：容易忘记关闭
file = open("data.txt", "r")
content = file.read()
file.close()  # 如果中间出异常，永远不会执行

# 更好的方式：try-finally
file = open("data.txt", "r")
try:
    content = file.read()
finally:
    file.close()  # 总是执行

# 上下文管理器方式：简洁安全
with open("data.txt", "r") as file:
    content = file.read()
# 自动调用 file.close()
```

### 4.2 自定义上下文管理器

```python
# 方式1：使用类
class Timer:
    def __enter__(self):
        self.start = time.time()
        return self  # as 子句中返回的值

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        print(f"耗时: {elapsed:.2f}秒")
        return False  # 不屏蔽异常

with Timer() as timer:
    time.sleep(1)
# 输出: 耗时: 1.00秒
```

```python
# 方式2：使用生成器 + contextmanager
from contextlib import contextmanager

@contextmanager
def timer():
    start = time.time()
    try:
        yield  # 这里暂停，执行with块内的代码
    finally:
        elapsed = time.time() - start
        print(f"耗时: {elapsed:.2f}秒")

with timer():
    time.sleep(1)
# 输出: 耗时: 1.00秒
```

### 4.3 实际项目中的应用

**源码位置：** `src/core/history.py`

```python
def _get_conn():
    """获取数据库连接的上下文管理器"""
    # 确保目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 建立连接
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 方便用列名访问
    try:
        yield conn  # 返回连接给with块使用
    finally:
        conn.close()  # with块结束后自动关闭

# 使用方式
with _get_conn() as conn:
    rows = conn.execute("SELECT * FROM metrics").fetchall()
    for row in rows:
        print(row["cpu_percent"])  # 用列名访问
# 连接自动关闭
```

---

## 5. 生成器 (Generator)

### 5.1 生成器是什么？

生成器是一种**惰性计算**的迭代器，不是一次性生成所有值。

```python
# 普通函数：返回列表
def get_numbers(n):
    result = []
    for i in range(n):
        result.append(i)
    return result

# 生成器：惰性计算
def get_numbers_gen(n):
    for i in range(n):
        yield i  # yield 暂停函数执行，返回值

numbers = get_numbers(1000000)  # 普通函数立即创建100万个元素
gen = get_numbers_gen(1000000)  # 生成器延迟，不立即计算
```

### 5.2 生成器的优势

```python
import sys

# 对比内存占用
large_list = list(range(1000000))
print(sys.getsizeof(large_list))  # ~8MB

large_gen = (x for x in range(1000000))
print(sys.getsizeof(large_gen))   # ~200 bytes！节省40倍！

# 使用生成器
for x in large_gen:
    print(x)
    if x > 10:
        break  # 可以随时停止，不浪费资源
```

### 5.3 实际项目中的应用

**源码位置：** `src/core/system.py`

```python
def get_per_disk_io_rate(self, interval: float = 1.0, fast: bool = False):
    """
    采集磁盘I/O数据，使用生成器模式
    """
    # 第一次采样（立即获取）
    reads1, writes1 = self._get_disk_io_counts()

    # 等待间隔
    if not fast and interval > 0:
        time.sleep(interval)

    # 第二次采样
    reads2, writes2 = self._get_disk_io_counts()

    # 生成器模式：懒加载
    for dev in set(reads1.keys()) | set(reads2.keys()):
        yield {
            "device": dev,
            "reads_per_sec": (reads2.get(dev, 0) - reads1.get(dev, 0)) / interval,
            "writes_per_sec": (writes2.get(dev, 0) - writes1.get(dev, 0)) / interval,
        }
```

---

## 6. 并发编程 (ThreadPoolExecutor)

### 6.1 什么时候用多线程？

- **I/O密集型任务**：网络请求、文件读写、SSH连接
- **不是 CPU 密集型**：Python有GIL，多线程不能加速CPU计算
- **GIL释放原理**：GIL只在CPU计算时生效，I/O等待时会自动释放，所以SSH并发用线程池是正确的选择

**重要：paramiko 线程安全**
paramiko 不是线程安全的，每个线程必须创建独立连接。这在 monitor.py 中通过 `check_remote_host` 函数实现（每个任务创建自己的 SSHClient）。

```python
# ✅ 正确：每个线程独立连接
def check_remote_host(host):
    client = paramiko.SSHClient()  # 每个任务创建新连接
    client.connect(host)
    result = client.exec_command("...")
    client.close()
    return result

# ❌ 错误：共享连接
shared_client = paramiko.SSHClient()  # 不能在线程间共享！
```

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 模拟I/O任务（SSH连接）
def fetch_from_server(server):
    time.sleep(1)  # 模拟网络延迟
    return f"Result from {server}"

servers = ["server1", "server2", "server3", "server4"]

# 单线程：4秒
start = time.time()
for s in servers:
    fetch_from_server(s)
print(f"单线程: {time.time() - start:.2f}s")  # ~4秒

# 多线程：1秒
start = time.time()
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(fetch_from_server, s) for s in servers]
    for future in as_completed(futures):
        print(future.result())
print(f"多线程: {time.time() - start:.2f}s")  # ~1秒
```

### 6.2 实际项目中的应用

**源码位置：** `src/core/monitor.py`

```python
def inspect_hosts(hosts: List[str], ...):
    """批量巡检多台主机"""
    results = []

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=min(max_workers, total)) as executor:
        # 提交所有任务
        futures = {}
        for host in hosts:
            future = executor.submit(
                check_remote_host,
                host, port, username, password, key_path, ssh_timeout
            )
            futures[future] = host  # 记录哪个future对应哪个host

        # 收集结果（as_completed：谁先完成谁先处理）
        for future in as_completed(futures):
            host = futures[future]
            try:
                report = future.result()  # 获取结果
                results.append(report)
            except Exception as e:
                # 处理异常
                results.append(HostReport(host=host, success=False, error=str(e)))

    return results
```

### 6.3 max_workers 设置原则

```python
# 不要太大：太多并发会打爆目标服务器
max_workers = min(4, len(hosts))  # 最多4个并发

# 也不要太小：失去了并发的意义
max_workers = 1  # 退化成串行了
```

---

## 7. 字典的高级用法

### 7.1 安全获取嵌套值

```python
# 传统方式：繁琐
data = {"cpu": {"usage": 50}}
if "cpu" in data and "usage" in data["cpu"]:
    value = data["cpu"]["usage"]
else:
    value = 0

# get方法链（安全获取嵌套字典值）
# 注意：默认值要用 {} 而不是 None，否则无法链式调用
value = data.get("cpu", {}).get("usage", 0)

# 更安全的方式
def safe_get(obj, *keys, default=None):
    """安全获取嵌套字典的值"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, default)
        else:
            return default
    return obj

value = safe_get(data, "cpu", "usage", 0)
```

### 7.2 defaultdict 避免KeyError

```python
from collections import defaultdict

# 普通字典：访问不存在的key会报错
counts = {}
counts["cpu"] += 1  # ❌ KeyError

# defaultdict：访问不存在的key自动创建
counts = defaultdict(int)  # 默认值是0
counts["cpu"] += 1  # ✅ 自动创建，初始值为0
print(counts["cpu"])  # 1

# 实际应用：聚合数据
device_stats = defaultdict(list)
for disk in ["sda", "sdb", "sda", "sdc", "sdb"]:
    device_stats[disk].append(1)

print(dict(device_stats))
# {'sda': [1, 1], 'sdb': [1, 1], 'sdc': [1]}
```

### 7.3 字典推导式

```python
# 基本用法
squares = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# 过滤
data = {"cpu": 50, "memory": 80, "disk": 90}
high_usage = {k: v for k, v in data.items() if v > 70}
# {"memory": 80, "disk": 90}

# 实际应用：格式化输出
results = {
    "CPU": {"status": "正常", "value": "50%"},
    "内存": {"status": "告警", "value": "85%"},
}

# 提取状态
status_map = {name: info["status"] for name, info in results.items()}
# {"CPU": "正常", "内存": "告警"}
```

---

## 8. 异常处理最佳实践

### 8.1 异常处理原则

```python
# ❌ 过于宽泛：捕获一切
try:
    do_something()
except Exception:
    pass

# ✅ 精确捕获
try:
    age = int(user_input)
except ValueError:
    print("请输入有效数字")

# ✅ 捕获多个特定异常
try:
    file.open()
except (FileNotFoundError, PermissionError) as e:
    print(f"无法访问文件: {e}")

# ✅ 记录异常并重新抛出
try:
    do_something()
except SpecificError as e:
    logger.error(f"发生错误: {e}")
    raise  # 重新抛出，让调用者知道
```

### 8.2 自定义异常

```python
# 定义自定义异常
class ThresholdFileError(Exception):
    """阈值文件不存在或读取失败"""
    pass

class ValidationError(Exception):
    """参数验证失败"""
    pass

# 使用自定义异常
def load_thresholds(path):
    if not os.path.exists(path):
        raise ThresholdFileError(f"阈值文件不存在: {path}")

# 捕获并处理
try:
    config = load_thresholds("config.yaml")
except ThresholdFileError as e:
    print(f"配置错误: {e}")
    sys.exit(1)
```

### 8.3 实际项目中的应用

**源码位置：** `src/core/health.py`

```python
class ThresholdFileError(Exception):
    """阈值文件不存在或读取失败"""
    pass

def load_thresholds(thresholds_path=None):
    if thresholds_path:
        if not os.path.exists(thresholds_path):
            # 精确的异常类型 + 清晰的错误信息
            raise ThresholdFileError(f"阈值文件不存在: {thresholds_path}")
        elif os.path.isfile(thresholds_path):
            try:
                with open(thresholds_path, "r") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                # 具体说明什么错了
                raise ThresholdFileError(f"阈值文件读取失败: {e}")
    return DEFAULT_THRESHOLDS
```

---

## 9. Lambda 和函数式编程

### 9.1 Lambda 表达式

```python
# 基本语法
square = lambda x: x ** 2
print(square(5))  # 25

# 多参数
add = lambda x, y: x + y
print(add(3, 4))  # 7

# 实际应用：排序
students = [{"name": "Alice", "age": 20}, {"name": "Bob", "age": 19}]
students.sort(key=lambda s: s["age"])  # 按年龄排序
```

### 9.2 map, filter, reduce

```python
# map：对每个元素做操作
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, numbers))
# [1, 4, 9, 16, 25]

# filter：过滤元素
evens = list(filter(lambda x: x % 2 == 0, numbers))
# [2, 4]

# reduce：聚合计算
from functools import reduce
total = reduce(lambda x, y: x + y, numbers)
# 15

# 组合使用
result = reduce(
    lambda x, y: x + y,
    map(lambda x: x**2, filter(lambda x: x % 2 == 0, numbers))
)
# 4 + 16 = 20
```

### 9.3 列表推导式替代 map/filter

```python
# map → 列表推导式
squared = [x**2 for x in numbers]

# filter → 列表推导式（带条件）
evens = [x for x in numbers if x % 2 == 0]

# 一般来说，列表推导式更易读
```

---

## 10. 魔术方法 (Magic Methods)

### 10.1 什么是魔术方法？

以双下划线 `__` 开头和结尾的方法，由Python解释器在特定情况下自动调用。

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):        # str() 或 print() 时调用
        return f"{self.name}, {self.age}岁"

    def __repr__(self):       # 调试时显示
        return f"Person(name='{self.name}', age={self.age})"

    def __eq__(self, other):  # == 比较时调用
        return self.name == other.name and self.age == other.age

p = Person("张三", 25)
print(p)              # __str__  → 张三, 25岁
repr(p)              # __repr__ → Person(name='张三', age=25)
```

### 10.2 dataclass 自动生成的魔术方法

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

p1 = Point(1, 2)
p2 = Point(1, 2)

print(p1)           # __str__  → Point(x=1, y=2)
print(p1 == p2)     # __eq__   → True（自动比较内容）
print(hash(p1))     # __hash__ → 可哈希（可用于dict的key）
```

### 10.3 实际项目中的应用

**源码位置：** `src/core/types.py`

```python
@dataclass
class CPUInfo:
    """CPU信息 - dataclass 自动生成所有魔术方法"""

    physical_cores: int
    logical_cores: int

    # 自定义属性
    @property
    def utilization(self) -> float:
        """利用率（兼容USE方法论）"""
        return self.usage_percent

    @property
    def saturation(self) -> float:
        """饱和度（归一化负载）"""
        return self.normalized_load_1min

# dataclass 自动生成：
# __init__(self, physical_cores, logical_cores, ...)
# __repr__(self) → Point(physical_cores=4, logical_cores=8, ...)
# __eq__(self, other) → 比较所有字段
# __hash__(self) → 基于所有字段生成hash
```

### 🏋️ 实践练习

学完本教程后，用这些练习巩固知识：

**练习1：dataclass（初级）**
```python
# 在 src/core/types.py 中添加一个新数据类 NetworkInfo
# 包含字段：bytes_sent, bytes_recv, errors, bandwidth_mbps
# 然后在 system.py 的 get_network_info() 中使用它
```

**练习2：类型提示（初级）**
```python
# 为 health.py 中的 check_cpu() 函数添加完整的类型提示
# 验证：你写的类型提示可以被 mypy 检查
```

**练习3：装饰器（中级）**
```python
# 在 src/utils/ 目录下创建一个计时装饰器 @timer
# 测量函数执行时间，用于性能分析
```

**练习4：并发（中级）**
```python
# 修改 src/core/monitor.py，支持通过参数控制 max_workers
# 验证：增加并发数能加快多主机巡检速度
```

**练习5：实际任务（高级）**
```python
# 为 Smart Ops CLI 添加一个新命令 top，
# 显示CPU/内存使用最高的5个进程
# 提示：参考 src/core/process_monitor.py
```

**验证方法**：完成练习后：
1. 运行 `python3 -m pytest tests/` 确保测试通过
2. 运行你的新命令验证功能正确
3. 对比输出与 `tool ps --sort=cpu --num=5` 的结果

---

## 附录：常用标准库速查

| 模块 | 用途 | 本项目中的应用 |
|------|------|--------------|
| `dataclasses` | 数据类 | types.py |
| `typing` | 类型提示 | 全局 |
| `pathlib` | 路径操作 | history.py |
| `contextlib` | 上下文管理器 | - |
| `concurrent.futures` | 并发 | monitor.py |
| `sqlite3` | SQLite | history.py |
| `threading` | 多线程 | - |
| `subprocess` | 执行外部命令 | benchmark.py |
| `functools` | 函数式工具 | 装饰器 |
| `collections` | 集合类型 | defaultdict |

---

*教程版本: 1.0*
*更新日期: 2026-04-22*
