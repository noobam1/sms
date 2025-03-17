from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '8178022961:AAGERHlcXoYzmfVcQ0NYWxs5cQusQnA2pwQ'
OWNER_ID = 708030615  # Your Telegram ID

# Ultra-Fast Deleter for Channels & Groups
async def delete_all_messages(chat_id, bot):
    try:
        # Fetch latest 100000 messages
        async for message in bot.get_chat_history(chat_id, limit=100000):
            try:
                await bot.delete_message(chat_id, message.message_id)
                await asyncio.sleep(0.2)  # Avoid rate limits
            except Exception as e:
                logger.error(f"Failed to delete {message.message_id}: {e}")
    except Exception as e:
        logger.error(f"Mass Delete Error: {e}")

# Command: /nuke (Deletes EVERYTHING)
async def nuke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only Owner can use this command!")
        return

    chat = update.effective_chat
    if chat.type not in ["channel", "group", "supergroup"]:
        await update.message.reply_text("❌ This works only in Channels/Groups!")
        return

    # Check Bot Permissions
    bot_member = await chat.get_member(context.bot.id)
    if not bot_member.can_delete_messages:
        await update.message.reply_text("🔒 Bot needs DELETE permission!")
        return

    await update.message.reply_text("☢️ NUKE INITIATED! Deleting ALL messages...")
    await delete_all_messages(chat.id, context.bot)
    await update.message.reply_text("✅ Chat nuked successfully!")

# Start the Bot
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("nuke", nuke))
    application.run_polling()

if __name__ == '__main__':
    main()