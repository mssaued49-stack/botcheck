# utils.py
import re
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from texts import get_text

def create_main_menu_keyboard(language='ar'):
    """إنشاء لوحة المفاتيح الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("📝 إضافة جروب", callback_data="add_group")],
        [InlineKeyboardButton("👥 الجروبات النشطة", callback_data="active_groups")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [
            InlineKeyboardButton("🔍 تحقق من الاشتراك", callback_data="check_subscription"),
            InlineKeyboardButton("🌐 اللغة", callback_data="change_language")
        ],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")]
    ]
    
    if language == 'en':
        keyboard = [
            [InlineKeyboardButton("📝 Add Group", callback_data="add_group")],
            [InlineKeyboardButton("👥 Active Groups", callback_data="active_groups")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
            [
                InlineKeyboardButton("🔍 Check Subscription", callback_data="check_subscription"),
                InlineKeyboardButton("🌐 Language", callback_data="change_language")
            ],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def create_language_keyboard():
    """إنشاء لوحة اختيار اللغة"""
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")
        ],
        [InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_keyboard(language='ar'):
    """إنشاء زر الرجوع فقط"""
    back_text = "↩️ رجوع" if language == 'ar' else "↩️ Back"
    keyboard = [[InlineKeyboardButton(back_text, callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)

def create_yes_no_keyboard(language='ar'):
    """إنشاء لوحة نعم/لا"""
    if language == 'ar':
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم", callback_data="yes_channel"),
                InlineKeyboardButton("❌ لا", callback_data="no_channel")
            ],
            [InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data="yes_channel"),
                InlineKeyboardButton("❌ No", callback_data="no_channel")
            ],
            [InlineKeyboardButton("↩️ Back", callback_data="back_to_main")]
        ]
    return InlineKeyboardMarkup(keyboard)

def extract_username(text):
    """استخراج المعرف من النص"""
    # البحث عن معرفات مثل @username
    username_match = re.search(r'@(\w+)', text)
    if username_match:
        return f"@{username_match.group(1)}"
    
    # البحث في الروابط
    link_match = re.search(r'(?:t\.me/|telegram\.me/)(\w+)', text)
    if link_match:
        return f"@{link_match.group(1)}"
    
    return None

async def check_subscription(bot, user_id, channel_username):
    """التحقق من اشتراك المستخدم في القناة"""
    try:
        chat_member = await bot.get_chat_member(channel_username, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"❌ Error checking subscription: {e}")
        return False

async def delete_message_with_delay(context, chat_id, message_id, delay=180):
    """حذف الرسالة بعد تأخير"""
    async def delete():
        try:
            await context.bot.delete_message(chat_id, message_id)
        except Exception as e:
            logging.error(f"❌ Error deleting message: {e}")
    
    context.job_queue.run_once(lambda _: delete(), delay)

def escape_markdown(text):
    """تهريب الأحرف الخاصة في Markdown"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])
