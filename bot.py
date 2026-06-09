import os
import random
import string
import requests
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Logging
logging.basicConfig(level=logging.INFO)

# Bot token
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    print("❌ BOT_TOKEN not set!")
    exit(1)

# Database (file-based)
import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT, username TEXT, last_seen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_admins 
                 (group_id INTEGER, admin_id INTEGER, PRIMARY KEY (group_id, admin_id))''')
    conn.commit()
    conn.close()

init_db()

# Helper function to save user
def save_user(user_id, first_name, username):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users (user_id, first_name, username, last_seen) 
                 VALUES (?, ?, ?, ?)''', (user_id, first_name, username, datetime.now()))
    conn.commit()
    conn.close()

# Start command
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
        f"I'm Info Bot. Send /help for all commands.\n\n"
        f"Click buttons below 👇",
        reply_markup=reply_markup
    )

# Info command - WORKING FIXED
def info(update, context):
    user = update.effective_user
    save_user(user.id, user.first_name, user.username)
    
    text = f"""
👤 **YOUR INFORMATION**

• Name: {user.first_name} {user.last_name or ''}
• User ID: `{user.id}`
• Username: @{user.username if user.username else 'Not set'}
• Language: {user.language_code or 'EN'}
• Is Premium: {'✅ Yes' if getattr(user, 'is_premium', False) else '❌ No'}

📅 Last seen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    update.message.reply_text(text, parse_mode='Markdown')

# ID command - WORKING
def my_id(update, context):
    user = update.effective_user
    chat = update.effective_chat
    
    text = f"""
🆔 **ID INFORMATION**

• Your ID: `{user.id}`
• Chat ID: `{chat.id}`
• Chat Type: {chat.type}
"""
    update.message.reply_text(text, parse_mode='Markdown')

# Admins command - MENTIONS ALL ADMINS
def admins(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        update.message.reply_text("❌ This command only works in groups!")
        return
    
    try:
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
            text += f"\n   └ Status: {admin.status}\n\n"
        
        # Save admins to database
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        for admin in admins_list:
            c.execute('''INSERT OR REPLACE INTO group_admins (group_id, admin_id) 
                         VALUES (?, ?)''', (chat.id, admin.user.id))
        conn.commit()
        conn.close()
        
        update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

# User info command - WORKS WITH MENTION
def user_info(update, context):
    if not context.args:
        update.message.reply_text("❌ Usage: `/user @username`", parse_mode='Markdown')
        return
    
    username = context.args[0].replace('@', '')
    
    try:
        user = context.bot.get_chat(f"@{username}")
        text = f"""
👤 **USER INFORMATION**

• Name: {user.first_name} {user.last_name or ''}
• User ID: `{user.id}`
• Username: @{user.username if user.username else 'None'}
• Type: {user.type}
• Link: [Click here](tg://user?id={user.id})
"""
        update.message.reply_text(text, parse_mode='Markdown')
    except:
        update.message.reply_text(f"❌ User @{username} not found!")

# Group info command
def group_info(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        update.message.reply_text("❌ This command works only in groups!")
        return
    
    try:
        member_count = chat.get_member_count()
        admins = chat.get_administrators()
        
        text = f"""
📊 **GROUP INFORMATION**

• Name: {chat.title}
• Group ID: `{chat.id}`
• Type: {chat.type}
• Members: {member_count}
• Admins: {len(admins)}
"""
        update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

# Bot info
def bot_info(update, context):
    bot = context.bot.get_me()
    text = f"""
🤖 **BOT INFORMATION**

• Name: {bot.first_name}
• Username: @{bot.username}
• Bot ID: `{bot.id}`
• Status: 🟢 Online
• Commands: 15+
"""
    update.message.reply_text(text, parse_mode='Markdown')

# Ping command
def ping(update, context):
    import time
    start = time.time()
    msg = update.message.reply_text("🏓 Pinging...")
    end = time.time()
    ms = (end - start) * 1000
    msg.edit_text(f"🏓 **Pong!**\n\nResponse Time: `{ms:.2f}ms`\nStatus: 🟢 Active", parse_mode='Markdown')

# Random number
def random_num(update, context):
    if len(context.args) == 2:
        try:
            min_val = int(context.args[0])
            max_val = int(context.args[1])
            num = random.randint(min_val, max_val)
            update.message.reply_text(f"🎲 **Random Number:** `{num}`\nRange: {min_val} - {max_val}", parse_mode='Markdown')
        except:
            update.message.reply_text("❌ Use: `/random 1 100`", parse_mode='Markdown')
    else:
        num = random.randint(1, 100)
        update.message.reply_text(f"🎲 **Random Number:** `{num}`\nRange: 1 - 100", parse_mode='Markdown')

# Password generator
def password(update, context):
    length = 12
    if context.args and context.args[0].isdigit():
        length = min(int(context.args[0]), 32)
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(random.choice(chars) for _ in range(length))
    
    # Ensure at least one of each
    if not any(c.isupper() for c in pwd):
        pwd = pwd[:-1] + random.choice(string.ascii_uppercase)
    if not any(c.islower() for c in pwd):
        pwd = pwd[:-1] + random.choice(string.ascii_lowercase)
    if not any(c.isdigit() for c in pwd):
        pwd = pwd[:-1] + random.choice(string.digits)
    
    update.message.reply_text(f"🔐 **Generated Password** ({length} chars):\n`{pwd}`\n\n⚠️ Copy it now!", parse_mode='Markdown')

# DateTime
def datetime_cmd(update, context):
    now = datetime.now()
    text = f"""
📅 **DATE & TIME**

• Date: `{now.strftime('%A, %B %d, %Y')}`
• Time: `{now.strftime('%H:%M:%S')}`
• Timezone: `Asia/Kolkata`
• Timestamp: `{int(now.timestamp())}`
"""
    update.message.reply_text(text, parse_mode='Markdown')

# IP Info
def ipinfo(update, context):
    ip = context.args[0] if context.args else None
    
    if not ip:
        try:
            r = requests.get('https://api.ipify.org?format=json', timeout=5)
            ip = r.json()['ip']
            update.message.reply_text(f"🌐 Fetching info for: `{ip}`", parse_mode='Markdown')
        except:
            update.message.reply_text("❌ Usage: `/ipinfo 8.8.8.8`", parse_mode='Markdown')
            return
    
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = r.json()
        
        if data['status'] == 'success':
            text = f"""
🌐 **IP INFORMATION:** `{ip}`

📍 **Location:**
• Country: {data['country']} ({data['countryCode']})
• Region: {data['regionName']}
• City: {data['city']}
• ZIP: {data['zip']}

🏢 **Network:**
• ISP: {data['isp']}
• Organization: {data['org']}
• Timezone: {data['timezone']}
"""
            update.message.reply_text(text, parse_mode='Markdown')
        else:
            update.message.reply_text("❌ Invalid IP address!")
    except:
        update.message.reply_text("❌ Error fetching IP info!")

# Help command - COMPLETE LIST
def help_command(update, context):
    text = """
📚 **COMPLETE COMMANDS LIST**

**📊 Basic Commands:**
• `/start` - Start the bot
• `/help` - Show this help
• `/ping` - Check bot status

**👤 User Commands:**
• `/info` - Your information
• `/user @username` - Get user info
• `/id` - Get your ID
• `/admins` - Mention all group admins

**👥 Group Commands:**
• `/group` - Group information
• `/admins` - List & mention admins

**🔧 Utility Commands:**
• `/random [min max]` - Generate random number
• `/password [length]` - Generate strong password
• `/datetime` - Current date & time
• `/ipinfo [ip]` - IP address details
• `/bot` - Bot information

**💡 Tips:**
• Use `/admins` in groups - it will mention all admins
• For random number: `/random 1 100`
• For password: `/password 16`
• For IP info: `/ipinfo 8.8.8.8`

*Bot is fully functional! 🚀*
"""
    update.message.reply_text(text, parse_mode='Markdown')

# Button callbacks
def button_click(update, context):
    query = update.callback_query
    query.answer()
    
    if query.data == 'info':
        user = query.from_user
        text = f"👤 **Your Info**\n\nName: {user.first_name}\nID: `{user.id}`\nUsername: @{user.username if user.username else 'None'}"
        query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == 'bot_info':
        bot = context.bot.get_me()
        text = f"🤖 **Bot Info**\n\nName: {bot.first_name}\nUsername: @{bot.username}\nID: `{bot.id}`"
        query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == 'admins':
        # Get chat admins
        chat = query.message.chat
        if chat.type in ['group', 'supergroup']:
            try:
                admins_list = chat.get_administrators()
                text = "👑 **Admins:**\n\n"
                for admin in admins_list:
                    user = admin.user
                    mention = f"[{user.first_name}](tg://user?id={user.id})"
                    text += f"• {mention}\n"
                query.edit_message_text(text, parse_mode='Markdown', disable_web_page_preview=True)
            except:
                query.edit_message_text("❌ Cannot fetch admins!")
        else:
            query.edit_message_text("❌ This works only in groups!")
    
    elif query.data == 'my_id':
        user = query.from_user
        text = f"🆔 **Your ID:** `{user.id}`"
        query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == 'help':
        text = "/info - Your info\n/user - User info\n/id - Your ID\n/admins - List admins\n/group - Group info\n/random - Random number\n/password - Password\n/datetime - Time\n/ipinfo - IP info\n/ping - Status"
        query.edit_message_text(text)

# Purane main function ko replace karo isse:

def main():
    print("🤖 Starting Info Bot...")
    print(f"Port: {PORT}")
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add all handlers (same rahenge)
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
    
    # Start webhook instead of polling (for Render)
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/{TOKEN}"
    )
    
    print("✅ Bot is ready on webhook mode!")
    updater.idle()

if __name__ == '__main__':
    main()
