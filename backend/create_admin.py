#!/usr/bin/env python3
"""
创建高级管理员账户的脚本

使用方法：
1. 创建新用户并设置为高级管理员：
   python create_admin.py --username admin --email admin@example.com --password your_password

2. 将现有用户提升为高级管理员：
   python create_admin.py --username existing_user --promote

3. 查看所有管理员：
   python create_admin.py --list
"""

import os
import sys
import argparse
from werkzeug.security import generate_password_hash

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from datetime import datetime

def create_admin(username, email, password, phone='', department='', user_type='student'):
    """创建新的高级管理员账户"""
    with app.app_context():
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            print(f"❌ 错误：用户名 '{username}' 已存在")
            return False
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            print(f"❌ 错误：邮箱 '{email}' 已被注册")
            return False
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            phone=phone,
            department=department,
            user_type=user_type,
            role='admin',
            admin_level='high',
            admin_appointed_by=None,
            created_at=datetime.now()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ 成功创建高级管理员账户：")
        print(f"   用户名: {username}")
        print(f"   邮箱: {email}")
        print(f"   角色: admin")
        print(f"   级别: high (高级管理员)")
        return True

def promote_to_admin(username):
    """将现有用户提升为高级管理员"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ 错误：用户 '{username}' 不存在")
            return False
        
        if user.role == 'admin' and user.admin_level == 'high':
            print(f"ℹ️  用户 '{username}' 已经是高级管理员")
            return True
        
        user.role = 'admin'
        user.admin_level = 'high'
        user.admin_appointed_by = None
        
        db.session.commit()
        
        print(f"✅ 成功将用户 '{username}' 提升为高级管理员")
        return True

def list_admins():
    """列出所有管理员"""
    with app.app_context():
        admins = User.query.filter_by(role='admin').all()
        if not admins:
            print("📋 当前没有管理员账户")
            return
        
        print(f"📋 当前管理员列表（共 {len(admins)} 个）：")
        print("-" * 80)
        print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'级别':<10}")
        print("-" * 80)
        
        level_map = {'low': '低级', 'mid': '中级', 'high': '高级'}
        for admin in admins:
            level = level_map.get(admin.admin_level, admin.admin_level or '未知')
            print(f"{admin.id:<5} {admin.username:<20} {admin.email:<30} {level:<10}")
        
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description='创建或管理高级管理员账户')
    parser.add_argument('--username', '-u', help='用户名')
    parser.add_argument('--email', '-e', help='邮箱地址')
    parser.add_argument('--password', '-p', help='密码')
    parser.add_argument('--phone', help='手机号（可选）')
    parser.add_argument('--department', '-d', help='部门（可选）')
    parser.add_argument('--user-type', '-t', choices=['student', 'teacher'], default='student', help='用户类型（默认：student）')
    parser.add_argument('--promote', action='store_true', help='将现有用户提升为高级管理员')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有管理员')
    
    args = parser.parse_args()
    
    if args.list:
        list_admins()
        return
    
    if not args.username:
        parser.print_help()
        print("\n❌ 错误：必须提供用户名")
        return
    
    if args.promote:
        promote_to_admin(args.username)
    else:
        if not args.email or not args.password:
            parser.print_help()
            print("\n❌ 错误：创建新用户时必须提供邮箱和密码")
            return
        create_admin(
            username=args.username,
            email=args.email,
            password=args.password,
            phone=args.phone or '',
            department=args.department or '',
            user_type=args.user_type
        )

if __name__ == '__main__':
    main()
