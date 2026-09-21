import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_SECURITY = """🛡️ SECURITY PROTOCOL — ACTIVE

🔒 This channel is under direct management and continuous security monitoring.

⚠️ All access, administrative changes, and suspicious activities are regularly reviewed and documented.

🚫 Any attempt at unauthorized access, disruption, impersonation, spam, or coordinated abuse will be detected and documented.

🔐 SECURED • MONITORED • PROTECTED

© CHANNEL SECURITY SYSTEM"""

GROUP_SECURITY = """🛡️ GROUP SECURITY PROTOCOL — ACTIVE

🔒 This group is under active administration and continuous security monitoring.

⚠️ Member activity, administrative changes, and suspicious behavior are regularly reviewed.

🚫 Spam, impersonation, unauthorized access, disruptive activity, and coordinated abuse are monitored and documented.

🔐 SECURED • MONITORED • PROTECTED

© GROUP SECURITY SYSTEM"""


# کاربران در حال انجام Verify
pending = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📢 Channel", callback_data="channel"),
            InlineKeyboardButton("👥 Group", callback_data="group"),
        ]
    ]

    await update.message.reply_text(
        "Select where you want to activate the security system:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data

    pending[user_id] = choice

    if choice == "channel":
        text = (
            "📢 Channel selected.\n\n"
            "1️⃣ Add this bot to your channel as an administrator.\n"
            "2️⃣ Give it permission to post messages and pin messages.\n"
            "3️⃣ After adding it, send /verify in your channel.\n\n"
            "The bot will then activate the security system."
        )
    else:
        text = (
            "👥 Group selected.\n\n"
            "1️⃣ Add this bot to your group as an administrator.\n"
            "2️⃣ Give it permission to send and pin messages.\n"
            "3️⃣ After adding it, send /verify in your group.\n\n"
            "The bot will then activate the security system."
        )

    await query.edit_message_text(text)


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # فقط گروه و کانال
    if chat.type not in ["group", "supergroup", "channel"]:
        await update.effective_message.reply_text(
            "❌ /verify must be used inside the target group or channel."
        )
        return

    # بررسی ادمین بودن ربات
    bot_member = await context.bot.get_chat_member(
        chat.id,
        context.bot.id
    )

    if bot_member.status not in ["administrator", "creator"]:
        await update.effective_message.reply_text(
            "❌ Verification failed.\n\n"
            "Please make the bot an administrator first."
        )
        return

    # بررسی دسترسی‌های لازم
    if bot_member.status == "administrator":
        if chat.type == "channel":
            if not getattr(bot_member, "can_post_messages", False):
                await update.effective_message.reply_text(
                    "❌ The bot needs permission to post messages."
                )
                return

            if not getattr(bot_member, "can_edit_messages", False):
                await update.effective_message.reply_text(
                    "❌ The bot needs permission to pin/edit messages."
                )
                return

        else:
            if not getattr(bot_member, "can_pin_messages", False):
                await update.effective_message.reply_text(
                    "❌ The bot needs permission to pin messages."
                )
                return

    # نام و یوزرنیم
    if chat.username:
        target = f"@{chat.username}"
    else:
        target = chat.title or "Unknown"

    if chat.type == "channel":
        message = CHANNEL_SECURITY + f"\n\n📢 Channel: {target}"
    else:
        message = GROUP_SECURITY + f"\n\n👥 Group: {target}"

    # ارسال پیام امنیتی
    sent = await context.bot.send_message(
        chat_id=chat.id,
        text=message,
    )

    # Pin
    await context.bot.pin_chat_message(
        chat_id=chat.id,
        message_id=sent.message_id,
        disable_notification=True,
    )

    # پاک کردن /verify در گروه اگر ممکن باشد
    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=update.effective_message.message_id,
        )
    except Exception:
        pass

    # اطلاع به کاربر
    user_id = None

    if update.effective_user:
        user_id = update.effective_user.id

    if user_id and user_id in pending:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ Verification successful!\n\n"
                    f"Target: {target}\n"
                    "🔐 Security protocol activated.\n"
                    "📌 Security message pinned."
                ),
            )
        except Exception:
            pass

        del pending[user_id]


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("ERROR:", context.error)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CallbackQueryHandler(choose))

    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
