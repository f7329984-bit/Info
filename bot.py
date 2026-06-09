import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Logging
logging.basicConfig(level=logging.INFO)

# Bot token and port
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    print("❌ BOT_TOKEN not set!")
    exit(1)

# ============ COMMANDS ============

# /start command
def start(update, context):
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("📋 My Info", callback_data='info'),
         InlineKeyboardButton("🆔 My ID", callback_data='id')],
        [InlineKeyboardButton("👑 Admins", callback_data='admins'),
         InlineKeyboardButton("📊 Group Info", callback_data='group')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"🎉 Welcome {user.first_name}!\n\n"
        f"Commands:\n"
        f"/info - Get user info (reply or tag)\n"
        f"/id - Get user ID (reply or tag)\n"
        f"/group - Group information\n"
        f"/admins - Tag all admins\n"
        f"/help - Show all commands\n\n"
        f"Click buttons below 👇",
        reply_markup=reply_markup
    )

# ============ /info COMMAND ============
def info(update, context):
    message = update.message
    user = update.effective_user
    
    # Check if user replied to someone
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        text = f"""
👤 **USER INFORMATION** (Replied user)

• First Name: {target.first_name}
• Last Name: {target.last_name or 'Not set'}
• User ID: `{target.id}`
• Username: @{target.username if target.username else 'Not set'}
• Is Bot: {'Yes' if target.is_bot else 'No'}
"""
    # Check if user tagged someone
    elif context.args:
        username = context.args[0].replace('@', '')
        try:
            target = context.bot.get_chat(f"@{username}")
            text = f"""
👤 **USER INFORMATION** (@{username})

• First Name: {target.first_name}
• Last Name: {target.last_name or 'Not set'}
• User ID: `{target.id}`
• Username: @{target.username if target.username else 'Not set'}
• Is Bot: {'Yes' if target.is_bot else 'No'}
"""
        except:
            text = f"❌ User @{username} not found!"
    else:
        # Show own info
        text = f"""
👤 **YOUR INFORMATION**

• First Name: {user.first_name}
• Last Name: {user.last_name or 'Not set'}
• User ID: `{user.id}`
• Username: @{user.username if user.username else 'Not set'}
• Language: {user.language_code or 'EN'}
• Is Premium: {'✅ Yes' if getattr(user, 'is_premium', False) else '❌ No'}
"""
    
    update.message.reply_text(text, parse_mode='Markdown')

# ============ /id COMMAND ============
def get_id(update, context):
    message = update.message
    user = update.effective_user
    
    # Check if user replied to someone
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        text = f"🆔 **User ID** (Replied): `{target.id}`"
    # Check if user tagged someone
    elif context.args:
        username = context.args[0].replace('@', '')
        try:
            target = context.bot.get_chat(f"@{username}")
            text = f"🆔 **User ID** (@{username}): `{target.id}`"
        except:
            text = f"❌ User @{username} not found!"
    else:
        # Show own ID
        chat = update.effective_chat
        text = f"""
🆔 **ID INFORMATION**

• Your ID: `{user.id}`
• Chat ID: `{chat.id}`
• Chat Type: {chat.type}
"""
    
    update.message.reply_text(text, parse_mode='Markdown')

# ============ /group COMMAND ============
def group_info(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        update.message.reply_text("❌ This command only works in groups!")
        return
    
    try:
        member_count = chat.get_member_count()
        admins = chat.get_administrators()
        description = chat.description if chat.description else "No description"
        
        invite_link = "Not available"
        try:
            if chat.invite_link:
                invite_link = chat.invite_link
        except:
            pass
        
        text = f"""
📊 **GROUP INFORMATION**

📌 **Basic Info:**
• Name: {chat.title}
• Group ID: `{chat.id}`
• Type: {chat.type}
• Members: {member_count}
• Admins: {len(admins)}

📝 **Description:**
{description[:200]}

🔗 **Invite Link:**
{invite_link}

📅 **Info fetched:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

# ============ /admins COMMAND ============
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
        
        text += f"\n📅 Total: {len(admins_list)} admins"
        
        update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

# ============ /help COMMAND ============
def help_command(update, context):
    text = """
📚 **COMPLETE COMMANDS GUIDE**

**👤 USER COMMANDS:**

• `/info` - Your information
• `/info @username` - Get user info by tag
• `/info` (reply to someone) - Get replied user's info

• `/id` - Your ID
• `/id @username` - Get user ID by tag
• `/id` (reply to someone) - Get replied user's ID

**👥 GROUP COMMANDS:**

• `/group` - Complete group information
• `/admins` - **TAG all group admins** (mentions everyone)

**🤖 OTHER COMMANDS:**

• `/start` - Start the bot
• `/help` - Show this menu

**💡 HOW TO USE:**

1. **Get someone's info:** `/info @username` or reply to their message and type `/info`
2. **Get someone's ID:** `/id @username` or reply to their message and type `/id`
3. **Tag all admins:** Type `/admins` in group
4. **Group info:** Type `/group` in group

**🎯 EXAMPLES:**
• `/info @telegram` - Get Telegram's info
• Reply to a message then `/id` - Get that person's ID

*Bot is fully functional! 🚀*
"""
    update.message.reply_text(text, parse_mode='Markdown')

# ============ BUTTON CALLBACKS ============
def button_click(update, context):
    query = update.callback_query
    query.answer()
    
    if query.data == 'info':
        user = query.from_user
        text = f"👤 {user.first_name}\nID: `{user.id}`"
        query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == 'id':
        user = query.from_user
        query.edit_message_text(f"🆔 Your ID: `{user.id}`", parse_mode='Markdown')
    
    elif query.data == 'admins':
        query.edit_message_text("👑 Type /admins in group to tag all admins")
    
    elif query.data == 'group':
        query.edit_message_text("📊 Type /group in group for information")
    
    elif query.data == 'help':
        help_command(update, context)

# ============ MAIN FUNCTION ============
def main():
    print("🤖 Starting Info Bot...")
    print(f"Port: {PORT}")
    print(f"Bot token: {TOKEN[:10]}...")
    
    # Create updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("id", get_id))
    dp.add_handler(CommandHandler("group", group_info))
    dp.add_handler(CommandHandler("admins", admins))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(button_click))
    
    # Start bot with webhook (for Render)
    print("✅ Bot is ready!")
    print("🚀 Starting webhook...")
    
    # Get Render URL
    render_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
    webhook_url = f"https://{render_url}/{TOKEN}"
    
    print(f"Webhook URL: {webhook_url}")
    
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=webhook_url
    )
    
    updater.idle()

if __name__ == '__main__':
    main()
