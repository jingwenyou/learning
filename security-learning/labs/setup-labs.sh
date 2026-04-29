#!/bin/bash
# 安全测试靶场一键部署脚本
# 使用前确保已安装Docker和docker-compose

set -e

echo "=========================================="
echo "  安全测试靶场部署脚本"
echo "=========================================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "[!] Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com | sh
    echo "[✓] Docker安装完成"
fi

echo ""
echo "[1/3] 部署DVWA（最常用的Web安全靶场）..."
echo "  访问地址：http://localhost:8081"
echo "  默认账号：admin / password"
docker rm -f dvwa 2>/dev/null || true
docker run -d \
  --name dvwa \
  -p 8081:80 \
  --restart unless-stopped \
  vulnerables/web-dvwa
echo "[✓] DVWA部署完成"

echo ""
echo "[2/3] 部署WebGoat（OWASP官方教学靶场）..."
echo "  访问地址：http://localhost:8082/WebGoat"
echo "  首次访问需注册账号"
docker rm -f webgoat 2>/dev/null || true
docker run -d \
  --name webgoat \
  -p 8082:8080 \
  -p 9090:9090 \
  --restart unless-stopped \
  webgoat/webgoat
echo "[✓] WebGoat部署完成"

echo ""
echo "[3/3] 部署Pikachu（中文靶场）..."
echo "  访问地址：http://localhost:8083"
docker rm -f pikachu 2>/dev/null || true
docker run -d \
  --name pikachu \
  -p 8083:80 \
  --restart unless-stopped \
  area39/pikachu
echo "[✓] Pikachu部署完成"

echo ""
echo "=========================================="
echo "  部署完成！靶场列表："
echo "=========================================="
echo ""
echo "  DVWA:     http://localhost:8081"
echo "            首次访问点击 'Create / Reset Database'"
echo "            账号: admin / password"
echo "            设置安全等级: DVWA Security → Low"
echo ""
echo "  WebGoat:  http://localhost:8082/WebGoat"
echo "            首次需要注册账号"
echo ""
echo "  Pikachu:  http://localhost:8083"
echo "            点击初始化安装"
echo ""
echo "  在线靶场（无需部署）:"
echo "  PortSwigger Academy: https://portswigger.net/web-security"
echo ""
echo "=========================================="
echo "  管理命令："
echo "=========================================="
echo "  查看运行状态: docker ps"
echo "  停止所有靶场: docker stop dvwa webgoat pikachu"
echo "  启动所有靶场: docker start dvwa webgoat pikachu"
echo "  删除所有靶场: docker rm -f dvwa webgoat pikachu"
echo ""
echo "  ⚠️  靶场仅用于学习目的，不要暴露在公网！"
