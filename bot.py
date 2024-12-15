import os
import json
from telethon import TelegramClient, events
from datetime import datetime, timedelta

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# File to store data
DATA_FILE = 'bot_data.json'

# Load data from file or initialize if not exists
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return (
                data.get('channel_ids', []),
                data.get('text_links', {}),
                data.get('user_data', {})
            )
    except (FileNotFoundError, json.JSONDecodeError):
        return [], {}, {}


# Save data to file
def save_data(channel_ids, text_links, user_data):
    data = {
        'channel_ids': channel_ids,
        'text_links': text_links,
        'user_data': user_data
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize the bot with data from storage
CHANNEL_IDS, text_links, user_data = load_data()


# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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
        return is_user_active(user_id)


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    user_id = event.sender_id
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
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}")  # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern=r'/addlink (.+) (https?://[^\s]+)'))
async def add_link(event):
    """Adds a text and link pair to the dictionary."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    text = event.pattern_match.group(1).strip()  # Added .strip() to remove leading/trailing spaces
    link = event.pattern_match.group(2)
    text_links[text] = link
    save_data(CHANNEL_IDS, text_links,user_data)
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    print(f"Current text_links: {text_links}")  # Debugging line: show current text_links

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
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}")  # Debugging line: show current channel ids

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
    print(f"Current text_links: {text_links}")  # Debugging line: show current text_links

@client.on(events.NewMessage(pattern=r'/removechannel (-?\d+)'))
async def remove_channel(event):
    """Removes a channel from the list of monitored channels."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    try:
        channel_id = int(event.pattern_match.group(1))
        if channel_id in CHANNEL_IDS:
            CHANNEL_IDS.remove(channel_id)
            save_data(CHANNEL_IDS, text_links,user_data)
            await event.respond(f'Channel ID {channel_id} removed! 👍')
        else:
             await event.respond(f'Channel ID {channel_id} not found! ⚠️')
    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}") # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern=r'/removelink (.+)'))
async def remove_link(event):
    """Removes a text-link pair from the dictionary."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    text = event.pattern_match.group(1).strip()
    if text in text_links:
        del text_links[text]
        save_data(CHANNEL_IDS, text_links,user_data)
        await event.respond(f'Link with text "{text}" removed! 👍')
    else:
         await event.respond(f'Link with text "{text}" not found! ⚠️')
    print(f"Current text_links: {text_links}")  # Debugging line: show current text_links


@client.on(events.NewMessage(pattern=r'/activate (-?\d+)'))
async def activate_user(event):
    """Activates a user for 30 days after payment."""
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return

    try:
        user_id_to_activate = int(event.pattern_match.group(1))
        if user_id_to_activate in user_data:
            user_data[user_id_to_activate]['start_date'] = datetime.now().isoformat()
            user_data[user_id_to_activate]['is_paid'] = True
            user_data[user_id_to_activate]['is_blocked'] = False
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'User ID {user_id_to_activate} activated for 30 days! ✅')
        else:
             await event.respond(f'User ID {user_id_to_activate} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')

@client.on(events.NewMessage(pattern=r'/block (-?\d+)'))
async def block_user(event):
    """Blocks a user from using the bot."""
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return

    try:
        user_id_to_block = int(event.pattern_match.group(1))
        if user_id_to_block in user_data:
            user_data[user_id_to_block]['is_blocked'] = True
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'User ID {user_id_to_block} blocked! 🚫')
        else:
             await event.respond(f'User ID {user_id_to_block} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.NewMessage(pattern=r'/unblock (-?\d+)'))
async def unblock_user(event):
    """Unblocks a user from using the bot."""
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return

    try:
        user_id_to_unblock = int(event.pattern_match.group(1))
        if user_id_to_unblock in user_data:
            user_data[user_id_to_unblock]['is_blocked'] = False
            save_data(CHANNEL_IDS, text_links, user_data)
            await event.respond(f'User ID {user_id_to_unblock} unblocked! ✅')
        else:
             await event.respond(f'User ID {user_id_to_unblock} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')


@client.on(events.NewMessage())
async def add_links(event):
    user_id = event.sender_id
    if not check_user_status(user_id):
        if event.is_private:
            await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    if event.is_channel and event.chat_id in CHANNEL_IDS:
        print(f"Message received from channel ID: {event.chat_id}")
        message_text = event.message.message
        for text, link in text_links.items():
            if message_text.strip() == text:  # Added .strip() to remove leading/trailing spaces during match
                new_message_text = f"{text}\n{link}"
                try:
                    await event.edit(new_message_text)
                    print(f"Edited message in channel ID: {event.chat_id}")
                except Exception as e:
                    print(f"Error editing message in channel {event.chat_id}: {e}")
                break


# Start the bot
with client:
    client.run_until_disconnected()
