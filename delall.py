from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'YOUR_TOKEN' with your bot's token
TOKEN = '8178022961:AAGERHlcXoYzmfVcQ0NYWxs5cQusQnA2pwQ'

# Replace 'OWNER_ID' with your Telegram user ID (optional, for broadcast security)
OWNER_ID = 708030615  # Change this to your Telegram user ID

# Command handler for /delall
async def delall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id

    # Check if the command is issued in a channel
    if update.message.chat.type == 'channel':
        # Get the bot's own permissions in the channel
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        
        # Check if the bot has the permission to delete messages
        if bot_member.can_delete_messages:
            # Fetch and delete messages in batches
            message_id = update.message.message_id - 1  # Start from the message before the command
            while message_id > 0:
                try:
                    await context.bot.delete_message(chat_id, message_id)
                    message_id -= 1
                except Exception as e:
                    logger.error(f"Failed to delete message {message_id}: {e}")
                    break
            
            await update.message.reply_text("All messages have been deleted.")
        else:
            await update.message.reply_text("I don't have permission to delete messages in this channel.")
    else:
        await update.message.reply_text("This command can only be used in a channel.")

# Command handler for /broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the command is issued by the owner (optional)
    user_id = update.message.from_user.id
    if OWNER_ID and user_id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Extract the broadcast message from the command
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a message to broadcast. Usage: /broadcast <message>")
        return

    broadcast_message = " ".join(context.args)

    # Send the broadcast message to all members of the channel/group
    try:
        chat_id = update.message.chat_id

        # For channels, use `send_message` directly
        if update.message.chat.type == 'channel':
            await context.bot.send_message(chat_id=chat_id, text=broadcast_message)
            await update.message.reply_text("Broadcast sent successfully to the channel!")
        else:
            # For groups, send to each member individually
            members_count = await context.bot.get_chat_members_count(chat_id)
            for i in range(members_count):
                try:
                    await context.bot.send_message(chat_id=chat_id, text=broadcast_message)
                except Exception as e:
                    logger.error(f"Failed to send message to a member: {e}")
            
            await update.message.reply_text("Broadcast sent successfully to all members!")
    except Exception as e:
        logger.error(f"Failed to broadcast: {e}")
        await update.message.reply_text("Failed to send broadcast.")

async def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Register the /delall command handler
    application.add_handler(CommandHandler("delall", delall))

    # Register the /broadcast command handler
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())