# config.py
import os

# إعدادات البوت - يتم أخذ التوكن من متغيرات البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8122538449:AAGE9NIO18L6OqF5DZlQxsIK6x7LdHDJwmA')
REQUIRED_CHANNEL = os.environ.get('REQUIRED_CHANNEL', '@Msayedinfoo')
DB_NAME = os.environ.get('DB_NAME', 'bot_data.db')

# إعدادات التوقيت
WARNING_DELETE_TIMEOUT = 180  # 3 دقائق بالثواني

# إعدادات التطوير
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# إعدادات Railway
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
