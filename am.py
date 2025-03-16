import sqlite3
import random
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Fast2SMS API Key
FAST2SMS_API_KEY = "vOC4pPHFXVy8UEkGstm6ZYRul0rx7wqnd3b2NhSQgozBcDfiMewZp4bNRzlLQ8m1GFqMsHEfj6dYaXTK"

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7884864217:AAEmmLWJFuCpF5nJJPK4o0RWQF-ZMsdueTc"

# Channel username (e.g., "@yourchannel")
CHANNEL_USERNAME = "@NOOB_AM_VIP"

# Database setup
def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            joined_channel INTEGER DEFAULT 0
        )
    ''')
    # Create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

# Add admin
def add_admin(admin_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO admin (admin_id) VALUES (?)', (admin_id,))
    conn.commit()
    conn.close()

# Add or update user
def add_user(chat_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
    conn.commit()
    conn.close()

# Check if user has joined the channel
async def check_channel_join(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    try:
        # Check if the user is a member of the channel
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            # Update database
            update_channel_join(chat_id, 1)
            return True
        else:
            # Update database
            update_channel_join(chat_id, 0)
            return False
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

# Update channel join status
def update_channel_join(chat_id, status):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET joined_channel = ? WHERE chat_id = ?', (status, chat_id))
    conn.commit()
    conn.close()

# Deduct coins from user
def deduct_coins(chat_id, coins):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = coins - ? WHERE chat_id = ?', (coins, chat_id))
    conn.commit()
    conn.close()

# Get user coins
def get_coins(chat_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Add coins to user (admin only)
def add_coins(chat_id, coins):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = coins + ? WHERE chat_id = ?', (coins, chat_id))
    conn.commit()
    conn.close()

# Send OTP via Fast2SMS API
def send_otp(phone_number, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "sender_id": "FSTSMS",
        "message": f"Your OTP is: {otp}",
        "language": "english",
        "route": "v3",
        "numbers": phone_number
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Command: /start
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    add_user(chat_id)

    # Check if the user has joined the channel
    if await check_channel_join(update, context):
        await update.message.reply_text(
            "Welcome! Use /getnumber to get a virtual number for OTP."
        )
    else:
        await update.message.reply_text(
            f"Please join our channel to use this bot: {CHANNEL_USERNAME}\n\n"
            "After joining, click here: /start"
        )

# Command: /getnumber
async def get_number(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    # Check if the user has joined the channel
    if not await check_channel_join(update, context):
        await update.message.reply_text(
            f"You must join our channel to use this bot: {CHANNEL_USERNAME}\n\n"
            "After joining, click here: /start"
        )
        return

    coins = get_coins(chat_id)
    if coins < 40:
        await update.message.reply_text(
            f"You need 40 coins to generate a number. You have {coins} coins."
        )
        return

    # Deduct coins
    deduct_coins(chat_id, 40)

    # Generate a random virtual number (for simulation)
    virtual_number = "+91" + str(random.randint(9000000000, 9999999999))

    # Send the virtual number to the user
    await update.message.reply_text(
        f"Your virtual number is: {virtual_number}. "
        "Use this number to receive OTP."
    )

    # Generate and send OTP via Fast2SMS
    otp = str(random.randint(100000, 999999))
    try:
        response = send_otp(virtual_number, otp)
        if response.get('return'):
            await update.message.reply_text(
                f"OTP sent to {virtual_number}. "
                f"Your OTP is: {otp}"
            )
        else:
            await update.message.reply_text(
                "Failed to send OTP. Please try again later."
            )
    except Exception as e:
        await update.message.reply_text(
            f"An error occurred: {str(e)}"
        )

# Command: /addcoins (admin only)
async def add_coins_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT admin_id FROM admin WHERE admin_id = ?', (chat_id,))
    if not cursor.fetchone():
        await update.message.reply_text("You are not an admin.")
        return

    try:
        target_chat_id = int(context.args[0])
        coins = int(context.args[1])
        add_coins(target_chat_id, coins)
        await update.message.reply_text(f"Added {coins} coins to user {target_chat_id}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addcoins <chat_id> <coins>")

# Main function to run the bot
async def main():
    # Initialize database
    init_db()

    # Add admin (replace with your admin chat ID)
    add_admin(708030615)  # Replace with your admin chat ID

    # Initialize Telegram bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getnumber", get_number))
    application.add_handler(CommandHandler("addcoins", add_coins_command))

    # Start the bot
    print("Bot is running...")
    await application.run_polling()

# Run the bot
if __name__ == "__main__":
    try:
        # Check if an event loop is already running
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If a loop is already running, use it
            loop.create_task(main())
        else:
            # If no loop is running, create a new one
            asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")