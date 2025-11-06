# database.py
import sqlite3
import logging
from config import DB_NAME

class Database:
    def __init__(self):
        self.db_name = DB_NAME
        self.init_database()

    def get_connection(self):
        """إنشاء اتصال قاعدة البيانات"""
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """تهيئة جداول قاعدة البيانات"""
        try:
            with self.get_connection() as conn:
                # جدول إعدادات الجروبات
                conn.execute('''
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

                # جدول قنوات الجروبات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS group_channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_username TEXT,
                        channel_username TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # جدول الرسائل المحذوفة
                conn.execute('''
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

                # جدول إعدادات المستخدمين
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language TEXT DEFAULT 'ar',
                        is_subscribed BOOLEAN DEFAULT 0,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                logging.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")

    # دوال الجروبات
    def add_group(self, group_username, group_chat_id, keyword, language='ar'):
        """إضافة جروب جديد"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO group_settings 
                    (group_username, group_chat_id, keyword, language) 
                    VALUES (?, ?, ?, ?)
                ''', (group_username, group_chat_id, keyword, language))
                return True
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الجروب: {e}")
            return False

    def get_group(self, group_username):
        """الحصول على بيانات الجروب"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM group_settings WHERE group_username = ?', 
                    (group_username,)
                )
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات الجروب: {e}")
            return None

    def get_all_groups(self):
        """الحصول على جميع الجروبات"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM group_settings WHERE is_active = 1')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الجروبات: {e}")
            return []

    # دوال القنوات
    def add_group_channel(self, group_username, channel_username):
        """إضافة قناة للجروب"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO group_channels 
                    (group_username, channel_username) 
                    VALUES (?, ?)
                ''', (group_username, channel_username))
                return True
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة القناة: {e}")
            return False

    def get_group_channel(self, group_username):
        """الحصول على قناة الجروب"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM group_channels WHERE group_username = ? AND is_active = 1', 
                    (group_username,)
                )
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"❌ خطأ في جلب قناة الجروب: {e}")
            return None

    # دوال المستخدمين
    def add_user(self, user_id, username, first_name, language='ar'):
        """إضافة/تحديث مستخدم"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_settings 
                    (user_id, username, first_name, language) 
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, first_name, language))
                return True
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة المستخدم: {e}")
            return False

    def get_user(self, user_id):
        """الحصول على بيانات المستخدم"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM user_settings WHERE user_id = ?', 
                    (user_id,)
                )
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات المستخدم: {e}")
            return None

    def update_user_language(self, user_id, language):
        """تحديث لغة المستخدم"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE user_settings SET language = ? WHERE user_id = ?', 
                    (language, user_id)
                )
                return True
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث لغة المستخدم: {e}")
            return False

    # دوال الإحصائيات
    def get_stats(self):
        """الحصول على الإحصائيات"""
        try:
            with self.get_connection() as conn:
                # عدد الجروبات النشطة
                active_groups = conn.execute(
                    'SELECT COUNT(*) FROM group_settings WHERE is_active = 1'
                ).fetchone()[0]

                # عدد الرسائل المحذوفة
                deleted_messages = conn.execute(
                    'SELECT COUNT(*) FROM deleted_messages'
                ).fetchone()[0]

                # عدد المستخدمين
                total_users = conn.execute(
                    'SELECT COUNT(*) FROM user_settings'
                ).fetchone()[0]

                return {
                    'active_groups': active_groups,
                    'deleted_messages': deleted_messages,
                    'total_users': total_users
                }
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الإحصائيات: {e}")
            return {'active_groups': 0, 'deleted_messages': 0, 'total_users': 0}

    # دوال التسجيل
    def log_deleted_message(self, group_username, user_id, user_name, message_text, language, reason):
        """تسجيل الرسائل المحذوفة"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO deleted_messages 
                    (group_username, user_id, user_name, message_text, language, reason) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (group_username, user_id, user_name, message_text, language, reason))
                return True
        except Exception as e:
            logging.error(f"❌ خطأ في تسجيل الرسالة المحذوفة: {e}")
            return False
