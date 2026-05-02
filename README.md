# UniFind 校园寻宝

> 一个面向校园用户的失物招领系统，支持失物/拾物发布、收藏与认领、物品评论、实时私信、举报管理和管理员申请审核等功能。

![Vue](https://img.shields.io/badge/Vue-3.5.22-4FC08D?logo=vue.js)
![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?logo=flask)
![Element Plus](https://img.shields.io/badge/Element%20Plus-2.11.7-409EFF?logo=element)

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
  - [后端部署](#后端部署)
  - [前端部署](#前端部署)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [开发说明](#开发说明)

---

## 📖 项目简介

**UniFind 校园寻宝** 是一个完整的校园失物招领平台，旨在帮助校园用户快速发布和查找失物信息。系统支持用户注册登录、物品发布与管理、收藏与认领、物品评论、实时私信、举报处理、隐私设置、管理员申请审核及管理后台等完整功能。

### 核心特点

- 🎯 **简单易用**：界面简洁美观，操作流程清晰
- 🔒 **安全可靠**：JWT 认证、权限管理、数据加密
- 💬 **实时沟通**：基于 WebSocket 的实时私信功能
- 📱 **响应式设计**：支持多种设备访问
- 🌓 **主题切换**：支持明暗主题切换

---

## ✨ 功能特性

### 👤 用户功能

#### 账号管理
- ✅ 普通用户注册（新用户统一为普通用户）
- ✅ 登录/退出登录
- ✅ 忘记密码重置功能
- ✅ 个人资料管理（头像、邮箱、手机号、院系、年级、班级、学号、性别）
- ✅ 头像上传（支持 jpg、png、gif 等格式，单张 ≤ 10MB）
- ✅ 个人中心申请管理员，支持审核中/拒绝冷却/撤销冷却等状态提示

#### 物品发布与管理
- ✅ 发布失物/拾物信息
  - 支持多图上传（最多 8 张，第一张作为主图）
  - 支持 Ctrl/Shift 多选图片
  - 包含标题、描述、类型、地点、日期、联系人等信息
- ✅ 物品列表浏览
  - 按类型筛选（失物/拾物）
  - 按状态筛选（进行中/已解决）
  - 关键词搜索
  - 日期范围筛选
  - 服务端分页
- ✅ 物品详情查看
  - 完整信息展示
  - 图片预览（支持放大缩小）
  - 时间线展示
- ✅ 我的发布管理
  - 修改已发布信息
  - 更换/删除图片
  - 标记已解决
  - 删除发布

#### 收藏与认领
- ✅ 收藏物品（我的收藏）
- ✅ 对拾物发起认领申请
- ✅ 我的认领记录（待处理/已批准/已拒绝）
- ✅ 认领管理（发布者处理他人认领申请）

#### 物品评论
- ✅ 在物品详情页发表评论
- ✅ 支持回复评论（二级回复）
- ✅ 评论点赞

#### 私信功能
- ✅ 实时私信沟通（基于 WebSocket）
- ✅ 文本消息发送
- ✅ 图片消息发送（支持预览）
- ✅ 已读状态显示
- ✅ 正在输入提示
- ✅ 消息撤回功能

#### 通知与隐私
- ✅ 消息与认领等通知提醒
- ✅ 隐私设置：发布历史可见性（隐藏/部分隐藏/不隐藏）、可见名单、查看他人发布历史（遵循隐私规则）

#### 举报功能
- ✅ 物品举报（支持匿名举报）
- ✅ 举报类别选择（垃圾信息/骚扰或辱骂/虚假信息/其他）
- ✅ 严重级别设置（低/中/高）
- ✅ 证据图片上传
- ✅ 举报管理（查看、修改、撤回）

### 👨‍💼 管理员功能

#### 权限等级
- 🔴 **高级管理员**（唯一）：拥有所有管理权限，可审核管理员申请、直接任命管理员、撤销管理员身份
- 🟡 **管理员**：拥有用户、物品、举报、统计和数据导出等常规管理权限
- ⚪ **普通用户**：可发布、认领、收藏、评论、举报和申请管理员

#### 管理功能
- ✅ 用户管理
  - 查看用户列表
  - 封禁/解封用户
  - 高级管理员可直接任命管理员、撤销管理员身份
  - 创建/删除用户
- ✅ 物品管理
  - 查看所有物品
  - 标记物品状态
  - 删除物品
- ✅ 举报处理
  - 查看举报列表
  - 查看证据图片
  - 处理举报（删除物品、封禁用户）
  - 设置处理状态和备注
- ✅ 数据统计
  - 用户总数
  - 物品总数
  - 失物/拾物数量统计
  - 已解决数量
  - 未处理举报数量
- ✅ 管理员申请审核（通过/拒绝待审核申请，可查看历史）
- ✅ 数据导出（Excel）

---

## 🛠 技术栈

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.22 | 渐进式 JavaScript 框架 |
| Element Plus | 2.11.7 | Vue 3 组件库 |
| Vue Router | 4.6.3 | 官方路由管理器 |
| Axios | 1.13.2 | HTTP 客户端 |
| Socket.IO Client | 4.8.1 | WebSocket 客户端 |
| Vite | 7.1.11 | 前端构建工具 |

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Flask | 3.0.0 | Python Web 框架 |
| SQLAlchemy | 3.1.1 | ORM 数据库工具 |
| Flask-JWT-Extended | 4.5.3 | JWT 认证 |
| Flask-SocketIO | 5.3.5 | WebSocket 支持 |
| Flask-CORS | 4.0.0 | 跨域资源共享 |
| Pillow | 10.1.0 | 图像处理库 |
| openpyxl | 3.1.2 | Excel 导出 |
| SQLite | - | 轻量级数据库 |

---

## 💻 环境要求

在开始之前，请确保您的开发环境满足以下要求：

### 必需软件

1. **Node.js**
   - 版本要求：`^20.19.0` 或 `>=22.12.0`
   - 下载地址：https://nodejs.org/
   - 验证安装：打开命令行，输入 `node -v`，应显示版本号

2. **Python**
   - 版本要求：`>= 3.10`
   - 下载地址：https://www.python.org/
   - 验证安装：打开命令行，输入 `python --version`，应显示版本号

3. **npm**（通常随 Node.js 一起安装）
   - 验证安装：打开命令行，输入 `npm -v`，应显示版本号

### 推荐工具

- **Git**：用于版本控制
- **VS Code** 或 **Cursor**：代码编辑器
- **Chrome/Edge**：现代浏览器

---

## 🚀 快速开始

### 第一步：克隆项目

```bash
# 使用 Git 克隆项目（如果有 Git 仓库）
git clone https://github.com/sincos1314/campus-lost-found.git

# 或者直接下载 ZIP 文件并解压
```

### 第二步：后端部署

#### 1. 进入后端目录

```bash
cd backend
```

#### 2. 创建虚拟环境（推荐）

**Windows 系统：**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

**macOS/Linux 系统：**

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

> 💡 **提示**：激活虚拟环境后，命令行前面会显示 `(venv)` 标识

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

> ⚠️ **注意**：如果下载速度慢，可以使用国内镜像源：
> ```bash
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

#### 4. 初始化数据库

首次运行会自动创建数据库文件 `lost_found.db`，无需手动创建。

#### 5. 启动后端服务

```bash
python app.py
```

看到以下信息表示启动成功：

```
 * Running on http://127.0.0.1:5000
```

> 📌 **默认地址**：`http://localhost:5000`
> 
> ⚠️ **注意**：请保持此命令行窗口打开，关闭窗口会停止后端服务

### 第三步：前端部署

#### 1. 打开新的命令行窗口

保持后端服务运行，打开一个新的命令行窗口。

#### 2. 进入前端目录

```bash
cd frontend
```

#### 3. 安装依赖

```bash
npm install
```

> ⚠️ **注意**：如果下载速度慢，可以使用国内镜像源：
> ```bash
> npm install --registry=https://registry.npmmirror.com
> ```

#### 4. 启动开发服务器

```bash
npm run dev
```

看到以下信息表示启动成功：

```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

> 📌 **默认地址**：`http://localhost:5173`

### 第四步：访问系统

1. 打开浏览器（推荐 Chrome 或 Edge）
2. 访问：`http://localhost:5173`
3. 您应该能看到 UniFind 校园寻宝的首页

---

## 📚 使用指南

### 首次使用

#### 1. 注册账号

- 点击页面右上角"注册"按钮
- 填写用户名、密码、邮箱等信息
- 填写院系、年级、班级、学号、性别
- 点击"注册"完成

#### 2. 登录系统

- 使用注册的用户名和密码登录
- 忘记密码可点击"忘记密码"进行重置

#### 3. 发布信息

- 点击导航栏"发布信息"
- 选择信息类型（失物/拾物）
- 填写物品信息
- **上传图片**：
  - 点击上传区域
  - 可按住 **Ctrl** 键多选图片
  - 可按住 **Shift** 键选择连续图片
  - 最多上传 8 张，第一张作为主图
- 点击"提交发布"

#### 4. 浏览物品

- **失物广场**：查看所有失物信息
- **拾物广场**：查看所有拾物信息
- 使用筛选和搜索功能快速找到目标物品

#### 5. 收藏与认领

- **收藏**：在物品详情页可收藏物品，在「我的收藏」中查看
- **认领**：对拾物可发起认领申请，在「我的认领记录」查看状态；发布者可在「认领管理」中处理申请

#### 6. 私信沟通

- 在物品详情页点击"联系发布者"
- 或进入"私信"页面查看所有会话
- 支持发送文本和图片消息
- 实时接收消息通知

### 管理员使用

#### 设置管理员

首次使用需要设置高级管理员，推荐使用项目自带脚本（需先激活后端虚拟环境并进入 `backend` 目录）：

**方法一：使用 create_admin.py 脚本（推荐）**

```bash
cd backend
source venv/bin/activate   # Windows: venv\Scripts\activate

# 创建新的高级管理员账户
python create_admin.py --username admin --email admin@example.com --password your_password

# 查看所有管理员
python create_admin.py --list
```

> 高级管理员全系统唯一，业务层不提供创建第二个高级管理员或转让高级管理员的入口。普通用户可在个人中心提交管理员申请，由高级管理员审核。

#### 管理员功能

- 管理员登录后，导航栏会显示"数据看板"入口
- 进入管理员界面可以：
  - 管理用户（封禁、任命管理员等）
  - 管理物品（删除、标记状态等）
  - 处理举报（查看证据、删除物品、封禁用户等）
  - 查看统计数据
  - 高级管理员可审核管理员申请、直接任命管理员、撤销管理员身份

---

## 📁 项目结构

```
campus-lost-found/
│
├── backend/                    # 后端代码目录
│   ├── app.py                  # Flask 主应用文件
│   ├── requirements.txt        # Python 依赖列表
│   ├── create_admin.py         # 初始化唯一高级管理员脚本
│   ├── migrate_admin_roles.py  # 管理员角色与教师字段历史迁移脚本
│   ├── create_test_items.py    # 生成测试物品数据脚本
│   ├── lost_found.db           # SQLite 数据库（运行后自动生成）
│   └── uploads/                # 上传文件存储目录（自动创建）
│       ├── avatars/            # 用户头像
│       ├── items/              # 物品图片
│       ├── messages/           # 私信图片
│       └── reports/            # 举报证据图片
│
├── frontend/                   # 前端代码目录
│   ├── public/                 # 静态资源
│   │   └── favicon.png         # 网站图标
│   ├── src/                    # 源代码目录
│   │   ├── assets/             # 资源文件
│   │   │   └── main.css        # 主样式文件
│   │   ├── components/         # Vue 组件
│   │   │   └── ReportDialog.vue # 举报对话框组件
│   │   ├── router/             # 路由配置
│   │   │   └── index.js        # 路由定义
│   │   ├── utils/              # 工具函数
│   │   │   ├── auth.js         # 认证相关
│   │   │   └── request.js      # HTTP 请求封装
│   │   ├── views/          # 页面视图
│   │   │   ├── HomeView.vue        # 首页
│   │   │   ├── LoginView.vue       # 登录页
│   │   │   ├── RegisterView.vue   # 注册页
│   │   │   ├── PostItem.vue       # 发布信息页
│   │   │   ├── ItemList.vue       # 物品列表页
│   │   │   ├── ItemDetail.vue       # 物品详情页
│   │   │   ├── MyItems.vue          # 我的发布页
│   │   │   ├── MyFavorites.vue      # 我的收藏页
│   │   │   ├── MyClaims.vue         # 我的认领记录页
│   │   │   ├── ClaimManagement.vue  # 认领管理页
│   │   │   ├── ProfileView.vue      # 个人中心页
│   │   │   ├── NotificationsView.vue # 通知页
│   │   │   ├── MessagesView.vue     # 私信列表页
│   │   │   ├── ChatView.vue         # 聊天页面
│   │   │   ├── MyReports.vue        # 我的举报页
│   │   │   ├── UserItems.vue        # 用户发布历史页
│   │   │   └── AdminView.vue        # 管理员页面
│   │   ├── App.vue             # 根组件
│   │   └── main.js             # 入口文件
│   ├── index.html              # HTML 模板
│   ├── package.json            # 前端依赖配置
│   └── vite.config.js          # Vite 配置文件
│
└── README.md                   # 项目说明文档（本文件）
```

---

## ❓ 常见问题

### 部署问题

**Q: 前端构建时显示 "Killed" 或被中断？**

A: 这是内存不足导致的。解决方案：
1. **升级服务器配置**（推荐）：将内存升级到至少 4GB
2. **在本地构建后上传**：
   ```bash
   # 在本地构建
   cd frontend
   npm run build
   # 打包 dist 目录
   # Windows: Compress-Archive -Path dist -DestinationPath dist.zip
   # 上传到服务器后解压
   ```
3. **创建 Swap 交换空间**（临时方案）：
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

**Q: 构建后 dist 目录只有 favicon.png，没有 index.html？**

A: 构建未完成，通常是内存不足。请参考上面的解决方案。

### 安装问题

**Q: npm install 报错怎么办？**

A: 尝试以下解决方案：
1. 清除 npm 缓存：`npm cache clean --force`
2. 删除 `node_modules` 文件夹和 `package-lock.json`，重新运行 `npm install`
3. 使用国内镜像：`npm install --registry=https://registry.npmmirror.com`

**Q: pip install 报错怎么办？**

A: 尝试以下解决方案：
1. 升级 pip：`python -m pip install --upgrade pip`
2. 使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
3. 确保 Python 版本 >= 3.10

### 运行问题

**Q: 后端启动失败，提示端口被占用？**

A: 
1. 检查是否有其他程序占用 5000 端口
2. 修改 `app.py` 中的端口号（如改为 5001）
3. 同时修改前端 `.env.development` 中的 API 地址

**Q: 前端启动失败，提示端口被占用？**

A:
1. 检查是否有其他程序占用 5173 端口
2. 修改 `vite.config.js` 中的端口配置
3. 或使用 `npm run dev -- --port 3000` 指定其他端口

**Q: 无法访问后端 API？**

A:
1. 确保后端服务已启动（命令行窗口保持打开）
2. 检查后端地址是否为 `http://localhost:5000`
3. 检查前端 `.env.development` 中的 API 配置
4. 查看浏览器控制台是否有 CORS 错误

### 功能问题

**Q: 图片上传失败？**

A:
1. 检查图片大小是否超过 10MB
2. 检查图片格式是否为 jpg、png、gif、webp、bmp
3. 检查后端 `uploads` 文件夹是否有写入权限
4. 查看后端命令行是否有错误信息

**Q: 私信功能不工作？**

A:
1. 确保后端 SocketIO 服务正常运行
2. 检查浏览器控制台是否有 WebSocket 连接错误
3. 确保防火墙没有阻止 WebSocket 连接

**Q: 忘记密码功能不工作？**

A:
1. 确保邮箱配置正确（如果使用邮件发送）
2. 检查后端日志查看具体错误信息

### 数据库问题

**Q: 如何重置数据库？**

A:
1. 停止后端服务
2. 删除 `backend/lost_found.db` 文件
3. 重新启动后端，会自动创建新数据库

**Q: 如何备份数据库？**

A:
1. 停止后端服务
2. 复制 `backend/lost_found.db` 文件到安全位置
3. 需要恢复时，替换原文件即可

---

## 🔧 开发说明

### 开发模式

- **前端热重载**：修改前端代码后，浏览器会自动刷新
- **后端自动重载**：修改后端代码后，需要手动重启服务

### 后端脚本

- **create_admin.py**：初始化唯一高级管理员、查看管理员列表（见上文「设置管理员」）
- **migrate_admin_roles.py**：一次性历史迁移脚本，用于将旧中级管理员迁移为管理员、旧低级管理员降级为普通用户、删除教师身份字段，并校验高级管理员唯一性：
  ```bash
  cd backend
  python migrate_admin_roles.py
  ```
- **create_test_items.py**：生成测试物品数据，例如：
  ```bash
  cd backend
  python create_test_items.py                    # 默认数量
  python create_test_items.py --lost 20 --found 20  # 指定失物/拾物数量
  python create_test_items.py --user-id 1        # 指定发布用户 ID
  ```

### 生产构建

#### 构建前端

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录。

#### 预览生产版本

```bash
cd frontend
npm run preview
```

### 环境变量配置

#### 前端环境变量

创建 `.env.development`（开发环境）和 `.env.production`（生产环境）：

```env
# 开发环境通常可不配置，默认使用 http://localhost:5000
VITE_API_BASE=http://localhost:5000
VITE_SOCKET_ORIGIN=http://localhost:5000
```

#### 后端环境变量

在 `app.py` 中配置：

```python
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
```

### API 接口说明

主要接口路径：

- **认证相关**：`/api/auth/*`
- **物品相关**：`/api/items`
- **私信相关**：`/api/conversations`
- **举报相关**：`/api/reports`
- **管理员相关**：`/api/admin/*`
- **管理员申请相关**：`/api/admin-application`

详细接口文档请查看后端代码注释。

---

## 📝 更新日志

### 最新版本

- ✅ 支持多图片上传（Ctrl/Shift 多选）
- ✅ 优化个人中心界面（移除重置按钮）
- ✅ 更新网页标题为"UniFind校园寻宝"
- ✅ 完善隐私设置功能
- ✅ 优化举报处理流程
- ✅ 简化管理员角色为普通用户/管理员/高级管理员
- ✅ 新增管理员申请审核、直接任命与撤销管理员身份流程

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**祝您使用愉快！** 🎉

