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

# 敏感词列表（中英文）- 以多字词/短语为主，避免单字误伤（如曹操、日本、生日、干活、打球等）
SENSITIVE_WORDS = [
    # 中文敏感词（短语优先，不含易误伤单字如操/日/干/打/死/杀/骗/偷/抢/盗/性/淫/骚/贱）
    '傻逼', '傻B', 'SB', '草泥马', '操你妈', '操他妈', '你妈', '他妈的', '妈的', '卧槽', '我靠',
    '滚', '去死', '打死', '杀人', '砍死', '揍你', '干你', '艹',
    '垃圾', '废物', '白痴', '智障', '脑残', '弱智', '蠢货', '笨蛋',
    '骗子', '诈骗', '坑人', '骗人', '偷窃', '抢劫', '盗窃', '强奸',
    '色情', '黄色', '做爱', '性爱', '淫荡', '淫秽', '骚货', '贱人',
    '政治', '政府', '党', '国家', '领导人',
    # 英文敏感词（整词匹配，避免 skill 中含 kill 等误伤在下方逻辑中处理）
    'fuck', 'shit', 'damn', 'bitch', 'asshole', 'bastard', 'crap',
    'stupid', 'idiot', 'moron', 'retard', 'dumb', 'fool',
    'kill', 'die', 'death', 'murder', 'suicide',
    'sex', 'porn', 'pornography', 'nude', 'naked', 'erotic',
    'drug', 'cocaine', 'heroin', 'marijuana',
    'hate', 'violence', 'terror', 'terrorist',
    'spam', 'scam', 'fraud', 'cheat', 'steal', 'rob'
]

# 安全词白名单：包含敏感字但为正常用语的词/短语，检测前会先替换为占位符，避免误伤
# 按长度从长到短排序，先替换长短语再替换短词（如先“曹操”再“操”所在的其他安全词）
SAFE_PHRASES = [
    # 含“操”
    '曹操', '操作', '体操', '操守', '操劳', '操持', '操办', '操场', '操练', '情操', '节操',
    # 含“日”
    '日本', '日期', '生日', '今日', '明日', '昨日', '节日', '假日', '星期日', '工作日', '日用', '日记', '日光', '日常', '日用品', '某日',
    # 含“干”
    '干活', '干净', '干杯', '饼干', '若干', '干扰', '干练', '干吗', '才干', '树干', '骨干', '包干', '晾干', '风干', '相干',
    # 含“打”
    '打球', '打字', '打工', '打扫', '打针', '打饭', '打包', '打车', '打水', '打开', '打算', '打听', '打扮', '打击', '打印', '打折', '打勾', '打杂', '打牌', '打游戏', '打电话',
    # 含“死”（仅保留明显中性）
    '生死', '死亡', '死活', '死心', '死党', '死结', '死胡同', '猝死', '生死线',
    # 含“杀”（游戏/中性）
    '杀菌', '杀毒', '杀青', '杀价', '杀气', '杀鸡', '杀鱼',
    # 含“坑”
    '坑道', '坑洼', '坑口', '矿坑', '泥坑', '坑坑洼洼',
    # 含“骗”的少，不加；含“偷”“抢”“盗”的常见中性词
    '偷懒', '偷看', '偷听', '偷袭', '抢购', '抢修', '抢收', '抢答', '盗版', '盗墓', '盗贼', '海盗', '盗窃案',
    # 含“性”
    '性别', '性格', '理性', '感性', '人性', '个性', '性质', '性能', '弹性', '惯性', '记性', '索性', '索性', '良性', '恶性', '中性',
    # 含“淫”（书面/中性）
    '淫雨', '淫威',
    # 含“骚”
    '骚动', '骚乱', '风骚', '离骚',
    # 含“贱”
    '贱卖', '贱价', '贵贱', '贫贱',
    # 英文：ass 在 class、pass、glass 等中误伤，用整词匹配时已避免；kill 在 skill 等，用整词
]
# 按长度降序，优先替换更长短语
SAFE_PHRASES_SORTED = sorted(SAFE_PHRASES, key=len, reverse=True)

# 占位符：用于替换安全词，避免被敏感词匹配（使用零宽字符，不改变长度）
def _placeholder(length):
    return '\u200B' * length  # 零宽空格

def _is_word_boundary(text, start, length):
    """判断 start 处长度为 length 的子串是否为整词（前后非字母/数字）"""
    if start > 0 and (text[start - 1].isalnum() or text[start - 1] == '_'):
        return False
    end = start + length
    if end < len(text) and (text[end].isalnum() or text[end] == '_'):
        return False
    return True

def contains_sensitive_words(text):
    """检查文本是否包含敏感词（先屏蔽安全词白名单，再检测，减少误伤如曹操、操作、日本等）"""
    if not text:
        return False, []
    # 先对原文做安全词替换（仅用于检测的副本）
    check_text = text
    for phrase in SAFE_PHRASES_SORTED:
        if phrase in check_text:
            check_text = check_text.replace(phrase, _placeholder(len(phrase)))
    # 再对替换后的文本做敏感词检测
    check_lower = check_text.lower()
    found_words = []
    for word in SENSITIVE_WORDS:
        w_lower = word.lower()
        if w_lower not in check_lower:
            continue
        # 英文敏感词要求整词匹配，避免误伤 skill(kill)、class(ass)、password(ass) 等
        if word.isascii():
            idx = 0
            while True:
                pos = check_lower.find(w_lower, idx)
                if pos == -1:
                    break
                if _is_word_boundary(check_text, pos, len(word)):
                    found_words.append(word)
                    break
                idx = pos + 1
        else:
            found_words.append(word)
    return len(found_words) > 0, found_words

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
    if request.method in ['POST', 'PUT'] and ('/api/reports/' in request.path or '/api/items/' in request.path):
        print(f'[BEFORE_REQUEST] Method: {request.method}')
        print(f'[BEFORE_REQUEST] Path: {request.path}')
        print(f'[BEFORE_REQUEST] Content-Type: {request.content_type}')
        print(f'[BEFORE_REQUEST] Headers: {dict(request.headers)}')
        if '/api/items/' in request.path and '/images' in request.path:
            print(f'[BEFORE_REQUEST] Items images request detected')
            print(f'[BEFORE_REQUEST] Form keys: {list(request.form.keys())}')
            print(f'[BEFORE_REQUEST] Files keys: {list(request.files.keys())}')

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
    teacher_approval_status = db.Column(db.String(20), default='approved')  # 教师审核状态: pending/approved/rejected
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
            'teacher_approval_status': self.teacher_approval_status or 'approved',
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

class Favorite(db.Model):
    """收藏表"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    user = db.relationship('User', backref='favorites')
    item = db.relationship('Item', backref='favorited_by')
    
    # 唯一约束：一个用户只能收藏一个物品一次
    __table_args__ = (db.UniqueConstraint('user_id', 'item_id', name='unique_user_item_favorite'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_id': self.item_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Comment(db.Model):
    """评论表"""
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # 父评论ID（用于回复）
    reply_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 回复的目标用户ID（用于二级回复）
    is_deleted = db.Column(db.Boolean, default=False)
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    item = db.relationship('Item', backref='comments')
    user = db.relationship('User', foreign_keys=[user_id], backref='comments')
    reply_to_user = db.relationship('User', foreign_keys=[reply_to_user_id], backref='replied_comments')
    parent = db.relationship('Comment', remote_side=[id], backref='replies')
    
    def to_dict(self, current_user_id=None):
        # 检查当前用户是否已点赞
        is_liked = False
        if current_user_id:
            is_liked = CommentLike.query.filter_by(
                comment_id=self.id,
                user_id=current_user_id
            ).first() is not None
        
        # 判断是几级回复
        level = 0  # 0表示顶级评论
        if self.parent_id:
            parent_comment = Comment.query.get(self.parent_id)
            if parent_comment:
                if parent_comment.parent_id:
                    level = 2  # 二级回复（回复的回复）
                else:
                    level = 1  # 一级回复（回复顶级评论）
        
        return {
            'id': self.id,
            'item_id': self.item_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'user_avatar': f'/api/avatar/{self.user.avatar_path}' if self.user and self.user.avatar_path else None,
            'content': self.content,
            'parent_id': self.parent_id,
            'reply_to_user_id': self.reply_to_user_id,
            'reply_to_username': self.reply_to_user.username if self.reply_to_user else None,
            'is_deleted': self.is_deleted,
            'like_count': self.like_count,
            'is_liked': is_liked,
            'level': level,  # 回复层级：1=一级回复，2=二级回复
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'replies': [reply.to_dict(current_user_id) for reply in self.replies if not reply.is_deleted] if self.replies else [],
            'replies_count': len([r for r in self.replies if not r.is_deleted]) if self.replies else 0
        }

class CommentLike(db.Model):
    """评论点赞表"""
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    comment = db.relationship('Comment', backref='likes')
    user = db.relationship('User', backref='comment_likes')
    
    # 唯一约束：一个用户只能点赞一个评论一次
    __table_args__ = (db.UniqueConstraint('comment_id', 'user_id', name='unique_comment_user_like'),)

class Claim(db.Model):
    """认领表"""
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 认领人
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 发布者
    description = db.Column(db.Text)  # 认领说明/证据描述
    image_path = db.Column(db.String(255))  # 认领证据图片路径（单张，JSON格式存储多张）
    status = db.Column(db.String(20), default='pending')  # pending: 待确认, approved: 已确认, rejected: 已拒绝
    is_public = db.Column(db.Boolean, default=False)  # 是否公开认领历史
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    item = db.relationship('Item', backref='claims')
    claimant = db.relationship('User', foreign_keys=[claimant_id], backref='claims_made')
    owner = db.relationship('User', foreign_keys=[owner_id], backref='claims_received')
    
    def to_dict(self):
        # 解析图片路径（支持JSON格式的多张图片）
        image_urls = []
        if self.image_path:
            try:
                import json
                image_paths = json.loads(self.image_path) if self.image_path.startswith('[') else [self.image_path]
                image_urls = [f'/api/image/{path}' for path in image_paths]
            except:
                image_urls = [f'/api/image/{self.image_path}'] if self.image_path else []
        
        return {
            'id': self.id,
            'item_id': self.item_id,
            'claimant_id': self.claimant_id,
            'claimant_username': self.claimant.username if self.claimant else None,
            'owner_id': self.owner_id,
            'description': self.description,
            'image_urls': image_urls,
            'status': self.status,
            'is_public': bool(self.is_public),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

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
            ('teacher_approval_status', 'TEXT'),
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
    
    # 创建新表（如果不存在）
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(basedir, 'lost_found.db'))
        cur = conn.cursor()
        
        # 检查表是否存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorite'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE favorite (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    FOREIGN KEY (item_id) REFERENCES item (id),
                    UNIQUE(user_id, item_id)
                )
            """)
            print('✅ Favorite 表创建成功')
        
        # 检查并添加claim表的image_path字段
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='claim'")
        if cur.fetchone():
            cur.execute("PRAGMA table_info(claim)")
            claim_cols = [row[1] for row in cur.fetchall()]
            if 'image_path' not in claim_cols:
                cur.execute("ALTER TABLE claim ADD COLUMN image_path TEXT")
                print('✅ Claim 表迁移成功：已添加 image_path 字段')
            # 检查并添加is_public字段
            if 'is_public' not in claim_cols:
                cur.execute("ALTER TABLE claim ADD COLUMN is_public BOOLEAN DEFAULT 0")
                print('✅ Claim 表迁移成功：已添加 is_public 字段')
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comment'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE comment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    parent_id INTEGER,
                    is_deleted BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES item (id),
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    FOREIGN KEY (parent_id) REFERENCES comment (id)
                )
            """)
            print('✅ Comment 表创建成功')
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='claim'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE claim (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    claimant_id INTEGER NOT NULL,
                    owner_id INTEGER NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES item (id),
                    FOREIGN KEY (claimant_id) REFERENCES user (id),
                    FOREIGN KEY (owner_id) REFERENCES user (id)
                )
            """)
            print('✅ Claim 表创建成功')
        
        # 检查comment表是否需要添加新字段
        cur.execute("PRAGMA table_info(comment)")
        comment_cols = [row[1] for row in cur.fetchall()]
        if 'like_count' not in comment_cols:
            cur.execute("ALTER TABLE comment ADD COLUMN like_count INTEGER DEFAULT 0")
            print('✅ Comment 表已添加 like_count 字段')
        if 'reply_to_user_id' not in comment_cols:
            cur.execute("ALTER TABLE comment ADD COLUMN reply_to_user_id INTEGER")
            print('✅ Comment 表已添加 reply_to_user_id 字段')
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comment_like'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE comment_like (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comment_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (comment_id) REFERENCES comment (id),
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    UNIQUE(comment_id, user_id)
                )
            """)
            print('✅ CommentLike 表创建成功')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'新表创建失败: {e}')

# 文件上传辅助函数
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'avif', 'svg', 'tiff', 'tif', 'ico', 'heic', 'heif'}
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
    
    # 教师需要审核，学生直接通过
    if identity == 'teacher':
        user.role = 'user'  # 先设为普通用户
        user.admin_level = None
        user.admin_appointed_by = None
        user.teacher_approval_status = 'pending'  # 待审核
    else:
        user.teacher_approval_status = 'approved'  # 学生直接通过
    
    db.session.add(user)
    db.session.commit()
    
    # 如果是教师，通知高级管理员审核
    if identity == 'teacher':
        # 查找所有高级管理员
        high_admins = User.query.filter_by(role='admin', admin_level='high').all()
        for admin in high_admins:
            create_notification(
                admin.id,
                '新教师注册待审核',
                f'教师 {user.username} ({user.email}) 申请注册，请前往管理员页面审核。',
                'warning'
            )
        return jsonify({
            'message': '注册成功，您的账户正在等待管理员审核，审核通过后即可使用',
            'user': user.to_dict(),
            'requires_approval': True
        }), 201
    else:
        # 学生直接创建欢迎通知
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
    
    # 检查教师审核状态
    if user.user_type == 'teacher' and user.teacher_approval_status == 'pending':
        return jsonify({
            'message': '您的账户正在等待管理员审核，审核通过后即可登录',
            'requires_approval': True
        }), 403
    
    if user.user_type == 'teacher' and user.teacher_approval_status == 'rejected':
        return jsonify({
            'message': '您的注册申请已被拒绝，如有疑问请联系管理员',
            'approval_rejected': True
        }), 403
    
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
    
    # 敏感词检查
    title = data.get('title', '')
    description = data.get('description', '')
    has_sensitive, found_words = contains_sensitive_words(title + ' ' + description)
    if has_sensitive:
        return jsonify({
            'message': f'发布内容包含敏感词，请修改后再发布。检测到的敏感词：{", ".join(found_words[:3])}',
            'sensitive_words': found_words
        }), 400
    
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
    print(f'[DEBUG] ========== 收到更新图片请求 ==========')
    print(f'[DEBUG] item_id={item_id}, method={request.method}')
    print(f'[DEBUG] Content-Type: {request.content_type}')
    print(f'[DEBUG] URL: {request.url}')
    print(f'[DEBUG] Path: {request.path}')
    print(f'[DEBUG] Form data keys: {list(request.form.keys())}')
    print(f'[DEBUG] Files keys: {list(request.files.keys())}')
    
    try:
        user_id = int(get_jwt_identity())
    except Exception as e:
        print(f'[ERROR] JWT 验证失败: {e}')
        raise
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
            # 处理 "blob" 文件名
            if original_filename.lower() == 'blob' or not original_filename:
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
            if allowed_file(original_filename):
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
                # 处理 "blob" 文件名
                if original_filename.lower() == 'blob' or not original_filename:
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
                if allowed_file(original_filename):
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
            # URL 解码，处理可能的编码字符
            try:
                from urllib.parse import unquote
                filename = unquote(filename)
            except:
                pass
            # 清理文件名：只取文件名部分，去除路径
            filename = os.path.basename(filename)
            # 验证文件是否存在
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                final_image_paths.append(filename)
            else:
                print(f'[WARNING] 要保留的图片文件不存在，跳过: {filename}')
                print(f'[WARNING] 文件路径: {filepath}')
    
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

# 添加一个测试路由来验证路由注册
@app.route('/api/test/items-images', methods=['GET', 'POST'])
def test_items_images_route():
    """测试路由是否注册"""
    return jsonify({'message': '路由已注册', 'path': request.path, 'method': request.method}), 200

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
        # URL 解码，处理可能的编码字符
        try:
            from urllib.parse import unquote
            filename = unquote(filename)
        except:
            pass
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
        # 创建解封通知
        try:
            create_notification(
                user.id,
                '账户解封',
                f'{current_admin.username} 于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 已为你解封，现在可以正常使用系统了。',
                'success'
            )
            print(f'[DEBUG] 已为用户 {user.id} ({user.username}) 创建解封通知')
        except Exception as e:
            print(f'[ERROR] 创建解封通知失败: {e}')
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

@app.route('/api/admin/teachers/pending', methods=['GET'])
@jwt_required()
def get_pending_teachers():
    """获取待审核的教师列表（仅高级管理员）"""
    current_admin = get_current_user()
    if not admin_required() or current_admin.admin_level != 'high':
        return jsonify({'message': 'forbidden'}), 403
    
    pending_teachers = User.query.filter_by(
        user_type='teacher',
        teacher_approval_status='pending'
    ).order_by(User.created_at.desc()).all()
    
    return jsonify([user.to_dict() for user in pending_teachers])

@app.route('/api/admin/teachers/<int:teacher_id>/approve', methods=['POST'])
@jwt_required()
def approve_teacher(teacher_id):
    """批准教师注册（仅高级管理员）"""
    current_admin = get_current_user()
    if not admin_required() or current_admin.admin_level != 'high':
        return jsonify({'message': 'forbidden'}), 403
    
    teacher = User.query.get_or_404(teacher_id)
    if teacher.user_type != 'teacher':
        return jsonify({'message': '该用户不是教师'}), 400
    
    if teacher.teacher_approval_status != 'pending':
        return jsonify({'message': '该教师已审核'}), 400
    
    # 批准：设置为管理员
    teacher.teacher_approval_status = 'approved'
    teacher.role = 'admin'
    teacher.admin_level = 'mid'
    teacher.admin_appointed_by = current_admin.id
    
    db.session.commit()
    
    # 通知教师审核通过
    create_notification(
        teacher.id,
        '注册审核通过',
        f'恭喜！您的教师账户已通过审核，现在可以使用系统了。',
        'success'
    )
    
    return jsonify({
        'message': '审核通过',
        'user': teacher.to_dict()
    })

@app.route('/api/admin/teachers/<int:teacher_id>/reject', methods=['POST'])
@jwt_required()
def reject_teacher(teacher_id):
    """拒绝教师注册（仅高级管理员）"""
    current_admin = get_current_user()
    if not admin_required() or current_admin.admin_level != 'high':
        return jsonify({'message': 'forbidden'}), 403
    
    teacher = User.query.get_or_404(teacher_id)
    if teacher.user_type != 'teacher':
        return jsonify({'message': '该用户不是教师'}), 400
    
    if teacher.teacher_approval_status != 'pending':
        return jsonify({'message': '该教师已审核'}), 400
    
    data = request.json or {}
    reason = data.get('reason', '')
    
    # 拒绝
    teacher.teacher_approval_status = 'rejected'
    teacher.role = 'user'  # 保持为普通用户
    
    db.session.commit()
    
    # 通知教师审核被拒绝
    reject_msg = f'很抱歉，您的教师注册申请未通过审核。'
    if reason:
        reject_msg += f' 原因：{reason}'
    create_notification(
        teacher.id,
        '注册审核未通过',
        reject_msg,
        'error'
    )
    
    return jsonify({
        'message': '已拒绝',
        'user': teacher.to_dict()
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

# ==================== 收藏相关API ====================

@app.route('/api/items/<int:item_id>/favorite', methods=['POST'])
@jwt_required()
def add_favorite(item_id):
    """收藏物品"""
    user_id = int(get_jwt_identity())
    item = Item.query.get_or_404(item_id)
    
    # 检查是否已收藏
    existing = Favorite.query.filter_by(user_id=user_id, item_id=item_id).first()
    if existing:
        return jsonify({'message': '已收藏'}), 400
    
    favorite = Favorite(user_id=user_id, item_id=item_id)
    db.session.add(favorite)
    db.session.commit()
    
    # 创建通知给发布者
    if item.user_id != user_id:
        create_notification(
            item.user_id,
            '物品被收藏',
            f'你的{item.category == "lost" and "失物" or "拾物"}《{item.title}》被收藏了',
            'info',
            item_id
        )
    
    return jsonify({'message': '收藏成功', 'favorite': favorite.to_dict()}), 201

@app.route('/api/items/<int:item_id>/favorite', methods=['DELETE'])
@jwt_required()
def remove_favorite(item_id):
    """取消收藏"""
    user_id = int(get_jwt_identity())
    favorite = Favorite.query.filter_by(user_id=user_id, item_id=item_id).first()
    
    if not favorite:
        return jsonify({'message': '未收藏'}), 404
    
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({'message': '取消收藏成功'})

@app.route('/api/items/<int:item_id>/favorite/status', methods=['GET'])
@jwt_required()
def get_favorite_status(item_id):
    """获取收藏状态"""
    user_id = int(get_jwt_identity())
    favorite = Favorite.query.filter_by(user_id=user_id, item_id=item_id).first()
    
    return jsonify({'is_favorited': favorite is not None})

@app.route('/api/my-favorites', methods=['GET'])
@jwt_required()
def get_my_favorites():
    """获取我的收藏列表"""
    user_id = int(get_jwt_identity())
    page = int(request.args.get('page', 1) or 1)
    page_size = int(request.args.get('page_size', 12) or 12)
    
    favorites = Favorite.query.filter_by(user_id=user_id)\
        .order_by(Favorite.created_at.desc())\
        .paginate(page=page, per_page=page_size, error_out=False)
    
    items = [fav.item.to_dict() for fav in favorites.items]
    
    return jsonify({
        'items': items,
        'total': favorites.total,
        'page': page,
        'page_size': page_size
    })

# ==================== 评论相关API ====================

@app.route('/api/items/<int:item_id>/comments', methods=['GET'])
def get_comments(item_id):
    """获取物品评论列表"""
    # 尝试获取当前用户ID（如果已登录）
    current_user_id = None
    try:
        # 从请求头或查询参数获取token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            current_user_id = int(decoded['sub'])
    except:
        pass
    
    # 获取顶级评论（parent_id为None）
    top_level_comments = Comment.query.filter_by(item_id=item_id, parent_id=None, is_deleted=False)\
        .order_by(Comment.created_at.desc()).all()
    
    result = []
    for comment in top_level_comments:
        comment_dict = comment.to_dict(current_user_id)
        # 获取该评论的所有一级回复
        level1_replies = Comment.query.filter_by(parent_id=comment.id, is_deleted=False)\
            .order_by(Comment.created_at.asc()).all()
        
        # 获取所有二级回复（parent_id指向一级回复的）
        all_replies = []
        for level1_reply in level1_replies:
            level1_reply_dict = level1_reply.to_dict(current_user_id)
            # 获取该一级回复的所有二级回复
            level2_replies = Comment.query.filter_by(parent_id=level1_reply.id, is_deleted=False)\
                .order_by(Comment.created_at.asc()).all()
            level1_reply_dict['level2_replies'] = [r.to_dict(current_user_id) for r in level2_replies]
            all_replies.append(level1_reply_dict)
        
        comment_dict['replies'] = all_replies
        comment_dict['replies_count'] = len(all_replies)
        result.append(comment_dict)
    
    return jsonify(result)

@app.route('/api/items/<int:item_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(item_id):
    """创建评论"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法评论'}), 403
    
    item = Item.query.get_or_404(item_id)
    data = request.json
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id')
    reply_to_user_id = data.get('reply_to_user_id')  # 回复的目标用户ID
    
    if not content:
        return jsonify({'message': '评论内容不能为空'}), 400
    
    # 如果是回复，确定reply_to_user_id
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if parent_comment:
            # 如果指定了reply_to_user_id，使用指定的；否则回复父评论的作者
            if not reply_to_user_id:
                reply_to_user_id = parent_comment.user_id
            # 如果自己回复自己，reply_to_user_id保持为父评论的作者（用于显示格式判断）
        else:
            return jsonify({'message': '父评论不存在'}), 404
    
    comment = Comment(
        item_id=item_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id,
        reply_to_user_id=reply_to_user_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # 刷新对象以获取关联数据
    db.session.refresh(comment)
    
    # 创建通知
    if parent_id:
        # 回复评论：通知被回复的用户
        if reply_to_user_id and reply_to_user_id != user_id:
            create_notification(
                reply_to_user_id,
                '新回复',
                f'{user.username} 回复了你的评论',
                'info',
                item_id
            )
    else:
        # 一级评论：通知物品发布者
        if item.user_id != user_id:
            create_notification(
                item.user_id,
                '新评论',
                f'{user.username} 评论了你的{item.category == "lost" and "失物" or "拾物"}《{item.title}》',
                'info',
                item_id
            )
    
    return jsonify(comment.to_dict(user_id)), 201

@app.route('/api/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """更新评论"""
    user_id = int(get_jwt_identity())
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'message': '评论内容不能为空'}), 400
    
    comment.content = content
    db.session.commit()
    
    return jsonify(comment.to_dict(user_id))

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """删除评论（软删除）"""
    user_id = int(get_jwt_identity())
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    comment.is_deleted = True
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@jwt_required()
def like_comment(comment_id):
    """点赞评论"""
    user_id = int(get_jwt_identity())
    comment = Comment.query.get_or_404(comment_id)
    
    # 检查是否已点赞
    existing = CommentLike.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    if existing:
        return jsonify({'message': '已点赞'}), 400
    
    # 添加点赞
    like = CommentLike(comment_id=comment_id, user_id=user_id)
    comment.like_count = (comment.like_count or 0) + 1
    db.session.add(like)
    db.session.commit()
    
    return jsonify({'message': '点赞成功', 'like_count': comment.like_count}), 201

@app.route('/api/comments/<int:comment_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_comment(comment_id):
    """取消点赞"""
    user_id = int(get_jwt_identity())
    like = CommentLike.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    
    if not like:
        return jsonify({'message': '未点赞'}), 404
    
    comment = Comment.query.get_or_404(comment_id)
    comment.like_count = max((comment.like_count or 0) - 1, 0)
    db.session.delete(like)
    db.session.commit()
    
    return jsonify({'message': '取消点赞成功', 'like_count': comment.like_count})

# ==================== 认领相关API ====================

@app.route('/api/items/<int:item_id>/claim', methods=['POST'])
@jwt_required()
def create_claim(item_id):
    """创建认领申请（支持图片上传）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if getattr(user, 'is_banned', False):
        return jsonify({'message': '账户已被封禁，无法认领'}), 403
    
    item = Item.query.get_or_404(item_id)
    
    # 不能认领自己的物品
    if item.user_id == user_id:
        return jsonify({'message': '不能认领自己发布的物品'}), 400
    
    # 检查是否已有待处理的认领
    existing = Claim.query.filter_by(
        item_id=item_id,
        claimant_id=user_id,
        status='pending'
    ).first()
    
    if existing:
        return jsonify({'message': '已有待处理的认领申请'}), 400
    
    # 获取表单数据（支持JSON和FormData）
    if request.is_json:
        data = request.json
        description = data.get('description', '').strip()
        image_paths = []
    else:
        # FormData格式
        description = request.form.get('description', '').strip()
        image_paths = []
        
        # 处理上传的图片（支持多张）
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    import time
                    import random
                    import string
                    timestamp = int(time.time() * 1000)
                    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    original_filename = file.filename
                    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
                    filename = secure_filename(f"claim_{timestamp}_{random_suffix}.{ext}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_paths.append(filename)
    
    # 保存图片路径（JSON格式，统一保存为数组）
    image_path_json = None
    if image_paths:
        import json
        image_path_json = json.dumps(image_paths)  # 统一保存为JSON数组格式
    
    claim = Claim(
        item_id=item_id,
        claimant_id=user_id,
        owner_id=item.user_id,
        description=description,
        image_path=image_path_json,
        status='pending'
    )
    
    db.session.add(claim)
    db.session.commit()
    
    # 创建通知给发布者
    create_notification(
        item.user_id,
        '认领申请',
        f'{user.username} 申请认领你的{item.category == "lost" and "失物" or "拾物"}《{item.title}》',
        'warning',
        item_id
    )
    
    return jsonify(claim.to_dict()), 201

@app.route('/api/items/<int:item_id>/claims', methods=['GET'])
@jwt_required()
def get_item_claims(item_id):
    """获取物品的认领列表（仅发布者可见）"""
    user_id = int(get_jwt_identity())
    item = Item.query.get_or_404(item_id)
    
    # 只有发布者可以查看认领列表
    if item.user_id != user_id:
        return jsonify({'message': '无权限查看'}), 403
    
    claims = Claim.query.filter_by(item_id=item_id)\
        .order_by(Claim.created_at.desc()).all()
    
    return jsonify([claim.to_dict() for claim in claims])

@app.route('/api/claims/<int:claim_id>/approve', methods=['PUT'])
@jwt_required()
def approve_claim(claim_id):
    """批准认领"""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)
    item = Item.query.get_or_404(claim.item_id)
    
    # 只有发布者可以批准
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    if claim.status != 'pending':
        return jsonify({'message': '认领状态不正确'}), 400
    
    # 更新认领状态
    claim.status = 'approved'
    claim.updated_at = datetime.now()
    
    # 更新物品状态为已解决
    item.status = 'closed'
    
    # 拒绝其他待处理的认领
    Claim.query.filter_by(
        item_id=claim.item_id,
        status='pending'
    ).filter(Claim.id != claim_id).update({'status': 'rejected'})
    
    db.session.commit()
    
    # 创建通知给认领人
    create_notification(
        claim.claimant_id,
        '认领成功',
        f'你的认领申请已通过！物品《{item.title}》已确认为你的{item.category == "lost" and "失物" or "拾物"}。',
        'success',
        claim.item_id
    )
    
    # 创建通知给发布者
    create_notification(
        item.user_id,
        '认领完成',
        f'物品《{item.title}》已被认领，状态已更新为已解决。',
        'success',
        claim.item_id
    )
    
    return jsonify(claim.to_dict())

@app.route('/api/claims/<int:claim_id>/reject', methods=['PUT'])
@jwt_required()
def reject_claim(claim_id):
    """拒绝认领"""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)
    item = Item.query.get_or_404(claim.item_id)
    
    # 只有发布者可以拒绝
    if item.user_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    if claim.status != 'pending':
        return jsonify({'message': '认领状态不正确'}), 400
    
    claim.status = 'rejected'
    claim.updated_at = datetime.now()
    db.session.commit()
    
    # 创建通知给认领人
    create_notification(
        claim.claimant_id,
        '认领被拒绝',
        f'你的认领申请未通过。物品《{item.title}》的认领申请已被拒绝。',
        'warning',
        claim.item_id
    )
    
    return jsonify(claim.to_dict())

@app.route('/api/my-claims', methods=['GET'])
@jwt_required()
def get_my_claims():
    """获取我的认领记录"""
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '')
    
    query = Claim.query.filter_by(claimant_id=user_id)
    if status:
        query = query.filter_by(status=status)
    
    claims = query.order_by(Claim.created_at.desc()).all()
    
    result = []
    for claim in claims:
        claim_dict = claim.to_dict()
        claim_dict['item'] = claim.item.to_dict() if claim.item else None
        result.append(claim_dict)
    
    return jsonify(result)

@app.route('/api/pending-claims', methods=['GET'])
@jwt_required()
def get_pending_claims():
    """获取所有认领申请（仅发布者可见，支持状态筛选）"""
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '')  # 空字符串表示获取所有状态
    
    # 获取该用户发布的所有物品的认领申请
    query = Claim.query.join(Item).filter(Item.user_id == user_id)
    
    # 如果指定了状态，则筛选
    if status:
        query = query.filter(Claim.status == status)
    
    claims = query.order_by(Claim.created_at.desc()).all()
    
    result = []
    for claim in claims:
        claim_dict = claim.to_dict()
        claim_dict['item'] = claim.item.to_dict() if claim.item else None
        result.append(claim_dict)
    
    return jsonify(result)

@app.route('/api/claims/<int:claim_id>/public', methods=['PUT'])
@jwt_required()
def toggle_claim_public(claim_id):
    """切换认领记录的公开状态"""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)
    
    # 只有认领人自己可以修改公开状态
    if claim.claimant_id != user_id:
        return jsonify({'message': '无权限操作'}), 403
    
    data = request.json
    is_public = data.get('is_public', False)
    
    claim.is_public = bool(is_public)
    db.session.commit()
    
    return jsonify({
        'message': '操作成功',
        'is_public': claim.is_public
    })

@app.route('/api/users/<int:user_id>/public-claims', methods=['GET'])
def get_user_public_claims(user_id):
    """获取用户公开的认领历史记录"""
    user = User.query.get_or_404(user_id)
    
    # 只返回已批准且公开的认领记录
    claims = Claim.query.filter_by(
        claimant_id=user_id,
        status='approved',
        is_public=True
    ).order_by(Claim.created_at.desc()).all()
    
    result = []
    for claim in claims:
        claim_dict = claim.to_dict()
        claim_dict['item'] = claim.item.to_dict() if claim.item else None
        # 隐藏敏感信息，只显示基本信息
        claim_dict['description'] = None  # 不显示认领说明
        claim_dict['image_urls'] = []  # 不显示证据图片
        result.append(claim_dict)
    
    return jsonify(result)

# ==================== 匹配推荐API ====================

@app.route('/api/items/<int:item_id>/matches', methods=['GET'])
def get_matched_items(item_id):
    """获取匹配的物品推荐"""
    item = Item.query.get_or_404(item_id)
    
    # 匹配逻辑：寻找相反类型的物品（失物匹配拾物，拾物匹配失物）
    opposite_category = 'found' if item.category == 'lost' else 'lost'
    
    # 基础查询：相同类型、相同地点、状态为进行中
    matches = Item.query.filter(
        Item.category == opposite_category,
        Item.status == 'open',
        Item.id != item_id
    )
    
    # 按类型匹配
    if item.item_type:
        type_matches = matches.filter(Item.item_type == item.item_type).all()
    else:
        type_matches = []
    
    # 按地点匹配（包含相同关键词）
    location_matches = []
    if item.location:
        location_keywords = item.location.split()
        for keyword in location_keywords:
            if len(keyword) > 1:  # 忽略单字
                location_matches.extend(
                    matches.filter(Item.location.contains(keyword)).all()
                )
    
    # 按描述关键词匹配
    description_matches = []
    if item.description:
        # 提取关键词（简单实现，可以改进）
        desc_keywords = item.description.split()
        for keyword in desc_keywords:
            if len(keyword) > 2:  # 只匹配长度大于2的词
                description_matches.extend(
                    matches.filter(
                        (Item.description.contains(keyword)) |
                        (Item.title.contains(keyword))
                    ).all()
                )
    
    # 合并并去重
    all_matches = {}
    match_scores = {}
    
    # 类型匹配得分最高（3分）
    for match in type_matches:
        if match.id not in all_matches:
            all_matches[match.id] = match
            match_scores[match.id] = 3
    
    # 地点匹配（2分）
    for match in location_matches:
        if match.id not in all_matches:
            all_matches[match.id] = match
            match_scores[match.id] = 2
        elif match_scores.get(match.id, 0) < 2:
            match_scores[match.id] = 2
    
    # 描述匹配（1分）
    for match in description_matches:
        if match.id not in all_matches:
            all_matches[match.id] = match
            match_scores[match.id] = 1
        elif match_scores.get(match.id, 0) < 1:
            match_scores[match.id] = 1
    
    # 按得分排序，返回前5个
    sorted_matches = sorted(
        all_matches.values(),
        key=lambda x: match_scores.get(x.id, 0),
        reverse=True
    )[:5]
    
    return jsonify([match.to_dict() for match in sorted_matches])

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
    
    # 敏感词检查
    has_sensitive, found_words = contains_sensitive_words(content)
    if has_sensitive:
        return jsonify({
            'message': f'消息包含敏感词，请修改后再发送。检测到的敏感词：{", ".join(found_words[:3])}',
            'sensitive_words': found_words
        }), 400
    
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
        content = data.get('content', '').strip()
        
        # 敏感词检查
        if content:
            has_sensitive, found_words = contains_sensitive_words(content)
            if has_sensitive:
                emit('error', {
                    'message': f'消息包含敏感词，请修改后再发送。检测到的敏感词：{", ".join(found_words[:3])}',
                    'sensitive_words': found_words
                })
                return
        
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
