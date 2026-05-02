"""
一次性历史数据迁移脚本。

执行方式：
  python migrate_admin_roles.py

迁移内容：
  1. 创建 admin_application 表。
  2. 旧中级管理员平迁为管理员，旧低级管理员降级为普通用户，旧高级管理员迁为高级管理员。
  3. 删除 user 表中的教师身份字段：user_type、staff_id、teacher_approval_status。
  4. 校验高级管理员数量必须等于 1。

如果迁移前没有高级管理员，脚本会使用环境变量创建一个：
  DEFAULT_SUPER_ADMIN_USERNAME，默认 super_admin
  DEFAULT_SUPER_ADMIN_EMAIL，默认 super_admin@example.com
  DEFAULT_SUPER_ADMIN_PASSWORD，默认 admin123456
"""

import os
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'lost_found.db')

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_SUPER_ADMIN = 'super_admin'


def table_columns(cur, table_name):
    cur.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cur.fetchall()]


def create_admin_application_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_application (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            apply_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            review_time DATETIME,
            reviewer_id INTEGER,
            reject_reason TEXT,
            CHECK (status IN ('pending', 'approved', 'rejected', 'revoked')),
            CHECK (length(reason) >= 20 OR reason = '高级管理员直接任命' OR status = 'revoked'),
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (reviewer_id) REFERENCES user (id)
        )
    """)


def normalize_roles(cur):
    cols = table_columns(cur, 'user')
    if 'role' not in cols:
        cur.execute("ALTER TABLE user ADD COLUMN role TEXT")
    if 'admin_level' in cols:
        cur.execute("UPDATE user SET role = ? WHERE role = 'admin' AND admin_level = 'high'", (ROLE_SUPER_ADMIN,))
        cur.execute("UPDATE user SET role = ? WHERE role = 'admin' AND admin_level = 'mid'", (ROLE_ADMIN,))
        cur.execute("UPDATE user SET role = ? WHERE role = 'admin' AND admin_level = 'low'", (ROLE_USER,))
    cur.execute("UPDATE user SET role = ? WHERE role = '高级管理员'", (ROLE_SUPER_ADMIN,))
    cur.execute("UPDATE user SET role = ? WHERE role = '管理员'", (ROLE_ADMIN,))
    cur.execute("UPDATE user SET role = ? WHERE role = '普通用户' OR role IS NULL OR role = ''", (ROLE_USER,))
    cur.execute(
        "UPDATE user SET role = ? WHERE role NOT IN (?, ?, ?)",
        (ROLE_USER, ROLE_USER, ROLE_ADMIN, ROLE_SUPER_ADMIN)
    )


def ensure_one_super_admin(cur):
    cur.execute("SELECT COUNT(*) FROM user WHERE role = ?", (ROLE_SUPER_ADMIN,))
    count = cur.fetchone()[0]
    if count == 0:
        username = os.getenv('DEFAULT_SUPER_ADMIN_USERNAME', 'super_admin')
        email = os.getenv('DEFAULT_SUPER_ADMIN_EMAIL', 'super_admin@example.com')
        password = os.getenv('DEFAULT_SUPER_ADMIN_PASSWORD', 'admin123456')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE user SET role = ? WHERE id = ?", (ROLE_SUPER_ADMIN, row[0]))
        else:
            cur.execute("""
                INSERT INTO user (username, password_hash, email, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, generate_password_hash(password), email, ROLE_SUPER_ADMIN, now))
        print(f"已初始化高级管理员账号：{username}")
    cur.execute("SELECT COUNT(*) FROM user WHERE role = ?", (ROLE_SUPER_ADMIN,))
    count = cur.fetchone()[0]
    if count != 1:
        raise RuntimeError(f"迁移校验失败：高级管理员数量为 {count}，必须手动处理为 1 个后重跑脚本")


def drop_teacher_columns(cur):
    for column in ('user_type', 'staff_id', 'teacher_approval_status'):
        if column not in table_columns(cur, 'user'):
            continue
        cur.execute(f"ALTER TABLE user DROP COLUMN {column}")
        print(f"已删除 user.{column}")


def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"数据库不存在：{DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        create_admin_application_table(cur)
        normalize_roles(cur)
        ensure_one_super_admin(cur)
        drop_teacher_columns(cur)
        conn.commit()
        print("迁移完成：角色、教师字段、管理员申请表均已处理")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
