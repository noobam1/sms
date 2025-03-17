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

async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat.type != "channel":
            await update.message.reply_text("❌ यह कमांड सिर्फ चैनल में काम करता है!")
            return

        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if not bot_member.can_delete_messages:
            await update.message.reply_text("❌ बॉट को मैसेज डिलीट करने की अनुमति नहीं है!")
            return

        async for message in context.bot.get_chat_history(chat.id):
            try:
                await context.bot.delete_message(chat.id, message.message_id)
            except Exception as e:
                logger.error(f"Failed to delete message {message.message_id}: {e}")
                break

        await update.message.reply_text("✅ सभी मैसेज सफलतापूर्वक डिलीट कर दिए गए हैं!")
    except Exception as e:
        logger.error(f"Error in /delall: {e}")
        await update.message.reply_text("⚠️ एक गड़बड़ी हुई है! बाद में कोशिश करें।")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        if OWNER_ID and user.id != OWNER_ID:
            await update.message.reply_text("❌ आपके पास यह कमांड चलाने की अनुमति नहीं है!")
            return

        if not context.args:
            await update.message.reply_text("ℹ️ उपयोग: /broadcast <मैसेज>")
            return

        message = " ".join(context.args)
        chat = update.effective_chat

        if chat.type == "channel":
            await context.bot.send_message(chat.id, message)
            await update.message.reply_text("✅ ब्रॉडकास्ट सफल!")
        else:
            members = await context.bot.get_chat_administrators(chat.id)
            for member in members:
                try:
                    await context.bot.send_message(member.user.id, message)
                except Exception as e:
                    logger.error(f"Failed to send to {member.user.id}: {e}")

            await update.message.reply_text(f"✅ ब्रॉडकास्ट {len(members)} यूजर्स को भेजा गया!")
    except Exception as e:
        logger.error(f"Error in /broadcast: {e}")
        await update.message.reply_text("⚠️ ब्रॉडकास्ट में समस्या आई!")

async def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("delall", delall))
    application.add_handler(CommandHandler("broadcast", broadcast))
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_running_loop()
            task = loop.create_task(main())
            loop.run_until_complete(task)