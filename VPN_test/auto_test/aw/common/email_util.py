import os
import smtplib
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.append(os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])
from common.exception_utils import *
from common.text_util import base_dir


# @exception_utils
def email_util(username, password, receiver, att=None, content=None, subject=None):
    """_summary_
        发邮件的方法
    Args:
        username (_type_): _description_ 邮件发送人用户名
        password (_type_): _description_ 邮件发送人密码
        receiver (_type_): _description_ 邮件接收人
        att (_type_, optional): _description_. Defaults to None. 附件
        content (_type_, optional): _description_. Defaults to None. 邮件内容
        subject (_type_, optional): _description_. Defaults to None. 邮件主题
    """
    content = content

    if att is None:  # 不带附件的
        message = MIMEText(content)
        message['subject'] = subject
        message['from'] = username
        message['to'] = receiver
    else:  # 带附件发送
        message = MIMEMultipart()
        txt = MIMEText(content, _charset='utf-8', _subtype="html")
        part = MIMEApplication(open('%s/%s' % (base_dir, att), 'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=att.split('\\')[-1])
        message['subject'] = subject
        message['from'] = username
        message['to'] = receiver
        message.attach(txt)
        message.attach(part)

    # 登录smtp服务器
    smtpserver = 'smtp.exmail.qq.com'
    smtp = smtplib.SMTP_SSL(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(username, receiver, message.as_string())
    smtp.quit()


# if __name__ == '__main__':
#     email_util(content="<i>测试发送邮件</i>", subject="测试发送邮件-主题", att='output/run_result_excel/运行结果_20221216_12_05_47.xlsx')
