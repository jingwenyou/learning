import sys
sys.path.append(r'/root/AI/VPN_test/auto_test')

from aw.feature.general_net_platf.pages.login_page import LoginPage

CAPTCHA_OLD = (
    'getCaptchaCode();return a.toLowerCase()===t.toLowerCase()'
    '?Promise.resolve():(d.value.refresh(),Promise.reject'
    '(new Error(o("views.login.errorVerCode"))))'
)
CAPTCHA_NEW = 'getCaptchaCode();return Promise.resolve()'


class VpnHomePage(LoginPage):
    """VPN安全网关(8443端口)主页及菜单导航"""

    def login(self, username: str, password: str) -> None:
        """VPN网关登录：用Ant Design Select方式选角色，更健壮"""
        three_admins_dk = {'安全管理员': 'security', '系统管理员': 'system', '审计管理员': 'audit'}

        # 确保验证码绕过已设置（幂等，重复添加无副作用）
        try:
            ctx = self.page.context
            ctx.route('**/login-password*.js', self._patch_captcha_route)
        except Exception:
            pass

        # 等待登录表单渲染完成
        self.page.wait_for_selector('.ant-select-selector', timeout=20000)
        self.page.wait_for_timeout(300)

        # 用 Ant Design Select 方式选角色
        self._select_role_antd(username)

        # 填密码和验证码
        self.page.get_by_label('密码').fill(password)
        self.page.locator('#normal_login_vercode').fill('bypass')
        self.page.wait_for_timeout(200)

        # 点击登录
        self.page.get_by_role('button', name='登 录').click()

        # 等待登录成功（dashboard出现角色名）
        user_key = three_admins_dk.get(username, 'security')
        self.page.wait_for_selector(f'text={user_key}', timeout=30000)

    def _patch_captcha_route(self, route):
        try:
            resp = route.fetch(timeout=10000)
            body = resp.body().decode('utf-8')
            body = body.replace(CAPTCHA_OLD, CAPTCHA_NEW)
            route.fulfill(response=resp, body=body,
                          headers={**resp.headers, 'content-type': 'application/javascript'})
        except Exception:
            route.continue_()

    def _select_role_antd(self, username: str) -> None:
        """通过Ant Design Select组件选择角色"""
        # 点击 select 打开下拉
        self.page.locator('.ant-select-selector').first.click()
        self.page.wait_for_timeout(400)
        # 点击对应选项
        self.page.locator(f'.ant-select-item-option-content:text-is("{username}")').click(timeout=5000)
        self.page.wait_for_timeout(200)

    def click_ssl(self, sub_menu: str = None) -> None:
        """点击 SSL服务 及子菜单（限定在SSL父菜单popup内避免与IPSec重名冲突）"""
        self.page.get_by_text('SSL服务', exact=True).click()
        if sub_menu:
            self.page.wait_for_timeout(300)
            # SSL子菜单在 vpnServer-ssl-popup 容器内
            ssl_popup = self.page.locator('[id*="vpnServer-ssl-popup"]')
            if ssl_popup.count() > 0:
                ssl_popup.get_by_text(sub_menu, exact=True).click()
            else:
                self.page.get_by_text(sub_menu, exact=True).first.click()

    def click_ipsec(self, sub_menu: str = None) -> None:
        """点击 IPSec服务 及子菜单（限定在ipsec-popup容器内避免与SSL重名冲突）"""
        self.page.get_by_text('IPSec服务', exact=True).click()
        if sub_menu:
            self.page.wait_for_timeout(300)
            # IPSec子菜单在 ipsec-popup 容器内
            ipsec_popup = self.page.locator('[id*="ipsec-popup"]')
            if ipsec_popup.count() > 0:
                ipsec_popup.get_by_text(sub_menu, exact=True).click()
            else:
                self.page.get_by_text(sub_menu, exact=True).last.click()

    def click_network(self, sub_menu: str = None) -> None:
        """点击 网络配置 及子菜单"""
        self.page.get_by_text('网络配置', exact=True).click()
        if sub_menu:
            self.page.get_by_text(sub_menu, exact=True).click()

    def click_firewall(self) -> None:
        self.page.get_by_text('防火墙', exact=True).click()

    def click_log(self, sub_menu: str = None) -> None:
        """点击 日志管理 及子菜单（限定在log-popup容器内）"""
        self.page.get_by_text('日志管理', exact=True).click()
        if sub_menu:
            self.page.wait_for_timeout(300)
            log_popup = self.page.locator('[id*="log-popup"]')
            if log_popup.count() > 0:
                log_popup.get_by_text(sub_menu, exact=True).click()
            else:
                self.page.get_by_text(sub_menu, exact=True).first.click()

    def click_maintenance(self, sub_menu: str = None) -> None:
        """点击 系统维护 及子菜单（限定在sub_menu_4-popup容器内）"""
        self.page.get_by_text('系统维护', exact=True).click()
        if sub_menu:
            self.page.wait_for_timeout(300)
            # 系统维护子菜单在 sub_menu_4-popup 容器内
            mnt_popup = self.page.locator('[id*="sub_menu_4-popup"]')
            if mnt_popup.count() > 0:
                mnt_popup.get_by_text(sub_menu, exact=True).click()
            else:
                self.page.get_by_text(sub_menu, exact=True).first.click()

    def get_menu_items(self) -> list:
        """返回当前用户可见的所有菜单项文本"""
        self.page.wait_for_selector('.ant-menu', timeout=5000)
        items = self.page.locator('.ant-menu-item, .ant-menu-submenu-title').all()
        return [i.text_content().strip() for i in items if i.text_content().strip()]

    def logout(self) -> None:
        """退出登录（先关闭可能打开的modal，再点击退出）"""
        # 关闭可能打开的modal/drawer
        try:
            self.page.keyboard.press('Escape')
            self.page.wait_for_timeout(300)
        except Exception:
            pass
        self.page.get_by_label('logout').locator('path').click()
        self.page.get_by_role('button', name='确 认').click()
        self.page.wait_for_timeout(1500)

    def get_dashboard_info(self) -> dict:
        """获取首页仪表盘信息"""
        info = {}
        try:
            content = self.page.locator('.ant-layout-content').text_content(timeout=5000)
            import re
            for key, pattern in [
                ('product_model', r'产品型号(\S+)'),
                ('serial_no', r'产品序列号(\S+)'),
                ('version', r'产品版本(\S+)'),
                ('ssl_connections', r'SSL并发连接数([\d.]+%)'),
                ('cpu', r'CPU状态([\d.]+%)'),
                ('memory', r'内存状态\(([^)]+)\)'),
                ('disk', r'磁盘状态\(([^)]+)\)'),
            ]:
                m = re.search(pattern, content)
                if m:
                    info[key] = m.group(1)
        except Exception:
            pass
        return info
