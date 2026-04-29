FROM python:3.12-slim

LABEL maintainer="ops@example.com"
LABEL description="Smart Ops CLI Performance Monitor"

# 安装必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -s /bin/bash ops

# 复制应用
COPY dist/smart-ops-x86_64 /usr/local/bin/smart-ops

# 权限设置
RUN chown ops:ops /usr/local/bin/smart-ops && \
    chmod 500 /usr/local/bin/smart-ops

# 创建数据目录
RUN mkdir -p /home/ops/data && \
    chown ops:ops /home/ops/data

# 切换到非root用户
USER ops
WORKDIR /home/ops

# 默认命令
ENTRYPOINT ["/usr/local/bin/smart-ops"]
CMD ["--help"]