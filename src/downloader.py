import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="pdf_records.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """获取本地 SQLite 数据库连接"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """初始化 SQLite 数据库及存储表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                raw_text TEXT,
                structured_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def insert_record(self, file_name, file_path, raw_text, structured_data):
        """插入解析与清洗后的文档记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO records (file_name, file_path, raw_text, structured_data)
            VALUES (?, ?, ?, ?)
        ''', (file_name, file_path, raw_text, structured_data))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return record_id

    def fetch_all_records(self):
        """查询所有已处理的记录概要"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, file_name, file_path, created_at FROM records ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
