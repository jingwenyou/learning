# Python 学习计划

> 目标：建立完整的 Python Web 测试平台知识体系，见树木也见森林

---

## 学习路线总览

```
阶段1 ── 过渡周 ── 阶段2 ── 阶段3 ── 阶段4 ── 阶段5 ── 阶段6
  │        │        │        │        │        │        │
  ▼        ▼        ▼        ▼        ▼        ▼        ▼
Python   HTTP     FastAPI  SQLAlchemy 前端极简  pytest深度  完整
高级语法  +请求基础 +pytest   +DB     +JWT    +读开源框架  项目
                   基础
```

| 阶段 | 周期 | 核心输出 |
|------|------|----------|
| 阶段1 | 3-4周 | 能自己写装饰器、上下文管理器，理解类型注解 |
| 过渡周 | 1周 | 能用 requests 调 API，理解 HTTP 请求/响应 |
| 阶段2 | 4-5周 | 能写 REST API（CRUD）+ 用 pytest 测试它 |
| 阶段3 | 2-3周 | 能设计数据模型 |
| 阶段4A | 1周 | 能看懂 HTML/CSS/JS，能用原生 JS 发请求和展示数据 |
| 阶段4B | 1周 | 能实现 JWT 认证 |
| 阶段5 | 4-5周 | pytest 深度 + 读开源框架 + mock + 测试策略 + Web 集成 |
| 阶段6 | 4-6周 | 模仿开源项目，搭建自己的测试管理平台 |

**预计总时长：5-7 个月**

> 说明：按每天1小时、周末2小时算，实际有效学习时间约为预估的 60-70%（生活、加班、状态波动）。
> 每个阶段结束留1周弹性缓冲，用来补没搞懂的或休息，不算在上面的周期里。

### 贯穿线：框架架构 + 设计模式

> 不单独学设计模式，而是在每个阶段读源码时，点出"这里用了什么模式、为什么这么设计"。
> 目标：读别人框架时能看出套路，自己写代码时知道怎么组织。

```
┌─────────────────────────────────────────────────────────┐
│          设计模式 & 架构 在各阶段的出现位置                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  阶段1: 装饰器模式（Decorator Pattern）                   │
│         → Flask @app.route、pytest @fixture              │
│         工厂模式（Factory Pattern）                       │
│         → pytest.fixture 就是一个"测试数据工厂"          │
│                                                         │
│  阶段2: 依赖注入（Dependency Injection）                  │
│         → FastAPI Depends() 是 DI 的教科书级实现         │
│         分层架构（Layered Architecture）                  │
│         → 路由层 → 业务层 → 数据层                       │
│                                                         │
│  阶段3: 仓储模式（Repository Pattern）                    │
│         → 数据访问层的抽象                                │
│         工作单元（Unit of Work）                          │
│         → SQLAlchemy Session 就是 UoW                    │
│                                                         │
│  阶段5: 插件/钩子架构（Plugin/Hook Architecture）         │
│         → pytest 的 hook 系统（最重要！）                 │
│         观察者模式（Observer Pattern）                     │
│         → pytest hook = 事件发布/订阅                    │
│         模板方法（Template Method）                       │
│         → 测试生命周期：setup → test → teardown          │
│                                                         │
│  阶段6: 项目架构设计                                      │
│         → 分层架构实战 + 模块划分 + API 设计原则           │
│                                                         │
│  学习方式：不背书，遇到就标注                              │
│    ✅ "这段源码用了 XX 模式" → 记到知识地图               │
│    ✅ "这个框架的扩展点在哪" → 理解插件架构               │
│    ❌ 不需要背 23 种 GoF 模式                            │
└─────────────────────────────────────────────────────────┘
```

---

## 每日节奏

```
周一~周五（不指定时段，自己安排）：
  Session 1（30min）  看教程
  Session 2（30min）  敲代码
  Session 3（10min）  记1-3句话

周末：
  1-2h   做练手项目（解决自己工作中的重复劳动）

里程碑产出：
  里程碑0 → 用 requests 调通 GitHub API（过渡周结束）
  里程碑1 → 自己的博客 API + 测试（阶段2结束）
  里程碑2 → 给博客加数据库（阶段3结束）
  里程碑3 → 给博客加极简前端 + JWT 登录（阶段4结束）
  里程碑4 → clone pytest-html 并改一个功能 + pytest 集成进 Web 平台（阶段5结束）

### 周复盘模板（每周五晚上填，3分钟搞定）

```
周复盘：第 ___ 周
  1. 这周学了什么？（3句话）
  2. 哪里卡住了？（下周重点解决）
  3. 下周必须完成的 1 件事？

坚持不下来时的对策：
  - 学不动就把今天的任务砍一半，完成一半也是进步
  - 看教程看不进去就直接敲代码，反过来也行
  - 连续3天没学不要有负罪感，第4天接上就行
  - 找个学习伙伴互相监督（可选）
```

### 学习终极验证：能说清楚就算懂了

```
每个阶段结束，除了做产出，还有一个最终验证：

✅ 能说清楚 → 真正理解
❌ 说不清楚 → 还没懂，继续学

怎么验证（任选一种）：
  首选：写一段文字解释这个知识点（发到笔记或博客）
  备选：在代码里用注释解释每一行在干什么
  高阶：录屏讲解，或找人讲 10 分钟

原因：教是最好的学。能说清楚 = 真正理解。
```

---

## 阶段1：Python 高级语法（3-4周）

### 学习目标
- 理解闭包原理，知道装饰器为什么能工作
- 理解装饰器原理，能写带参数的装饰器
- 理解 `*args, **kwargs` 的拆包/打包
- 理解上下文管理器，能自己实现 `__enter__` / `__exit__`
- 理解生成器和迭代器，能读懂别人的 `yield` 代码，知道"生成器→协程→async"的关系
- 了解 abc 抽象基类（选学，遇到再深入）
- 掌握基础类型注解，为 FastAPI 做准备

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| 闭包 | Real Python: Python Closures | https://realpython.com/python-closures/ | **必读** |
| 装饰器 | Real Python: Primer on Python Decorators | https://realpython.com/primer-on-python-decorators/ | **必读** |
| 上下文管理器 | Real Python: Python Context Managers | https://realpython.com/python-with-statement/ | **必读** |
| 生成器与迭代器 | Real Python: Introduction to Python Generators | https://realpython.com/introduction-to-python-generators/ | **必读** |
| 迭代器深入 | Real Python: Python Iterators and Iterables | https://realpython.com/python-iterators-iterables/ | 选读 |
| 类型注解 | Real Python: Python Type Checking | https://realpython.com/python-type-checking/ | **必读**（只看基础部分） |

> 📖 《Fluent Python》推迟到阶段3之后再读。这本书是给有1-2年 Python 经验的人写的，
> 阶段1用 Real Python 教程足够。等你完成阶段3、有了实际编码经验后，再回头读会事半功倍。

### 书籍说明

```
《Fluent Python》：推迟到阶段3之后再读（见上方说明）。

《Python Cookbook》精读指引（阶段1可选读）：
  Chapter 1 (数据结构和算法) → 选读，有时间可以翻翻
  其他章节遇到再查，不需要提前读
```

### 源码阅读路径

```
阶段1 源码阅读（按顺序）：

Step 1: flask/app.py（找 @app.route 装饰器）
  → 目标：理解装饰器怎么实现路由注册
  → 位置：找 def route 方法，返回一个装饰器函数
  → 读多少：50-80行
  → 🏗️ 设计模式：装饰器模式（Decorator Pattern）
     问自己：route() 做了什么？→ 它没有改原函数，而是"注册"了函数
     这就是装饰器模式的核心：不改原函数，给它附加行为

Step 2: src/_pytest/fixtures.py（找 @pytest.fixture 装饰器）
  → 目标：理解 pytest fixture 的装饰器实现
  → 位置：找 fixture() 函数，理解它返回什么
  → 读多少：100-150行
  → 🏗️ 设计模式：工厂模式（Factory Pattern）
     问自己：fixture 返回的是什么？→ 它是一个"测试数据工厂"
     每次测试调用 fixture，它就"生产"一份新的测试数据
     工厂模式 = 用函数/类来生产对象，调用者不关心怎么生产的

Step 3: contextlib.py（找 @contextmanager）
  → 目标：理解上下文管理器怎么用生成器实现
  → 位置：找 contextmanager 函数
  → 读多少：50行
  → 🏗️ 设计模式：模板方法（Template Method）
     问自己：with 语句的结构是什么？→ enter → 你的代码 → exit
     这个"固定流程，中间留空给你填"就是模板方法

每步产出：
  - 在知识地图里记录：这个源码的入口在哪里
  - 画出调用链（手画拍照也行）
  - 标注：这里用了什么设计模式？为什么用？
```

### 知识地图

```
┌─────────────────────────────────────────────────────────┐
│                     知识地图：闭包                        │
├─────────────────────────────────────────────────────────┤
│ 位置：函数内部定义函数，内层函数引用外层变量              │
│                                                         │
│ 上游：函数是一等对象（可以赋值、传递、返回）            │
│  ↓                                                     │
│ 下游：装饰器（闭包的典型应用）                          │
│                                                         │
│ 核心三要素：                                            │
│   1. 外层函数返回内层函数                                │
│   2. 内层函数引用外层函数的变量                          │
│   3. 外层函数执行结束后，变量仍然被内层函数"记住"        │
│                                                         │
│ 为什么重要：                                            │
│   装饰器 = 闭包 + 函数作为参数                          │
│   不理解闭包，装饰器就只能"背模板"                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     知识地图：装饰器                       │
├─────────────────────────────────────────────────────────┤
│ 位置：函数外面加一层逻辑                                  │
│                                                         │
│ 上游：闭包（函数返回函数）                               │
│  ↓  被 @装饰器 包装                                      │
│ 下游：带新功能的函数                                      │
│                                                         │
│ Web 框架应用：                                            │
│   Flask:  @app.route('/')  →  路由注册                   │
│   pytest:  @pytest.fixture  →  测试夹具                   │
│   FastAPI: @app.middleware() →  中间件                   │
│                                                         │
│ 源码对照：                                                │
│   Flask 源码: flask/app.py 找 @app.route 定义            │
│   pytest 源码: src/_pytest/fixtures.py 找 fixture 装饰器 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   知识地图：上下文管理器                    │
├─────────────────────────────────────────────────────────┤
│ 位置：资源获取和释放的配对                                │
│                                                         │
│ 上游：打开资源（文件/数据库/网络）                         │
│  ↓  with 语句自动调用 __enter__                         │
│ 下游：自动调用 __exit__ 释放资源                         │
│                                                         │
│ Web 框架应用：                                            │
│   数据库连接: with db.session: → 自动提交/回滚            │
│   文件操作:  with open(): → 自动关闭                     │
│   pytest:   with pytest.raises(): → 断言异常             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   知识地图：生成器                         │
├─────────────────────────────────────────────────────────┤
│ 位置：惰性计算，按需生成数据                              │
│                                                         │
│ 上游：普通函数（一次返回所有结果）                        │
│  ↓  yield 替代 return                                   │
│ 下游：按需产出值，节省内存                                │
│                                                         │
│ 演化路径（知道就行，不用深入）：                          │
│   生成器 yield                                          │
│     ↓ 加上 send() → 协程                               │
│     ↓ 语法糖 → async/await                             │
│     ↓ FastAPI 就是基于 async 的框架                     │
│                                                         │
│ Web 框架应用：                                            │
│   FastAPI: async def + yield → 异步依赖注入              │
│   pytest:  yield fixture → setup/teardown               │
│   contextlib: @contextmanager 用 yield 实现 with        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   知识地图：类型注解                       │
├─────────────────────────────────────────────────────────┤
│ 位置：给变量和函数标注类型                                │
│                                                         │
│ 为什么现在学：                                            │
│   FastAPI 的 路由参数、Pydantic 模型、依赖注入            │
│   全部依赖类型注解。不学这个，阶段2 会处处卡住            │
│                                                         │
│ 只需掌握：                                              │
│   基础: int, str, float, bool                           │
│   容器: List[str], Dict[str, int], Tuple[int, ...]     │
│   可选: Optional[int]（= int | None）                   │
│   函数: def foo(x: int, y: str = "hi") -> bool:        │
│                                                         │
│ 不需要学（后面遇到再说）：                                │
│   TypeVar, Protocol, Generic, Literal, overload         │
└─────────────────────────────────────────────────────────┘
```

### 验证方式（可检验产出）

```
产出1: 写一个 @retry 装饰器（带参数，可配置重试次数）
       → 代码发到笔记里，能跑通即可

产出2: 在 pytest fixtures.py 源码里找到 fixture 装饰器
       → 截图标出它的函数签名和核心逻辑

产出3: 在 Flask 源码里找一个装饰器，说说它的作用
       → 记录到知识地图的「源码对照」里

产出4: 阶段1结束前：不看教程，自己写一个带参数的装饰器
       → 发给别人讲清楚（学以致教）

产出5: 给一个函数加上完整的类型注解（参数+返回值）
       → 用 mypy 检查通过（选做）
```

### 阶段1 周任务

---

## Week 1：闭包 + 装饰器（Day 0-5）

### Day 0：函数是"一等对象"（闭包的前置知识）

> 为什么加这一天：闭包的基础是"函数可以像变量一样传来传去"。
> 如果这个概念不通，后面的闭包和装饰器就只能靠背模板。

**Session 1（30min）：敲代码体验**
```python
# 1. 函数可以赋值给变量
f = print
f("hello")  # 输出 hello —— f 就是 print

# 2. 函数可以作为参数传递
def do_twice(func, arg):
    func(arg)
    func(arg)

do_twice(print, "hi")  # 输出两次 hi

# 3. 函数可以作为返回值
def make_greeter(greeting):
    def greeter(name):
        print(f"{greeting}, {name}!")
    return greeter  # 返回一个函数，不是返回一个值

hello = make_greeter("Hello")
hello("Alice")  # Hello, Alice!
hello("Bob")    # Hello, Bob!

# 关键理解：
# - 函数和整数、字符串一样，可以赋值、传递、返回
# - make_greeter 返回的是 greeter 函数本身（不带括号）
# - 这就是闭包和装饰器的基础
```

**Session 2（10min）：记1-3句话**
```
今天的关键理解：
  函数是"一等对象"，可以赋值、传参、返回，和普通变量没区别。
```

---

### Day 1：闭包基础（装饰器的前置知识）

**Session 1（30min）：看教程**
- 打开：https://realpython.com/python-closures/
- 重点理解：什么是闭包、内层函数怎么"记住"外层变量

**Session 2（30min）：敲代码**
```python
# 1. 最简单的闭包
def outer(msg):
    def inner():
        print(msg)  # inner 引用了 outer 的 msg
    return inner

hello = outer("Hello")
hello()  # 输出 Hello —— outer 已经结束了，但 msg 还在

# 2. 闭包 = 函数 + 它记住的变量
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c = make_counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3
```

**Session 3（10min）：记1-3句话**
```
闭包 = 内层函数 + 外层变量。装饰器就是闭包的一种用法。
```

---

### Day 2：装饰器基础

**Session 1（30min）：看教程**
- 打开：https://realpython.com/primer-on-python-decorators/
- 只看 Part 1-2（What is a Decorator? + Simple Decorators）
- 边看边在 Python 交互式窗口敲一遍

**Session 2（30min）：敲代码**
```python
# 1. 最简单的装饰器（就是闭包！）
def my_decorator(func):
    def wrapper():
        print("Before")
        func()
        print("After")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()

# 2. 理解 @ 语法糖
# @my_decorator 等价于：
# say_hello = my_decorator(say_hello)
```

**Session 3（10min）：记1-3句话**
```
装饰器 = 闭包，只是外层参数是函数。@my_decorator 等于 say_hello = my_decorator(say_hello)。
```

---

### Day 3：*args, **kwargs + 带参数的装饰器

**Session 1（30min）：先练 *args, **kwargs**
```python
# 1. *args：接收任意数量的位置参数
def show_args(*args):
    for i, arg in enumerate(args):
        print(f"arg[{i}] = {arg}")

show_args(1, "hello", True)

# 2. **kwargs：接收任意数量的关键字参数
def show_kwargs(**kwargs):
    for key, value in kwargs.items():
        print(f"{key} = {value}")

show_kwargs(name="Alice", age=30)

# 3. 拆包：反过来用
def greet(name, age):
    print(f"{name} is {age}")

data = {"name": "Bob", "age": 25}
greet(**data)  # 等于 greet(name="Bob", age=25)
```

**Session 2（30min）：带参数的装饰器**
```python
# 装饰器工厂：外面再包一层
def repeat(num_times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(num_times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(num_times=3)
def greet(name):
    print(f"Hello {name}")

greet("World")

# 理解三层嵌套：
# repeat(3) 返回 decorator
# decorator(greet) 返回 wrapper
# wrapper("World") 执行 greet("World") 三次
```

**Session 3（10min）：记1-3句话**
```
装饰器工厂 = 三层嵌套：最外层接配置，中间层接函数，最内层执行。
```

---

### Day 4：装饰器实战练习

**Session 1（30min）：思考**
- 想一个工作中可以用装饰器的场景
- 比如：记录函数执行时间、打印日志、异常重试

**Session 2（1h）：写代码**
```python
# 写一个计时装饰器
import time
import functools

def timer(func):
    @functools.wraps(func)  # 保留原函数的名字和文档
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    print("Done")

slow_function()
print(slow_function.__name__)  # 应该打印 "slow_function"，不是 "wrapper"
```

**Session 3（10min）：记1-3句话**
```
functools.wraps 保留原函数信息。装饰器实战：计时、日志、重试。
```

---

### Day 5：读 Flask 源码里的装饰器 + 周复盘

**Session 1（30min）：找源码**
- 如果装了 Flask：找 `flask/app.py`
- 如果没装：在线看 https://github.com/pallets/flask/blob/main/src/flask/app.py
- 搜索 `def route`

**Session 2（30min）：读代码**
```python
# 找到的 route 装饰器简化版大概是：
def route(self, rule, **options):
    def decorator(f):
        self.add_url_rule(rule, f.__name__, **options)
        return f
    return decorator

# 理解：
# @app.route('/') 其实是 @app.route('/')(index)
# route('/') 返回 decorator，decorator(index) 返回 index
```

**Session 3（10min）：周复盘**
```
Week 1 周复盘：
  1. 这周学了什么？（3句话）
  2. 哪里卡住了？
  3. 下周必须完成的 1 件事？
```

---

## Week 2：上下文管理器（Day 6-10）

### Day 6：上下文管理器基础

**Session 1（30min）：看教程**
- 打开：https://realpython.com/python-with-statement/
- 看 Part 1-2（Understanding Python's with Statement）

**Session 2（30min）：敲代码**
```python
# 1. 抄一遍基本用法
with open('test.txt', 'w') as f:
    f.write('Hello')

# 2. 自己实现一个
class MyContextManager:
    def __enter__(self):
        print("Entering")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exiting")
        return False

with MyContextManager() as m:
    print("Inside")
```

---

### Day 7：contextlib 实现

**Session 1（30min）：看教程**
- 继续看 Real Python Part 3（Beyond the Context Manager）

**Session 2（30min）：敲代码**
```python
# 用 contextlib 实现上下文管理器（更简单）
from contextlib import contextmanager

@contextmanager
def my_context():
    print("Entering")
    try:
        yield "resource"
    finally:
        print("Exiting")

with my_context() as res:
    print(f"Got {res}")
```

---

### Day 8：contextlib 练习

**Session 1（1h）：写一个数据库连接的上下文管理器**

```python
from contextlib import contextmanager

@contextmanager
def db_transaction(connection):
    try:
        connection.begin()
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise

# 使用
class FakeDB:
    def begin(self): print("begin")
    def commit(self): print("commit")
    def rollback(self): print("rollback")

with db_transaction(FakeDB()) as db:
    print("Transaction running")
```

---

### Day 9：装饰器 vs 上下文管理器

**Session 1（1h）：对比整理**
```
装饰器 vs 上下文管理器：

装饰器：
  - 作用在函数上
  - 包装函数行为
  - 例子：@timer, @retry, @app.route

上下文管理器：
  - 作用在代码块上
  - 管理资源（进入/退出）
  - 例子：with open(), with db.transaction()

什么时候用哪个？
  - 想增强一个函数 → 装饰器
  - 想管理资源/代码块 → 上下文管理器
```

---

### Day 10：Week 2 周复盘

**Session 1（30min）：自测**
```python
# 不看教程，自己写一个上下文管理器
# 要求：统计代码块执行时间
import time

class TimerContext:
    # 你的代码

with TimerContext() as t:
    time.sleep(0.5)

print(t.elapsed)  # 应该打印 0.5
```

**Session 2（10min）：周复盘**
```
Week 2 周复盘：
  1. 这周学了什么？（3句话）
  2. 哪里卡住了？
  3. 下周必须完成的 1 件事？
```

---

## Week 3：生成器 + 面向对象深入（Day 11-16）

### Day 11-12：生成器基础

**Session 1（30min）：看教程**
- https://realpython.com/introduction-to-python-generators/

**Session 2（1h）：敲代码**
```python
# 1. 最简单的生成器
def count_up_to(n):
    count = 1
    while count <= n:
        yield count
        count += 1

for num in count_up_to(5):
    print(num)

# 2. 生成器表达式
squares = (x**2 for x in range(5))
print(list(squares))

# 3. 对比：列表 vs 生成器的内存差异
import sys
list_comp = [x**2 for x in range(10000)]
gen_expr = (x**2 for x in range(10000))
print(f"列表: {sys.getsizeof(list_comp)} bytes")
print(f"生成器: {sys.getsizeof(gen_expr)} bytes")
```

---

### Day 13：生成器进阶 + 概念桥接

**Session 1（1h）：理解 yield from 和概念桥接**
```python
# 1. yield from（委托生成器）
def inner():
    yield 1
    yield 2

def outer():
    yield from inner()  # 等于 for x in inner(): yield x
    yield 3

print(list(outer()))  # [1, 2, 3]

# 2. 概念桥接图（不用写代码，理解关系就行）
#
#   生成器 (yield)
#     ↓ 可以暂停和恢复
#   协程 (coroutine)
#     ↓ Python 3.5+ 语法糖
#   async/await
#     ↓ 框架封装
#   FastAPI（异步 Web 框架）
#
#   现在只需要知道：async def 就是"高级版的生成器"
#   到阶段2学 FastAPI 时会自然用到
```

---

### Day 14-15：面向对象补充（abc 抽象基类，选学）

> MRO 和 abc 在日常开发中用得不多，了解概念即可，不用深入。
> 如果时间紧，可以跳过这两天，直接进 Day 16。

**Session 1（30min）：看教程**
- 搜索 Real Python "Abstract Base Classes"
- 重点理解：什么是 ABC（抽象基类），为什么要用

**Session 2（30min）：敲代码**
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * self.radius ** 2

c = Circle(5)
print(c.area())

# MRO：多继承时的方法查找顺序
class A:
    def hello(self): print("A")
class B(A):
    def hello(self): print("B")
class C(A):
    def hello(self): print("C")
class D(B, C):
    pass

d = D()
d.hello()  # 打印什么？
print(D.__mro__)  # 查看方法查找顺序
```

---

### Day 16：类型注解基础 + 阶段1总复习

**Session 1（30min）：类型注解**
```python
from typing import List, Optional, Dict

# 1. 基础类型注解
name: str = "Alice"
age: int = 30
scores: List[int] = [90, 85, 92]

# 2. 函数类型注解
def greet(name: str, times: int = 1) -> str:
    return f"Hello {name}! " * times

# 3. Optional（可以是 None）
def find_user(user_id: int) -> Optional[str]:
    if user_id == 1:
        return "Alice"
    return None

# 4. 复杂类型
def process_data(items: List[Dict[str, int]]) -> List[str]:
    return [f"{k}={v}" for item in items for k, v in item.items()]

# 为什么这很重要：FastAPI 的写法就长这样
# @app.get("/users/{user_id}")
# def get_user(user_id: int) -> User:  ← 类型注解决定了参数验证和文档
#     ...
```

**Session 2（1h）：阶段1自测**

```
产出1: 写一个 @retry 装饰器（带参数，可配置重试次数）
产出2: 自己实现一个上下文管理器（不用 contextlib）
产出3: 在 Flask 源码里找一个装饰器，说说它的作用
产出4: 给下面这个函数加上类型注解：
       def process_items(items, filter_func, default):
           ...
```

**Session 3：阶段1总复盘**
```
阶段1 总复盘：

1. 闭包：能说清"闭包是什么"吗？
2. 装饰器：能写了吗？能讲清楚了吗？
3. 上下文管理器：能写了吗？能讲清楚了吗？
4. 生成器：能读懂别人的 yield 代码了吗？知道和 async 的关系了吗？
5. 类型注解：能给函数加注解了吗？
6. 源码：Flask 装饰器找到了吗？
7. 阶段1通关了吗？（6选4算过）
```

---

## 过渡周：HTTP + requests（1周）

> 为什么加这一周：阶段1是纯 Python 语法，阶段2是 Web 开发。
> 中间没有过渡的话，你会同时面对"Web 概念"和"框架语法"两个陌生事物。
> 这一周用 requests 库**调别人的 API**，先理解 HTTP，再到阶段2自己**写 API**。

### 学习目标
- 理解 HTTP 请求/响应模型（Method, URL, Header, Body, Status Code）
- 能用 requests 库发 GET/POST 请求
- 能解析 JSON 响应
- 理解 REST API 的基本设计（资源 + 动词）

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| HTTP 基础 | MDN: HTTP 概述 | https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Overview | **必读** |
| requests 库 | Real Python: Requests | https://realpython.com/python-requests/ | **必读** |
| REST API 概念 | RESTful API 设计指南 | https://restfulapi.net/ | 选读 |

### 知识地图

```
┌─────────────────────────────────────────────────────────┐
│              知识地图：HTTP 请求/响应                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  客户端（你的 Python 脚本）                              │
│    │                                                   │
│    │── GET /repos/python/cpython ────→  服务器（GitHub） │
│    │   Header: Accept: application/json                │
│    │                                                   │
│    │←── 200 OK ──────────────────────  服务器           │
│    │    Body: {"id": 123, "name": ...}                 │
│    │                                                   │
│  关键概念：                                              │
│    Method:  GET(查) POST(增) PUT(改) DELETE(删)         │
│    URL:     https://api.github.com/repos/{owner}/{repo}│
│    Header:  元信息（认证、格式、缓存）                   │
│    Body:    请求/响应的数据（通常是 JSON）               │
│    Status:  200成功 400客户端错 401未认证 404没找到 500服务器错│
│                                                         │
│  和后面的关系：                                          │
│    过渡周：用 requests 调别人的 API（客户端）             │
│    阶段2：用 FastAPI 自己写 API（服务端）                │
│    阶段4：用 JS fetch 调自己的 API（前端客户端）         │
└─────────────────────────────────────────────────────────┘
```

### 周任务

```
Day 1-2: HTTP 基础概念 + requests 库入门
  - 安装 requests: pip install requests
  - 用 requests.get() 调 GitHub API
  - 理解 response.status_code, response.json(), response.headers

Day 3-4: 完整 CRUD 练习
  - 用一个公开的练习 API（如 https://jsonplaceholder.typicode.com）
  - GET /posts         → 获取列表
  - GET /posts/1       → 获取单个
  - POST /posts        → 创建（带 JSON body）
  - PUT /posts/1       → 更新
  - DELETE /posts/1    → 删除
  - 理解每个请求的 Method + URL + Body + 返回值

Day 5: 实战 + 复盘
  - 用 requests 写一个脚本：获取 GitHub 仓库信息，打印 star 数和最近更新时间
  - 处理异常情况：404、网络超时
  - 复盘：HTTP 知识地图填完
```

### 里程碑产出

```
产出: 一个 Python 脚本，能做以下事情：
  1. 调 GitHub API 获取仓库信息
  2. 调 JSONPlaceholder API 完成增删改查
  3. 打印请求和响应的关键信息（Method, URL, Status, Body）

验证标准：
  - 能说清 GET 和 POST 的区别
  - 能说清 200, 400, 401, 404, 500 分别代表什么
  - 能用 requests 发带 Header 和 Body 的请求
```

---

## 阶段2：FastAPI Web 开发 + pytest 基础（4-5周）

> 变化说明：这个阶段比原来多了 pytest 基础。
> 你是测试工程师，写代码的同时写测试应该是本能。
> 阶段5保留 pytest 源码阅读和深度集成，这里只学"会用"。

### 学习目标
- 能写 REST API（增删改查）
- 理解 Pydantic 数据验证
- 理解路由与依赖注入
- 理解 Web 请求 → 响应完整流程
- **能用 pytest + TestClient 测试自己写的 API**

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| FastAPI 入门 | FastAPI 官方教程 | https://fastapi.tiangolo.com/tutorial/ | **必读** |
| Pydantic | FastAPI 文档: Pydantic | https://fastapi.tiangolo.com/python-types/ | **必读** |
| 依赖注入 | FastAPI 文档: Dependencies | https://fastapi.tiangolo.com/tutorial/dependencies/ | **必读** |
| REST API 设计 | 《Python Cookbook》ch6 | 纸质/电子版 | **必读** |
| FastAPI 测试 | FastAPI 文档: Testing | https://fastapi.tiangolo.com/tutorial/testing/ | **必读** |
| pytest 入门 | pytest 文档: Getting Started | https://docs.pytest.org/en/latest/getting-started.html | **必读** |
| pytest fixture | pytest 文档: Fixtures | https://docs.pytest.org/en/latest/how-to/fixtures.html | **必读** |

### 源码阅读路径

```
阶段2 源码阅读：

Step 1: fastapi/routing.py（找路由匹配逻辑）
  → 目标：理解 @app.get() 怎么对应到函数
  → 位置：找 APIRoute 类，理解它的 __init__ 和 call
  → 读多少：80-100行
  → 🏗️ 架构概念：路由注册表
     问自己：所有的 @app.get() 最终存到了哪里？→ 一个路由表（字典/列表）
     请求进来时，框架拿 URL 去路由表里查 → 找到对应的函数 → 调用它
     这就是"注册-查找"模式，很多框架都这么干

Step 2: fastapi/dependencies/utils.py（找 Depends 实现）
  → 目标：理解依赖注入怎么工作
  → 位置：找 Depends 类，理解它怎么获取依赖
  → 读多少：50-80行
  → 🏗️ 设计模式：依赖注入（Dependency Injection）
     问自己：为什么不直接在函数里 import 数据库连接，而要用 Depends()？
     答：因为测试时可以"注入"一个假的数据库，不碰真数据库
     DI 的核心：函数不自己创建依赖，而是"外面给我什么我就用什么"
     → 这解释了为什么 pytest fixture 也是依赖注入（函数参数名 = fixture 名）

每步产出：
  - 在知识地图里记录：这个函数的上游和下游是什么
  - 画一个简单的调用时序图
  - 标注：这里用了什么模式？对测试有什么意义？
```

### 🏗️ 阶段2 架构意识：分层架构

```
写博客 API 时，注意代码怎么组织：

  ❌ 不好的写法：所有逻辑塞在路由函数里
     @app.get("/articles")
     def list_articles():
         # 查数据库、过滤、分页、格式化... 全在这里
         # 200 行的函数

  ✅ 好的写法：分层
     路由层（router）：接收请求、返回响应
       ↓ 调用
     业务层（service）：业务逻辑（过滤、分页、权限判断）
       ↓ 调用
     数据层（repository）：数据库操作

  为什么分层？
    - 每一层可以独立测试（单元测试只测 service，不碰数据库）
    - 换数据库时只改数据层，不动业务逻辑
    - 读别人框架时，先找"它分了几层"，就能快速理解结构

  现在不需要严格分层，但写代码时想一想：
    "这段逻辑属于哪一层？" → 至少把路由和业务逻辑分开
```

### 知识地图

```
┌─────────────────────────────────────────────────────────┐
│              知识地图：FastAPI 请求处理流程               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 请求进来（HTTP）                                     │
│     ↓                                                   │
│  2. ASGI 服务器接收（Uvicorn）                           │
│     ↓                                                   │
│  3. FastAPI 路由匹配（@app.get/post/put/delete）        │
│     ↓                                                   │
│  4. 依赖注入（Depends）                                  │
│     ↓                                                   │
│  5. Pydantic 验证请求数据                                │
│     ↓                                                   │
│  6. 业务逻辑（你自己写的函数）                            │
│     ↓                                                   │
│  7. Pydantic 验证响应数据                                │
│     ↓                                                   │
│  8. 响应返回（JSON）                                     │
│                                                         │
│ 关键文件对应：                                            │
│   路由定义: main.py 里的 @app.get()                     │
│   依赖注入: FastAPI 文档 Depends()                       │
│   数据验证: Pydantic BaseModel                          │
└─────────────────────────────────────────────────────────┘
```

### 里程碑产出：自己的博客 API + 测试

```
功能：
  - 发表文章（POST /articles）
  - 获取文章列表（GET /articles）
  - 获取单篇文章（GET /articles/{id}）
  - 更新文章（PUT /articles/{id}）
  - 删除文章（DELETE /articles/{id}）

要求：
  - 不看教程能写出来
  - 有基本的数据验证（Pydantic）
  - 返回合适的 HTTP 状态码
  - 每个接口至少有 1 个 pytest 测试用例
```

### 验证方式（可检验产出）

```
产出1: 不看教程，自己写一个博客 API
       → 代码能跑通，有增删改查即可

产出2: 画出 FastAPI 请求处理流程图
       → 手画拍照也行，关键是要能说清每步做什么

产出3: 用 pytest + TestClient 给博客 API 写测试
       → 至少覆盖：正常 CRUD + 参数错误 + 404
       → 这比 Postman 手动点更贴合你的职业

产出4: 在 routing.py 里找一个类，说出它的 3 个关键方法
       → 记录到知识地图「源码对照」里

产出5: 给别人讲 FastAPI 和 Flask 有什么区别
       → 能讲清楚算过，不要求全对
```

### 阶段2 周任务

```
Week 1:
  Day1-2: FastAPI 官方教程（请求 + 路由）
  Day3-4: Pydantic 数据验证
  Day5:   第一个 API：Hello World

Week 2:
  Day1-2: CRUD 完整示例（博客 API）
  Day3-4: 依赖注入（Depends）
  Day5:   给自己的 API 加分页

Week 3:
  Day1-2: 错误处理（HTTPException）
  Day3-4: 中间件基础
  Day5:   博客 API 完整练习（不看教程重写）

Week 4: pytest 基础 + API 测试
  Day1: pytest 入门（assert、test_前缀、运行方式）
  Day2: pytest fixture（setup/teardown）
  Day3: pytest 参数化（@pytest.mark.parametrize）
  Day4-5: 用 TestClient 给博客 API 写完整测试

Week 5（弹性周）:
  Day1-2: 博客 API 功能完善
  Day3-4: 补充测试用例（边界情况、错误情况）
  Day5:   阶段2总复习 + 知识地图
```

---

## 阶段3：数据库 + ORM（2-3周）

### 学习目标
- 能用 SQLAlchemy 定义数据模型
- 理解数据如何在 API ↔ ORM ↔ DB 之间流转
- 能设计关联表（用例 + 缺陷）
- 会用 Alembic 管理数据库版本

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| SQLAlchemy 入门 | Real Python: SQLAlchemy | https://realpython.com/sqlalchemy/ | **必读** |
| SQLAlchemy 关系 | Real Python: SQLAlchemy Relations | https://realpython.com/sqlalchemy-relations/ | **必读** |
| Alembic 迁移 | Alembic 官方文档 | https://alembic.sqlalchemy.org/en/latest/ | **必读** |
| 数据库设计 | 《SQL 必知必会》| 纸质/电子版 | **必读** |

### 源码阅读路径

```
阶段3 源码阅读：

Step 1: sqlalchemy/orm.py（找查询构建逻辑）
  → 目标：理解 db.query() 怎么变成 SQL
  → 位置：找 Query 类，理解它的 filter 方法
  → 读多少：80-100行
  → 🏗️ 设计模式：构建器模式（Builder Pattern）
     问自己：db.query(Article).filter(...).order_by(...).limit(10) 为什么能链式调用？
     答：每个方法都返回自己（self），让你一步步"构建"查询
     Builder 模式 = 一步步配置，最后生成结果

Step 2: sqlalchemy/models.py（找 DeclarativeBase 实现）
  → 目标：理解 class Article(Base) 怎么变成表
  → 位置：找 __tablename__ 是怎么定义的
  → 读多少：50行
  → 🏗️ 架构概念：数据映射器（Data Mapper）
     问自己：为什么写 class Article(Base) 就自动对应一张表？
     答：SQLAlchemy 在幕后把"Python 类"映射成"数据库表"
     你只管写 Python 对象，它负责翻译成 SQL → 这就是 ORM 的核心思想

每步产出：
  - 在知识地图里记录：ORM 操作对应的 SQL 是什么
  - 说出这个函数的核心逻辑（1句话）
  - 标注：这里用了什么模式？
```

### 🏗️ 阶段3 架构意识：仓储模式 + 工作单元

```
写数据库操作时，注意两个重要概念：

仓储模式（Repository Pattern）：
  把数据库操作封装成一个"仓库"类，外部只调接口，不直接写 SQL

  ❌ 路由里直接查数据库：
     @app.get("/articles")
     def list_articles(db: Session):
         return db.query(Article).filter(...).all()

  ✅ 用仓储封装：
     class ArticleRepo:
         def __init__(self, db: Session):
             self.db = db
         def list_all(self, skip=0, limit=10):
             return self.db.query(Article).offset(skip).limit(limit).all()

  好处：换数据库时只改 Repo，路由层不动

工作单元（Unit of Work）：
  SQLAlchemy 的 Session 就是一个工作单元：
  - db.add(article)     → 先记着，还没存
  - db.add(comment)     → 也记着
  - db.commit()         → 一次性全部存到数据库
  - 如果中间出错 → db.rollback() → 全部撤销

  好处：要么全部成功，要么全部失败，数据不会出现"存了一半"的情况
  → 这就是阶段1学的上下文管理器的典型应用场景
```

### 知识地图

```
┌─────────────────────────────────────────────────────────┐
│              知识地图：数据如何在三层之间流转              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  API 层（FastAPI）                                      │
│    ↓ 接收请求                                           │
│    ↓ 调用                                               │
│  ORM 层（SQLAlchemy）                                   │
│    ↓ 生成 SQL                                           │
│    ↓ 执行                                               │
│  DB 层（SQLite/PostgreSQL）                             │
│    ↓ 返回结果                                           │
│    ↓                                                   │
│  ORM 层（结果映射为对象）                                 │
│    ↓                                                   │
│  API 层（返回 JSON）                                    │
│                                                         │
│  关键对应：                                              │
│    模型定义: class Article(Base)                        │
│    表操作:  db.query(Article)                           │
│    迁移:    alembic revision -m "add title"            │
│                                                         │
│  用例管理平台的数据模型：                                  │
│    TestCase ←→ TestCaseRun（1对多）                     │
│    TestCase ←→ Bug（多对多，通过关联表）                  │
└─────────────────────────────────────────────────────────┘
```

### 里程碑产出：给博客加数据库

```
功能：
  - 用 SQLAlchemy 定义 Article 模型
  - 用 Alembic 创建迁移
  - 博客 API 接入数据库（不写死数据）
  - 更新 pytest 测试（用测试数据库）

数据模型：
  Article(id, title, content, author, created_at, updated_at)
```

### 验证方式（可检验产出）

```
产出1: 能设计：用例（TestCase）和缺陷（Bug）的关联表
       → 说出 2 种方案及优劣（能讲清楚即可）

产出2: 能独立用 Alembic 做数据库迁移
       → 实际跑一遍，记录迁移命令

产出3: 能给自己的博客 API 加上数据库
       → 代码能跑通，查询能出结果

产出4: 在 sqlalchemy/orm.py 里找 3 个方法，说出它们的作用
       → 记录到知识地图「源码对照」里
```

### 阶段3 周任务

```
Week 1:
  Day1-2: SQLAlchemy 基本操作（CRUD）
  Day3-4: 定义数据模型（Article 模型）
  Day5:   SQLAlchemy 关系（外键、一对多）

Week 2:
  Day1-2: Alembic 数据库迁移
  Day3-4: 给博客 API 接入数据库
  Day5:   整理笔记：ORM vs 原生 SQL 的区别

Week 3:
  Day1-2: 设计：用例 + 缺陷关联表（练习）
  Day3-4: 高级查询（filter, join, 聚合）
  Day5:   阶段3总复习 + 自测题
```

---

## 阶段4A：前端极简（1周）

> 目标不是成为前端工程师，而是"能用 HTML 表格展示数据 + 用 JS 调 API"。
> 不追求好看，能用就行。

### 前置知识：HTTP 基础（已在过渡周学过）

```
过渡周已经学过 HTTP 基础，这里直接用。
如果忘了，回顾过渡周的知识地图。

前端需要额外理解的：
  - 跨域问题（CORS）：前端和后端不在同一个地址时会遇到
  - Fetch API：浏览器内置的发请求方式（类似 requests）
```

### 学习目标
- 能看懂 HTML/CSS 基础
- 能写简单页面
- 理解 JavaScript 核心（DOM 操作、事件、Fetch）
- 能用原生 JS 发请求对接 API

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| HTML 基础 | MDN: HTML 教程 | https://developer.mozilla.org/zh-CN/docs/Learn/HTML | **必读** |
| CSS 基础 | MDN: CSS 教程 | https://developer.mozilla.org/zh-CN/docs/Learn/CSS | **必读** |
| JavaScript 核心 | MDN: JavaScript 教程 | https://developer.mozilla.org/zh-CN/docs/Web/JavaScript | **必读** |
| Fetch API | MDN: Fetch 教程 | https://developer.mozilla.org/zh-CN/docs/Web/API/Fetch_API | **必读** |

### 验证方式（可检验产出）

```
产出1: 用 HTML + CSS 写一个简单页面（博客列表页）
       → 不要求好看，能显示数据就行

产出2: 用原生 JS 给页面加交互（点击按钮弹窗）
       → 代码能跑通

产出3: 用 Fetch API 发一个 GET 请求到自己的 FastAPI
       → 能拿到数据并显示在页面上
```

### 阶段4A 周任务

```
Day1: HTML 基础（标签、表单、列表）+ CSS 极简样式
Day2: JavaScript 基础（变量、函数、DOM 操作）
Day3: JavaScript 事件 + Fetch API
Day4: 用 Fetch 调自己的博客 API，把数据渲染到 HTML 表格
Day5: 完善页面（加个表单能提交数据到 API）
```

---

## 阶段4B：JWT 认证（1周）

### 学习目标
- 理解 JWT 认证原理
- 能给 FastAPI 加登录功能
- 能用前端 + JWT 做登录状态管理

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| JWT 认证 | FastAPI 文档: Security | https://fastapi.tiangolo.com/tutorial/security/ | **必读** |
| OAuth2 + JWT | FastAPI 文档: OAuth2 | https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ | **必读** |

### 源码阅读路径

```
阶段4 源码阅读：

Step 1: fastapi/security.py（找 JWT 实现）
  → 目标：理解 OAuth2PasswordBearer 怎么验证 Token
  → 位置：找 get_authorization_scheme_param 函数
  → 读多少：50行

Step 2: python-jose 源码（如果装了）
  → 目标：理解 JWT 的 encode/decode
  → 位置：找 jose/jwt.py 的 encode 和 decode
  → 读多少：50行

每步产出：
  - 在知识地图里记录：JWT 的工作流程
  - 画出 Token 验证的流程图
```

### 验证方式（可检验产出）

```
产出1: 给博客 API 加登录接口（POST /login）
       → 返回 JWT Token

产出2: 用前端 + Token 发请求
       → 能用 Token 访问需要认证的接口

产出3: 在 security.py 里找到 Token 验证逻辑
       → 记录到知识地图「源码对照」里
```

### 知识地图：前端 ↔ API ↔ 认证

```
┌─────────────────────────────────────────────────────────┐
│              知识地图：前端和 API 怎么配合                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  前端（HTML+JS）        API（FastAPI）         DB        │
│     │                     │                    │        │
│     │──GET /articles────→│                    │        │
│     │←─JSON 列表─────────│                    │        │
│     │                     │                    │        │
│     │──POST /login──────→│                    │        │
│     │←─JWT Token ───────│                    │        │
│     │                     │                    │        │
│     │──POST /articles──→│（带 Token）         │        │
│     │   Header:          │                    │        │
│     │   Authorization:  │                    │        │
│     │   Bearer xxx      │                    │        │
│                                                         │
│  JWT 工作流程：                                          │
│  1. 用户登录 → 后端验证 → 返回 Token                      │
│  2. 前端存 Token（localStorage）                         │
│  3. 后续请求带 Token → 后端验证 → 处理请求                 │
│  4. Token 过期 → 前端重新登录                             │
└─────────────────────────────────────────────────────────┘
```

### 里程碑产出：给博客加前端 + 登录

```
功能：
  - 博客文章列表页（HTML + JS，纯原生即可）
  - 登录页面
  - JWT Token 认证
  - 发表文章（登录后才能发）
```

### 阶段4 周任务总览

```
阶段4A（Week 1）:
  HTML + CSS 极简 + JavaScript + Fetch API（5天）

阶段4B（Week 2）:
  Day1-2: JWT 认证原理 + FastAPI 实现
  Day3-4: 前端 + Token 对接（用 Fetch 发带 Token 的请求）
  Day5:   阶段4总复习 + 知识地图
```

---

## 阶段5：pytest 深度集成（3-4周）

> 这个阶段是你作为测试工程师的核心竞争力。
> 阶段2已经学了 pytest 基础用法，这里深入源码、集成、mock、测试策略。

### 前置要求

```
阶段5 开始前，必须满足：
  ✅ 能独立写一个 FastAPI CRUD API（阶段2）
  ✅ 能用 pytest + TestClient 写 API 测试（阶段2）
  ✅ 理解 SQLAlchemy 模型关系（阶段3）

达不到的话，先回滚阶段2-3，不要硬上。
```

### 学习目标
- 理解测试金字塔和测试策略（什么时候写什么测试）
- 掌握 mock/patch，能隔离外部依赖
- 能用 Python 代码调用 pytest（不只是命令行）
- 能收集测试结果、生成报告
- 能把测试集成到 Web 平台
- 能用 cron 或 GitHub Actions 做定时测试
- **能读懂 pytest 源码的关键模块**

### 学习素材

| 内容 | 资源 | 地址 | 必读/选读 |
|------|------|------|-----------|
| 测试策略 | Martin Fowler: Test Pyramid | https://martinfowler.com/articles/practical-test-pyramid.html | **必读** |
| mock | Real Python: Understanding Mock | https://realpython.com/python-mock-library/ | **必读** |
| pytest 进阶 | 《Python Testing with pytest》| 纸质/电子版 | **必读** |
| pytest Python API | pytest 文档: API Reference | https://docs.pytest.org/en/latest/reference/reference.html | **必读** |
| pytest-html 源码 | GitHub: pytest-html | https://github.com/pytest-dev/pytest-html | **必读**（Week 3 读源码用） |
| JUnit XML 格式 | JUnit 官方文档 | https://github.com/windyroad/JUnit-Schema | 选读 |
| GitHub Actions | GitHub 文档: Actions | https://docs.github.com/en/actions | 选读（定时执行测试用） |

### 测试策略：先建立思维框架

```
┌─────────────────────────────────────────────────────────┐
│              知识地图：测试金字塔                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│           /\                                            │
│          /  \    E2E 测试（少量）                        │
│         / E2E\   → 整个系统跑通，最慢，最贵              │
│        /──────\  → 例：Selenium 打开浏览器点一遍         │
│       /  集成  \  集成测试（适量）                        │
│      /  测试    \ → 多个模块协作，中等速度               │
│     /────────────\→ 例：API + DB 一起测                │
│    /   单元测试   \ 单元测试（大量）                      │
│   /    (最多)      \ → 单个函数/类，最快，最便宜        │
│  /──────────────────\→ 例：纯逻辑函数的测试             │
│                                                         │
│ 你的博客项目应该有：                                     │
│   单元测试: 验证函数（如分页计算、数据转换）             │
│   集成测试: API + DB（TestClient + 测试数据库）         │
│   E2E测试:  前端 + API + DB（可选，阶段6再做）          │
│                                                         │
│ 什么时候用 mock？                                       │
│   - 外部服务不可控时（第三方 API、邮件服务）             │
│   - 想隔离测试某一层时（只测业务逻辑，不碰 DB）         │
│   - 不要过度 mock：能用真实依赖就用真实依赖             │
└─────────────────────────────────────────────────────────┘
```

### 源码阅读路径

```
阶段5 源码阅读：

Step 1: src/_pytest/config.py（找 pytest 主入口）
  → 目标：理解 pytest 怎么加载配置和插件
  → 位置：找 console_main 函数，理解测试发现流程
  → 读多少：80-100行
  → 🏗️ 架构概念：插件架构（Plugin Architecture）★ 最重要
     问自己：pytest 怎么支持那么多插件（pytest-html, pytest-xdist...）？
     答：它定义了一堆"钩子"（hook），插件只需要实现这些 hook
     这就是"开放-封闭原则"：框架本身不改，通过插件扩展功能
     → 你以后读任何测试框架，第一件事就是找"它的扩展点/hook 在哪"

Step 2: src/_pytest/main.py（找测试收集逻辑）
  → 目标：理解 pytest_collection 怎么工作
  → 位置：找 collect 函数，理解怎么找到测试
  → 读多少：60行
  → 🏗️ 设计模式：观察者模式（Observer Pattern）
     问自己：pytest_collection 是谁调用的？→ 不是直接调用，是通过 hook 触发
     hook = 事件发布/订阅：pytest 发布"要收集测试了"，所有注册的插件收到通知
     → 这就是为什么安装 pytest-html 后不需要改 pytest 代码，它自动生效

Step 3: src/_pytest/terminal.py（找输出逻辑）
  → 目标：理解测试报告怎么生成
  → 位置：找 TerminalReporter 类
  → 读多少：50行

Step 4: src/_pytest/fixtures.py（深入理解 fixture）
  → 目标：阶段1看过入口，现在理解完整的 fixture 生命周期
  → 位置：找 FixtureManager 类，理解 scope 怎么控制
  → 读多少：100行
  → 🏗️ 设计模式：模板方法（Template Method）
     fixture 的 scope 控制了生命周期：
       session scope: 整个测试 session 只执行一次 setup/teardown
       function scope: 每个测试函数都执行一次
     → 固定流程：setup → yield（你的测试） → teardown
     → 框架定义流程骨架，你只填 setup 和 teardown 的具体内容

每步产出：
  - 在知识地图里记录：这个模块的输入是什么，输出是什么
  - 画出这个函数的调用链
  - ★ 标注：pytest 的扩展点（hook）在哪？插件怎么接入？
```

### 🏗️ 阶段5 架构意识：读懂框架的三板斧

```
读任何测试框架（pytest、unittest、HttpRunner...），都问这三个问题：

  1. 入口在哪？
     → 用户执行什么命令？入口函数在哪个文件？
     → pytest: console_main() in config.py

  2. 扩展点在哪？
     → 框架怎么让别人加功能？hook？插件？继承？
     → pytest: pluggy hook 系统（pytest_runtest_setup 等）
     → 这是最重要的问题——理解了扩展点，就理解了框架的设计思想

  3. 数据怎么流的？
     → 输入是什么？中间经过哪些处理？输出是什么？
     → pytest: 测试文件 → 收集 → 执行 → 结果 → 报告

  Week 3 clone pytest-html 时，用这三板斧来读：
    1. 入口：plugin.py 的 pytest_configure hook
    2. 扩展点：它怎么通过 hook 拿到测试结果
    3. 数据流：测试结果 → HTML 模板 → 输出文件
```

### 知识地图：测试执行 ↔ API ↔ 报告

```
┌─────────────────────────────────────────────────────────┐
│           知识地图：pytest 集成进 Web 平台                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Web API                        pytest                  │
│    │                              │                     │
│    │ POST /run-tests ──────────────→                     │
│    │         │                     │                     │
│    │         │   subprocess.run(    │                     │
│    │         │     ['pytest', ...] │                     │
│    │         │   )                 │                     │
│    │         │                     │                     │
│    │         │←──────────────────── │                     │
│    │         │   JUnit XML 结果     │                     │
│    │                              │                     │
│    ↓                               ↓                     │
│  存入 DB                         测试执行                 │
│    ↓                               ↓                     │
│  前端展示报告 ←────────────────────────────────          │
│                                                         │
│  集成方式对比：                                          │
│  方式1: subprocess（简单，隔离好）                        │
│  方式2: pytest API（结果结构化，方便）                   │
│  方式3: pytest-xdist（并行执行）                         │
│                                                         │
│  定时任务：                                              │
│  cron / GitHub Actions → 定时触发 /run-tests → 结果存 DB │
└─────────────────────────────────────────────────────────┘
```

### 里程碑产出：给博客加自动化测试 + 集成

```
功能：
  - 完整的测试套件（单元测试 + 集成测试）
  - mock 外部依赖的测试用例
  - 用 pytest API 调用测试（非命令行）
  - 测试结果存入数据库
  - 前端展示测试报告
```

### 验证方式（可检验产出）

```
产出1: 用 mock.patch 写一个测试，隔离外部依赖
       → 代码能跑通，理解 mock 的原理

产出2: 用 Python 代码调用 pytest，不只是命令行
       → 代码能跑通，返回测试结果

产出3: 能把 JUnit XML 结果解析成 JSON
       → 能提取 passed、failed、skipped 数量

产出4: 能给博客 API 写完整的单元测试 + 集成测试
       → 测试能跑通，有覆盖率

产出5: ★ clone pytest-html → 读懂核心逻辑 → 改一个小功能
       → 能说清楚"它怎么生成报告的"
       → 这是测试工程师最核心的技能：读别人的框架、改、用

产出6: 在 pytest config.py 里找到测试发现逻辑
       → 记录到知识地图「源码对照」里

产出7: 能画出测试金字塔，说清三层的区别和适用场景
       → 能讲清楚算过
```

### 阶段5 周任务

```
Week 1: 测试策略 + mock
  Day1:   测试金字塔（读 Martin Fowler 文章）
  Day2-3: unittest.mock 和 pytest-mock
          → mock.patch, MagicMock, side_effect
  Day4-5: 给博客 API 加 mock 测试
          → mock 数据库操作，只测业务逻辑

Week 2: pytest 深度 + 源码
  Day1-2: pytest Python API 文档
  Day3:   读 _pytest/config.py 源码（主入口）
  Day4:   读 _pytest/main.py 源码（测试收集）
  Day5:   读 _pytest/fixtures.py 源码（fixture 生命周期）

Week 3: ★ 读开源框架 → 改 → 用（核心练习）
  Day1: clone pytest-html（https://github.com/pytest-dev/pytest-html）
        → pip install -e . → 跑通它的测试
  Day2: 读核心代码（找 plugin.py 入口，理解它怎么生成报告）
        → 目标：能说清楚"它的输入是什么、输出是什么"
  Day3: 改一个小功能（比如：改报告标题、加一列自定义数据）
        → 体验"在别人代码上改"的流程
  Day4: 把改好的 pytest-html 集成到自己的博客项目
        → pytest --html=report.html 跑博客的测试
  Day5: 复盘：对比"从零写"和"在别人代码上改"的区别
        → 记录：读别人代码时最大的困难是什么

Week 4: Web 集成 + 报告
  Day1-2: 用 subprocess 调用 pytest + 解析 JUnit XML
  Day3-4: pytest 集成进 FastAPI（POST /run-tests）
  Day5:   测试结果存入数据库

Week 5: 报告展示 + 定时执行
  Day1-2: 前端展示测试报告（用 HTML 表格即可）
  Day3-4: 定时执行测试（用 cron 或 GitHub Actions，比 APScheduler 更实用）
  Day5:   阶段5总复习 + 知识地图
```

---

## 阶段6：完整项目（4-6周）

### 项目目标

**模仿开源项目，搭建自己的测试管理平台（极简版）**

```
技术栈：FastAPI + SQLAlchemy + JWT + HTML/JS(极简) + pytest
功能：测试用例管理 + 测试执行 + 报告展示
```

### 🏗️ 阶段6 架构设计：动手之前先画图

```
Week 1 的核心任务不是写代码，而是"读懂 + 画图"。

读开源项目时，用阶段5学的"三板斧"：
  1. 入口在哪？→ 它的 main.py / app.py 长什么样
  2. 扩展点在哪？→ 它怎么支持不同的测试框架
  3. 数据怎么流的？→ 用例定义 → 测试执行 → 结果存储 → 报告展示

画自己的架构图时，要回答这些问题：
  - 分几层？（前端 / API / 业务 / 数据）
  - 每层的职责是什么？（一句话说清）
  - 层与层之间怎么通信？（HTTP? 函数调用?）
  - 数据模型之间什么关系？（1对多? 多对多?）
  - 哪些之前学的设计模式可以用？
    → 仓储模式：封装数据库操作
    → 依赖注入：FastAPI Depends() 管理数据库连接
    → 工厂模式：生成测试数据
```

### 执行流程

```
Week 1: 先找一个开源测试平台，读懂它的架构
         - 推荐：HttpRunner（https://github.com/httprunner/httprunner）
         - 或者找一个更简单的：搜 "pytest management platform github"
         - 用"三板斧"读：入口？扩展点？数据流？
         - 画出它的架构图（手画拍照即可）

Week 2: 模仿它的架构，画自己的设计图
         - 不需要"从零发明"，站在巨人肩膀上改
         - 简化：只保留核心功能（用例 CRUD + 执行 + 报告）
         - 画出：分层图、数据模型图、API 列表、页面列表
         - 标注：每个模块用了什么模式（仓储、DI、工厂...）

Week 3-4: 开始写代码，按模块做
         - 模块1: 用例 CRUD（用仓储模式封装数据库操作）
         - 模块2: 测试执行（用 subprocess 调 pytest）
         - 模块3: 报告展示（解析 JUnit XML → 存 DB → 前端展示）

Week 5-6: 联调 + 完善 + 部署
```

### 源码阅读路径（对比自己的设计和开源）

```
阶段6 源码阅读（对比学习）：

Step 1: pytest-xdist（测试并行执行）
  → 地址: https://github.com/pytest-dev/pytest-xdist
  → 目标：理解怎么并行执行测试
  → 读多少：核心逻辑 100 行

Step 2: allure-pytest（测试报告）
  → 地址: https://github.com/allure-framework/allure-python
  → 目标：理解怎么生成测试报告
  → 读多少：核心逻辑 80 行

Step 3: TestRail API（用例管理）
  → 地址: https://github.com/testrail/TestRail-API-Python
  → 目标：理解用例管理的 API 设计
  → 读多少：API 封装层 50 行

每步产出：
  - 对比自己的设计和开源方案，列出 3 个差异
  - 思考：开源方案好在哪，你能借鉴什么
```

### 架构设计（先自己想，再对比开源）

```
┌─────────────────────────────────────────────────────────┐
│           测试管理平台架构（v1）+ 设计模式标注              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  前端层（HTML+JS）                                      │
│    ├── 用例列表页                                        │
│    ├── 用例编辑页                                        │
│    ├── 测试执行页                                        │
│    └── 报告展示页                                        │
│                                                         │
│  API 层（FastAPI）                ← 分层架构              │
│    ├── /api/v1/cases      （用例 CRUD）                  │
│    ├── /api/v1/runs       （测试执行）                   │
│    ├── /api/v1/reports    （报告查询）                   │
│    └── /api/v1/auth       （认证）                      │
│    └── Depends()          ← 依赖注入                    │
│                                                         │
│  业务层（Service）                ← 阶段2学的分层         │
│    ├── CaseService        （用例业务逻辑）               │
│    ├── RunService         （执行业务逻辑）               │
│    └── ReportService      （报告业务逻辑）               │
│                                                         │
│  数据层（SQLAlchemy）             ← 仓储模式              │
│    ├── CaseRepo           （用例数据操作）               │
│    ├── RunRepo            （执行数据操作）               │
│    ├── 数据模型：                                        │
│    │   TestCase ←→ TestCaseRun（1对多）                  │
│    │   TestCase ←→ Bug（多对多，通过关联表）              │
│    └── Session            ← 工作单元                    │
│                                                         │
│  执行层（pytest）                                        │
│    ├── subprocess 调用 pytest                            │
│    ├── JUnit XML 结果解析                                │
│    └── 测试产物存储                                       │
│                                                         │
│  定时任务（cron / GitHub Actions）                        │
│    └── 定时回归测试                                       │
└─────────────────────────────────────────────────────────┘

  各层用到的设计模式：
    API 层:    依赖注入（Depends 管理 DB 连接和认证）
    业务层:    策略模式（不同测试框架用不同执行策略，可选）
    数据层:    仓储模式 + 工作单元（封装 DB 操作）
    执行层:    工厂模式（根据配置生成不同的 pytest 命令）
```

### 里程碑

```
里程碑A: 用例 CRUD 完成，可运行
里程碑B: 测试执行功能完成
里程碑C: 报告展示完成
里程碑D: 定时任务完成
里程碑E: 完整系统联调完成
```

### 阶段6 最低要求（4选2）

```
阶段6 不一定要做完整平台，但必须做以下其中 2 项：

A. 给开源项目提一个 PR（文档改进也算）
   → 地址: https://github.com/pytest-dev/pytest/pulls
   → 从 good first issue 开始

B. 模仿博客项目，做一个自己的小工具（带 Web 界面）
   → 可以是：测试数据生成器、用例转换工具、报告小工具
   → 至少要有：FastAPI API + 前端页面

C. 写一篇学习笔记（3000字以上）
   → 发到掘金、CSDN、知乎等平台
   → 或者写成系列博客

D. 教别人一个知识点（录屏或直播）
   → 录一个 15 分钟的知识点讲解
   → 发到 B 站或 YouTube

原因：
  教是最好的学
  能讲清楚 = 真正理解
  输出倒逼输入
```

---

## 学习素材汇总

### 官方文档（最权威，永远最新）

| 资源 | 地址 |
|------|------|
| Python 文档 | https://docs.python.org/3/ |
| FastAPI 文档 | https://fastapi.tiangolo.com/ |
| pytest 文档 | https://docs.pytest.org/en/latest/ |
| SQLAlchemy 文档 | https://docs.sqlalchemy.org/ |
| MDN Web Docs | https://developer.mozilla.org/zh-CN/ |
| pytest-html | https://github.com/pytest-dev/pytest-html |

### 在线教程（必读清单）

| 资源 | 地址 | 对应阶段 |
|------|------|----------|
| Real Python: Closures | https://realpython.com/python-closures/ | 阶段1 |
| Real Python: Decorators | https://realpython.com/primer-on-python-decorators/ | 阶段1 |
| Real Python: Context Managers | https://realpython.com/python-with-statement/ | 阶段1 |
| Real Python: Generators | https://realpython.com/introduction-to-python-generators/ | 阶段1 |
| Real Python: Iterators | https://realpython.com/python-iterators-iterables/ | 阶段1 |
| Real Python: Type Checking | https://realpython.com/python-type-checking/ | 阶段1 |
| Real Python: Requests | https://realpython.com/python-requests/ | 过渡周 |
| Real Python: SQLAlchemy | https://realpython.com/sqlalchemy/ | 阶段3 |
| Real Python: Mock | https://realpython.com/python-mock-library/ | 阶段5 |
| FastAPI 官方教程 | https://fastapi.tiangolo.com/tutorial/ | 阶段2 |
| FastAPI Testing | https://fastapi.tiangolo.com/tutorial/testing/ | 阶段2 |
| FastAPI Security | https://fastapi.tiangolo.com/tutorial/security/ | 阶段4B |
| Martin Fowler: Test Pyramid | https://martinfowler.com/articles/practical-test-pyramid.html | 阶段5 |

### 强推博客（★★★★★）

| 博客 | 地址 | 为什么强推 |
|------|------|-----------|
| **Real Python** | https://realpython.com | 所有教程都有深度，不是浅尝辄止，每个知识点都配有完整代码 |
| **PyCQA** | https://github.com/pycqa | flake8、isort、autopep8 源码，代码质量高 |
| **Test Automation University** | https://testautomationu.applitools.com | 免费自动化测试课程，有 Python 专项 |

### 强推课程

| 课程 | 地址 | 对应阶段 |
|------|------|----------|
| **Corey Schafer - Python Tutorials** (YouTube) | https://www.youtube.com/@coreyms | ★★★★★ Python 基础最推荐，语速适中，代码风格好 |
| **Corey Schafer - Flask/Bokeh** (YouTube) | 同上 | 阶段2 Web 开发 |
| **FastAPI 官方视频教程** | https://fastapi.tiangolo.com/tutorial/ | 阶段2 官方出品 |

### 书籍精读指南

```
《Fluent Python》（阶段3之后再读，请核实你的版本号）
  第2版:
    Chapter 7 (闭包和装饰器)      → ★必读，回顾阶段1
    Chapter 9 (装饰器进阶)        → ★必读
    Chapter 17 (迭代器和生成器)    → ★必读
    Chapter 18 (上下文管理器)      → ★必读
    其他章节                      → 选读
  第1版:
    Chapter 7 (闭包和装饰器)      → ★必读
    Chapter 14 (生成器)           → ★必读
    Chapter 15 (上下文管理器)      → ★必读

《Python Cookbook》
  Chapter 1 (数据结构和算法)    → ★必读，异常处理技巧
  Chapter 3 (数字和日期)        → 选读
  Chapter 6 (数据编码)          → 选读
  Chapter 10 (模块和包)         → 选读

《Python Testing with pytest》
  Chapter 1-2 (pytest基础)     → ★必读（阶段2用）
  Chapter 3 (fixtures)         → ★必读（阶段2用）
  Chapter 4 (参数化)           → ★必读（阶段2用）
  Chapter 5 (标记和跳过)        → 选读（阶段5用）
```

### 源码阅读路径汇总

```
阶段1: 装饰器 → 上下文管理器 → 生成器
  flask/app.py                    （路由装饰器）
  src/_pytest/fixtures.py          （fixture装饰器）
  contextlib.py                    （contextmanager）

阶段2: 路由 → 依赖注入
  fastapi/routing.py              （路由匹配）
  fastapi/dependencies/utils.py    （Depends实现）

阶段3: ORM 查询 → 数据模型
  sqlalchemy/orm.py                （查询构建）
  sqlalchemy/models.py             （DeclarativeBase）

阶段4: JWT 认证
  fastapi/security.py              （OAuth2实现）
  jose/jwt.py                      （JWT encode/decode）

阶段5: pytest 深度（源码 + fixture 生命周期 + 读开源框架）
  src/_pytest/config.py            （主入口）
  src/_pytest/main.py              （测试收集）
  src/_pytest/terminal.py          （报告输出）
  src/_pytest/fixtures.py          （fixture 完整生命周期）
  pytest-html/plugin.py            （★ clone → 读 → 改 → 用）

阶段6: 对比开源
  pytest-xdist                     （并行执行）
  allure-python                    （报告生成）
  TestRail-API-Python              （用例管理API）
```

### 源码阅读方法论

```
1. 先看项目结构和 README（5分钟）
2. 找到入口点（main/__init__.py）
3. 用 pdb/ipdb 断点跟一遍（30分钟）
4. 画一个简单时序图（手画拍照也行）
5. 摘抄3句最让你困惑的代码
6. 记录到知识地图「源码对照」里

原则：
  - 不求全懂，只求抓重点
  - 读不懂的先跳过，回头再看
  - 重点关注：扩展点在哪、异常怎么处理
```

---

## 自测题（每阶段结束做）

```
阶段1 自测：
  产出1: 用自己的话解释闭包，写一个闭包的例子
  产出2: 写一个 @retry 装饰器（带参数，可配置重试次数）
  产出3: 自己实现一个上下文管理器（不用 contextlib）
  产出4: 在 Flask 源码里找一个装饰器，说说它的作用
  产出5: 给一个函数加上完整的类型注解
  → 能讲清楚算过

过渡周 自测：
  产出1: 用 requests 调一个 API，打印请求和响应的所有关键信息
  产出2: 说清 GET 和 POST 的区别，说清 5 个常见状态码
  → 能讲清楚算过

阶段2 自测：
  产出1: 不看教程，写一个带分页的 GET API
  产出2: 画出 FastAPI 请求处理流程图
  产出3: 用 pytest + TestClient 写至少 5 个测试用例
  → 代码能跑 + 流程图清晰 + 测试全绿

阶段3 自测：
  产出1: 设计：用例和缺陷的关联，说 2 种方案及优劣
  产出2: 用 Alembic 做一次数据库迁移
  产出3: 在 sqlalchemy/orm.py 找 3 个方法，说出作用
  → 能讲清楚 + 实际跑通

阶段4 自测：
  产出1: 用 HTML+JS 写博客列表页（用 Fetch 调 API 展示数据）
  产出2: 给博客加 JWT 登录（前端 + 后端）
  产出3: 在 security.py 里找 Token 验证逻辑
  → 代码能跑

阶段5 自测：
  产出1: 画出测试金字塔，说清三层区别
  产出2: 用 mock.patch 写一个隔离外部依赖的测试
  产出3: 用 Python 代码调用 pytest（非命令行）
  产出4: 解析 JUnit XML 结果，提取 passed/failed/skipped
  产出5: ★ clone pytest-html → 读懂 → 改一个功能 → 集成到项目
  产出6: 在 pytest 源码里找到测试发现逻辑，画出调用链
  → 代码能跑 + 源码能讲 + 能在别人代码上改东西

阶段6 自测：
  产出1: 画出自己的平台架构图（对比参考的开源项目）
  产出2: 对比开源项目，列出 3 个"我借鉴了什么"
  产出3: 哪个模块做得最好，哪个最烂，为什么？
  → 有图有分析
```

---

## 常见问题

**Q: 学到一半卡住了怎么办？**
A: 先跳过这块，往后学。有时候回头看，卡住的地方自然通了。

**Q: 教程看懂了，但自己写不出来？**
A: 正常。先抄教程，然后改一点，再完全自己写。

**Q: 断了一两周，再捡起来很难？**
A: 先回顾上一阶段的笔记，再继续。里程碑帮你找回节奏。

**Q: 时间太长坚持不下去？**
A: 找同伴一起学，或者把自己的进度发到网上。成就感驱动。

**Q: 阶段之间有弹性缓冲周吗？**
A: 有。每个阶段结束后留1周弹性时间，不算在计划周期内。用来补漏或休息。

---

## 附录：知识地图模板

每学完一个知识块，填写这个模板：

```
┌─────────────────────────────────────────────────────────┐
│                 知识地图：[主题]                         │
├─────────────────────────────────────────────────────────┤
│ 位置：                                                  │
│                                                         │
│ 上游：                                                  │
│  ↓                                                     │
│ 下游：                                                  │
│                                                         │
│ Web 框架应用：                                           │
│                                                         │
│ 源码对照：                                               │
│                                                         │
│ 我的理解（用自己的话写）：                                 │
│                                                         │
│ 还有什么不懂的：                                          │
└─────────────────────────────────────────────────────────┘
```
