import os
import json
from telethon import TelegramClient, events
from datetime import datetime, timedelta
import logging

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))  # New channel ID


# ... [Your existing code for DATA_FILE, load_data, save_data, client initialization, is_trial_active, is_user_active, check_user_status] ...

# Set up logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_notification(message):
    """Sends a message to the specified notification channel."""
    try:
        await client.send_message(NOTIFICATION_CHANNEL_ID, message)
        logging.info(f"Notification sent to channel {NOTIFICATION_CHANNEL_ID}: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    user_id = event.sender_id
    logging.info(f"User ID {user_id} used /start command.")

    if not check_user_status(user_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    if user_id not in user_data:
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

@client.on(events.NewMessage(pattern=r'/addchannel (-?\d+)'))
async def add_channel(event):
    """Adds a channel ID to the list of monitored channels."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    try:
        channel_id = int(event.pattern_match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, text_links,user_data)
            await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
            await send_notification(f"Channel added by user {event.sender_id}:\nChannel ID: {channel_id}")
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern=r'/addlink (.+) (https?://[^\s]+)'))
async def add_link(event):
    """Adds a text and link pair to the dictionary."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    text = event.pattern_match.group(1).strip()
    link = event.pattern_match.group(2)
    text_links[text] = link
    save_data(CHANNEL_IDS, text_links,user_data)
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    await send_notification(f"Link added by user {event.sender_id}:\nText: {text}\nLink: {link}")
    logging.info(f"Current text_links: {text_links}")

# ... [Your existing code for other commands] ...

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
