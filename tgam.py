from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from datetime import datetime

# Replace with your bot token and channel username
BOT_TOKEN = "7658259988:AAFKN4LLdMLqeqJzja9THadqH_SyU9KdOw0"
CHANNEL_USERNAME = "@TG_PREMIUMGIVEAWAY"
ADMIN_USER_ID = 708030615  # Replace with your Telegram user ID

# Dictionary to store user points, referral data, and user IDs
user_points = {}
referral_data = {}  # {referrer_id: [referred_user_ids]}
user_ids = set()  # Store all user IDs for broadcasting
daily_bonus_data = {}  # {user_id: last_claim_timestamp}

# Check if user is in the channel
async def is_user_in_channel(user_id, context: CallbackContext):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

# Force join channel
async def force_join_channel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not await is_user_in_channel(user_id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        await update.message.reply_text(
            "You must join our channel to use this bot!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return False
    return True

# Start command with referral system
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_ids.add(user_id)  # Add user ID to the set

    # Check if the user was referred
    if context.args and context.args[0].startswith("ref_"):
        referrer_id = int(context.args[0].split("_")[1])
        if referrer_id != user_id:  # Prevent self-referral
            if referrer_id in referral_data:
                referral_data[referrer_id].append(user_id)
            else:
                referral_data[referrer_id] = [user_id]
            user_points[referrer_id] = user_points.get(referrer_id, 0) + 1  # Award 1 coin to referrer
            await context.bot.send_message(chat_id=referrer_id, text=f"🎉 You earned 1 coin! New user joined using your link. Total coins: {user_points[referrer_id]}")

    # Welcome message with referral link
    welcome_message = (
        "🌟 *Welcome to the Telegram Premium Giveaway Bot!* 🌟\n\n"
        "🎉 *Unlock Telegram Premium for FREE!* 🎉\n\n"
        "🚀 *How It Works:*\n"
        "1. *Earn Coins:*\n"
        "   - Share your referral link and earn **1 coin** for each new user who joins using your link.\n"
        "   - Claim your **daily bonus** of 1 coin with `/daily`.\n\n"
        "2. *Redeem Telegram Premium:*\n"
        "   - Collect **50 coins** to unlock **Telegram Premium** for FREE!\n"
        "   - Use the `/redeem` command to claim your reward.\n\n"
        "3. *Join Our Channel:*\n"
        "   - You must join our channel to participate in the giveaway.\n"
        "   - Click the button below to join:\n\n"
        "💎 *Telegram Premium Benefits:*\n"
        "   - No ads\n"
        "   - Faster downloads\n"
        "   - Exclusive stickers and emojis\n"
        "   - Increased limits for chats, files, and more!\n"
    )

    # Add buttons for joining the channel and sharing the referral link
    keyboard = [
        [InlineKeyboardButton("🚀 Join Channel 🚀", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("📤 Share Referral Link 📤", callback_data="share_link")]
    ]
    await update.message.reply_text(
        welcome_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Handle callback queries (for buttons)
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "share_link":
        user_id = query.from_user.id
        referral_link = f"https://t.me/your_bot_username?start=ref_{user_id}"  # Replace with your bot username
        await query.edit_message_text(
            f"📤 *Share your referral link and earn coins!* 📤\n\n"
            f"Your referral link:\n`{referral_link}`\n\n"
            f"Send this link to your friends. When they join using your link, you'll earn 1 coin!",
            parse_mode="Markdown"
        )

# Daily bonus command
async def daily_bonus(update: Update, context: CallbackContext):
    if not await force_join_channel(update, context):
        return

    user_id = update.message.from_user.id
    today = datetime.now().date()

    if user_id in daily_bonus_data and daily_bonus_data[user_id] == today:
        await update.message.reply_text("You have already claimed your daily bonus today. Come back tomorrow!")
        return

    daily_bonus_data[user_id] = today
    user_points[user_id] = user_points.get(user_id, 0) + 1  # Award 1 coin
    await update.message.reply_text("🎉 You claimed your daily bonus of 1 coin!")

# Leaderboard command
async def leaderboard(update: Update, context: CallbackContext):
    if not await force_join_channel(update, context):
        return

    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
    leaderboard_message = "🏆 *Top 10 Users* 🏆\n\n"
    for idx, (user_id, points) in enumerate(sorted_users):
        leaderboard_message += f"{idx + 1}. User {user_id}: {points} coins\n"
    await update.message.reply_text(leaderboard_message, parse_mode="Markdown")

# Referral history command
async def referral_history(update: Update, context: CallbackContext):
    if not await force_join_channel(update, context):
        return

    user_id = update.message.from_user.id
    if user_id not in referral_data or not referral_data[user_id]:
        await update.message.reply_text("You haven't referred any users yet.")
        return

    referred_users = referral_data[user_id]
    history_message = "📜 *Your Referral History* 📜\n\n"
    history_message += f"Total Referrals: {len(referred_users)}\n"
    history_message += f"Total Coins Earned: {len(referred_users)} coins\n"
    await update.message.reply_text(history_message, parse_mode="Markdown")

# Redeem Telegram Premium
async def redeem_premium(update: Update, context: CallbackContext):
    if not await force_join_channel(update, context):
        return

    user_id = update.message.from_user.id
    if user_points.get(user_id, 0) >= 50:
        user_points[user_id] -= 50
        await update.message.reply_text(
            "🎉 Congratulations! You have successfully redeemed **Telegram Premium**.\n\n"
            "The admin will contact you shortly to gift your premium subscription."
        )
        # Notify admin to gift Telegram Premium
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"User {user_id} has redeemed Telegram Premium. Please gift them the subscription."
        )
    else:
        await update.message.reply_text("You need at least 50 coins to redeem Telegram Premium.")

# Admin commands
async def add_coins(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        user_id = int(context.args[0])
        coins = int(context.args[1])
        user_points[user_id] = user_points.get(user_id, 0) + coins
        await update.message.reply_text(f"Added {coins} coins to user {user_id}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addcoins <user_id> <coins>")

async def remove_coins(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        user_id = int(context.args[0])
        coins = int(context.args[1])
        user_points[user_id] = max(user_points.get(user_id, 0) - coins, 0)
        await update.message.reply_text(f"Removed {coins} coins from user {user_id}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /removecoins <user_id> <coins>")

async def reset_coins(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        user_id = int(context.args[0])
        user_points[user_id] = 0
        await update.message.reply_text(f"Reset coins for user {user_id}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /resetcoins <user_id>")

# User profile command
async def profile(update: Update, context: CallbackContext):
    if not await force_join_channel(update, context):
        return

    user_id = update.message.from_user.id
    profile_message = (
        f"👤 *Your Profile* 👤\n\n"
        f"Coins: {user_points.get(user_id, 0)}\n"
        f"Referrals: {len(referral_data.get(user_id, []))}\n"
    )
    await update.message.reply_text(profile_message, parse_mode="Markdown")

# Broadcast command (for admins only)
async def broadcast(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Get the broadcast message from the command
    broadcast_message = " ".join(context.args)
    if not broadcast_message:
        await update.message.reply_text("Please provide a message to broadcast. Usage: /broadcast <message>")
        return

    # Send the message to all users
    success_count = 0
    fail_count = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=broadcast_message)
            success_count += 1
        except Exception as e:
            print(f"Failed to send message to {uid}: {e}")
            fail_count += 1

    await update.message.reply_text(f"Broadcast completed!\nSuccess: {success_count}\nFailed: {fail_count}")

# Help command
async def help_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id == ADMIN_USER_ID:
        # Admin help message
        help_message = (
            "🛠️ *Admin Commands:*\n"
            "   - `/addcoins <user_id> <coins>`: Add coins to a user.\n"
            "   - `/removecoins <user_id> <coins>`: Remove coins from a user.\n"
            "   - `/resetcoins <user_id>`: Reset a user's coins to 0.\n"
            "   - `/broadcast <message>`: Send a message to all users.\n\n"
            "👤 *User Commands:*\n"
            "   - `/start`: Start the bot and get your referral link.\n"
            "   - `/daily`: Claim your daily bonus of 1 coin.\n"
            "   - `/share`: Get your referral link to share with friends.\n"
            "   - `/referrals`: View your referral history.\n"
            "   - `/leaderboard`: View the top 10 users.\n"
            "   - `/redeem`: Redeem Telegram Premium for 50 coins.\n"
            "   - `/profile`: View your profile (coins and referrals).\n"
            "   - `/help`: Show this help message.\n"
        )
    else:
        # User help message
        help_message = (
            "👤 *User Commands:*\n"
            "   - `/start`: Start the bot and get your referral link.\n"
            "   - `/daily`: Claim your daily bonus of 1 coin.\n"
            "   - `/share`: Get your referral link to share with friends.\n"
            "   - `/referrals`: View your referral history.\n"
            "   - `/leaderboard`: View the top 10 users.\n"
            "   - `/redeem`: Redeem Telegram Premium for 50 coins.\n"
            "   - `/profile`: View your profile (coins and referrals).\n"
            "   - `/help`: Show this help message.\n"
        )
    await update.message.reply_text(help_message, parse_mode="Markdown")

# Main function to run the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("daily", daily_bonus))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("referrals", referral_history))
    application.add_handler(CommandHandler("redeem", redeem_premium))
    application.add_handler(CommandHandler("addcoins", add_coins))
    application.add_handler(CommandHandler("removecoins", remove_coins))
    application.add_handler(CommandHandler("resetcoins", reset_coins))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("help", help_command))  # Add help command
    application.add_handler(CallbackQueryHandler(button_handler))  # Add this line to handle button clicks

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()