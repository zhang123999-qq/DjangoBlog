"""
自定义 SQLite 数据库后端
禁用外键约束检查，解决 Django 4.1+ 迁移问题
"""

from django.db.backends.sqlite3 import base


class DatabaseWrapper(base.DatabaseWrapper):
    """
    自定义 SQLite 后端，禁用外键约束检查

    Django 4.1+ 在迁移时对外键约束检查更严格，
    这会导致 SQLite 迁移失败。此前端在每次连接时
    自动禁用外键约束。
    """

    def get_new_connection(self, conn_params):
        conn = super().get_new_connection(conn_params)
        # 禁用外键约束检查
        conn.execute("PRAGMA foreign_keys = OFF")
        return conn
