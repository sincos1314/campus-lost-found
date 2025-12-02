# 部署到阿里云轻量应用服务器

## 前提

- 服务器公网 IP `8.163.2.139`
- 目标目录 `/home/admin/campus-lost-found`
- 放行安全组入站 `80`（HTTP），如需 HTTPS 另放行 `443`

## 连接服务器

- Windows: 使用 PowerShell 或 PuTTY 通过 SSH 登录
- SSH 示例: `ssh admin@8.163.2.139`

## 安装基础环境

- Ubuntu/Debian: `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip nginx nodejs npm`
- CentOS/Rocky: 安装等价软件包

## 拉取代码

- `sudo mkdir -p /home/admin/campus-lost-found`
- `sudo chown -R admin:admin /home/admin`
- `cd /home/admin`
- `git clone <你的仓库地址> campus-lost-found`

## 后端部署

- `cd /home/admin/campus-lost-found/backend`
- `python3 -m venv venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`
- `pip install eventlet`
- 设置 JWT 密钥（systemd 将注入）
- 创建并安装 systemd 服务:
  - 将本仓库 `deploy/campus-lost-found-backend.service` 拷贝到 `/etc/systemd/system/campus-lost-found-backend.service`
  - 修改其中 `Environment=JWT_SECRET_KEY=change_me_strong_secret` 为高强度随机值
  - `sudo systemctl daemon-reload`
  - `sudo systemctl enable campus-lost-found-backend`
  - `sudo systemctl start campus-lost-found-backend`
  - `sudo systemctl status campus-lost-found-backend` 确认运行正常
- 手动运行调试（可选）:
  - `export JWT_SECRET_KEY=<强密钥>`
  - `python app.py`

## 前端构建

- `cd /home/admin/campus-lost-found/frontend`
- `npm install`
- 根据生产环境创建 `.env.production`（已提供模板）:
  - `VITE_API_BASE=http://8.163.2.139`
  - `VITE_SOCKET_ORIGIN=http://8.163.2.139`
- `npm run build`
- 构建产物位于 `frontend/dist`

## Nginx 配置

- 将本仓库 `deploy/nginx.conf` 拷贝到 `/etc/nginx/conf.d/campus-lost-found.conf`
- 如系统默认使用 `/etc/nginx/sites-available/default`，可替换为本配置内容
- 检查配置: `sudo nginx -t`
- 重新加载: `sudo systemctl reload nginx`

## 防火墙与安全组

- 阿里云控制台放行 `80`（HTTP）或 `443`（HTTPS）
- 本机防火墙如启用 `ufw`:
  - `sudo ufw allow 80/tcp`
  - `sudo ufw allow 443/tcp`

## 访问验证

- 打开 `http://8.163.2.139`
- 注册并登录，发布失物，上传图片，查看通知
- 打开私信页面，确认 WebSocket 实时消息正常

## 启用 HTTPS（可选）

- 准备域名并解析到服务器 IP
- 安装证书工具（以 Ubuntu 为例）:
  - `sudo apt install -y certbot python3-certbot-nginx`
  - `sudo certbot --nginx -d <你的域名>`
- 前端环境改为 `https`:
  - `.env.production` 设置 `VITE_API_BASE=https://<你的域名>`
  - `.env.production` 设置 `VITE_SOCKET_ORIGIN=https://<你的域名>`
- 重新 `npm run build` 并 `reload nginx`

## 运维

- 查看后端日志: `sudo journalctl -u campus-lost-found-backend -f`
- 重启后端: `sudo systemctl restart campus-lost-found-backend`
- 备份数据库: `/home/admin/campus-lost-found/backend/lost_found.db`
