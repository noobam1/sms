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
OWNER_ID = 708030615  # Replace with your Telegram ID

# ------------------- START MESSAGE -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    start_text = f"""
    🚀 **Welcome {user.first_name}!** 🚀

    🤖 I'm a Power Delete Bot. Here's what I can do:

    ✅ `/delall` - Delete ALL messages in a channel
    ✅ `/broadcast` - Send message to all users
    ✅ `/stats` - Check bot statistics

    📝 **How to Use**:
    1. Add me to your channel as ADMIN
    2. Give me *Delete Messages* permission
    3. Send `/delall` to clean the channel!

    👑 **Owner**: [NOOB_AM](https://t.me/NOOB_AM)
    """
    await update.message.reply_text(start_text, parse_mode='Markdown')

# ------------------- DELETE ALL MESSAGES -------------------
async def delete_all_messages(chat_id, bot):
    try:
        async for message in bot.get_chat_history(chat_id):
            try:
                await bot.delete_message(chat_id, message.message_id)
                await asyncio.sleep(0.2)  # Avoid rate limits
            except Exception as e:
                if "message not found" not in str(e):
                    logger.error(f"Error deleting {message.message_id}: {e}")
    except Exception as e:
        logger.error(f"Mass Delete Error: {e}")

async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if user.id != OWNER_ID:
        await update.message.reply_text("❌ Only Owner can use this command!")
        return

    if chat.type != "channel":
        await update.message.reply_text("⚠️ This command works only in Channels!")
        return

    try:
        bot_member = await chat.get_member(context.bot.id)
        if not bot_member.can_delete_messages:
            await update.message.reply_text("🔒 Grant DELETE permission to bot!")
            return

        await update.message.reply_text("⚡ Deleting ALL messages...")
        await delete_all_messages(chat.id, context.bot)
        await update.message.reply_text("✅ Channel Cleared Successfully!")

    except Exception as e:
        logger.error(f"DelAll Error: {e}")
        await update.message.reply_text("🚨 Error! Contact @NOOB_AM")

# ------------------- MAIN SETUP -------------------
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delall", delall))
    
    # Start bot
    application.run_polling()
    print("Bot is running...")

if __name__ == '__main__':
    main()