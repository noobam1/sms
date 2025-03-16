import sqlite3
import random
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext  # Change here

# Fast2SMS API Key
FAST2SMS_API_KEY = "vOC4pPHFXVy8UEkGstm6ZYRul0rx7wqnd3b2NhSQgozBcDfiMewZp4bNRzlLQ8m1GFqMsHEfj6dYaXTK"

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7884864217:AAEmmLWJFuCpF5nJJPK4o0RWQF-ZMsdueTc"

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
def check_channel_join(chat_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT joined_channel FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

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
def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    add_user(chat_id)
    if check_channel_join(chat_id):
        update.message.reply_text(
            "Welcome! Use /getnumber to get a virtual number for OTP."
        )
    else:
        update.message.reply_text(
            "Please join our channel to use this bot: @yourchannel\n\n"
            "After joining, click here: /start"
        )

# Command: /getnumber
def get_number(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if not check_channel_join(chat_id):
        update.message.reply_text(
            "You must join our channel to use this bot: @yourchannel\n\n"
            "After joining, click here: /start"
        )
        return

    coins = get_coins(chat_id)
    if coins < 40:
        update.message.reply_text(
            f"You need 40 coins to generate a number. You have {coins} coins."
        )
        return

    # Deduct coins
    deduct_coins(chat_id, 40)

    # Generate a random virtual number (for simulation)
    virtual_number = "+91" + str(random.randint(9000000000, 9999999999))

    # Send the virtual number to the user
    update.message.reply_text(
        f"Your virtual number is: {virtual_number}. "
        "Use this number to receive OTP."
    )

    # Generate and send OTP via Fast2SMS
    otp = str(random.randint(100000, 999999))
    try:
        response = send_otp(virtual_number, otp)
        if response.get('return'):
            update.message.reply_text(
                f"OTP sent to {virtual_number}. "
                f"Your OTP is: {otp}"
            )
        else:
            update.message.reply_text(
                "Failed to send OTP. Please try again later."
            )
    except Exception as e:
        update.message.reply_text(
            f"An error occurred: {str(e)}"
        )

# Command: /addcoins (admin only)
def add_coins_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT admin_id FROM admin WHERE admin_id = ?', (chat_id,))
    if not cursor.fetchone():
        update.message.reply_text("You are not an admin.")
        return

    try:
        target_chat_id = int(context.args[0])
        coins = int(context.args[1])
        add_coins(target_chat_id, coins)
        update.message.reply_text(f"Added {coins} coins to user {target_chat_id}.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /addcoins <chat_id> <coins>")

# Check if user has joined the channel
def check_user_channel_join(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if check_channel_join(chat_id):
        update.message.reply_text("You have already joined the channel.")
    else:
        update.message.reply_text(
            "You must join our channel to use this bot: @yourchannel\n\n"
            "After joining, click here: /start"
        )

# Main function to run the bot
def main():
    # Initialize database
    init_db()

    # Add admin (replace with your admin chat ID)
    add_admin(708030615)  # Replace with your admin chat ID

    # Initialize Telegram bot
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("getnumber", get_number))
    dp.add_handler(CommandHandler("addcoins", add_coins_command))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_channel_join))  # Change here

    # Start the bot
    updater.start_polling()
    print("Bot is running...")

    # Keep the bot running
    updater.idle()

if __name__ == "__main__":
    main()