import json
import os
import re
import sys
from typing import Any, Dict, Literal, Optional, Union

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append(os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])
sys.path.append(r'd:/learning/python/auto_test')

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from aw.common.log_util import LogUtil
from aw.common.text_util import *

log_util = LogUtil()

# 常量定义
MAX_BINARY_PREVIEW = 30
MAX_TEXT_PREVIEW = 200
DEFAULT_TIMEOUT = 30


class CustomSession(requests.Session):
    """自定义会话类，继承requests.Session并重写request方法"""

    def __init__(self):
        super().__init__()
        self.verify = False
        # 禁用代理，避免代理连接问题
        self.proxies = {
            'http': None,
            'https': None
        }
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总重试次数
            backoff_factor=1,  # 重试间隔时间因子
            status_forcelist=[500, 502, 503, 504],  # 需要重试的状态码
            allowed_methods=["GET", "POST"],  # 允许重试的请求方法
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        # 挂载适配器到HTTP和HTTPS协议
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def _format_data_for_log(self, data):
        """格式化数据用于日志记录，避免记录过长的数据"""
        if isinstance(data, bytes):
            # 对于二进制数据，只记录长度和前N个字节的十六进制表示
            data_len = len(data)
            preview = data[:MAX_BINARY_PREVIEW].hex() if data_len > MAX_BINARY_PREVIEW else data.hex()
            return f'binary, len={data_len}, preview={preview}...'
        else:
            # 对于其他类型数据，限制日志长度
            data_str = str(data)
            if len(data_str) > MAX_TEXT_PREVIEW:
                # 对于长文本，只记录前N个字符和长度
                return f'text, len={len(data_str)}, preview={data_str[:MAX_TEXT_PREVIEW]}...'
            return data_str

    def _build_request_log(self, method, url, **kwargs):
        """构建请求日志文本"""
        log_parts = [f'url:{url}.\t method:{method}.']

        # 按顺序记录各个参数
        params_to_log = [
            ('params', kwargs.get('params')),
            ('data', kwargs.get('data')),
            ('headers', kwargs.get('headers')),
            ('cookies', kwargs.get('cookies')),
            ('files', kwargs.get('files')),
            ('auth', kwargs.get('auth')),
            ('json', kwargs.get('json')),
        ]

        for param_name, param_value in params_to_log:
            if param_value is not None:
                if param_name == 'data':
                    formatted_data = self._format_data_for_log(param_value)
                    log_parts.append(f'\t{param_name}: {formatted_data}')
                elif param_name == 'stream' and param_value:
                    log_parts.append(f'\tstream: {str(param_value)[:50]}')
                else:
                    log_parts.append(f'\t{param_name}: {str(param_value)}')

        return '\n'.join(log_parts)

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=DEFAULT_TIMEOUT,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        stream=None,
        verify=False,
        cert=None,
        json=None,
    ) -> requests.Response:
        """
        重写request方法，在请求前后添加日志记录
        """
        # 构建并记录请求前日志
        request_log = self._build_request_log(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            stream=stream,
            json=json,
        )
        log_util.info(request_log)

        # 调用父类（requests.Session）的request方法
        try:
            resp = super().request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=True,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify,
                cert=cert,
                json=json,
            )

            # 记录响应状态码
            log_util.info(f'status_code: {resp.status_code}')

            # 记录响应内容
            try:
                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    # 尝试解析JSON响应
                    try:
                        response_json = resp.json()
                        log_util.info(response_json)
                    except json.JSONDecodeError:
                        # JSON解析失败，记录原始内容
                        content_preview = self._format_data_for_log(resp.content)
                        log_util.warning(f'响应头表示为JSON，但解析失败，原始内容: {content_preview}')
                else:
                    # 对于非JSON响应，限制日志长度
                    content_preview = self._format_data_for_log(resp.content)
                    log_util.info(f'{content_preview}')
            except Exception as e:
                log_util.error(f'记录响应内容时出错: {e}')

            return resp
        except requests.exceptions.RequestException as e:
            log_util.error(f'请求失败: {e}')
            raise


class Request_tools(CustomSession):
    """HTTP请求工具类，提供便捷的API测试方法"""

    # 请求匹配类型常量
    MATCH_KEY = 'key'
    MATCH_CONTENT = 'content'
    MATCH_ALL = 'all'

    def __init__(self, base_url=''):
        """初始化请求工具类

        Args:
            base_url: 基础URL，用于拼接endpoint
        """
        super().__init__()  # 调用父类初始化
        self.headers: Dict[str, str] = {}  # 存储默认请求头
        self.base_url = base_url

    def get_request_info(
        self,
        endpoint: str,
        match: str = MATCH_KEY,
        method: str = 'get',
        keyword: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        payloads: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        verify: Optional[bool] = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> Union[requests.Response, str, bool, Any]:
        """
        发送HTTP请求并根据指定的匹配方式处理响应

        Args:
            endpoint: API端点路径
            match: 匹配方式，可选值：'key'(获取JSON中指定key的值)、'content'(获取响应文本)、'all'(返回完整响应对象)
            method: 请求方法，默认为'get'
            keyword: 当match为'key'时，用于获取对应的值
            headers: 请求头，将与默认请求头合并
            payloads: POST请求的JSON数据
            params: URL查询参数
            verify: 是否验证SSL证书，默认为None（使用session默认值）
            timeout: 请求超时时间，默认30秒
            **kwargs: 其他传递给request方法的参数

        Returns:
            响应对象、文本内容、指定key的值或布尔值
        """
        url = self.base_url + endpoint
        final_headers = self.headers.copy()
        if headers:
            final_headers.update(headers)

        try:
            # 统一处理GET和POST请求
            if method.lower() == 'get':
                resp = self.get(url, headers=final_headers, params=params, verify=verify, timeout=timeout, **kwargs)
            else:
                resp = self.post(
                    url, headers=final_headers, json=payloads, params=params, verify=verify, timeout=timeout, **kwargs
                )

            # 根据匹配类型返回不同结果
            if match == self.MATCH_ALL:
                return resp

            if resp.status_code == 200:
                if match == self.MATCH_KEY:
                    try:
                        response_json = resp.json()
                        return response_json.get('data', {}).get(keyword)
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        log_util.error(f'解析JSON响应时出错: {e}')
                        return False
                elif match == self.MATCH_CONTENT:
                    return resp.text
                else:
                    return True

            log_util.warning(f'请求返回非200状态码: {resp.status_code}')
            return False

        except requests.exceptions.RequestException as e:
            log_util.error(f"请求失败: {e}")
            return False

    # 国密证书相关功能（建议在未来版本中移到单独的模块，如cert_util.py）
    def _download_binary_file(
        self,
        url: str,
        description: str,
        min_length: int = 100,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Optional[bytes]:
        """
        通用的二进制文件下载方法，减少重复代码

        Args:
            url: 下载URL
            description: 文件描述，用于日志
            min_length: 判断文件是否有效的最小长度
            headers: 请求头
            stream: 是否使用流式下载

        Returns:
            文件内容字节数据，下载失败返回None
        """
        try:
            response = self.get(url, headers=headers, stream=stream, verify=False)

            if response.status_code == 200 and len(response.content) > min_length:
                log_util.info(f'{description}:')
                # 使用通用的二进制数据日志格式化方法
                data_len = len(response.content)
                preview = (
                    response.content[:MAX_BINARY_PREVIEW].hex()
                    if data_len > MAX_BINARY_PREVIEW
                    else response.content.hex()
                )
                log_util.info(f'binary data, len={data_len}, preview={preview}...')
                return response.content

            log_util.warning(f'{description}下载失败: 状态码{response.status_code} 或 内容长度不足')
            return None

        except Exception as e:
            log_util.error(f'{description}下载异常: {e}')
            return None

    def get_gmcert_chain(self, cert_type: Literal[0, 1, 2, 3], alg: Literal['SM2', 'ECC', 'RSA']) -> Optional[bytes]:
        """
        获取国密证书实验室里的证书链

        Args:
            cert_type: 证书类型，0:根证书, 1:中间证书, 2:pem格式根+中间证书, 3:pkc#7格式根+中间证书
            alg: 证书算法类型，支持'SM2'/'ECC'/'RSA'三种类型

        Returns:
            证书链的二进制数据，失败返回None
        """
        # 根据参数动态构建下载URL
        download_url = f"https://www.gmcrt.cn/gmcrt/Tool_Misc_Crt?CMD=Trust&Type={cert_type}&Alg={alg}"

        # 配置请求头
        headers = {
            "Cookie": "Hm_lvt_c01e2f6d5309271f7891bcf9b28b4505=1775031205; HMACCOUNT=A126F93D16880DE2; JSESSIONID=4DCD35CED10AD47942CF75F51A932C03; Hm_lpvt_c01e2f6d5309271f7891bcf9b28b4505=1775031902",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Referer": "https://www.gmcrt.cn/gmcrt/CA_Cert_CA.jsp",
        }

        return self._download_binary_file(
            url=download_url, description='国密证书实验室下载证书链', min_length=100, headers=headers, stream=True
        )

    def get_gmcert_crl(self, crl_type: Literal['sm2', 'ecc', 'rsa']) -> Optional[bytes]:
        """
        获取国密证书实验室里的CRL

        Args:
            crl_type: CRL类型，'sm2'/'ecc'/'rsa'

        Returns:
            CRL的二进制数据，失败返回None
        """
        # 根据参数动态构建下载URL
        download_url = f"https://www.gmcrt.cn/{crl_type}.crl"

        return self._download_binary_file(url=download_url, description='国密证书实验室下载CRL', min_length=40)


if __name__ == '__main__':
    req = Request_tools()
    crl_content = req.get_gmcert_crl(crl_type='sm2')
    assert crl_content, '获取crl失败'
    # context=ssl.SSLContext(ssl.PROTOCOL_TLS)
    # context.set_ciphers('ECDHE-SM2-WITH-SMS4-SM3')
    # url='https://192.168.110.99:10000/cgi-bin/luci/'
    # response = requests.get(url, verify=False)
    # print(response)
