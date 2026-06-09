import logging
import platform
import sys
import time
import sqlite3
import os
import json
import requests
import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Bot token - Environment variable se le rahe hain
TOKEN = os.environ.get("BOT_TOKEN", "")

# Check if token is set
if not TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    print("Please set your bot token in Render environment variables")
    sys.exit(1)

# Bot start time
BOT_START_TIME = time.time()

# Database setup
def init_database():
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            commands_used INTEGER DEFAULT 0
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            chat_type TEXT,
            first_seen TIMESTAMP,
            last_activity TIMESTAMP
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            command TEXT,
            timestamp TIMESTAMP,
            chat_id INTEGER
        )''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database error: {e}")

# Track user activity
async def track_user_activity(update, user_id, username, first_name, last_name, chat_id, command):
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, last_seen, commands_used) 
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT commands_used FROM users WHERE user_id=?), 0) + 1)''',
            (user_id, username or '', first_name or '', last_name or '', datetime.now(), user_id))
        
        c.execute('''INSERT INTO command_logs (user_id, command, timestamp, chat_id) 
            VALUES (?, ?, ?, ?)''', (user_id, command, datetime.now(), chat_id))
        
        if update.effective_chat:
            chat = update.effective_chat
            c.execute('''INSERT OR REPLACE INTO groups 
                (chat_id, chat_title, chat_type, last_activity) 
                VALUES (?, ?, ?, ?)''',
                (chat.id, chat.title or "Private", chat.type, datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Track error: {e}")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await track_user_activity(update, user.id, user.username, user.first_name, 
                             user.last_name, chat_id, "/start")
    
    welcome_text = f"""
🎉 **Welcome to Info Bot** {user.first_name}! 🎉

Main aapki help karne wala bot hoon.

**Available Commands:**
• /info - Apni information
• /user @username - User info
• /group - Group info
• /ipinfo - IP address info
• /datetime - Current date/time
• /random - Random number
• /password - Generate password
• /dashboard - Bot statistics
• /help - All commands

Bot is ready! 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton("👤 My Info", callback_data='my_info'),
         InlineKeyboardButton("🤖 Bot Info", callback_data='bot_info')],
        [InlineKeyboardButton("📊 Dashboard", callback_data='dashboard'),
         InlineKeyboardButton("❓ Help", callback_data='help_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# /info command
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user if update.effective_user else update.callback_query.from_user
    chat_id = update.effective_chat.id if update.effective_chat else user.id
    
    await track_user_activity(update, user.id, user.username, user.first_name, 
                             user.last_name, chat_id, "/info")
    
    info_text = f"""
👤 **Your Information**

• Name: {user.first_name} {user.last_name or ''}
• Username: @{user.username if user.username else 'Not set'}
• User ID: `{user.id}`
• Language: {user.language_code or 'Unknown'}
"""
    if update.message:
        await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(info_text, parse_mode=ParseMode.MARKDOWN)

# /user command
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide a username!\nExample: `/user @username`", parse_mode=ParseMode.MARKDOWN)
        return
    
    username = context.args[0].replace('@', '')
    
    try:
        user = await context.bot.get_chat(f"@{username}")
        info_text = f"""
👤 **User Information:** @{username}

• Name: {user.first_name} {user.last_name or ''}
• User ID: `{user.id}`
• Username: @{user.username if user.username else 'Not set'}
• Type: {user.type}
"""
        await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ User not found!")

# /group command
async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    try:
        member_count = await chat.get_member_count()
        info_text = f"""
📊 **Group Information**

• Name: {chat.title}
• Group ID: `{chat.id}`
• Type: {chat.type}
• Members: {member_count}
"""
        await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# /ipinfo command
async def ip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await track_user_activity(update, user.id, user.username, user.first_name, 
                             user.last_name, chat_id, "/ipinfo")
    
    ip = context.args[0] if context.args else None
    
    if not ip:
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            ip = response.json()['ip']
            await update.message.reply_text(f"🌐 Getting info for your IP: `{ip}`", parse_mode=ParseMode.MARKDOWN)
        except:
            await update.message.reply_text("❌ Please provide an IP address!\nExample: `/ipinfo 8.8.8.8`", parse_mode=ParseMode.MARKDOWN)
            return
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = response.json()
        
        if data['status'] == 'success':
            info_text = f"""
🌐 **IP Information:** `{ip}`

📍 **Location:**
• Country: {data['country']} ({data['countryCode']})
• Region: {data['regionName']}
• City: {data['city']}
• ISP: {data['isp']}
"""
            await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ Invalid IP address!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# /datetime command
async def date_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    
    info_text = f"""
📅 **Date & Time**

• Date: `{now.strftime('%A, %B %d, %Y')}`
• Time: `{now.strftime('%H:%M:%S')}`
• Timezone: `{time.tzname[0]}`
• Timestamp: `{int(now.timestamp())}`
"""
    await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)

# /random command
async def random_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 2:
        try:
            min_val = int(context.args[0])
            max_val = int(context.args[1])
            rand_num = random.randint(min_val, max_val)
            await update.message.reply_text(f"🎲 **Random Number:** `{rand_num}`", parse_mode=ParseMode.MARKDOWN)
        except:
            await update.message.reply_text("❌ Use: `/random 1 100`", parse_mode=ParseMode.MARKDOWN)
    else:
        rand_num = random.randint(1, 100)
        await update.message.reply_text(f"🎲 **Random Number (1-100):** `{rand_num}`", parse_mode=ParseMode.MARKDOWN)

# /password command
async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 12
    if context.args and context.args[0].isdigit():
        length = min(int(context.args[0]), 32)
    
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    
    await update.message.reply_text(f"🔐 **Generated Password:**\n`{password}`\n\n⚠️ Copy it now!", parse_mode=ParseMode.MARKDOWN)

# /dashboard command
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM command_logs")
        total_commands = c.fetchone()[0]
        
        conn.close()
        
        uptime_seconds = int(time.time() - BOT_START_TIME)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        dashboard_text = f"""
📊 **Dashboard**

• Total Users: `{total_users}`
• Commands: `{total_commands}`
• Uptime: `{hours}h {minutes}m`
• Status: 🟢 Online
"""
        await update.message.reply_text(dashboard_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"📊 **Dashboard**\n\nStatus: 🟢 Online", parse_mode=ParseMode.MARKDOWN)

# /bot command
async def bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_user = await context.bot.get_me()
    info_text = f"""
🤖 **Bot Info**

• Name: {bot_user.first_name}
• Username: @{bot_user.username}
• Status: 🟢 Online
• Python: {sys.version.split()[0]}
"""
    await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)

# /ping command
async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    message = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    await message.edit_text(f"🏓 **Pong!**\nResponse: `{response_time:.2f}ms`", parse_mode=ParseMode.MARKDOWN)

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 **Commands List**

**User Commands:**
• /info - Your information
• /user @username - User info
• /id - Get IDs

**Group Commands:**
• /group - Group info
• /admins - List admins

**Utility Commands:**
• /ipinfo [ip] - IP address info
• /datetime - Current date/time
• /random [min max] - Random number
• /password [length] - Generate password
• /dashboard - Bot statistics
• /bot - Bot info
• /ping - Check status
• /help - This menu
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# /id command
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(f"🆔 **Your ID:** `{user.id}`\n**Chat ID:** `{chat.id}`", parse_mode=ParseMode.MARKDOWN)

# /admins command
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Groups only!")
        return
    
    try:
        admins = await chat.get_administrators()
        admin_list = "\n".join([f"• {admin.user.first_name}" for admin in admins[:5]])
        await update.message.reply_text(f"👑 **Admins:**\n{admin_list}", parse_mode=ParseMode.MARKDOWN)
    except:
        await update.message.reply_text("❌ Cannot fetch admins")

# Callback handler
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'my_info':
        await my_info(update, context)
    elif query.data == 'bot_info':
        await bot_info(update, context)
    elif query.data == 'dashboard':
        await dashboard(update, context)
    elif query.data == 'help_menu':
        await help_command(update, context)

# Set commands for menu
async def set_commands(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("info", "Your information"),
        BotCommand("user", "Get user info"),
        BotCommand("group", "Group information"),
        BotCommand("ipinfo", "Get IP information"),
        BotCommand("datetime", "Current date & time"),
        BotCommand("random", "Generate random number"),
        BotCommand("password", "Generate password"),
        BotCommand("dashboard", "Bot statistics"),
        BotCommand("ping", "Check bot status"),
        BotCommand("help", "Show all commands")
    ]
    await application.bot.set_my_commands(commands)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# Main function
def main():
    print("🤖 Starting Info Bot...")
    print(f"Python version: {sys.version}")
    
    # Initialize database
    init_database()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", my_info))
    application.add_handler(CommandHandler("user", user_info))
    application.add_handler(CommandHandler("group", group_info))
    application.add_handler(CommandHandler("ipinfo", ip_info))
    application.add_handler(CommandHandler("datetime", date_time))
    application.add_handler(CommandHandler("random", random_number))
    application.add_handler(CommandHandler("password", generate_password))
    application.add_handler(CommandHandler("dashboard", dashboard))
    application.add_handler(CommandHandler("bot", bot_info))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("admins", list_admins))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    # Set commands
    application.post_init = set_commands
    
    print("✅ Bot is ready!")
    print("🚀 Starting polling...")
    
    # Start bot with polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
