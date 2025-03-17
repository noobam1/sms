from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import asyncio
import nest_asyncio

# Fix for event loop issue
nest_asyncio.apply()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '8178022961:AAGERHlcXoYzmfVcQ0NYWxs5cQusQnA2pwQ'
OWNER_ID = 708030615  # Change this to your ID
OWNER_USERNAME = "@NOOB_AM"

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "🤖 Hello! I am your Telegram bot.\n\n"
        "🔹 Use /delall to delete all messages in a channel.\n"
        "🔹 Halat ko dekhke bot bnaya hai.\n\n"
        f"👑 Owner: {OWNER_USERNAME}"
    )
    await update.message.reply_text(welcome_message)

# Command: /delall (Deletes all messages in a channel)
async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat.type != "channel":
            await update.message.reply_text("❌ This command works only in channels!")
            return

        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if not bot_member.can_delete_messages:
            await update.message.reply_text("❌ The bot does not have permission to delete messages!")
            return

        async for message in context.bot.get_chat_history(chat.id):
            try:
                await context.bot.delete_message(chat.id, message.message_id)
            except Exception as e:
                logger.error(f"Failed to delete message {message.message_id}: {e}")
                break

        await update.message.reply_text("✅ All messages have been successfully deleted!")
    except Exception as e:
        logger.error(f"Error in /delall: {e}")
        await update.message.reply_text("⚠️ An error occurred! Please try again later.")

# Command: /broadcast (Sends a message to channel/admins)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        if OWNER_ID and user.id != OWNER_ID:
            await update.message.reply_text("❌ You do not have permission to use this command!")
            return

        if not context.args:
            await update.message.reply_text("ℹ️ Usage: /broadcast <message>")
            return

        message = " ".join(context.args)
        chat = update.effective_chat

        if chat.type == "channel":
            await context.bot.send_message(chat.id, message)
            await update.message.reply_text("✅ Broadcast successful!")
        else:
            members = await context.bot.get_chat_administrators(chat.id)
            for member in members:
                try:
                    await context.bot.send_message(member.user.id, message)
                except Exception as e:
                    logger.error(f"Failed to send to {member.user.id}: {e}")

            await update.message.reply_text(f"✅ Broadcast sent to {len(members)} users!")
    except Exception as e:
        logger.error(f"Error in /broadcast: {e}")
        await update.message.reply_text("⚠️ An error occurred during broadcast!")

# Main Function
async def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delall", delall))
    application.add_handler(CommandHandler("broadcast", broadcast))

    print("Bot is running...")
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_running_loop()
            task = loop.create_task(main())
            loop.run_until_complete(task)
