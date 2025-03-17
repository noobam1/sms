from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest
import logging
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '8178022961:AAGERHlcXoYzmfVcQ0NYWxs5cQusQnA2pwQ'
OWNER_ID = 708030615  # Replace with your Telegram ID

# ------------------- ULTIMATE DELETE FUNCTION -------------------
async def nuclear_delete(chat_id, bot):
    try:
        # Get latest 1000 messages (Telegram API limit)
        messages = []
        async for message in bot.get_chat_history(chat_id, limit=1000):
            messages.append(message.message_id)

        # Delete in bulk (Reverse order for speed)
        for msg_id in reversed(messages):
            try:
                await bot.delete_message(chat_id, msg_id)
                await asyncio.sleep(0.1)  # Avoid FloodWait
            except BadRequest as e:
                if "Message to delete not found" not in str(e):
                    logger.error(f"Error: {e}")
            except Exception as e:
                logger.error(f"Critical Error: {e}")

        return True
    except Exception as e:
        logger.error(f"Nuclear Delete Failed: {e}")
        return False

# ------------------- DELALL COMMAND -------------------
async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        user = update.effective_user

        # Security Check
        if user.id != OWNER_ID:
            await update.message.reply_text("🚫 Owner Only Command!")
            return

        if chat.type != "channel":
            await update.message.reply_text("⚠️ Only Works in Channels!")
            return

        # Permission Check
        bot_member = await chat.get_member(context.bot.id)
        if not bot_member.can_delete_messages:
            await update.message.reply_text("🔒 Grant DELETE Permission to Bot!")
            return

        # Start Deletion
        await update.message.reply_text("☢️ NUCLEAR DELETE INITIATED!")
        success = await nuclear_delete(chat.id, context.bot)
        
        if success:
            await update.message.reply_text("✅ Channel Purged Successfully!")
        else:
            await update.message.reply_text("⚠️ Partial Deletion Done. Retry!")

    except Exception as e:
        logger.error(f"DelAll Error: {e}")
        await update.message.reply_text("🚨 Critical Error! Contact @NOOB_AM")

# ------------------- START COMMAND -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔥 **Ultimate Delete Bot**\n"
        "Delete ALL channel messages with /delall\n"
        "Owner: @NOOB_AM\n\n"
        "⚠️ Warning: This action is PERMANENT!"
    )

# ------------------- MAIN FUNCTION -------------------
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delall", delall))
    application.run_polling()
    print("⚡ Bot is Running...")

if __name__ == '__main__':
    main()