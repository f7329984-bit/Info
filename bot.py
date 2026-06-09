import os
import random
import string
import requests
import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler  # ✅ Purana import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    print("❌ BOT_TOKEN not set!")
    exit(1)

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

# Sab commands async banaye bina - SAME AS ORIGINAL
def start(update, context):
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
    
    update.message.reply_text(
        f"🎉 Welcome {user.first_name}!\n\n"
        f"Send /help for all commands.\n\n"
        f"Click buttons below 👇",
        reply_markup=reply_markup
    )

def info(update, context):
    user = update.effective_user
    text = f"""
👤 **YOUR INFORMATION**

• Name: {user.first_name} {user.last_name or ''}
• User ID: `{user.id}`
• Username: @{user.username if user.username else 'Not set'}
• Language: {user.language_code or 'EN'}

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    update.message.reply_text(text, parse_mode='Markdown')

def my_id(update, context):
    user = update.effective_user
    chat = update.effective_chat
    update.message.reply_text(f"🆔 **Your ID:** `{user.id}`\n**Chat ID:** `{chat.id}`", parse_mode='Markdown')

def admins(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        update.message.reply_text("❌ This command only works in groups!")
        return
    
    try:
        # v13 mein yeh sync hi kaam karta hai
        admins_list = chat.get_administrators()
        if not admins_list:
            update.message.reply_text("❌ Cannot fetch admins list!")
            return
        
        text = "👑 **GROUP ADMINS** 👑\n\n"
        
        for admin in admins_list:
            user = admin.user
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            text += f"• {mention}"
            if user.username:
                text += f" (@{user.username})"
            text += "\n"
        
        update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Admins error: {e}")
        update.message.reply_text(f"❌ Error: {str(e)}")

def user_info(update, context):
    if not context.args:
        update.message.reply_text("❌ Usage: `/user @username`", parse_mode='Markdown')
        return
    
    username = context.args[0].replace('@', '')
    
    try:
        user = context.bot.get_chat(f"@{username}")
        text = f"👤 **User:** @{username}\nName: {user.first_name}\nID: `{user.id}`"
        update.message.reply_text(text, parse_mode='Markdown')
    except:
        update.message.reply_text(f"❌ User @{username} not found!")

def group_info(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        update.message.reply_text("❌ Groups only!")
        return
    
    try:
        member_count = chat.get_member_count()
        admins = chat.get_administrators()
        
        text = f"📊 **Group:** {chat.title}\nID: `{chat.id}`\nMembers: {member_count}\nAdmins: {len(admins)}"
        update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

def bot_info(update, context):
    bot = context.bot.get_me()
    update.message.reply_text(f"🤖 **Bot:** {bot.first_name}\nUsername: @{bot.username}\nStatus: 🟢 Online", parse_mode='Markdown')

def ping(update, context):
    start = time.time()
    msg = update.message.reply_text("🏓 Pinging...")
    end = time.time()
    ms = (end - start) * 1000
    msg.edit_text(f"🏓 **Pong!**\nResponse: `{ms:.2f}ms`", parse_mode='Markdown')

def random_num(update, context):
    if len(context.args) == 2:
        try:
            min_val = int(context.args[0])
            max_val = int(context.args[1])
            num = random.randint(min_val, max_val)
            update.message.reply_text(f"🎲 **Random:** `{num}`", parse_mode='Markdown')
        except:
            update.message.reply_text("❌ Use: `/random 1 100`", parse_mode='Markdown')
    else:
        num = random.randint(1, 100)
        update.message.reply_text(f"🎲 **Random (1-100):** `{num}`", parse_mode='Markdown')

def password(update, context):
    length = 12
    if context.args and context.args[0].isdigit():
        length = min(int(context.args[0]), 32)
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(random.choice(chars) for _ in range(length))
    
    update.message.reply_text(f"🔐 **Password:** `{pwd}`", parse_mode='Markdown')

def datetime_cmd(update, context):
    now = datetime.now()
    update.message.reply_text(f"📅 {now.strftime('%Y-%m-%d %H:%M:%S')}")

def ipinfo(update, context):
    ip = context.args[0] if context.args else None
    
    if not ip:
        try:
            r = requests.get('https://api.ipify.org?format=json', timeout=10)
            ip = r.json()['ip']
        except:
            update.message.reply_text("❌ Usage: `/ipinfo 8.8.8.8`", parse_mode='Markdown')
            return
    
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
        data = r.json()
        
        if data['status'] == 'success':
            text = f"🌐 **IP:** `{ip}`\n📍 {data['city']}, {data['country']}\n🏢 {data['isp']}"
            update.message.reply_text(text, parse_mode='Markdown')
        else:
            update.message.reply_text("❌ Invalid IP!")
    except:
        update.message.reply_text("❌ Error!")

def help_command(update, context):
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
    update.message.reply_text(text)

def button_click(update, context):
    query = update.callback_query
    query.answer()
    
    if query.data == 'info':
        user = query.from_user
        query.edit_message_text(f"👤 {user.first_name}\nID: `{user.id}`", parse_mode='Markdown')
    elif query.data == 'bot_info':
        bot = context.bot.get_me()
        query.edit_message_text(f"🤖 @{bot.username}", parse_mode='Markdown')
    elif query.data == 'admins':
        query.edit_message_text("👑 Send /admins in group")
    elif query.data == 'my_id':
        user = query.from_user
        query.edit_message_text(f"🆔 Your ID: `{user.id}`", parse_mode='Markdown')
    elif query.data == 'help':
        query.edit_message_text("Send /help for commands")

def main():
    print(f"🤖 Starting Info Bot... Port: {PORT}")
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("user", user_info))
    dp.add_handler(CommandHandler("id", my_id))
    dp.add_handler(CommandHandler("admins", admins))
    dp.add_handler(CommandHandler("group", group_info))
    dp.add_handler(CommandHandler("bot", bot_info))
    dp.add_handler(CommandHandler("ping", ping))
    dp.add_handler(CommandHandler("random", random_num))
    dp.add_handler(CommandHandler("password", password))
    dp.add_handler(CommandHandler("datetime", datetime_cmd))
    dp.add_handler(CommandHandler("ipinfo", ipinfo))
    dp.add_handler(CallbackQueryHandler(button_click))
    
    render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if render_host:
        webhook_url = f"https://{render_host}/{TOKEN}"
        print(f"✅ Webhook URL: {webhook_url}")
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=webhook_url
        )
    else:
        print("⚠️  No webhook host, using polling...")
        updater.start_polling()
    
    updater.idle()

if __name__ == '__main__':
    main()
