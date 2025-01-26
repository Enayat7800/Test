import os
import re
from datetime import datetime, timedelta
import logging
from telethon import TelegramClient, events
from pymongo import MongoClient

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))
MONGO_URL = os.getenv('MONGO_URL')  # New MongoDB URL

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URL)
db = mongo_client['telegram_bot_db']
collection = db['bot_data']

# Load data from MongoDB
def load_data():
    data = collection.find_one({'_id': 'main'})
    if data:
        return (
            data.get('channel_ids', []),
            data.get('text_links', {}),
            data.get('user_data', {}),
            data.get('total_users', 0),
            data.get('active_channel_id', None)
        )
    else:
        collection.insert_one({
            '_id': 'main',
            'channel_ids': [],
            'text_links': {},
            'user_data': {},
            'total_users': 0,
            'active_channel_id': None
        })
        return [], {}, {}, 0, None

# Save data to MongoDB
def save_data(channel_ids, text_links, user_data, total_users, active_channel_id):
    collection.update_one(
        {'_id': 'main'},
        {'$set': {
            'channel_ids': channel_ids,
            'text_links': text_links,
            'user_data': user_data,
            'total_users': total_users,
            'active_channel_id': active_channel_id
        }},
        upsert=True
    )

# Initialize data
CHANNEL_IDS, text_links, user_data, total_users, active_channel_id = load_data()

# Initialize Telegram client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def send_notification(message):
    """Send notification to admin channel"""
    try:
        await client.send_message(NOTIFICATION_CHANNEL_ID, message)
        logging.info(f"Notification sent: {message}")
    except Exception as e:
        logging.error(f"Notification error: {e}")

def is_trial_active(user_id):
    if user_id in user_data:
        start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
        trial_end = start_date + timedelta(days=3)
        return datetime.now() <= trial_end, False
    return True, True  # New user gets trial

def is_user_active(user_id):
    if user_id in user_data:
        if user_data[user_id].get('is_paid', False):
            start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
            end_date = start_date + timedelta(days=30)
            return datetime.now() <= end_date
        return is_trial_active(user_id)[0]
    return is_trial_active(user_id)[0]

def check_user_status(user_id):
    if user_id in user_data:
        if user_data[user_id].get('is_blocked', False):
            return False
        return is_user_active(user_id)
    return is_trial_active(user_id)[0]

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    global total_users
    user_id = event.sender_id
    logging.info(f"/start by {user_id}")

    if not check_user_status(user_id):
        await event.respond("⚠️ Your trial has expired! Contact @captain_stive")
        return

    # New user registration
    if user_id not in user_data:
        user_data[user_id] = {
            'start_date': datetime.now().isoformat(),
            'is_paid': False,
            'is_blocked': False
        }
        total_users += 1
        save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
        
        # Send new user notification
        user = await client.get_entity(user_id)
        username = f"@{user.username}" if user.username else "No username"
        await send_notification(
            f"🚀 New User:\n"
            f"ID: {user_id}\n"
            f"Username: {username}"
        )

    # Send welcome message
    welcome_msg = (
        "Namaste! 🙏\n\n"
        "📢 Welcome to the Auto-Link Bot!\n\n"
        "🔗 This bot will automatically add predefined links to your channel messages.\n\n"
        "📝 Available commands:\n"
        "/allcommands - Show all commands\n"
        "/help - Support contact\n"
        "/addchannel - Add channel ID\n"
        "/addlink - Add text-link pair\n"
        "/selectchannel - Set active channel\n"
        "/totalusers - Show total users (admin only)"
    )
    await event.respond(welcome_msg)

@client.on(events.NewMessage(pattern='/allcommands'))
async def all_commands_handler(event):
    if not check_user_status(event.sender_id):
        await event.respond("⚠️ Your trial has expired! Contact @captain_stive")
        return
    
    commands = (
        "📜 All Commands:\n\n"
        "/start - Start the bot\n"
        "/help - Contact support\n"
        "/addchannel - Add channel (format: /addchannel -100123456789)\n"
        "/addlink - Add link (format: /addlink Text Link)\n"
        "/showchannels - List added channels\n"
        "/showlinks - Show all links\n"
        "/removechannel - Remove channel\n"
        "/removelink - Remove link\n"
        "/selectchannel - Set active channel\n"
        "/deselectchannel - Clear active channel\n"
        "/totalusers - Total users (admin)\n"
        "/broadcast - Broadcast message (admin)\n"
        "/adminactivate - Activate user (admin)\n"
        "/adminblock - Block user (admin)"
    )
    await event.respond(commands)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    help_text = (
        "❓ Need Help?\n\n"
        "Contact our support team:\n"
        "👉 @captain_stive\n\n"
        "For technical issues or bot customization queries, "
        "please message us directly."
    )
    await event.respond(help_text)

@client.on(events.NewMessage(pattern=r'/addchannel (-?\d+)'))
async def add_channel_handler(event):
    if not check_user_status(event.sender_id):
        await event.respond("⚠️ Your trial has expired! Contact @captain_stive")
        return

    match = re.match(r'/addchannel (-?\d+)', event.text)
    if not match:
        await event.respond("❌ Invalid format! Use: /addchannel -100123456789")
        return

    try:
        channel_id = int(match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
            await event.respond(f"✅ Channel {channel_id} added successfully!")
            await send_notification(f"#NewChannel Added by {event.sender_id}\nChannel ID: {channel_id}")
        else:
            await event.respond("⚠️ This channel is already added!")
    except Exception as e:
        logging.error(f"Add channel error: {e}")
        await event.respond("❌ Error adding channel!")

@client.on(events.NewMessage(pattern=r'/addlink (\S+) (\S+)'))
async def add_link_handler(event):
    if not check_user_status(event.sender_id):
        await event.respond("⚠️ Your trial has expired! Contact @captain_stive")
        return

    match = re.match(r'/addlink (\S+) (\S+)', event.text)
    if not match:
        await event.respond("❌ Invalid format! Use: /addlink Text Link")
        return

    text = match.group(1)
    link = match.group(2)
    text_links[text] = link
    save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
    await event.respond(f"✅ Link added!\nText: {text}\nLink: {link}")
    await send_notification(f"#NewLink Added by {event.sender_id}\n{text} → {link}")

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels_handler(event):
    if not CHANNEL_IDS:
        await event.respond("📭 No channels added yet!")
        return
    
    channels = "\n".join([f"📢 {cid}" for cid in CHANNEL_IDS])
    await event.respond(f"📜 Channel List:\n{channels}")

@client.on(events.NewMessage(pattern='/showlinks'))
async def show_links_handler(event):
    if not text_links:
        await event.respond("🔗 No links added yet!")
        return
    
    links = "\n".join([f"{text} → {link}" for text, link in text_links.items()])
    await event.respond(f"📚 Link Database:\n{links}")

@client.on(events.NewMessage(pattern=r'/removechannel (-?\d+)'))
async def remove_channel_handler(event):
    match = re.match(r'/removechannel (-?\d+)', event.text)
    if not match:
        await event.respond("❌ Invalid format! Use: /removechannel -100123456789")
        return

    channel_id = int(match.group(1))
    if channel_id in CHANNEL_IDS:
        CHANNEL_IDS.remove(channel_id)
        save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
        await event.respond(f"✅ Channel {channel_id} removed!")
        await send_notification(f"#ChannelRemoved by {event.sender_id}\nID: {channel_id}")
    else:
        await event.respond("⚠️ Channel not found!")

@client.on(events.NewMessage(pattern=r'/removelink (\S+)'))
async def remove_link_handler(event):
    match = re.match(r'/removelink (\S+)', event.text)
    if not match:
        await event.respond("❌ Invalid format! Use: /removelink Text")
        return

    text = match.group(1)
    if text in text_links:
        del text_links[text]
        save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
        await event.respond(f"✅ Link '{text}' removed!")
        await send_notification(f"#LinkRemoved by {event.sender_id}\nText: {text}")
    else:
        await event.respond("⚠️ Link not found!")

@client.on(events.NewMessage(pattern='/totalusers'))
async def total_users_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Admin only command!")
        return
    
    await event.respond(f"📊 Total Users: {total_users}")
    await send_notification(f"Admin checked total users: {total_users}")

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Admin only command!")
        return

    message = event.text.replace('/broadcast', '').strip()
    if not message:
        await event.respond("❌ Please add message!")
        return

    success = 0
    failures = 0
    for user_id in user_data:
        try:
            await client.send_message(user_id, message)
            success += 1
        except Exception as e:
            failures += 1
            logging.error(f"Broadcast error to {user_id}: {e}")

    report = (
        f"📢 Broadcast Report:\n"
        f"✅ Success: {success}\n"
        f"❌ Failures: {failures}"
    )
    await event.respond(report)
    await send_notification(report)

@client.on(events.NewMessage(pattern=r'/adminactivate (\d+)'))
async def admin_activate_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Admin only command!")
        return

    try:
        user_id = int(event.pattern_match.group(1))
        if user_id in user_data:
            user_data[user_id].update({
                'start_date': datetime.now().isoformat(),
                'is_paid': True,
                'is_blocked': False
            })
            save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
            await event.respond(f"✅ User {user_id} activated for 30 days!")
            await client.send_message(user_id, "🎉 Your account has been activated for 30 days!")
        else:
            await event.respond("⚠️ User not found!")
    except Exception as e:
        logging.error(f"Admin activate error: {e}")
        await event.respond("❌ Activation failed!")

@client.on(events.NewMessage(pattern=r'/adminblock (\d+)'))
async def admin_block_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Admin only command!")
        return

    try:
        user_id = int(event.pattern_match.group(1))
        if user_id in user_data:
            user_data[user_id]['is_blocked'] = True
            save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
            await event.respond(f"✅ User {user_id} blocked!")
            await client.send_message(user_id, "🚫 Your access has been blocked!")
        else:
            await event.respond("⚠️ User not found!")
    except Exception as e:
        logging.error(f"Admin block error: {e}")
        await event.respond("❌ Blocking failed!")

@client.on(events.NewMessage(pattern=r'/selectchannel (-?\d+)'))
async def select_channel_handler(event):
    global active_channel_id
    if not check_user_status(event.sender_id):
        await event.respond("⚠️ Your trial has expired! Contact @captain_stive")
        return

    match = re.match(r'/selectchannel (-?\d+)', event.text)
    if not match:
        await event.respond("❌ Invalid format! Use: /selectchannel -100123456789")
        return

    channel_id = int(match.group(1))
    if channel_id in CHANNEL_IDS:
        active_channel_id = channel_id
        save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
        await event.respond(f"✅ Active channel set to {channel_id}!")
        await send_notification(f"Active Channel Changed to {channel_id}")
    else:
        await event.respond("⚠️ Channel not in list! Add it first using /addchannel")

@client.on(events.NewMessage(pattern='/deselectchannel'))
async def deselect_channel_handler(event):
    global active_channel_id
    active_channel_id = None
    save_data(CHANNEL_IDS, text_links, user_data, total_users, active_channel_id)
    await event.respond("✅ Channel deselected! No automatic link adding.")
    await send_notification("Active Channel Deselected")

@client.on(events.ChatAction)
async def chat_action_handler(event):
    if event.user_added and await client.get_me() in event.users:
        channel = await event.get_chat()
        msg = (
            f"📢 Bot added to new channel!\n"
            f"Name: {channel.title}\n"
            f"ID: {channel.id}"
        )
        await send_notification(msg)

@client.on(events.NewMessage())
async def message_handler(event):
    # Check user status
    user_id = event.sender_id
    if not check_user_status(user_id):
        if event.is_private:
            await event.respond("⚠️ Your trial has expired! Contact @captain_stive")
        return

    # Handle channel messages
    if event.is_channel and event.chat_id == active_channel_id:
        msg_text = event.message.message
        for text, link in text_links.items():
            if msg_text.strip() == text:
                try:
                    await event.edit(f"{text}\n{link}")
                    logging.info(f"Message edited in {event.chat_id}")
                except Exception as e:
                    logging.error(f"Edit error: {e}")
                break

# Start the bot
with client:
    logging.info("Bot started successfully!")
    client.run_until_disconnected()
