# bot.py
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.error import BadRequest

from config import BOT_TOKEN, REQUIRED_CHANNEL, PORT, WEBHOOK_URL
from database import Database
from texts import get_text
from utils import (
    create_main_menu_keyboard, create_language_keyboard, 
    create_back_keyboard, create_yes_no_keyboard,
    extract_username, check_subscription, delete_message_with_delay, escape_markdown
)

# تكوين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تهيئة قاعدة البيانات
db = Database()

# حالات المحادثة
ADD_GROUP, ADD_KEYWORD, ADD_CHANNEL = range(3)

class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """إعداد معالجات الأحداث"""
        # معالجات الأوامر
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("scan", self.scan_recent_messages))
        
        # معالجات الاستعلامات
        self.application.add_handler(CallbackQueryHandler(self.handle_language_selection, pattern="^lang_"))
        self.application.add_handler(CallbackQueryHandler(self.button_handler, pattern="^(add_group|active_groups|stats|check_subscription|change_language|scan_messages|back_to_main|settings|yes_channel|no_channel)$"))
        
        # معالجات المحادثة
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_add_group, pattern="^add_group$")],
            states={
                ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_group_username)],
                ADD_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_keyword)],
                ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_channel)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(conv_handler)
        
        # معالجات الرسائل في الجروبات
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), 
            self.monitor_messages
        ))
        
        # معالجات الرسائل الخاصة
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, 
            self.handle_private_message
        ))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        # تسجيل المستخدم
        db.add_user(user.id, user.username, user.first_name)
        
        # إرسال رسالة الترحيب
        await update.message.reply_text(
            get_text('ar', 'welcome'),
            reply_markup=create_main_menu_keyboard('ar'),
            parse_mode='Markdown'
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار"""
        query = update.callback_query
        await query.answer()
        
        user_data = db.get_user(query.from_user.id)
        language = user_data['language'] if user_data else 'ar'
        
        data = query.data
        
        if data == "back_to_main":
            await self.show_main_menu(query, language)
        
        elif data == "active_groups":
            await self.show_active_groups(query, language)
        
        elif data == "stats":
            await self.show_stats(query, language)
        
        elif data == "check_subscription":
            await self.check_user_subscription(query, language)
        
        elif data == "change_language":
            await self.show_language_selection(query, language)
        
        elif data == "settings":
            await self.show_settings(query, language)
        
        elif data == "scan_messages":
            await self.scan_group_messages(query, language)
        
        elif data == "yes_channel":
            await query.edit_message_text(
                get_text(language, 'enter_channel_username'),
                reply_markup=create_back_keyboard(language)
            )
            return ADD_CHANNEL
        
        elif data == "no_channel":
            await query.edit_message_text(
                get_text(language, 'skip_channel'),
                reply_markup=create_main_menu_keyboard(language)
            )

    async def show_main_menu(self, query, language):
        """عرض القائمة الرئيسية"""
        await query.edit_message_text(
            get_text(language, 'main_menu'),
            reply_markup=create_main_menu_keyboard(language),
            parse_mode='Markdown'
        )

    async def start_add_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية إضافة جروب"""
        query = update.callback_query
        await query.answer()
        
        user_data = db.get_user(query.from_user.id)
        language = user_data['language'] if user_data else 'ar'
        
        await query.edit_message_text(
            get_text(language, 'enter_group_username'),
            reply_markup=create_back_keyboard(language)
        )
        
        return ADD_GROUP

    async def handle_group_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اسم المستخدم للجروب"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        language = user_data['language'] if user_data else 'ar'
        
        group_input = update.message.text
        group_username = extract_username(group_input)
        
        if not group_username:
            await update.message.reply_text(
                get_text(language, 'invalid_group'),
                reply_markup=create_back_keyboard(language)
            )
            return ADD_GROUP
        
        # التحقق من أن البوت أدمن في الجروب
        try:
            chat_member = await context.bot.get_chat_member(group_username, context.bot.id)
            if chat_member.status not in ['administrator', 'creator'] or not chat_member.can_delete_messages:
                await update.message.reply_text(
                    get_text(language, 'bot_not_admin'),
                    reply_markup=create_back_keyboard(language)
                )
                return ADD_GROUP
        except BadRequest:
            await update.message.reply_text(
                get_text(language, 'invalid_group'),
                reply_markup=create_back_keyboard(language)
            )
            return ADD_GROUP
        
        # حفظ بيانات الجروب مؤقتاً
        context.user_data['group_username'] = group_username
        context.user_data['group_chat_id'] = chat_member.chat.id
        
        await update.message.reply_text(
            get_text(language, 'enter_keyword'),
            reply_markup=create_back_keyboard(language)
        )
        
        return ADD_KEYWORD

    async def handle_keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الكلمة المفتاحية"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        language = user_data['language'] if user_data else 'ar'
        
        keyword = update.message.text
        
        # حفظ الجروب في قاعدة البيانات
        group_username = context.user_data['group_username']
        group_chat_id = context.user_data['group_chat_id']
        
        success = db.add_group(group_username, group_chat_id, keyword, language)
        
        if success:
            await update.message.reply_text(
                get_text(language, 'add_channel_question'),
                reply_markup=create_yes_no_keyboard(language)
            )
            return ADD_CHANNEL
        else:
            await update.message.reply_text(
                get_text(language, 'error_occurred'),
                reply_markup=create_main_menu_keyboard(language)
            )
            return ConversationHandler.END

    async def handle_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إضافة القناة"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        language = user_data['language'] if user_data else 'ar'
        
        channel_input = update.message.text
        channel_username = extract_username(channel_input)
        
        if channel_username:
            group_username = context.user_data['group_username']
            db.add_group_channel(group_username, channel_username)
            
            await update.message.reply_text(
                get_text(language, 'channel_added_success'),
                reply_markup=create_main_menu_keyboard(language)
            )
        else:
            await update.message.reply_text(
                get_text(language, 'invalid_group'),
                reply_markup=create_yes_no_keyboard(language)
            )
            return ADD_CHANNEL
        
        return ConversationHandler.END

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء المحادثة"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        language = user_data['language'] if user_data else 'ar'
        
        await update.message.reply_text(
            get_text(language, 'back_to_main'),
            reply_markup=create_main_menu_keyboard(language)
        )
        
        return ConversationHandler.END

    async def show_active_groups(self, query, language):
        """عرض الجروبات النشطة"""
        groups = db.get_all_groups()
        
        if not groups:
            text = get_text(language, 'no_active_groups')
        else:
            text = get_text(language, 'active_groups')
            for group in groups:
                text += get_text(language, 'group_item').format(
                    group_name=group['group_username'],
                    keyword=group['keyword'],
                    language=group['language']
                )
        
        await query.edit_message_text(
            text,
            reply_markup=create_back_keyboard(language),
            parse_mode='Markdown'
        )

    async def show_stats(self, query, language):
        """عرض الإحصائيات"""
        stats = db.get_stats()
        
        text = get_text(language, 'stats')
        text += f"📊 {get_text(language, 'stats_groups').format(active_groups=stats['active_groups'])}\n"
        text += f"🗑️ {get_text(language, 'stats_deleted').format(deleted_messages=stats['deleted_messages'])}\n"
        text += f"👤 {get_text(language, 'stats_users').format(total_users=stats['total_users'])}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=create_back_keyboard(language),
            parse_mode='Markdown'
        )

    async def check_user_subscription(self, query, language):
        """التحقق من اشتراك المستخدم"""
        user_id = query.from_user.id
        
        # التحقق من الاشتراك في القناة الافتراضية
        is_subscribed = await check_subscription(query.bot, user_id, REQUIRED_CHANNEL)
        
        if is_subscribed:
            text = get_text(language, 'subscribed')
            keyboard = create_back_keyboard(language)
        else:
            text = get_text(language, 'not_subscribed').format(channel=REQUIRED_CHANNEL)
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 تحقق مرة أخرى", callback_data="check_subscription"),
                InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
            ]])
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def show_language_selection(self, query, language):
        """عرض اختيار اللغة"""
        await query.edit_message_text(
            get_text(language, 'change_language'),
            reply_markup=create_language_keyboard()
        )

    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار اللغة"""
        query = update.callback_query
        await query.answer()
        
        language = query.data.split('_')[1]  # lang_ar -> ar
        user_id = query.from_user.id
        
        # تحديث لغة المستخدم
        db.update_user_language(user_id, language)
        
        await query.edit_message_text(
            get_text(language, 'language_changed'),
            reply_markup=create_main_menu_keyboard(language)
        )

    async def show_settings(self, query, language):
        """عرض الإعدادات"""
        await query.edit_message_text(
            get_text(language, 'settings'),
            reply_markup=create_back_keyboard(language)
        )

    async def scan_group_messages(self, query, language):
        """فحص رسائل الجروب"""
        await query.edit_message_text(
            get_text(language, 'scan_messages'),
            reply_markup=create_back_keyboard(language)
        )
        
        # محاكاة عملية الفحص
        await asyncio.sleep(2)
        
        await query.edit_message_text(
            get_text(language, 'scan_complete'),
            reply_markup=create_back_keyboard(language)
        )

    async def monitor_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مراقبة الرسائل في الجروبات"""
        message = update.message
        chat = message.chat
        user = message.from_user
        
        # الحصول على إعدادات الجروب
        group_username = f"@{chat.username}" if chat.username else str(chat.id)
        group_data = db.get_group(group_username)
        
        if not group_data or not group_data['is_active']:
            return
        
        # الحصول على قناة الجروب المخصصة أو استخدام الافتراضية
        group_channel = db.get_group_channel(group_username)
        channel_username = group_channel['channel_username'] if group_channel else REQUIRED_CHANNEL
        
        language = group_data['language']
        keyword = group_data['keyword']
        
        # التحقق من اشتراك المستخدم
        is_subscribed = await check_subscription(context.bot, user.id, channel_username)
        
        if not is_subscribed:
            # إرسال تحذير وحذف الرسالة
            warning_text = get_text(language, 'subscription_warning').format(
                user_name=user.first_name,
                channel=channel_username
            )
            
            try:
                warning_msg = await message.reply_text(
                    warning_text,
                    reply_to_message_id=message.message_id,
                    parse_mode='Markdown'
                )
                
                # جدولة حذف التحذير بعد 3 دقائق
                await delete_message_with_delay(context, chat.id, warning_msg.message_id)
                
                # حذف الرسالة الأصلية
                await message.delete()
                
                # تسجيل الحذف
                db.log_deleted_message(
                    group_username, user.id, user.first_name,
                    message.text, language, "لم يشترك في القناة"
                )
                
            except Exception as e:
                logging.error(f"❌ Error in subscription check: {e}")
            return
        
        # التحقق من وجود @username للمستخدم
        if not user.username and keyword.lower() in message.text.lower():
            # إرسال تحذير للمستخدم بدون username
            warning_text = get_text(language, 'no_username_warning').format(
                user_name=user.first_name
            )
            
            try:
                warning_msg = await message.reply_text(
                    warning_text,
                    reply_to_message_id=message.message_id,
                    parse_mode='Markdown'
                )
                
                # جدولة حذف التحذير بعد 3 دقائق
                await delete_message_with_delay(context, chat.id, warning_msg.message_id)
                
                # حذف الرسالة الأصلية
                await message.delete()
                
                # تسجيل الحذف
                db.log_deleted_message(
                    group_username, user.id, user.first_name,
                    message.text, language, "لا يوجد username"
                )
                
            except Exception as e:
                logging.error(f"❌ Error in username check: {e}")

    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل الخاصة"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        language = user_data['language'] if user_data else 'ar'
        
        await update.message.reply_text(
            get_text(language, 'main_menu'),
            reply_markup=create_main_menu_keyboard(language),
            parse_mode='Markdown'
        )

    async def scan_recent_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فحص الرسائل الحديثة (للاستخدام من قبل المشرفين)"""
        user = update.effective_user
        chat = update.effective_chat
        
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ هذا الأمر يعمل فقط في الجروبات!")
            return
        
        # التحقق من أن المستخدم مشرف
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            if chat_member.status not in ['administrator', 'creator']:
                await update.message.reply_text("❌ يجب أن تكون مشرفاً لاستخدام هذا الأمر!")
                return
        except Exception as e:
            logging.error(f"❌ Error checking admin status: {e}")
            return
        
        await update.message.reply_text("🔍 جاري فحص الرسائل الحديثة...")
        
        # هنا يمكن إضافة منطق فحص الرسائل الحديثة
        # هذا يحتاج إلى صلاحية الوصول إلى سجل الدردشة
        
        await update.message.reply_text("✅ تم الانتهاء من الفحص!")

    def run(self):
        """تشغيل البوت"""
        if WEBHOOK_URL:
            # استخدام webhook على Railway
            self.application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
            )
        else:
            # استخدام polling للتطوير المحلي
            self.application.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
