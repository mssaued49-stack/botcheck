# config.py
import os
import urllib.parse

# إعدادات البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8122538449:AAGE9NIO18L6OqF5DZlQxsIK6x7LdHDJwmA')
REQUIRED_CHANNEL = os.environ.get('REQUIRED_CHANNEL', '@Msayedinfoo')

# إعدادات قاعدة البيانات - Railway
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///bot_data.db')

# إذا كان لديك DATABASE_URL من Railway، استخدم PostgreSQL
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# إعدادات التوقيت
WARNING_DELETE_TIMEOUT = 180

# إعدادات التطوير
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 8080))
