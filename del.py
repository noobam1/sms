from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest, RetryAfter
import logging
import asyncio

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '8178022961:AAGERHlcXoYzmfVcQ0NYWxs5cQusQnA2pwQ'  # @BotFather से लें
OWNER_ID = 708030615      # अपना Telegram ID डालें

# ------------------- ADVANCED DELETE SYSTEM -------------------
async def delete_all_messages(chat_id, bot):
    try:
        # Get latest 2000 messages (Telegram limit)
        messages = []
        async for message in bot.get_chat_history(chat_id, limit=2000):
            messages.append(message.message_id)
        
        # Delete in reverse order (newest first)
        deleted_count = 0
        for msg_id in reversed(messages):
            try:
                await bot.delete_message(chat_id, msg_id)
                deleted_count += 1
                if deleted_count % 50 == 0:
                    await asyncio.sleep(2)  # Flood control
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 2)
            except BadRequest as e:
                if "Message to delete not found" not in str(e):
                    logger.error(f"Error: {msg_id} - {e}")
            except Exception as e:
                logger.error(f"Critical Error: {e}")

        return deleted_count
    except Exception as e:
        logger.error(f"Delete Process Failed: {e}")
        return 0

# ------------------- /delall COMMAND -------------------
async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat

        # Security Checks
        if user.id != OWNER_ID:
            await update.message.reply_text("🚫 Owner Only Command!")
            return

        if chat.type != "channel":
            await update.message.reply_text("⚠️ This works only in CHANNELS!")
            return

        # Permission Verification
        bot_member = await chat.get_member(context.bot.id)
        if not (bot_member.can_delete_messages and bot_member.status == 'administrator'):
            await update.message.reply_text("🔒 Grant DELETE + ADMIN rights to bot!")
            return

        # Start Mass Deletion
        status_msg = await update.message.reply_text("⚡ DELETION STARTED...")
        count = await delete_all_messages(chat.id, context.bot)
        
        # Final Report
        await status_msg.edit_text(f"✅ Success! Deleted {count} messages!")
        await context.bot.send_message(
            chat.id,
            f"🔥 Channel Purged Successfully!\n"
            f"• Deleted Messages: {count}\n"
            f"• Owner: @NOOB_AM"
        )

    except Exception as e:
        logger.error(f"Command Error: {e}")
        await update.message.reply_text("⚠️ Critical Error! Contact @NOOB_AM")

# ------------------- START MESSAGE -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Professional Delete Bot**\n"
        "Instant Channel Cleaner with /delall\n\n"
        "📌 Features:\n"
        "- Delete 2000+ messages/minute\n"
        "- FloodWait Protection\n"
        "- Owner Restricted\n\n"
        "👑 Owner: @NOOB_AM"
    )

# ------------------- MAIN SETUP -------------------
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delall", delall))
    application.run_polling()
    print("🤖 Bot Activated!")

if __name__ == '__main__':
    main()