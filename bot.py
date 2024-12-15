import os
import json
from telethon import TelegramClient, events
from datetime import datetime, timedelta
import logging
import re
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file (if present)

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://inayatalibarkaat:G2ts6PqdfIk60b9V@cluster0.w6fms.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Default value for Railway


# Database and collection names
DB_NAME = "telegram_bot_db"
COLLECTION_NAME = "bot_data"

# Initialize MongoDB client
client = MongoClient(MONGODB_URL, tls=True, tlsAllowInvalidCertificates=True)

db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Load data from MongoDB or initialize if not exists
def load_data():
    try:
        data = collection.find_one()
        if data:
            return (
                data.get('channel_ids', []),
                data.get('text_links', {}),
                data.get('user_data', {})
            )
        else:
            return [], {}, {}
    except Exception as e:
        logging.error(f"Error loading data from MongoDB: {e}")
        return [], {}, {}

# Save data to MongoDB
def save_data(channel_ids, text_links, user_data):
    data = {
        'channel_ids': channel_ids,
        'text_links': text_links,
        'user_data': user_data
    }
    try:
        collection.replace_one({}, data, upsert=True)
    except Exception as e:
        logging.error(f"Error saving data to MongoDB: {e}")

# Initialize the bot with data from storage
CHANNEL_IDS, text_links, user_data = load_data()

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Set up logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_notification(message):
    """Sends a message to the specified notification channel."""
    try:
        await client.send_message(NOTIFICATION_CHANNEL_ID, message)
        logging.info(f"Notification sent to channel {NOTIFICATION_CHANNEL_ID}: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")

def is_trial_active(user_id):
    if user_id in user_data:
        start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
        trial_end_date = start_date + timedelta(days=3)
        return datetime.now() <= trial_end_date, False

    return True, True # New user always gets the free trail
    
def is_user_active(user_id):
    if user_id in user_data:
        if user_data[user_id].get('is_paid',False):
            start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
            end_date = start_date + timedelta(days=30)
            return datetime.now() <= end_date
        else:
             return is_trial_active(user_id)[0]
    else:
         return is_trial_active(user_id)[0]
    
def check_user_status(user_id):
    if user_id in user_data:
        if user_data[user_id].get('is_blocked',False):
            return False
        else:
            return is_user_active(user_id)
    else:
        return is_trial_active(user_id)
    

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    user_id = event.sender_id
    logging.info(f"User ID {user_id} used /start command.")

    if not check_user_status(user_id):
       await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
       return
    
    is_new_user = user_id not in user_data
    if is_new_user:
       user_data[user_id] = {
        'start_date': datetime.now().isoformat(),
        'is_paid':False,
        'is_blocked':False
        }
       save_data(CHANNEL_IDS, text_links, user_data)
       user = await client.get_entity(user_id)
       username = user.username if user.username else "N/A"
       await send_notification(f"New user started the bot:\nUser ID: {user_id}\nUsername: @{username}")

    await event.respond('Namaste! 🙏  Bot mein aapka swagat hai! \n\n'
                        'Ye bot aapke messages mein automatically links add kar dega.\n\n'
                        'Agar aapko koi problem ho ya help chahiye, to /help command use karein.\n\n'
                        'Naye channel add karne ke liye, /addchannel command use karein (jaise: /addchannel -100123456789).\n\n'
                        'Text aur link add karne ke liye /addlink command use karein (jaise: /addlink text link).\n\n'
                         'Agar aapko added channel dekhna hai to /showchannels command use karein.\n\n'
                         'Agar aapko added links dekhna hai to /showlinks command use karein.\n\n'
                         'Agar channel remove karna hai to /removechannel command use karein (jaise: /removechannel -100123456789).\n\n'
                         'Agar link remove karna hai to /removelink command use karein (jaise: /removelink text).')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Provides help and contact information."""
    if not check_user_status(event.sender_id):
       await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
       return
    await event.respond('Aapko koi bhi problem ho, to mujhe yahaan contact karein: @captain_stive')

@client.on(events.NewMessage(pattern=r'/addchannel'))
async def add_channel(event):
    """Adds a channel ID to the list of monitored channels with format validation."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    full_command = event.text.strip()
    match = re.match(r'/addchannel (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /addchannel -100123456789')
        return

    try:
        channel_id = int(match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
            await send_notification(f"Channel added by user {event.sender_id}:\nChannel ID: {channel_id}")
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern=r'/addlink'))
async def add_link(event):
    """Adds a text and link pair to the dictionary with format validation."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    full_command = event.text.strip()
    match = re.match(r'/addlink (.+) (https?://[^\s]+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /addlink text link (eg: /addlink mytext https://example.com)')
        return

    text = match.group(1).strip()
    link = match.group(2)
    text_links[text] = link
    save_data(CHANNEL_IDS, text_links, user_data)
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    await send_notification(f"Link added by user {event.sender_id}:\nText: {text}\nLink: {link}")
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels(event):
    """Shows the list of added channels."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    if CHANNEL_IDS:
        channel_list = "\n".join([str(cid) for cid in CHANNEL_IDS])
        await event.respond(f'Current monitored channels:\n{channel_list}')
    else:
        await event.respond('No channels added yet.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern='/showlinks'))
async def show_links(event):
    """Shows the list of added text and links."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    if text_links:
        link_list = "\n".join([f'{text}: {link}' for text, link in text_links.items()])
        await event.respond(f'Current links:\n{link_list}')
    else:
        await event.respond('No links added yet.')
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern=r'/removechannel'))
async def remove_channel(event):
    """Removes a channel from the list of monitored channels with format validation."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    full_command = event.text.strip()
    match = re.match(r'/removechannel (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /removechannel -100123456789')
        return

    try:
        channel_id = int(match.group(1))
        if channel_id in CHANNEL_IDS:
            CHANNEL_IDS.remove(channel_id)
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'Channel ID {channel_id} removed! 👍')
        else:
             await event.respond(f'Channel ID {channel_id} not found! ⚠️')
    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern=r'/removelink'))
async def remove_link(event):
    """Removes a text-link pair from the dictionary with format validation."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    full_command = event.text.strip()
    match = re.match(r'/removelink (.+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /removelink text (eg: /removelink mytext)')
        return
        
    text = match.group(1).strip()
    if text in text_links:
        del text_links[text]
        save_data(CHANNEL_IDS, text_links, user_data)
        await event.respond(f'Link with text "{text}" removed! 👍')
    else:
         await event.respond(f'Link with text "{text}" not found! ⚠️')
    logging.info(f"Current text_links: {text_links}")


@client.on(events.NewMessage(pattern=r'/adminactivate'))
async def activate_user(event):
    """Activates a user for 30 days after payment. Only admin can use this command."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminactivate (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminactivate <user_id>')
        return
        
    try:
        user_id_to_activate = int(match.group(1))
        if user_id_to_activate in user_data:
            user_data[user_id_to_activate]['start_date'] = datetime.now().isoformat()
            user_data[user_id_to_activate]['is_paid'] = True
            user_data[user_id_to_activate]['is_blocked'] = False
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'User ID {user_id_to_activate} activated for 30 days! ✅')
            # Send a congratulatory message to the user
            await client.send_message(user_id_to_activate, "Congratulations! Your account has been activated for 30 days. Enjoy using the bot!")
        else:
             await event.respond(f'User ID {user_id_to_activate} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')

@client.on(events.NewMessage(pattern=r'/adminblock'))
async def block_user(event):
    """Blocks a user from using the bot. Only admin can use this command."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminblock (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminblock <user_id>')
        return
        
    try:
        user_id_to_block = int(match.group(1))
        if user_id_to_block in user_data:
            user_data[user_id_to_block]['is_blocked'] = True
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'User ID {user_id_to_block} blocked! 🚫')
        else:
             await event.respond(f'User ID {user_id_to_block} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.NewMessage(pattern=r'/adminunblock'))
async def unblock_user(event):
    """Unblocks a user from using the bot. Only admin can use this command."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminunblock (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminunblock <user_id>')
        return
    
    try:
        user_id_to_unblock = int(match.group(1))
        if user_id_to_unblock in user_data:
            user_data[user_id_to_unblock]['is_blocked'] = False
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'User ID {user_id_to_unblock} unblocked! ✅')
        else:
             await event.respond(f'User ID {user_id_to_unblock} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.ChatAction)
async def handle_chat_actions(event):
    """Handles chat actions, specifically bot added to channel."""
    if event.user_added and event.who == await client.get_me():
       try:
            chat = await client.get_entity(event.chat_id)
            if chat.username:
               await send_notification(f"Bot added to channel: @{chat.username}")
            else:
               await send_notification(f"Bot added to channel: {chat.title}")
       except Exception as e:
            logging.error(f"Error getting chat username: {e}")

@client.on(events.NewMessage())
async def add_links(event):
    user_id = event.sender_id
    if not check_user_status(user_id):
        if event.is_private:
            await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    if event.is_channel and event.chat_id in CHANNEL_IDS:
        logging.info(f"Message received from channel ID: {event.chat_id}")
        message_text = event.message.message
        for text, link in text_links.items():
            if message_text.strip() == text:
                new_message_text = f"{text}\n{link}"
                try:
                    await event.edit(new_message_text)
                    logging.info(f"Edited message in channel ID: {event.chat_id}")
                except Exception as e:
                    logging.error(f"Error editing message in channel {event.chat_id}: {e}")
                break


# Start the bot
with client:
    client.run_until_disconnected()
