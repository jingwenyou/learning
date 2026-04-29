"""
阶段1 · 第1课：闭包（Closure）

闭包三要素：
  1. 外层函数里定义了内层函数
  2. 内层函数引用了外层变量
  3. 外层函数把内层函数返回出去

核心理解：内层函数能"记住"外层函数的变量，即使外层函数已经执行结束。
"""

# ============================================================
# 1. 最简单的闭包
# ============================================================

def make_greeter(greeting):
    def greet(name):
        return f"{greeting}, {name}!"
    return greet

hello = make_greeter("你好")
hi = make_greeter("Hi")

print(hello("小明"))   # 你好, 小明!
print(hello("小红"))   # 你好, 小红!
print(hi("Tom"))       # Hi, Tom!

# hello 和 hi 是两个不同的函数对象，各自"记住"了不同的 greeting
print(hello is hi)     # False


# ============================================================
# 2. 闭包的"记忆"藏在哪里？
# ============================================================

# Python 把外层变量存在 __closure__ 里
print(hello.__closure__[0].cell_contents)  # 你好
print(hi.__closure__[0].cell_contents)     # Hi


# ============================================================
# 3. 没有引用外层变量 = 不是闭包
# ============================================================

def outer():
    x = 10
    def inner():
        return "我没用到 x"
    return inner

not_closure = outer()
print(not_closure.__closure__)  # None —— 没有闭包


# ============================================================
# 4. 实用例子：计数器
# ============================================================

def make_counter(start=0):
    count = [start]  # 用列表包一层，因为内层函数不能直接修改外层的不可变变量
    def counter():
        count[0] += 1
        return count[0]
    return counter

c = make_counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3

# 用 nonlocal 可以直接修改外层变量（Python 3）
def make_counter_v2(start=0):
    count = start
    def counter():
        nonlocal count  # 声明：count 是外层的变量，不是新建的局部变量
        count += 1
        return count
    return counter

c2 = make_counter_v2(10)
print(c2())  # 11
print(c2())  # 12


# ============================================================
# 5. 闭包的经典坑：循环变量陷阱
# ============================================================

# 错误写法
funcs_bad = []
for i in range(3):
    funcs_bad.append(lambda: i)  # 所有 lambda 引用的是同一个 i

print([f() for f in funcs_bad])  # [2, 2, 2] —— 全是 2！因为循环结束后 i=2

# 正确写法：用默认参数"拍快照"
funcs_good = []
for i in range(3):
    funcs_good.append(lambda x=i: x)  # x=i 在创建时就确定了值

print([f() for f in funcs_good])  # [0, 1, 2]


# ============================================================
# 6. 为什么要学闭包？—— 装饰器的前置知识
# ============================================================

# 装饰器本质上就是：闭包 + 把函数当参数传进去
# 下面是一个最简单的装饰器雏形（下节课展开讲）

def simple_log(func):           # 接收一个函数
    def wrapper(*args, **kwargs):
        print(f"调用了 {func.__name__}")
        return func(*args, **kwargs)   # 调用原函数
    return wrapper              # 返回新函数

@simple_log
def add(a, b):
    return a + b

print(add(1, 2))  # 先打印"调用了 add"，再打印 3


# ============================================================
# 练习题
# ============================================================

"""
练习1：写一个 make_multiplier(n)，返回一个函数，这个函数接收 x 并返回 x * n
  double = make_multiplier(2)
  triple = make_multiplier(3)
  print(double(5))   # 10
  print(triple(5))   # 15

练习2：写一个 make_accumulator(init)，返回一个函数，每次调用加上传入的值并返回累计值
  acc = make_accumulator(100)
  print(acc(10))   # 110
  print(acc(20))   # 130
  print(acc(5))    # 135

练习3：解释下面代码的输出，并说明为什么
  def outer():
      x = 1
      def inner():
          print(x)
      x = 2
      return inner
  outer()()   # 输出什么？为什么？
"""
