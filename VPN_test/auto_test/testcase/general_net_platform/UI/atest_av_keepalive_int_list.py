# http://106.37.95.242:48080/zentao/bug-view-28154.html
# 问题回归，双机热备可选的接口不完整

# 测试用例：
# 1. 登录https://192.168.110.244:8443/login?novc=1&type=pwd，忽略证书安全告警
# 2.class="ant-select-selection-item"选择安全管理员，type="password" 密码输入1111aac*，点击“登 录”
# 3. 在首页侧边栏点击“高可用管理”标签
#   点击“双机热备功能状态按钮”，使双机热备开启
#   点击“业务网络接口”下拉框，查看可选的网口有哪些intfs1
#   点击侧边栏的“网络配置”，点击“物理接口”，查看接口名称列表有哪些intfs2
#   对比intfs1和intfs2，intfs2里面除了eth0外都可以在intfs1里找到
