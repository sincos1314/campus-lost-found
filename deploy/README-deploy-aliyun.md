# 阿里云服务器部署指南

## 前提信息

- 公网 IP: 8.163.2.139

## 安全组与端口

- 在阿里云控制台为该实例安全组放行 `80` 与 `443` 入站
- 若暂不启用 HTTPS，可先放行 `80`

## 服务器基础环境

- SSH 登录 `ssh <用户名>@8.163.2.139`
- 更新并安装依赖
  - Ubuntu/Debian: `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip nginx nodejs npm`
  - CentOS/RHEL: `sudo yum install -y git python3 python3-venv python3-pip nginx nodejs npm`

## 拉取项目与目录

- `sudo mkdir -p /opt/lost-found-system`
- 将项目代码复制或 `git clone` 到 `/opt/lost-found-system`

## 后端运行

- 进入 `/opt/lost-found-system`
- 执行 `bash deploy/run_backend.sh`
- 该脚本会创建虚拟环境、安装依赖并启动后端监听 `0.0.0.0:5000`
- 如需后台常驻，使用 systemd
  - `sudo cp deploy/backend.service /etc/systemd/system/backend.service`
  - `sudo systemctl daemon-reload`
  - `sudo systemctl enable backend`
  - `sudo systemctl start backend`
  - 状态检查 `sudo systemctl status backend`

## 前端构建

- 在 `/opt/lost-found-system/frontend` 设置生产环境变量
  - `.env.production` 已生成，默认：
    - `VITE_API_BASE=http://8.163.2.139`
    - `VITE_SOCKET_ORIGIN=http://8.163.2.139`
- 构建前端
  - `npm ci`
  - `npm run build`
  - 生成的 `dist` 目录位于 `frontend/dist`

## Nginx 反向代理与静态托管

- 将 `deploy/nginx.conf` 安装到 Nginx
  - `sudo cp deploy/nginx.conf /etc/nginx/sites-available/lost-found`
  - `sudo ln -s /etc/nginx/sites-available/lost-found /etc/nginx/sites-enabled/lost-found`
  - 如为 CentOS，直接替换 `/etc/nginx/conf.d/lost-found.conf`
- 测试并重载 Nginx
  - `sudo nginx -t`
  - `sudo systemctl restart nginx`
- 访问 `http://8.163.2.139`

## HTTPS（可选但推荐）

- 安装 `certbot`，申请证书并配置到 Nginx 的 `443` 服务器块
- 将前端 `.env.production` 中地址改为 `https://你的域名`

## 日志与排查

- 后端日志：`journalctl -u backend -f`
- Nginx 访问日志：`/var/log/nginx/access.log`
- Nginx 错误日志：`/var/log/nginx/error.log`

## 验证清单

- 首页、登录、列表、详情均可访问
- 图片与头像加载正常
- 私信与图片发送正常，Socket 实时连接正常
- 管理员页面各模块可正常访问与操作
- 举报上传与证据预览正常

## 维护与更新

- 更新代码后端：`sudo systemctl restart backend`
- 更新前端：在 `frontend` 重新构建并刷新 Nginx 静态内容
