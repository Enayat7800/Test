import os
from telethon import TelegramClient, events
import re
import json

# Load environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# File to store data
DATA_FILE = 'bot_data.json'

# Function to load data
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'channels': {}, 'text_links': {}}

# Function to save data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize the Telegram client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Load existing data
data = load_data()

# /start command handler
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Responds to the /start command."""
    await event.respond('Hello! I am a bot that adds links to messages based on text.')

                        'Available commands:\n'
                        '/setchannel <channel_id> - Set the channel ID\n'
                        '/addlink <text> <link> - Add a new link\n'
                        '/removelink <text> - Remove a link\n'
                        '/listlinks - View all saved links')

# /setchannel command handler
@client.on(events.NewMessage(pattern='/setchannel'))
async def set_channel_handler(event):
    """Sets the channel ID for the user."""
    try:
        channel_id = int(event.text.split(' ', 1)[1])
        user_id = event.sender_id
        data['channels'][user_id] = channel_id
        save_data(data)
        await event.respond(f'Channel ID {channel_id} set successfully.')
    except (IndexError, ValueError):
        await event.respond('Invalid format. Correct format: /setchannel <channel_id>')

# /addlink command handler
@client.on(events.NewMessage(pattern='/addlink'))
async def add_link_handler(event):
    """Adds a text-link pair for the user."""
    try:
        parts = event.text.split(' ', 2)
        text = parts[1]
        link = parts[2]
        user_id = event.sender_id
        if user_id not in data['text_links']:
           data['text_links'][user_id] = {}
        data['text_links'][user_id][text] = link
        save_data(data)
        await event.respond(f'Link `{link}` added for text `{text}`.')
    except IndexError:
        await event.respond('Invalid format. Correct format: /addlink <text> <link>')

# /removelink command handler
@client.on(events.NewMessage(pattern='/removelink'))
async def remove_link_handler(event):
    """Removes a text-link pair for the user."""
    try:
        text = event.text.split(' ', 1)[1]
        user_id = event.sender_id
        if user_id in data['text_links'] and text in data['text_links'][user_id]:
            del data['text_links'][user_id][text]
            save_data(data)
            await event.respond(f'Link for text `{text}` removed.')
        else:
            await event.respond('Text link not found.')
    except IndexError:
        await event.respond('Invalid format. Correct format: /removelink <text>')

# /listlinks command handler
@client.on(events.NewMessage(pattern='/listlinks'))
async def list_links_handler(event):
    """Lists all text-link pairs for the user."""
    user_id = event.sender_id
    if user_id in data['text_links'] and data['text_links'][user_id]:
        links_list = "\n".join([f"{text}: {link}" for text, link in data['text_links'][user_id].items()])
        await event.respond(f'Saved links:\n{links_list}')
    else:
        await event.respond('No links saved.')

# Automatically add links to channel messages
@client.on(events.NewMessage)
async def add_links(event):
    """Edits channel messages to add links based on user-defined text."""
    for user_id, channel_id in data['channels'].items():
        if event.chat_id == channel_id:
            message_text = event.message.message
            new_message_text = message_text

            if user_id in data['text_links']:
                for text, link in data['text_links'][user_id].items():
                    # Case-insensitive matching with regex
                    pattern = re.compile(r'(?i)\b' + re.escape(text) + r'\b')
                    new_message_text = re.sub(pattern, f"{text} ({link})", new_message_text)

            if new_message_text != message_text:
                await event.reply(new_message_text)

# Run the bot
with client:
    print("Bot is running...")
    client.run_until_disconnected()
