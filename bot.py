import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
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


pending = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📢 Channel", callback_data="channel"),
            InlineKeyboardButton("👥 Group", callback_data="group"),
        ]
    ]

    await update.effective_message.reply_text(
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
            "2️⃣ Give it permission to post and pin messages.\n"
            "3️⃣ Add the bot first, then use /verify in the channel.\n\n"
            "The bot will verify its permissions and activate the security system."
        )
    else:
        text = (
            "👥 Group selected.\n\n"
            "1️⃣ Add this bot to your group as an administrator.\n"
            "2️⃣ Give it permission to send and pin messages.\n"
            "3️⃣ Add the bot first, then use /verify in the group.\n\n"
            "The bot will verify its permissions and activate the security system."
        )

    await query.edit_message_text(text)


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in ("group", "supergroup", "channel"):
        await update.effective_message.reply_text(
            "❌ /verify must be used inside the target group or channel."
        )
        return

    try:
        bot_info = await context.bot.get_me()

        bot_member = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=bot_info.id,
        )

    except Exception as e:
        print("VERIFY ERROR:", e)

        try:
            await update.effective_message.reply_text(
                "❌ I couldn't verify my permissions.\n\n"
                "Make sure I am an administrator and try again."
            )
        except Exception:
            pass

        return

    if bot_member.status not in ("administrator", "creator"):
        try:
            await update.effective_message.reply_text(
                "❌ Verification failed.\n\n"
                "Please make the bot an administrator first."
            )
        except Exception:
            pass

        return

    # Check permissions
    if bot_member.status == "administrator":

        if chat.type == "channel":

            if not getattr(bot_member, "can_post_messages", False):
                await update.effective_message.reply_text(
                    "❌ I need permission to post messages in this channel."
                )
                return

            if not getattr(bot_member, "can_edit_messages", False):
                await update.effective_message.reply_text(
                    "❌ I need permission to edit/pin channel messages."
                )
                return

        else:

            if not getattr(bot_member, "can_pin_messages", False):
                await update.effective_message.reply_text(
                    "❌ I need permission to pin messages in this group."
                )
                return

    # Get target name
    if chat.username:
        target = f"@{chat.username}"
    else:
        target = chat.title or "Unknown"

    # Create security message
    if chat.type == "channel":
        message = CHANNEL_SECURITY + f"\n\n📢 Channel: {target}"
    else:
        message = GROUP_SECURITY + f"\n\n👥 Group: {target}"

    try:
        # Send security message
        sent = await context.bot.send_message(
            chat_id=chat.id,
            text=message,
        )

        # Pin it
        await context.bot.pin_chat_message(
            chat_id=chat.id,
            message_id=sent.message_id,
            disable_notification=True,
        )

    except Exception as e:
        print("SEND/PIN ERROR:", e)

        try:
            await update.effective_message.reply_text(
                "❌ I couldn't send or pin the security message.\n\n"
                "Please check my administrator permissions."
            )
        except Exception:
            pass

        return

    # Delete /verify message when possible
    try:
        if update.effective_message:
            await context.bot.delete_message(
                chat_id=chat.id,
                message_id=update.effective_message.message_id,
            )
    except Exception:
        pass

    # Notify user privately
    user = update.effective_user

    if user and user.id in pending:

        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    "✅ Verification successful!\n\n"
                    f"Target: {target}\n"
                    "🔐 Security protocol activated.\n"
                    "📌 Security message pinned."
                ),
            )
        except Exception:
            pass

        del pending[user.id]


async def channel_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /verify inside channel posts.
    Telegram channels deliver posts differently from normal chats.
    """

    message = update.channel_post

    if not message:
        return

    chat = update.effective_chat

    if not chat:
        return

    # Only react to /verify
    text = message.text or ""

    if not text.startswith("/verify"):
        return

    try:
        bot_info = await context.bot.get_me()

        bot_member = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=bot_info.id,
        )

        if bot_member.status not in ("administrator", "creator"):
            return

        if bot_member.status == "administrator":

            if not getattr(bot_member, "can_post_messages", False):
                return

            if not getattr(bot_member, "can_edit_messages", False):
                return

        target = f"@{chat.username}" if chat.username else (
            chat.title or "Unknown"
        )

        message_text = (
            CHANNEL_SECURITY
            + f"\n\n📢 Channel: {target}"
        )

        sent = await context.bot.send_message(
            chat_id=chat.id,
            text=message_text,
        )

        await context.bot.pin_chat_message(
            chat_id=chat.id,
            message_id=sent.message_id,
            disable_notification=True,
        )

        try:
            await context.bot.delete_message(
                chat_id=chat.id,
                message_id=message.message_id,
            )
        except Exception:
            pass

    except Exception as e:
        print("CHANNEL VERIFY ERROR:", e)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("ERROR:", context.error)


def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    app = Application.builder().token(TOKEN).build()

    # Private/group commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("verify", verify)
    )

    # Buttons
    app.add_handler(
        CallbackQueryHandler(choose)
    )

    # Channel posts
    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST,
            channel_verify
        )
    )

    app.add_error_handler(error_handler)

    print("Bot is running...")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
