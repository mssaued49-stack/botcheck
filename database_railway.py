# database_railway.py
import os
import sqlite3
import logging
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.db_url = DATABASE_URL
        self.init_database()

    def get_connection(self):
        """إنشاء اتصال قاعدة البيانات"""
        if self.db_url.startswith('postgresql://'):
            # استخدم PostgreSQL على Railway
            import psycopg2
            from urllib.parse import urlparse
            result = urlparse(self.db_url)
            conn = psycopg2.connect(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            return conn
        else:
            # استخدم SQLite محلياً
            conn = sqlite3.connect('bot_data.db', check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def init_database(self):
        """تهيئة جداول قاعدة البيانات"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith('postgresql://'):
                # إنشاء الجداول في PostgreSQL
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS group_settings (
                        group_id SERIAL PRIMARY KEY,
                        group_username TEXT UNIQUE,
                        group_chat_id INTEGER,
                        keyword TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        language TEXT DEFAULT 'ar',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS group_channels (
                        id SERIAL PRIMARY KEY,
                        group_username TEXT,
                        channel_username TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS deleted_messages (
                        id SERIAL PRIMARY KEY,
                        group_username TEXT,
                        user_id INTEGER,
                        user_name TEXT,
                        message_text TEXT,
                        language TEXT,
                        reason TEXT,
                        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language TEXT DEFAULT 'ar',
                        is_subscribed BOOLEAN DEFAULT FALSE,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # إنشاء الجداول في SQLite
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS group_settings (
                        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_username TEXT UNIQUE,
                        group_chat_id INTEGER,
                        keyword TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        language TEXT DEFAULT 'ar',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS group_channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_username TEXT,
                        channel_username TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS deleted_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_username TEXT,
                        user_id INTEGER,
                        user_name TEXT,
                        message_text TEXT,
                        language TEXT,
                        reason TEXT,
                        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language TEXT DEFAULT 'ar',
                        is_subscribed BOOLEAN DEFAULT 0,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            conn.commit()
            conn.close()
            logging.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")

    # باقي الدوال تبقى كما هي مع تعديلات بسيطة للتوافق
    def add_group(self, group_username, group_chat_id, keyword, language='ar'):
        """إضافة جروب جديد"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith('postgresql://'):
                cursor.execute('''
                    INSERT INTO group_settings 
                    (group_username, group_chat_id, keyword, language) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (group_username) DO UPDATE SET
                    group_chat_id = EXCLUDED.group_chat_id,
                    keyword = EXCLUDED.keyword,
                    language = EXCLUDED.language
                ''', (group_username, group_chat_id, keyword, language))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO group_settings 
                    (group_username, group_chat_id, keyword, language) 
                    VALUES (?, ?, ?, ?)
                ''', (group_username, group_chat_id, keyword, language))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الجروب: {e}")
            return False

    # ... باقي الدوال بنفس المنطق مع تعديل ? إلى %s لـ PostgreSQL
