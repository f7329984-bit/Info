import os
import random
import string
import requests
import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    print("❌ BOT_TOKEN not set!")
    exit(1)

# Database
import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT, username TEXT, last_seen TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_user(user_id, first_name, username):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users (user_id, first_name, username, last_seen) 
                 VALUES (?, ?, ?, ?)''', (user_id, first_name, username, datetime.now()))
    conn.commit()
    conn.close()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.first_name, user.username)
    
    keyboard = [
        [InlineKeyboardButton("👤 My Info", callback_data='info'),
         InlineKeyboardButton("🤖 Bot Info", callback_data='bot_info')],
        [InlineKeyboardButton("👑 Admins List", callback_data='admins'),
         InlineKeyboardButton("🆔 My ID", callback_data='my_id')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎉 Welcome {user.first_name}!\n\n"
        f"Send /help for all commands.\n\n"
        f"Click buttons below 👇",
        reply_markup=reply_markup
    )

# Info command
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""
👤 **YOUR INFORMATION**

• Name: {user.first_name} {user.last_name or ''}
• User ID: `{user.id}`
• Username: @{user.username if user.username else 'Not set'}
• Language: {user.language_code or 'EN'}

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    await update.message.reply_text(text, parse_mode='Markdown')

# ID command
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(f"🆔 **Your ID:** `{user.id}`\n**Chat ID:** `{chat.id}`", parse_mode='Markdown')

# Admins command
async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    try:
        admins_list = await chat.get_administrators()
        if not admins_list:
            await update.message.reply_text("❌ Cannot fetch admins list!")
            return
        
        text = "👑 **GROUP ADMINS** 👑\n\n"
        
        for admin in admins_list:
            user = admin.user
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            text += f"• {mention}"
            if user.username:
                text += f" (@{user.username})"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Admins error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# User info
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/user @username`", parse_mode='Markdown')
        return
    
    username = context.args[0].replace('@', '')
    
    try:
        user = await context.bot.get_chat(f"@{username}")
        text = f"👤 **User:** @{username}\nName: {user.first_name}\nID: `{user.id}`"
        await update.message.reply_text(text, parse_mode='Markdown')
    except:
        await update.message.reply_text(f"❌ User @{username} not found!")

# Group info
async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Groups only!")
        return
    
    try:
        member_count = await chat.get_member_count()
        admins = await chat.get_administrators()
        
        text = f"📊 **Group:** {chat.title}\nID: `{chat.id}`\nMembers: {member_count}\nAdmins: {len(admins)}"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Group info error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Bot info
async def bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = await context.bot.get_me()
    await update.message.reply_text(f"🤖 **Bot:** {bot.first_name}\nUsername: @{bot.username}\nStatus: 🟢 Online", parse_mode='Markdown')

# Ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    ms = (end_time - start_time) * 1000
    await msg.edit_text(f"🏓 **Pong!**\nResponse: `{ms:.2f}ms`", parse_mode='Markdown')

# Random number
async def random_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 2:
        try:
            min_val = int(context.args[0])
            max_val = int(context.args[1])
            num = random.randint(min_val, max_val)
            await update.message.reply_text(f"🎲 **Random:** `{num}`", parse_mode='Markdown')
        except:
            await update.message.reply_text("❌ Use: `/random 1 100`", parse_mode='Markdown')
    else:
        num = random.randint(1, 100)
        await update.message.reply_text(f"🎲 **Random (1-100):** `{num}`", parse_mode='Markdown')

# Password
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 12
    if context.args and context.args[0].isdigit():
        length = min(int(context.args[0]), 32)
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(random.choice(chars) for _ in range(length))
    
    await update.message.reply_text(f"🔐 **Password:** `{pwd}`", parse_mode='Markdown')

# DateTime
async def datetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    await update.message.reply_text(f"📅 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# IP Info
async def ipinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = context.args[0] if context.args else None
    
    if not ip:
        try:
            r = requests.get('https://api.ipify.org?format=json', timeout=10)
            ip = r.json()['ip']
        except:
            await update.message.reply_text("❌ Usage: `/ipinfo 8.8.8.8`", parse_mode='Markdown')
            return
    
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
        data = r.json()
        
        if data['status'] == 'success':
            text = f"🌐 **IP:** `{ip}`\n📍 {data['city']}, {data['country']}\n🏢 {data['isp']}"
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Invalid IP!")
    except:
        await update.message.reply_text("❌ Error!")

# Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📚 **COMMANDS**

/info - Your info
/user @username - User info
/id - Your ID
/admins - Mention all admins
/group - Group info
/random - Random number
/password - Generate password
/datetime - Current time
/ipinfo - IP details
/ping - Check status
/bot - Bot info
/help - This menu
"""
    await update.message.reply_text(text)

# Button callbacks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'info':
        user = query.from_user
        await query.edit_message_text(f"👤 {user.first_name}\nID: `{user.id}`", parse_mode='Markdown')
    elif query.data == 'bot_info':
        bot = await context.bot.get_me()
        await query.edit_message_text(f"🤖 @{bot.username}", parse_mode='Markdown')
    elif query.data == 'admins':
        await query.edit_message_text("👑 Send /admins in group")
    elif query.data == 'my_id':
        user = query.from_user
        await query.edit_message_text(f"🆔 Your ID: `{user.id}`", parse_mode='Markdown')
    elif query.data == 'help':
        await query.edit_message_text("Send /help for commands")

# Main
def main():
    print(f"🤖 Starting Info Bot... Port: {PORT}")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("user", user_info))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("group", group_info))
    app.add_handler(CommandHandler("bot", bot_info))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("random", random_num))
    app.add_handler(CommandHandler("password", password))
    app.add_handler(CommandHandler("datetime", datetime_cmd))
    app.add_handler(CommandHandler("ipinfo", ipinfo))
    app.add_handler(CallbackQueryHandler(button_click))
    
    # ✅ Sirf polling - koi webhook dependency nahi
    print("🚀 Bot starting via polling...")
    print("✅ Bot is running!")
    app.run_polling()
