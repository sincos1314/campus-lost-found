from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import base64
import json
from openpyxl import Workbook
from io import BytesIO

app = Flask(__name__)

# 配置CORS
CORS(app)

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'lost_found.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
# 允许 JWT 从查询参数或 header 中获取，避免在 multipart/form-data 请求中解析 body
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024

# 创建上传文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# 添加错误处理器来捕获 415 错误和其他错误
@app.errorhandler(415)
def unsupported_media_type(error):
    print(f'[ERROR] 415 Unsupported Media Type')
    print(f'[ERROR] Content-Type: {request.content_type}')
    print(f'[ERROR] Method: {request.method}')
    print(f'[ERROR] URL: {request.url}')
    print(f'[ERROR] Headers: {dict(request.headers)}')
    print(f'[ERROR] Has form: {request.form is not None}')
    print(f'[ERROR] Has files: {len(request.files) > 0}')
    return jsonify({'message': f'Unsupported media type: {request.content_type}'}), 415

# 添加请求前的钩子来记录所有请求
@app.before_request
def log_request_info():
    if request.method in ['POST', 'PUT'] and '/api/reports/' in request.path:
        print(f'[BEFORE_REQUEST] Method: {request.method}')
        print(f'[BEFORE_REQUEST] Path: {request.path}')
        print(f'[BEFORE_REQUEST] Content-Type: {request.content_type}')
        print(f'[BEFORE_REQUEST] Headers: {dict(request.headers)}')

# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    avatar_path = db.Column(db.String(200))
    department = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    class_name = db.Column(db.String(50))
    student_id = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')
    admin_level = db.Column(db.String(20))
    admin_appointed_by = db.Column(db.Integer)
    is_banned = db.Column(db.Boolean, default=False)
    banned_by = db.Column(db.Integer)
    user_type = db.Column(db.String(20))  # 学生/教师
    staff_id = db.Column(db.String(50))   # 工号（教师）
    visibility_setting = db.Column(db.String(20), default='public')
    others_policy = db.Column(db.String(20), default='show')
    created_at = db.Column(db.DateTime, default=datetime.now)
    items = db.relationship('Item', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        def compute_grade_display():
            try:
                init = (self.grade or '').strip()
                if not init:
                    return ''
                if init == '已毕业':
                    return '已毕业'
                idx_map = {'大一':1,'大二':2,'大三':3,'大四':4}
                if init not in idx_map:
                    return init
                init_idx = idx_map[init]
                now = datetime.now()
                reg = self.created_at or now
                # 学生用户自注册以来 9 月 1 日之后自动升级
                def first_sept1_after(d):
                    sept = datetime(d.year, 9, 1)
                    return sept if d < sept else datetime(d.year+1, 9, 1)
                cnt = 0
                boundary = first_sept1_after(reg)
                while boundary <= now and init_idx+cnt < 4:
                    cnt += 1
                    boundary = datetime(boundary.year+1, 9, 1)
                cur_idx = min(init_idx+cnt, 4)
                # 处理“大四”的特殊情况
                if cur_idx < 4:
                    rev_map = {1:'大一',2:'大二',3:'大三'}
                    return rev_map[cur_idx]
                if init_idx == 4:
                    july1 = datetime(reg.year, 7, 1)
                    grad_date = july1 if reg < july1 else datetime(reg.year+1, 7, 1)
                else:
                    promotions_needed = 4 - init_idx
                    boundary = first_sept1_after(reg)
                    for _ in range(promotions_needed-1):
                        boundary = datetime(boundary.year+1, 9, 1)
                    grad_date = datetime(boundary.year+1, 7, 1)
                return '已毕业' if now >= grad_date else '大四'
            except:
                return (self.grade or '')
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'avatar_url': f'/api/avatar/{self.avatar_path}' if self.avatar_path else None,
            'department': self.department,
            'grade': self.grade,
            'class_name': self.class_name,
            'student_id': self.student_id,
            'gender': self.gender,
            'role': self.role,
            'admin_level': self.admin_level,
            'admin_appointed_by': self.admin_appointed_by,
            'is_banned': bool(self.is_banned),
            'banned_by': self.banned_by,
            'user_type': self.user_type,
            'staff_id': self.staff_id,
            'visibility_setting': self.visibility_setting,
            'others_policy': self.others_policy,
            'grade_display': compute_grade_display(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    image_path = db.Column(db.String(200))  # 主图（向后兼容）
    images_path = db.Column(db.Text)  # 多张图片路径（JSON格式）
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='open')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        # 处理多张图片
        image_urls = []
        if self.images_path:
            try:
                image_paths = json.loads(self.images_path)
                if isinstance(image_paths, list):
                    image_urls = [f'/api/image/{path}' for path in image_paths if path]
            except:
                pass
        
        # 向后兼容：如果没有多张图片但有主图，使用主图
        if not image_urls and self.image_path:
            image_urls = [f'/api/image/{self.image_path}']
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'item_type': self.item_type,
            'location': self.location,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'date': self.date,
            'image_url': image_urls[0] if image_urls else None,  # 主图（向后兼容）
            'image_urls': image_urls,  # 所有图片列表
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        }


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    related_item_id = db.Column(db.Integer, db.ForeignKey('item.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'related_item_id': self.related_item_id
        }

class Message(db.Model):
    """消息表 - 记录具体的聊天消息"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)  # 文字消息内容
    message_type = db.Column(db.String(20), default='text')  
    image_path = db.Column(db.String(200))  # 图片路径
    is_read = db.Column(db.Boolean, default=False)  # 是否已读
    is_recalled = db.Column(db.Boolean, default=False)  # 是否已撤回
    is_deleted_by_sender = db.Column(db.Boolean, default=False)  # 发送者是否删除
    is_deleted_by_receiver = db.Column(db.Boolean, default=False)  # 接收者是否删除
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def to_dict(self, current_user_id):
        """转换为字典"""
        # 判断当前用户是否为发送者
        is_sender = self.sender_id == current_user_id
        
        # 判断消息是否被当前用户删除
        is_deleted = self.is_deleted_by_sender if is_sender else self.is_deleted_by_receiver
        
        # 如果被删除，不返回内容
        if is_deleted:
            return None
        
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'message_type': self.message_type,
            'image_url': f'/api/message-image/{self.image_path}' if self.image_path else None,
            'is_read': self.is_read,
            'is_recalled': self.is_recalled,
            'is_sender': is_sender,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Conversation(db.Model):
    """会话表 - 记录两个用户之间的会话"""
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_message = db.Column(db.Text)  # 最后一条消息内容
    last_message_time = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, current_user_id):
        """转换为字典，包含对方用户信息"""
        other_user_id = self.user2_id if self.user1_id == current_user_id else self.user1_id
        other_user = User.query.get(other_user_id)
        
        # 计算未读消息数
        unread_count = Message.query.filter_by(
            conversation_id=self.id,
            receiver_id=current_user_id,
            is_read=False,
            is_deleted_by_receiver=False
        ).count()
        
        return {
            'id': self.id,
            'other_user': {
                'id': other_user.id,
                'username': other_user.username,
                'role': other_user.role,
                'admin_level': other_user.admin_level
            },
            'last_message': self.last_message,
            'last_message_time': self.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_message_time else None,
            'unread_count': unread_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class VisibilityRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rule = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    category = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(10), default='medium')
    evidence_image_path = db.Column(db.String(200))  # 主图（向后兼容）
    evidence_images_path = db.Column(db.Text)  # 多张证据图片路径（JSON格式）
    resolution_note = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')
    user_withdrawn = db.Column(db.Boolean, default=False)
    anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

# 创建数据库表
with app.app_context():
    db.create_all()
    try:
        # 确保“头像路径”列存在（SQLite 快速迁移）
        import sqlite3
        conn = sqlite3.connect(os.path.join(basedir, 'lost_found.db'))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(user)")
        cols = [row[1] for row in cur.fetchall()]
        if 'avatar_path' not in cols:
            cur.execute("ALTER TABLE user ADD COLUMN avatar_path TEXT")
        for coldef in [
            ('department', 'TEXT'),
            ('grade', 'TEXT'),
            ('class_name', 'TEXT'),
            ('student_id', 'TEXT'),
            ('gender', 'TEXT'),
            ('role', 'TEXT'),
            ('admin_level', 'TEXT'),
            ('admin_appointed_by', 'INTEGER'),
            ('is_banned', 'INTEGER'),
            ('banned_by', 'INTEGER'),
            ('user_type', 'TEXT'),
            ('staff_id', 'TEXT'),
            ('visibility_setting', 'TEXT'),
            ('others_policy', 'TEXT')
        ]:
            if coldef[0] not in cols:
                cur.execute(f"ALTER TABLE user ADD COLUMN {coldef[0]} {coldef[1]}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'avatar_path migration skipped: {e}')

    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(basedir, 'lost_found.db'))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(report)")
        cols = [row[1] for row in cur.fetchall()]
        for coldef in [
            ('severity', 'TEXT'),
            ('evidence_image_path', 'TEXT'),
            ('evidence_images_path', 'TEXT'),  # 多张证据图片
            ('resolution_note', 'TEXT'),
            ('user_withdrawn', 'INTEGER'),
            ('anonymous', 'INTEGER')
        ]:
            if coldef[0] not in cols:
                cur.execute(f"ALTER TABLE report ADD COLUMN {coldef[0]} {coldef[1]}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'report migration skipped: {e}')

    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(basedir, 'lost_found.db'))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(item)")
        cols = [row[1] for row in cur.fetchall()]
        # 添加多张图片路径字段
        if 'images_path' not in cols:
            cur.execute("ALTER TABLE item ADD COLUMN images_path TEXT")
        conn.commit()
        conn.close()
        print('✅ Item 表迁移成功：已添加 images_path 字段')
    except Exception as e:
        print(f'item migration skipped: {e}')

# 文件上传辅助函数
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def file_too_large(file, limit=MAX_IMAGE_SIZE):
    try:
        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
        return size > limit
    except Exception:
        cl = getattr(file, 'content_length', None)
        if cl is not None:
            return cl > limit
        # 回退：不确定大小时认为未超限
        return False

def create_notification(user_id, title, content, notification_type='info', related_item_id=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=notification_type,
        related_item_id=related_item_id
    )
    db.session.add(notification)
    db.session.commit()

# JWT 错误处理
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Invalid token', 'error': str(error)}), 422

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({'message': 'Missing Authorization Header', 'error': str(error)}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token has expired'}), 401

# 全局 CORS 处理
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'authorization, content-type'
    response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT'
    return response

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        resp = make_response('', 200)
        return add_cors_headers(resp)

# 认证相关路由
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已被注册'}), 400
    
    # 创建新用户
    identity = (data.get('identity') or 'student').strip()
    user = User(
        username=data['username'],
        email=data['email'],
        phone=data.get('phone', ''),
        department=data.get('department', ''),
        grade=data.get('grade', ''),
        class_name=data.get('class_name', ''),
        student_id=data.get('student_id', ''),
        gender=data.get('gender', ''),
        user_type=identity,
        staff_id=data.get('staff_id', '')
    )
    user.set_password(data['password'])
    # 教师自动授予中级管理员
    if identity == 'teacher':
        user.role = 'admin'
        user.admin_level = 'mid'
        user.admin_appointed_by = None
    
    db.session.add(user)
    db.session.commit()
    
    # 创建欢迎通知
    create_notification(
        user.id,
        '欢迎加入校园失物招领系统！',
        f'你好 {user.username}，欢迎使用我们的系统。你可以在这里发布和查找失物信息。',
        'success'
    )
    
    return jsonify({'message': '注册成功', 'user': user.to_dict()}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    })

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    new_password = data.get('new_password', '').strip()
    if not username or not email or not new_password:
        return jsonify({'message': '参数不完整'}), 400
    if len(new_password) < 6:
        return jsonify({'message': '新密码长度至少6位'}), 400
    user = User.query.filter_by(username=username, email=email).first()
    if not user:
        return jsonify({'message': '用户不存在或邮箱不匹配'}), 404
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': '密码重置成功'})


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    return jsonify(user.to_dict())


@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改资料'}), 403
    data = request.json
    
    user.email = data.get('email', user.email)
    user.phone = data.get('phone', user.phone)
    user.department = data.get('department', user.department)
    user.grade = data.get('grade', user.grade)
    user.class_name = data.get('class_name', user.class_name)
    user.student_id = data.get('student_id', user.student_id)
    user.gender = data.get('gender', user.gender)
    
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/api/privacy', methods=['GET'])
@jwt_required()
def get_privacy():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    rules = VisibilityRule.query.filter_by(owner_user_id=user_id).all()
    return jsonify({
        'visibility_setting': user.visibility_setting,
        'others_policy': user.others_policy,
        'rules': [{'target_user_id': r.target_user_id, 'rule': r.rule} for r in rules]
    })

@app.route('/api/privacy', methods=['PUT'])
@jwt_required()
def update_privacy():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改隐私设置'}), 403
    data = request.json
    user.visibility_setting = data.get('visibility_setting', user.visibility_setting)
    user.others_policy = data.get('others_policy', user.others_policy)
    db.session.commit()
    return jsonify({'message': 'updated'})

@app.route('/api/privacy/rules', methods=['PUT'])
@jwt_required()
def update_privacy_rules():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改隐私设置'}), 403
    data = request.json
    VisibilityRule.query.filter_by(owner_user_id=user_id).delete()
    for tid in data.get('show_list', []):
        db.session.add(VisibilityRule(owner_user_id=user_id, target_user_id=int(tid), rule='show'))
    for tid in data.get('hide_list', []):
        db.session.add(VisibilityRule(owner_user_id=user_id, target_user_id=int(tid), rule='hide'))
    db.session.commit()
    return jsonify({'message': 'updated'})

@app.route('/api/reports', methods=['POST'])
@jwt_required()
def create_report():
    user_id = int(get_jwt_identity())
    
    # 处理多张证据图片
    evidence_paths = []
    
    # 处理主图（image）
    if 'image' in request.files:
        file = request.files['image']
        if file and hasattr(file, 'filename') and file.filename:
            original_filename = file.filename
            if original_filename.lower() != 'blob' and allowed_file(original_filename):
                if not file_too_large(file):
                    import random
                    timestamp = datetime.now().timestamp()
                    random_suffix = random.randint(1000, 9999)
                    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
                    filename = secure_filename(f"evidence_{timestamp}_{random_suffix}.{ext}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    evidence_paths.append(filename)
    
    # 处理副图（images）
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and hasattr(file, 'filename') and file.filename:
                original_filename = file.filename
                if original_filename.lower() != 'blob' and allowed_file(original_filename):
                    if not file_too_large(file):
                        import random
                        timestamp = datetime.now().timestamp()
                        random_suffix = random.randint(1000, 9999)
                        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
                        filename = secure_filename(f"evidence_{timestamp}_{random_suffix}.{ext}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        evidence_paths.append(filename)
    
    evidence_path = evidence_paths[0] if evidence_paths else None
    evidence_images_path_json = json.dumps(evidence_paths) if evidence_paths else None

    data = request.form.to_dict() if evidence_paths else (request.json or {})

    existing = Report.query.filter_by(
        reporter_id=user_id,
        target_user_id=data.get('target_user_id'),
        item_id=data.get('item_id'),
        status='open'
    ).first()
    if existing:
        return jsonify({'message': '重复的举报正在处理中'}), 400
    report = Report(
        reporter_id=user_id,
        target_user_id=data.get('target_user_id'),
        item_id=data.get('item_id'),
        category=(data.get('category') or 'other'),
        description=(data.get('description') or ''),
        severity=(data.get('severity') or 'medium'),
        evidence_image_path=evidence_path,  # 向后兼容
        evidence_images_path=evidence_images_path_json,  # 多张图片
        anonymous=bool(str(data.get('anonymous', 'false')).lower() in ['true','1','yes'])
    )
    db.session.add(report)
    db.session.commit()

    admins = User.query.filter_by(role='admin').all()
    cat_map = {'spam': '垃圾信息', 'abuse': '骚扰/辱骂', 'fake': '虚假信息', 'other': '其他'}
    sev_map = {'low': '低', 'medium': '中', 'high': '高'}
    for admin in admins:
        try:
            create_notification(
                admin.id,
                '新的举报',
                f"有新的举报需要处理（类别：{cat_map.get(report.category, report.category)}，严重级：{sev_map.get(report.severity, report.severity)}）",
                'warning',
                report.item_id
            )
        except:
            pass
    return jsonify({'message': 'reported', 'id': report.id}), 201


@app.route('/api/auth/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if 'avatar' not in request.files:
        return jsonify({'message': '未上传头像'}), 400
    file = request.files['avatar']
    if file_too_large(file):
        return jsonify({'message': '图片大小超过限制（最大10MB）'}), 400
    if file.filename == '':
        return jsonify({'message': '未选择文件'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(f"avatar_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # 删除旧头像文件
        if user.avatar_path:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], user.avatar_path))
            except:
                pass
        user.avatar_path = filename
        db.session.commit()
        return jsonify(user.to_dict())
    return jsonify({'message': '不支持的图片格式'}), 400


# 物品相关路由
@app.route('/api/items', methods=['GET'])
def get_items():
    category = request.args.get('category', '')
    item_type = request.args.get('item_type', '')
    status = request.args.get('status', 'open')
    search = request.args.get('search', '')
    # 分页参数
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1
    try:
        page_size = int(request.args.get('page_size', 12))
    except:
        page_size = 12
    page = 1 if page < 1 else page
    page_size = 1 if page_size < 1 else min(page_size, 50)
    # 日期范围
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    query = Item.query
    
    if category:
        query = query.filter_by(category=category)
    if item_type:
        query = query.filter_by(item_type=item_type)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (Item.title.contains(search)) | 
            (Item.description.contains(search))
        )
    
    # 日期范围过滤（Item.date 为字符串，尝试解析为日期）
    if start_date and end_date:
        try:
            from datetime import datetime as dt
            s = dt.strptime(start_date, '%Y-%m-%d')
            e = dt.strptime(end_date, '%Y-%m-%d')
            items_all = query.order_by(Item.created_at.desc()).all()
            filtered = []
            for it in items_all:
                try:
                    d = dt.strptime(it.date, '%Y-%m-%d')
                    if s <= d <= e:
                        filtered.append(it)
                except:
                    pass
            total = len(filtered)
            start_idx = (page - 1) * page_size
            items_page = filtered[start_idx:start_idx + page_size]
            return jsonify({
                'items': [item.to_dict() for item in items_page],
                'total': total,
                'page': page,
                'page_size': page_size
            })
        except:
            pass

    pagination = query.order_by(Item.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())

@app.route('/api/users/<int:user_id>/items', methods=['GET'])
def get_user_items(user_id):
    viewer_id = None
    token = request.args.get('token')
    if token:
        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            viewer_id = int(decoded['sub'])
        except:
            pass
    owner = User.query.get_or_404(user_id)
    page = int(request.args.get('page', 1) or 1)
    page_size = int(request.args.get('page_size', 12) or 12)
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    if owner.visibility_setting == 'hidden':
        return jsonify({'message': '该用户设置隐藏了自己的发布失物/拾物的历史信息'}), 403
    if owner.visibility_setting == 'partial':
        allowed = False
        if viewer_id:
            rule = VisibilityRule.query.filter_by(owner_user_id=user_id, target_user_id=viewer_id).first()
            if rule:
                allowed = rule.rule == 'show'
            else:
                allowed = owner.others_policy != 'hide'
        else:
            allowed = owner.others_policy != 'hide'
        if not allowed:
            return jsonify({'message': '该用户设置隐藏了自己的发布失物/拾物的历史信息'}), 403
    query = Item.query.filter_by(user_id=user_id)
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Item.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@app.route('/api/items/<int:item_id>/timeline', methods=['GET'])
def get_item_timeline(item_id):
    item = Item.query.get_or_404(item_id)
    events = [{
        'time': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'title': '发布',
        'description': f'用户 {item.user.username if item.user else ""} 发布了《{item.title}》'
    }]
    notis = Notification.query.filter_by(related_item_id=item_id).order_by(Notification.created_at.asc()).all()
    for n in notis:
        events.append({
            'time': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'title': n.title,
            'description': n.content,
            'type': n.type
        })
    return jsonify(events)


@app.route('/api/items', methods=['POST'])
@jwt_required()
def create_item():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法发布'}), 403
    data = request.form.to_dict()
    
    # 处理多张图片上传
    image_paths = []
    
    # 处理主图（image）
    if 'image' in request.files:
        file = request.files['image']
        if file:
            original_filename = file.filename if hasattr(file, 'filename') else None
            
            # 如果文件名为空或者是 "blob"，生成一个默认文件名
            if not original_filename or original_filename.lower() == 'blob':
                content_type = file.content_type if hasattr(file, 'content_type') else 'image/jpeg'
                ext_map = {
                    'image/jpeg': 'jpg',
                    'image/jpg': 'jpg',
                    'image/png': 'png',
                    'image/gif': 'gif',
                    'image/webp': 'webp',
                    'image/bmp': 'bmp'
                }
                ext = ext_map.get(content_type, 'jpg')
                original_filename = f'image_{datetime.now().timestamp()}.{ext}'
                print(f'[DEBUG] 主图生成默认文件名: {original_filename}')
            
            if original_filename and allowed_file(original_filename):
                if file_too_large(file):
                    return jsonify({'message': '图片大小超过限制（最大10MB）'}), 400
                filename = secure_filename(f"{datetime.now().timestamp()}_{original_filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_paths.append(filename)
                print(f'[DEBUG] 主图已保存: {filename}')
    
    # 处理副图（images）- 使用 getlist 获取所有同名文件
    # Flask 的 request.files.getlist 即使字段不存在也会返回空列表，不会报错
    files = request.files.getlist('images')
    print(f'[DEBUG] 获取到 {len(files)} 张副图')
    for idx, file in enumerate(files):
        if not file:
            print(f'[DEBUG] 第 {idx+1} 张副图为空，跳过')
            continue
            
        original_filename = file.filename if hasattr(file, 'filename') else None
        print(f'[DEBUG] 处理第 {idx+1} 张副图: {original_filename}')
        
        # 如果文件名为空或者是 "blob"，生成一个默认文件名
        if not original_filename or original_filename.lower() == 'blob':
            # 根据文件内容类型确定扩展名
            content_type = file.content_type if hasattr(file, 'content_type') else 'image/jpeg'
            ext_map = {
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg',
                'image/png': 'png',
                'image/gif': 'gif',
                'image/webp': 'webp',
                'image/bmp': 'bmp'
            }
            ext = ext_map.get(content_type, 'jpg')
            original_filename = f'image_{datetime.now().timestamp()}.{ext}'
            print(f'[DEBUG] 生成默认文件名: {original_filename}')
        
        # 检查文件扩展名
        if not allowed_file(original_filename):
            print(f'[DEBUG] 文件扩展名不允许: {original_filename}')
            continue
            
        if file_too_large(file):
            print(f'[DEBUG] 跳过过大的文件: {original_filename}')
            continue  # 跳过过大的文件
            
        filename = secure_filename(f"{datetime.now().timestamp()}_{original_filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_paths.append(filename)
        print(f'[DEBUG] 副图已保存: {filename}')
    
    # 保存图片路径（JSON格式）
    images_path_json = json.dumps(image_paths) if image_paths else None
    # 向后兼容：保存第一张作为主图
    image_path = image_paths[0] if image_paths else None
    
    print(f'[DEBUG] 上传的图片数量: {len(image_paths)}')
    print(f'[DEBUG] 图片路径列表: {image_paths}')
    print(f'[DEBUG] images_path_json: {images_path_json}')
    
    new_item = Item(
        title=data['title'],
        description=data['description'],
        category=data['category'],
        item_type=data['item_type'],
        location=data['location'],
        contact_name=data['contact_name'],
        contact_phone=data['contact_phone'],
        date=data['date'],
        image_path=image_path,  # 向后兼容
        images_path=images_path_json,  # 多张图片
        user_id=user_id
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    # 验证保存的数据
    print(f'[DEBUG] 保存后的 images_path: {new_item.images_path}')
    item_dict = new_item.to_dict()
    print(f'[DEBUG] 返回的 image_urls: {item_dict.get("image_urls", [])}')
    
    # 创建通知
    user = User.query.get(user_id)
    create_notification(
        user_id,
        '发布成功',
        f'你的{data["category"] == "lost" and "失物" or "拾物"}信息《{data["title"]}》已成功发布！',
        'success',
        new_item.id
    )
    
    return jsonify(item_dict), 201


@app.route('/api/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改'}), 403
    item = Item.query.get_or_404(item_id)
    
    # 检查权限
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    data = request.json
    
    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.category = data.get('category', item.category)
    item.contact_name = data.get('contact_name', item.contact_name)
    item.contact_phone = data.get('contact_phone', item.contact_phone)
    item.location = data.get('location', item.location)
    item.item_type = data.get('item_type', item.item_type)
    item.date = data.get('date', item.date)
    old_status = item.status
    item.status = data.get('status', item.status)
    
    db.session.commit()
    
    # 如果状态改变，创建通知
    if old_status != item.status and item.status == 'closed':
        create_notification(
            user_id,
            '物品已找回',
            f'恭喜！你的{item.category == "lost" and "失物" or "拾物"}《{item.title}》已标记为已解决。',
            'success',
            item.id
        )
    
    return jsonify(item.to_dict())

@app.route('/api/items/<int:item_id>/image', methods=['POST'])
@jwt_required()
def update_item_image(item_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改'}), 403
    item = Item.query.get_or_404(item_id)
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    if 'image' not in request.files:
        return jsonify({'message': '未上传图片'}), 400
    file = request.files['image']
    if file_too_large(file):
        return jsonify({'message': '图片大小超过限制（最大10MB）'}), 400
    
    # 处理文件名为空或 blob 的情况
    original_filename = file.filename if hasattr(file, 'filename') else None
    if not original_filename or original_filename.lower() == 'blob':
        content_type = file.content_type if hasattr(file, 'content_type') else 'image/jpeg'
        ext_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/bmp': 'bmp'
        }
        ext = ext_map.get(content_type, 'jpg')
        original_filename = f'image_{datetime.now().timestamp()}.{ext}'
    
    if not allowed_file(original_filename):
        return jsonify({'message': '不支持的图片格式'}), 400
    
    # 生成新的文件名（确保唯一性）
    # 使用时间戳 + 随机数，避免文件名冲突和复杂解析
    import random
    timestamp = datetime.now().timestamp()
    random_suffix = random.randint(1000, 9999)
    
    # 提取文件扩展名（从原始文件名或内容类型）
    if '.' in original_filename:
        ext = original_filename.rsplit('.', 1)[-1].lower()
        # 确保扩展名是允许的格式
        if ext not in ALLOWED_EXTENSIONS:
            ext = 'jpg'
    else:
        # 如果没有扩展名，根据内容类型判断
        content_type = file.content_type if hasattr(file, 'content_type') else 'image/jpeg'
        ext_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/bmp': 'bmp'
        }
        ext = ext_map.get(content_type, 'jpg')
    
    # 生成简洁的文件名：时间戳_随机数.扩展名
    filename = secure_filename(f"{timestamp}_{random_suffix}.{ext}")
    print(f'[DEBUG] 生成的文件名: {filename}, 原始文件名: {original_filename}')
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # 删除旧图片（包括单图和多图中的旧图片）
    old_paths_to_delete = []
    if item.image_path:
        old_paths_to_delete.append(item.image_path)
    if item.images_path:
        try:
            old_paths = json.loads(item.images_path)
            if isinstance(old_paths, list):
                old_paths_to_delete.extend(old_paths)
        except:
            pass
    
    for old_path in old_paths_to_delete:
        try:
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_path)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        except Exception as e:
            print(f'[DEBUG] 删除旧图片失败: {old_path}, 错误: {e}')
    
    # 更新图片路径（单图和多图都更新为新的单张图片）
    item.image_path = filename
    item.images_path = json.dumps([filename])  # 更新为只包含新图片的数组
    db.session.commit()
    
    # 验证保存的数据
    item_dict = item.to_dict()
    print(f'[DEBUG] 图片更新成功，新文件名: {filename}')
    print(f'[DEBUG] 返回的 image_url: {item_dict.get("image_url")}')
    print(f'[DEBUG] 返回的 image_urls: {item_dict.get("image_urls")}')
    
    return jsonify(item_dict)

@app.route('/api/items/<int:item_id>/images', methods=['POST'])
@jwt_required()
def update_item_images(item_id):
    """更新物品的多张图片（支持保留已存在的图片和上传新图片，按顺序更新）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改'}), 403
    item = Item.query.get_or_404(item_id)
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    # 获取要保留的已存在图片路径（从请求参数中，按顺序）
    keep_existing = request.form.getlist('keep_existing')  # 要保留的已存在图片路径列表（按顺序）
    print(f'[DEBUG] 要保留的已存在图片（按顺序）: {keep_existing}')
    
    # 处理新上传的图片
    image_paths = []
    
    # 处理主图（image）
    if 'image' in request.files:
        file = request.files['image']
        if file and hasattr(file, 'filename') and file.filename:
            original_filename = file.filename
            if original_filename.lower() != 'blob' and allowed_file(original_filename):
                if not file_too_large(file):
                    import random
                    timestamp = datetime.now().timestamp()
                    random_suffix = random.randint(1000, 9999)
                    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
                    filename = secure_filename(f"{timestamp}_{random_suffix}.{ext}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_paths.append(filename)
    
    # 处理副图（images）
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and hasattr(file, 'filename') and file.filename:
                original_filename = file.filename
                if original_filename.lower() != 'blob' and allowed_file(original_filename):
                    if not file_too_large(file):
                        import random
                        timestamp = datetime.now().timestamp()
                        random_suffix = random.randint(1000, 9999)
                        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
                        filename = secure_filename(f"{timestamp}_{random_suffix}.{ext}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        image_paths.append(filename)
    
    # 合并已存在的图片和新上传的图片
    # keep_existing 包含要保留的图片路径（相对于 /api/image/ 的路径）
    final_image_paths = []
    
    # 处理已存在的图片：从 /api/image/filename 提取 filename
    for existing_path in keep_existing:
        if existing_path:
            # 支持两种格式：/api/image/filename 或直接是 filename
            if existing_path.startswith('/api/image/'):
                filename = existing_path.replace('/api/image/', '')
            else:
                filename = existing_path
            # 验证文件是否存在
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                final_image_paths.append(filename)
    
    # 添加新上传的图片
    final_image_paths.extend(image_paths)
    
    # 删除不再使用的旧图片
    old_paths_to_delete = []
    if item.image_path:
        if item.image_path not in final_image_paths:
            old_paths_to_delete.append(item.image_path)
    if item.images_path:
        try:
            old_paths = json.loads(item.images_path)
            if isinstance(old_paths, list):
                for old_path in old_paths:
                    if old_path not in final_image_paths:
                        old_paths_to_delete.append(old_path)
        except:
            pass
    
    for old_path in old_paths_to_delete:
        try:
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_path)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        except Exception as e:
            print(f'[DEBUG] 删除旧图片失败: {old_path}, 错误: {e}')
    
    # 更新数据库
    if final_image_paths:
        item.images_path = json.dumps(final_image_paths)
        item.image_path = final_image_paths[0]  # 第一张作为主图（向后兼容）
        print(f'[DEBUG] 更新后的图片路径（按顺序）: {final_image_paths}')
    else:
        item.images_path = None
        item.image_path = None
        print(f'[DEBUG] 清空所有图片')
    
    db.session.commit()
    
    # 验证保存的数据
    item_dict = item.to_dict()
    print(f'[DEBUG] 返回的 image_urls: {item_dict.get("image_urls")}')
    
    return jsonify(item_dict)

@app.route('/api/items/<int:item_id>/image', methods=['DELETE'])
@jwt_required()
def delete_item_image(item_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法修改'}), 403
    item = Item.query.get_or_404(item_id)
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    if item.image_path:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.image_path))
        except:
            pass
    item.image_path = None
    item.images_path = None
    db.session.commit()
    return jsonify(item.to_dict())


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法删除'}), 403
    item = Item.query.get_or_404(item_id)
    
    # 检查权限
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    # 删除图片文件
    if item.image_path:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.image_path))
        except:
            pass
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})


@app.route('/api/image/<path:filename>')
def get_image(filename):
    try:
        # 安全检查：防止路径遍历攻击
        original_filename = filename
        filename = os.path.basename(filename)  # 只取文件名部分，去除路径
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 再次安全检查：确保文件路径在 UPLOAD_FOLDER 内
        upload_folder_abs = os.path.abspath(app.config['UPLOAD_FOLDER'])
        filepath_abs = os.path.abspath(filepath)
        if not filepath_abs.startswith(upload_folder_abs):
            print(f'[ERROR] 路径安全检查失败: 原始={original_filename}, 清理后={filename}')
            return jsonify({'message': '无效的文件路径'}), 403
        
        if not os.path.exists(filepath):
            print(f'[ERROR] 图片文件不存在: {filename}')
            print(f'[ERROR] 完整路径: {filepath_abs}')
            print(f'[ERROR] 上传文件夹: {upload_folder_abs}')
            # 列出上传文件夹中的文件（用于调试）
            try:
                files_in_folder = os.listdir(upload_folder_abs)
                print(f'[DEBUG] 上传文件夹中的文件数量: {len(files_in_folder)}')
                if len(files_in_folder) > 0:
                    print(f'[DEBUG] 前5个文件: {files_in_folder[:5]}')
            except:
                pass
            return jsonify({'message': '图片不存在'}), 404
        
        # 检查是否是文件（不是目录）
        if not os.path.isfile(filepath):
            print(f'[ERROR] 路径不是文件: {filename}')
            return jsonify({'message': '无效的文件路径'}), 400
        
        return send_file(filepath)
    except Exception as e:
        import traceback
        print(f'[ERROR] 获取图片失败: 原始={original_filename if "original_filename" in locals() else filename}, 错误: {e}')
        traceback.print_exc()
        return jsonify({'message': f'获取图片失败: {str(e)}'}), 500


@app.route('/api/avatar/<path:filename>')
def get_avatar(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


# 通知相关路由
@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifications])


@app.route('/api/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    user_id = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({'count': count})


@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    user_id = int(get_jwt_identity())
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify(notification.to_dict())


@app.route('/api/notifications/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': '所有通知已标记为已读'})


# 统计相关
@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_lost = Item.query.filter_by(category='lost').count()
    total_found = Item.query.filter_by(category='found').count()
    total_solved = Item.query.filter_by(status='closed').count()
    total_users = User.query.count()
    
    return jsonify({
        'total_lost': total_lost,
        'total_found': total_found,
        'total_solved': total_solved,
        'total_users': total_users
    })

def admin_required():
    try:
        uid = int(get_jwt_identity())
        user = User.query.get(uid)
        return user and user.role == 'admin'
    except:
        return False

def get_current_user():
    try:
        uid = int(get_jwt_identity())
        return User.query.get(uid)
    except:
        return None

level_rank = {'low': 1, 'mid': 2, 'high': 3}

def is_admin_user(u):
    return bool(u and u.role == 'admin' and (u.admin_level in level_rank))

def can_ban_or_delete(current_admin, target_user):
    if not is_admin_user(current_admin):
        return False
    if current_admin.admin_level == 'low':
        return False
    if is_admin_user(target_user):
        return level_rank[current_admin.admin_level] > level_rank[target_user.admin_level]
    return True

def can_mark_item_status(current_admin):
    return is_admin_user(current_admin) and current_admin.admin_level in ['mid', 'high']

def can_create_user_or_item(current_admin):
    return is_admin_user(current_admin)

def can_appoint_level(current_admin, level):
    if not is_admin_user(current_admin):
        return False
    if level == 'low':
        return current_admin.admin_level in ['mid', 'high']
    if level == 'mid':
        return current_admin.admin_level == 'high'
    return False

def can_revoke(current_admin, target_user):
    if not is_admin_user(current_admin) or not is_admin_user(target_user):
        return False
    if target_user.admin_level == 'low':
        return current_admin.admin_level in ['mid', 'high']
    if target_user.admin_level == 'mid':
        return current_admin.admin_level == 'high'
    return False

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_users():
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/admin/users/<int:user_id>/ban', methods=['PUT'])
@jwt_required()
def admin_user_ban(user_id):
    current_admin = get_current_user()
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    data = request.json
    user = User.query.get_or_404(user_id)
    if current_admin and user.id == current_admin.id:
        return jsonify({'message': 'forbidden'}), 403
    action_ban = bool(data.get('ban', False))
    if action_ban:
        if not can_ban_or_delete(current_admin, user):
            return jsonify({'message': 'forbidden'}), 403
        user.is_banned = True
        user.banned_by = current_admin.id
        create_notification(
            user.id,
            '账户封禁',
            f'{current_admin.username} 于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 将你封禁。',
            'warning'
        )
    else:
        if not is_admin_user(current_admin) or current_admin.admin_level not in ['mid', 'high']:
            return jsonify({'message': 'forbidden'}), 403
        user.is_banned = False
        user.banned_by = None
    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/api/admin/items', methods=['GET'])
@jwt_required()
def admin_items():
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    items = Item.query.order_by(Item.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/admin/items/<int:item_id>/status', methods=['PUT'])
@jwt_required()
def admin_item_status(item_id):
    current_admin = get_current_user()
    if not admin_required() or not can_mark_item_status(current_admin):
        return jsonify({'message': 'forbidden'}), 403
    item = Item.query.get_or_404(item_id)
    data = request.json
    item.status = data.get('status', item.status)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/admin/reports', methods=['GET'])
@jwt_required()
def admin_reports():
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    status = request.args.get('status', '')
    query = Report.query
    if status:
        query = query.filter_by(status=status)
    reports = query.order_by(Report.created_at.desc()).all()
    result = []
    for r in reports:
        it = Item.query.get(r.item_id) if r.item_id else None
        rep_user = User.query.get(r.reporter_id) if r.reporter_id else None
        tgt_user = User.query.get(r.target_user_id) if r.target_user_id else None
        # 处理多张证据图片
        evidence_image_urls = []
        if r.evidence_images_path:
            try:
                evidence_paths = json.loads(r.evidence_images_path)
                if isinstance(evidence_paths, list):
                    evidence_image_urls = [f'/api/image/{path}' for path in evidence_paths if path]
            except:
                pass
        # 向后兼容：如果没有多张图片但有主图，使用主图
        if not evidence_image_urls and r.evidence_image_path:
            evidence_image_urls = [f'/api/image/{r.evidence_image_path}']
        
        result.append({
            'id': r.id,
            'reporter_id': r.reporter_id,
            'target_user_id': r.target_user_id,
            'item_id': r.item_id,
            'item_title': (it.title if it else None),
            'item_category': (it.category if it else None),
            'reporter_username': (rep_user.username if rep_user else None),
            'target_username': (tgt_user.username if tgt_user else None),
            'anonymous': bool(r.anonymous),
            'category': r.category,
            'description': r.description,
            'severity': r.severity,
            'evidence_image_url': evidence_image_urls[0] if evidence_image_urls else None,  # 主图（向后兼容）
            'evidence_image_urls': evidence_image_urls,  # 所有图片列表
            'resolution_note': r.resolution_note,
            'status': r.status,
            'user_withdrawn': bool(r.user_withdrawn),
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result)

@app.route('/api/admin/reports/<int:report_id>', methods=['PUT'])
@jwt_required()
def admin_update_report(report_id):
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    report = Report.query.get_or_404(report_id)
    data = request.json
    if getattr(report, 'user_withdrawn', False):
        return jsonify({'message': '举报者已撤回，信息已锁定，无法更改状态'}), 403
    old_status = report.status
    report.status = data.get('status', report.status)
    report.resolution_note = data.get('resolution_note', report.resolution_note)
    db.session.commit()
    # notify reporter on status change
    if old_status != report.status:
        try:
            note = report.resolution_note or ''
            status_map = {
                'open': '已发布',
                'processing': '处理中',
                'resolved': '已解决',
                'rejected': '已拒绝',
                'withdrawn': '已撤回'
            }
            status_text = status_map.get(report.status, report.status)
            create_notification(report.reporter_id, '举报处理进度', f'你的举报状态已更新为：{status_text}。{note}', 'info', report.item_id)
        except:
            pass
    return jsonify({'message': 'updated'})

@app.route('/api/my-reports', methods=['GET'])
@jwt_required()
def my_reports():
    user_id = int(get_jwt_identity())
    reps = Report.query.filter_by(reporter_id=user_id).order_by(Report.created_at.desc()).all()
    result = []
    for r in reps:
        it = Item.query.get(r.item_id) if r.item_id else None
        # 处理多张证据图片
        evidence_image_urls = []
        if r.evidence_images_path:
            try:
                evidence_paths = json.loads(r.evidence_images_path)
                if isinstance(evidence_paths, list):
                    evidence_image_urls = [f'/api/image/{path}' for path in evidence_paths if path]
            except:
                pass
        # 向后兼容：如果没有多张图片但有主图，使用主图
        if not evidence_image_urls and r.evidence_image_path:
            evidence_image_urls = [f'/api/image/{r.evidence_image_path}']
        
        result.append({
            'id': r.id,
            'item_id': r.item_id,
            'item_title': (it.title if it else None),
            'category': r.category,
            'description': r.description,
            'severity': r.severity,
            'status': r.status,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'resolution_note': r.resolution_note,
            'evidence_image_url': evidence_image_urls[0] if evidence_image_urls else None,  # 主图（向后兼容）
            'evidence_image_urls': evidence_image_urls  # 所有图片列表
        })
    return jsonify(result)

@app.route('/api/reports/<int:report_id>', methods=['PUT','POST'])
@jwt_required(optional=False)
def update_report_by_user(report_id):
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)
    if report.reporter_id != user_id:
        return jsonify({'message': 'forbidden'}), 403
    if getattr(report, 'user_withdrawn', False):
        return jsonify({'message': '你已撤回举报，信息已锁定，无法修改'}), 403
    
    # 调试信息
    print(f'[DEBUG] 请求方法: {request.method}')
    print(f'[DEBUG] Content-Type: {request.content_type}')
    print(f'[DEBUG] is_json: {request.is_json}')
    print(f'[DEBUG] has form: {request.form is not None}')
    print(f'[DEBUG] has files: {len(request.files) > 0}')
    
    # 检查 Content-Type，如果不是 multipart/form-data 且没有文件，可能是 JSON 请求
    content_type = request.content_type or ''
    is_multipart = 'multipart/form-data' in content_type.lower()
    
    # 获取要保留的已存在图片路径（从请求参数中，按顺序）
    keep_existing = []
    if request.form:
        keep_existing = request.form.getlist('keep_existing')
        print(f'[DEBUG] keep_existing: {keep_existing}')
    elif not is_multipart and not request.files:
        # 可能是 JSON 请求，直接处理 JSON 数据
        data = request.json or {}
        if data.get('withdraw'):
            report.user_withdrawn = True
            report.status = 'withdrawn'
        if report.status != 'resolved':
            report.category = data.get('category', report.category)
            report.severity = data.get('severity', report.severity)
            report.description = data.get('description', report.description)
            if 'anonymous' in data:
                report.anonymous = bool(str(data.get('anonymous')).lower() in ['true','1','yes'])
        db.session.commit()
        return jsonify({'message': 'updated'})
    
    # 处理新上传的图片
    new_evidence_paths = []
    
    # 处理主图（image）
    if 'image' in request.files:
        file = request.files['image']
        if file and hasattr(file, 'filename') and file.filename:
            original_filename = file.filename
            if original_filename.lower() != 'blob' and allowed_file(original_filename):
                if not file_too_large(file):
                    import random
                    timestamp = datetime.now().timestamp()
                    random_suffix = random.randint(1000, 9999)
                    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
                    filename = secure_filename(f"evidence_{timestamp}_{random_suffix}.{ext}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    new_evidence_paths.append(filename)
    
    # 处理副图（images）
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and hasattr(file, 'filename') and file.filename:
                original_filename = file.filename
                if original_filename.lower() != 'blob' and allowed_file(original_filename):
                    if not file_too_large(file):
                        import random
                        timestamp = datetime.now().timestamp()
                        random_suffix = random.randint(1000, 9999)
                        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
                        filename = secure_filename(f"evidence_{timestamp}_{random_suffix}.{ext}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        new_evidence_paths.append(filename)
    
    # 合并已存在的图片和新上传的图片
    final_evidence_paths = []
    
    # 处理已存在的图片：从 /api/image/filename 或直接是 filename 提取
    # 使用 Set 去重，避免重复添加
    seen_filenames = set()
    for existing_path in keep_existing:
        if existing_path:
            if existing_path.startswith('/api/image/'):
                filename = existing_path.replace('/api/image/', '')
            else:
                filename = existing_path
            # 去重：如果已经添加过，跳过
            if filename not in seen_filenames:
                # 验证文件是否存在
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    final_evidence_paths.append(filename)
                    seen_filenames.add(filename)
    
    # 添加新上传的图片（也去重）
    for new_path in new_evidence_paths:
        if new_path and new_path not in seen_filenames:
            final_evidence_paths.append(new_path)
            seen_filenames.add(new_path)
    
    # 删除不再使用的旧图片
    old_paths_to_delete = []
    if report.evidence_image_path:
        if report.evidence_image_path not in final_evidence_paths:
            old_paths_to_delete.append(report.evidence_image_path)
    if report.evidence_images_path:
        try:
            old_paths = json.loads(report.evidence_images_path)
            if isinstance(old_paths, list):
                for old_path in old_paths:
                    if old_path not in final_evidence_paths:
                        old_paths_to_delete.append(old_path)
        except:
            pass
    
    for old_path in old_paths_to_delete:
        try:
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_path)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        except Exception as e:
            print(f'[DEBUG] 删除旧证据图片失败: {old_path}, 错误: {e}')
    
    # 更新数据库
    if final_evidence_paths:
        report.evidence_images_path = json.dumps(final_evidence_paths)
        report.evidence_image_path = final_evidence_paths[0]  # 第一张作为主图（向后兼容）
    else:
        report.evidence_images_path = None
        report.evidence_image_path = None
    
    # 获取其他表单数据
    # 优先从 form 获取（multipart/form-data），否则从 json 获取
    data = {}
    if request.form:
        data = request.form.to_dict()
    elif request.is_json:
        data = request.json or {}
    if data.get('withdraw'):
        report.user_withdrawn = True
        report.status = 'withdrawn'
    if report.status != 'resolved':
        report.category = data.get('category', report.category)
        report.severity = data.get('severity', report.severity)
        report.description = data.get('description', report.description)
        if 'anonymous' in data:
            report.anonymous = bool(str(data.get('anonymous')).lower() in ['true','1','yes'])
    
    db.session.commit()
    return jsonify({'message': 'updated'})


@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    return jsonify({
        'users': User.query.count(),
        'items': Item.query.count(),
        'lost': Item.query.filter_by(category='lost').count(),
        'found': Item.query.filter_by(category='found').count(),
        'closed': Item.query.filter_by(status='closed').count(),
        'reports_open': Report.query.filter_by(status='open').count()
    })

@app.route('/api/admin/users/create', methods=['POST'])
@jwt_required()
def admin_create_user():
    current_admin = get_current_user()
    if not admin_required() or not can_create_user_or_item(current_admin):
        return jsonify({'message': 'forbidden'}), 403
    data = request.json
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': '参数不完整'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已被注册'}), 400
    identity = (data.get('identity') or 'student').strip()
    user = User(
        username=data['username'],
        email=data['email'],
        phone=data.get('phone', ''),
        department=data.get('department', ''),
        grade=data.get('grade', ''),
        class_name=data.get('class_name', ''),
        student_id=data.get('student_id', ''),
        gender=data.get('gender', ''),
        role='user',
        user_type=identity,
        staff_id=data.get('staff_id', '')
    )
    user.set_password(data['password'])
    if identity == 'teacher':
        user.role = 'admin'
        user.admin_level = 'mid'
        user.admin_appointed_by = None
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    current_admin = get_current_user()
    if not admin_required() or not can_ban_or_delete(current_admin, User.query.get_or_404(user_id)):
        return jsonify({'message': 'forbidden'}), 403
    target = User.query.get_or_404(user_id)
    if current_admin and target.id == current_admin.id:
        return jsonify({'message': 'forbidden'}), 403
    try:
        # 删除头像文件
        if target.avatar_path:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], target.avatar_path))
            except:
                pass

        # 删除用户的物品及图片
        items = Item.query.filter_by(user_id=target.id).all()
        for it in items:
            if it.image_path:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], it.image_path))
                except:
                    pass
            db.session.delete(it)

        # 删除通知
        Notification.query.filter_by(user_id=target.id).delete()

        # 删除会话及其消息（对话设置了 cascade）
        conversations = Conversation.query.filter(
            (Conversation.user1_id == target.id) | (Conversation.user2_id == target.id)
        ).all()
        for conv in conversations:
            db.session.delete(conv)

        # 删除与该用户相关的举报
        Report.query.filter(
            (Report.reporter_id == target.id) | (Report.target_user_id == target.id)
        ).delete()

        # 删除其余消息（防御性，如果有孤立消息）
        Message.query.filter(
            (Message.sender_id == target.id) | (Message.receiver_id == target.id)
        ).delete()

        # 最后删除用户
        db.session.delete(target)
        db.session.commit()
        return jsonify({'message': 'deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '删除失败', 'error': str(e)}), 500

@app.route('/api/admin/items/create', methods=['POST'])
@jwt_required()
def admin_create_item():
    current_admin = get_current_user()
    if not admin_required() or not can_create_user_or_item(current_admin):
        return jsonify({'message': 'forbidden'}), 403
    data = request.json
    uid = int(data.get('user_id') or 0)
    user = User.query.get(uid)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    for f in ['title','description','category','item_type','location','contact_name','contact_phone','date']:
        if not data.get(f):
            return jsonify({'message': '参数不完整'}), 400
    item = Item(
        title=data['title'],
        description=data['description'],
        category=data['category'],
        item_type=data['item_type'],
        location=data['location'],
        contact_name=data['contact_name'],
        contact_phone=data['contact_phone'],
        date=data['date'],
        user_id=uid
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/admin/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_item(item_id):
    current_admin = get_current_user()
    if not admin_required() or not can_mark_item_status(current_admin):
        return jsonify({'message': 'forbidden'}), 403
    item = Item.query.get_or_404(item_id)
    if item.image_path:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.image_path))
        except:
            pass
    owner = User.query.get(item.user_id)
    title = item.title
    category_text = '失物' if item.category == 'lost' else '拾物'
    db.session.delete(item)
    db.session.commit()
    try:
        create_notification(owner.id, '发布删除', f'你的{category_text}信息《{title}》已被管理员删除。', 'warning')
    except:
        pass
    return jsonify({'message': 'deleted'})

@app.route('/api/admin/appoint', methods=['POST'])
@jwt_required()
def admin_appoint():
    current_admin = get_current_user()
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    data = request.json
    target_id = int(data.get('target_user_id') or 0)
    level = data.get('level')
    if level not in ['low','mid']:
        return jsonify({'message': '无效等级'}), 400
    if current_admin and target_id == current_admin.id:
        return jsonify({'message': 'forbidden'}), 403
    if not can_appoint_level(current_admin, level):
        return jsonify({'message': 'forbidden'}), 403
    target = User.query.get_or_404(target_id)
    if is_admin_user(target):
        return jsonify({'message': '已是管理员，不能重复任命'}), 400
    target.role = 'admin'
    target.admin_level = level
    target.admin_appointed_by = current_admin.id
    db.session.commit()
    return jsonify(target.to_dict())

@app.route('/api/admin/revoke', methods=['POST'])
@jwt_required()
def admin_revoke():
    current_admin = get_current_user()
    if not admin_required():
        return jsonify({'message': 'forbidden'}), 403
    data = request.json
    target_id = int(data.get('target_user_id') or 0)
    target = User.query.get_or_404(target_id)
    if current_admin and target.id == current_admin.id:
        return jsonify({'message': 'forbidden'}), 403
    if not can_revoke(current_admin, target):
        return jsonify({'message': 'forbidden'}), 403
    if target.admin_appointed_by and target.admin_appointed_by != current_admin.id:
        return jsonify({'message': 'forbidden'}), 403
    target.role = 'user'
    target.admin_level = None
    target.admin_appointed_by = None
    db.session.commit()
    return jsonify(target.to_dict())


@app.route('/api/my-stats', methods=['GET'])
@jwt_required()
def get_my_stats():
    user_id = int(get_jwt_identity())
    my_items = Item.query.filter_by(user_id=user_id).count()
    my_lost = Item.query.filter_by(user_id=user_id, category='lost').count()
    my_found = Item.query.filter_by(user_id=user_id, category='found').count()
    my_solved = Item.query.filter_by(user_id=user_id, status='closed').count()
    
    return jsonify({
        'my_items': my_items,
        'my_lost': my_lost,
        'my_found': my_found,
        'my_solved': my_solved
    })

@app.route('/api/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """获取当前用户的所有会话列表"""
    user_id = int(get_jwt_identity())
    
    # 查询所有包含当前用户的会话
    conversations = Conversation.query.filter(
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).order_by(Conversation.last_message_time.desc()).all()
    
    return jsonify([conv.to_dict(user_id) for conv in conversations])

@app.route('/api/conversations/<int:other_user_id>', methods=['GET', 'POST'])
@jwt_required()
def get_or_create_conversation(other_user_id):
    """获取或创建与指定用户的会话"""
    user_id = int(get_jwt_identity())
    
    if user_id == other_user_id:
        return jsonify({'message': '不能与自己创建会话'}), 400
    
    # 检查对方用户是否存在
    other_user = User.query.get(other_user_id)
    if not other_user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 查找是否已存在会话（双向查找）
    conversation = Conversation.query.filter(
        ((Conversation.user1_id == user_id) & (Conversation.user2_id == other_user_id)) |
        ((Conversation.user1_id == other_user_id) & (Conversation.user2_id == user_id))
    ).first()
    
    # 如果不存在，创建新会话
    if not conversation:
        conversation = Conversation(
            user1_id=user_id,
            user2_id=other_user_id
        )
        db.session.add(conversation)
        db.session.commit()
    
    return jsonify(conversation.to_dict(user_id))

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """获取指定会话的消息列表"""
    user_id = int(get_jwt_identity())
    
    # 验证会话是否属于当前用户
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user1_id != user_id and conversation.user2_id != user_id:
        return jsonify({'message': '无权限访问此会话'}), 403
    
    # 查询消息（不包括被撤回的）
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at.asc()).all()
    
    # 转换为字典，过滤掉被删除的消息
    result = []
    for msg in messages:
        msg_dict = msg.to_dict(user_id)
        if msg_dict is not None:
            result.append(msg_dict)
    
    # 标记所有未读消息为已读
    Message.query.filter_by(
        conversation_id=conversation_id,
        receiver_id=user_id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify(result)

@app.route('/api/conversation/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_by_id(conversation_id):
    user_id = int(get_jwt_identity())
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user1_id != user_id and conversation.user2_id != user_id:
        return jsonify({'message': '无权限访问此会话'}), 403
    return jsonify(conversation.to_dict(user_id))

def send_realtime_notification(user_id, notification_data):
    """发送实时通知到指定用户"""
    socketio.emit('new_notification', notification_data, room=f'user_{user_id}')

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """发送文字消息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # 验证会话
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user1_id != user_id and conversation.user2_id != user_id:
        return jsonify({'message': '无权限访问此会话'}), 403
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'message': '消息内容不能为空'}), 400
    
    # 确定接收者
    receiver_id = conversation.user2_id if conversation.user1_id == user_id else conversation.user1_id
    if getattr(user, 'is_banned', False) and (user.banned_by is None or receiver_id != user.banned_by):
        return jsonify({'message': '账户已被封禁，只能联系封禁管理员'}), 403
    
    # 创建消息
    message = Message(
        conversation_id=conversation_id,
        sender_id=user_id,
        receiver_id=receiver_id,
        content=content,
        message_type='text'
    )
    
    db.session.add(message)
    
    # 更新会话的最后消息
    conversation.last_message = content[:50] + ('...' if len(content) > 50 else '')
    conversation.last_message_time = datetime.now()
    
    db.session.commit()
    
    # 创建系统通知给接收者
    sender = User.query.get(user_id)
    create_notification(
        receiver_id,
        '新消息',
        f'{sender.username} 给你发送了一条消息',
        'info'
    )
    
    # 实时推送消息给接收者
    socketio.emit('new_message', message.to_dict(receiver_id), room=f'user_{receiver_id}')

    return jsonify(message.to_dict(user_id)), 201

@app.route('/api/conversations/<int:conversation_id>/send-image', methods=['POST'])
@jwt_required()
def send_image_message(conversation_id):
    """发送图片消息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # 验证会话
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user1_id != user_id and conversation.user2_id != user_id:
        return jsonify({'message': '无权限访问此会话'}), 403
    
    # 确定接收者
    receiver_id = conversation.user2_id if conversation.user1_id == user_id else conversation.user1_id
    if getattr(user, 'is_banned', False) and (user.banned_by is None or receiver_id != user.banned_by):
        return jsonify({'message': '账户已被封禁，只能联系封禁管理员'}), 403
    
    # 检查是否有文件
    if 'image' not in request.files:
        return jsonify({'message': '未上传图片'}), 400
    
    file = request.files['image']
    if file_too_large(file):
        return jsonify({'message': '图片大小超过限制（最大10MB）'}), 400
    
    original_filename = file.filename if hasattr(file, 'filename') else None
    
    # 如果文件名为空或者是 "blob"，生成一个默认文件名
    if not original_filename or original_filename == '' or original_filename.lower() == 'blob':
        # 根据文件内容类型确定扩展名
        content_type = file.content_type if hasattr(file, 'content_type') else 'image/jpeg'
        ext_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/bmp': 'bmp'
        }
        ext = ext_map.get(content_type, 'jpg')
        original_filename = f'image_{datetime.now().timestamp()}.{ext}'
    
    # 检查文件格式
    if not allowed_file(original_filename):
        return jsonify({'message': '不支持的图片格式'}), 400
    
    # 保存图片
    filename = secure_filename(f"msg_{datetime.now().timestamp()}_{original_filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # 创建消息记录
    message = Message(
        conversation_id=conversation_id,
        sender_id=user_id,
        receiver_id=receiver_id,
        content=None,
        message_type='image',
        image_path=filename
    )
    
    db.session.add(message)
    
    # 更新会话的最后消息
    conversation.last_message = '[图片]'
    conversation.last_message_time = datetime.now()
    
    db.session.commit()
    
    # 创建系统通知给接收者
    sender = User.query.get(user_id)
    create_notification(
        receiver_id,
        '新消息',
        f'{sender.username} 给你发送了一张图片',
        'info'
    )
    
    # 实时推送消息给接收者
    socketio.emit('new_message', message.to_dict(receiver_id), room=f'user_{receiver_id}')
    
    return jsonify(message.to_dict(user_id)), 201

@app.route('/api/message-image/<filename>', methods=['GET'])
def get_message_image(filename):
    """获取消息图片（通过query token验证）"""
    token = request.args.get('token')
    if not token:
        return jsonify({'message': 'Missing token'}), 401
    try:
        from flask_jwt_extended import decode_token
        decode_token(token)
    except Exception as e:
        return jsonify({'message': 'Invalid token'}), 422
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename)
        )
    except:
        return jsonify({'message': '图片不存在'}), 404

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """删除消息（只在自己这边删除）"""
    user_id = int(get_jwt_identity())
    message = Message.query.get_or_404(message_id)
    
    # 判断是发送者还是接收者
    if message.sender_id == user_id:
        message.is_deleted_by_sender = True
    elif message.receiver_id == user_id:
        message.is_deleted_by_receiver = True
    else:
        return jsonify({'message': '无权限删除此消息'}), 403
    
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/api/messages/<int:message_id>/recall', methods=['PUT'])
@jwt_required()
def recall_message(message_id):
    """撤回消息"""
    user_id = int(get_jwt_identity())
    message = Message.query.get_or_404(message_id)
    
    # 只有发送者可以撤回
    if message.sender_id != user_id:
        return jsonify({'message': '只能撤回自己发送的消息'}), 403
    
    # 检查是否已撤回
    if message.is_recalled:
        return jsonify({'message': '消息已撤回'}), 400
    
    # 检查撤回时间限制（可选，如2分钟内）
    time_diff = datetime.now() - message.created_at
    if time_diff.total_seconds() > 120:  # 2分钟
        return jsonify({'message': '超过2分钟无法撤回'}), 400
    
    # 标记为已撤回
    message.is_recalled = True
    
    # 删除图片文件
    if message.image_path:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], message.image_path))
        except:
            pass
    
    db.session.commit()
    
    return jsonify({'message': '撤回成功'})

@app.route('/api/messages/unread-count', methods=['GET'])
@jwt_required()
def get_unread_message_count():
    """获取未读消息总数"""
    user_id = int(get_jwt_identity())
    
    count = Message.query.filter_by(
        receiver_id=user_id,
        is_read=False,
        is_deleted_by_receiver=False
    ).count()
    
    return jsonify({'count': count})

# 数据导出
@app.route('/api/export', methods=['GET'])
@jwt_required()
def export_data():
    user_id = int(get_jwt_identity())
    category = request.args.get('category', '')
    
    # 查询数据
    query = Item.query
    if category:
        query = query.filter_by(category=category)
    
    items = query.order_by(Item.created_at.desc()).all()

    # 创建Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "失物招领数据"
    
    # 添加表头
    headers = ['ID', '标题', '描述', '类型', '物品类型', '地点', '联系人', '联系电话', '日期', '状态', '发布时间', '发布人']
    ws.append(headers)
    
    # 添加数据
    for item in items:
        ws.append([
            item.id,
            item.title,
            item.description,
            '失物' if item.category == 'lost' else '拾物',
            item.item_type,
            item.location,
            item.contact_name,
            item.contact_phone,
            item.date,
            '进行中' if item.status == 'open' else '已解决',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            item.user.username
        ])
    
    # 保存到内存
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'失物招领数据_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# ==================== WebSocket 事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    try:
        # 从请求中获取token（需要客户端在连接时传递）
        token = request.args.get('token')
        if not token:
            return False  # 拒绝连接
        
        # 验证token（使用Flask-JWT-Extended）
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
            user_id = decoded['sub']
            
            # 加入用户专属房间
            join_room(f'user_{user_id}')
            print(f'✅ 用户 {user_id} 已连接 WebSocket')
            
            # 可以存储用户在线状态到Redis等
            # r.sadd('online_users', user_id)
            
        except Exception as e:
            print(f'❌ Token验证失败: {e}')
            return False
            
    except Exception as e:
        print(f'❌ 连接失败: {e}')
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接事件"""
    try:
        token = request.args.get('token')
        if token:
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            user_id = decoded['sub']
            
            leave_room(f'user_{user_id}')
            print(f'🔌 用户 {user_id} 已断开 WebSocket')
            
            # 移除在线状态
            # r.srem('online_users', user_id)
            
    except Exception as e:
        print(f'❌ 断开连接处理失败: {e}')

@socketio.on('send_message')
def handle_send_message(data):
    """接收客户端发送的消息事件"""
    try:
        token = request.args.get('token')
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        
        conversation_id = data.get('conversation_id')
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        # 创建消息记录（复用现有逻辑）
        message = Message(
            conversation_id=conversation_id,
            sender_id=user_id,
            receiver_id=receiver_id,
            content=content,
            message_type='text'
        )
        db.session.add(message)
        
        # 更新会话
        conversation = Conversation.query.get(conversation_id)
        conversation.last_message = content[:50]
        conversation.last_message_time = datetime.now()
        
        db.session.commit()
        
        # 发送给接收者（实时推送）
        emit('new_message', message.to_dict(receiver_id), room=f'user_{receiver_id}')
        
        # 同时也发送给发送者（用于实时更新发送者界面）
        emit('message_sent', message.to_dict(user_id), room=f'user_{user_id}')
        
        print(f'✉️ 消息已发送：用户 {user_id} -> 用户 {receiver_id}')
        
    except Exception as e:
        print(f'❌ 发送消息失败: {e}')
        emit('error', {'message': '发送失败'})

@socketio.on('typing')
def handle_typing(data):
    """处理正在输入状态"""
    try:
        token = request.args.get('token')
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        
        receiver_id = data.get('receiver_id')
        
        # 通知对方正在输入
        emit('user_typing', {'user_id': user_id}, room=f'user_{receiver_id}')
        
    except Exception as e:
        print(f'❌ 处理输入状态失败: {e}')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ 数据库表创建成功！")
    
    print("🚀 服务器启动在 http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', debug=False, port=5000)

# 旧位置的同名路由删除，避免服务启动后再注册导致 404 预检命中默认处理
