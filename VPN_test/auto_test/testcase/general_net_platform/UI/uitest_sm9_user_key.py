# import pytest
# from playwright.sync import Page
# from aw.feature.general_net_platf.pages.sm9_user_page import SM9UserPage

# @pytest.mark.ui
# def test_sm9_user_key_operations(page: Page):
#     # 初始化页面对象
#     sm9_page = SM9UserPage(page)

#     # 1. 导航到SM9用户密钥页面
#     sm9_page.navigate_to_sm9_user_key_page()

#     # 2. 点击生成密钥按钮
#     sm9_page.click_generate_key_button()

#     # 3. 填写密钥生成表单
#     sm9_page.fill_key_generation_form(
#         index_range="1-10",
#         master_key_index="1",
#         user_id="1"
#     )

#     # 4. 提交密钥生成表单
#     sm9_page.submit_key_generation()

#     # 5. 验证密钥是否生成成功
#     assert not sm9_page.is_key_table_empty(), "密钥生成失败，表格仍然为空"

#     # 6. 删除索引号为1的密钥
#     sm9_page.delete_first_key()

#     # 7. 全选并批量删除所有密钥
#     sm9_page.batch_delete_all_keys()

#     # 8. 验证所有密钥已删除
#     assert sm9_page.is_key_table_empty(), "批量删除失败，表格中仍有关键数据"

#     print("SM9用户密钥自动化测试流程执行成功！")
