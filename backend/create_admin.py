#!/usr/bin/env python3
"""
创建高级管理员账户的脚本

使用方法：
1. 初始化唯一高级管理员：
   python create_admin.py --username admin --email admin@example.com --password your_password

2. 查看所有管理员：
   python create_admin.py --list
"""

import os
import sys
import argparse
from werkzeug.security import generate_password_hash

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, ROLE_ADMIN, ROLE_SUPER_ADMIN
from datetime import datetime

def create_admin(username, email, password, phone='', department=''):
    """初始化唯一高级管理员账户"""
    with app.app_context():
        existing_super_admin = User.query.filter_by(role=ROLE_SUPER_ADMIN).first()
        if existing_super_admin:
            if existing_super_admin.username != 'super_admin':
                print(f"❌ 错误：系统已存在高级管理员 '{existing_super_admin.username}'，不允许创建第二个高级管理员")
                return False
            existing_super_admin.username = username
            existing_super_admin.email = email
            existing_super_admin.phone = phone
            existing_super_admin.department = department
            existing_super_admin.set_password(password)
            db.session.commit()
            print(f"✅ 已更新种子高级管理员账户：{username}")
            return True

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
            role=ROLE_SUPER_ADMIN,
            created_at=datetime.now()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ 成功创建高级管理员账户：")
        print(f"   用户名: {username}")
        print(f"   邮箱: {email}")
        print(f"   角色: 高级管理员")
        return True

def list_admins():
    """列出所有管理员"""
    with app.app_context():
        admins = User.query.filter(User.role.in_([ROLE_ADMIN, ROLE_SUPER_ADMIN])).all()
        if not admins:
            print("📋 当前没有管理员账户")
            return
        
        print(f"📋 当前管理员列表（共 {len(admins)} 个）：")
        print("-" * 80)
        print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'角色':<10}")
        print("-" * 80)
        
        for admin in admins:
            role = '高级管理员' if admin.role == ROLE_SUPER_ADMIN else '管理员'
            print(f"{admin.id:<5} {admin.username:<20} {admin.email:<30} {role:<10}")
        
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description='创建或管理高级管理员账户')
    parser.add_argument('--username', '-u', help='用户名')
    parser.add_argument('--email', '-e', help='邮箱地址')
    parser.add_argument('--password', '-p', help='密码')
    parser.add_argument('--phone', help='手机号（可选）')
    parser.add_argument('--department', '-d', help='部门（可选）')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有管理员')
    
    args = parser.parse_args()
    
    if args.list:
        list_admins()
        return
    
    if not args.username:
        parser.print_help()
        print("\n❌ 错误：必须提供用户名")
        return
    
    if not args.email or not args.password:
        parser.print_help()
        print("\n❌ 错误：创建新用户时必须提供邮箱和密码")
        return
    create_admin(
        username=args.username,
        email=args.email,
        password=args.password,
        phone=args.phone or '',
        department=args.department or ''
    )

if __name__ == '__main__':
    main()
