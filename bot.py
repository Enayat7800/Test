import os
import json
from telethon import TelegramClient, events
import pymongo
from pymongo import MongoClient

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGODB_URL = os.getenv('MONGODB_URL') # New environment variable


# Initialize MongoDB client and database
client_mongo = None
db = None
if MONGODB_URL:
    try:
        client_mongo = MongoClient(MONGODB_URL)
        db = client_mongo.get_default_database()
    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")


# Function to load data from MongoDB
def load_data():
    if db:
      try:
        data = db.bot_data.find_one()
        if data:
          return data.get('channel_ids', []), data.get('text_links', {})
        else:
           return [], {}
      except Exception as e:
           print(f"Error loading data from MongoDB: {e}")
           return [], {}
    else:
        return [], {}


# Function to save data to MongoDB
def save_data(channel_ids, text_links):
    if db:
        try:
          db.bot_data.update_one({}, {'$set': {'channel_ids': channel_ids, 'text_links': text_links}}, upsert=True)
        except Exception as e:
          print(f"Error saving data to MongoDB: {e}")

# Initialize the bot with data from storage
CHANNEL_IDS, text_links = load_data()

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
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
    await event.respond('Aapko koi bhi problem ho, to mujhe yahaan contact karein: @captain_stive')

@client.on(events.NewMessage(pattern=r'/addchannel (-?\d+)'))
async def add_channel(event):
    """Adds a channel ID to the list of monitored channels."""
    try:
        channel_id = int(event.pattern_match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, text_links)
            await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}")  # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern=r'/addlink (.+) (https?://[^\s]+)'))
async def add_link(event):
    """Adds a text and link pair to the dictionary."""
    text = event.pattern_match.group(1).strip()  # Added .strip() to remove leading/trailing spaces
    link = event.pattern_match.group(2)
    text_links[text] = link
    save_data(CHANNEL_IDS, text_links)
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    print(f"Current text_links: {text_links}")  # Debugging line: show current text_links

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels(event):
    """Shows the list of added channels."""
    if CHANNEL_IDS:
        channel_list = "\n".join([str(cid) for cid in CHANNEL_IDS])
        await event.respond(f'Current monitored channels:\n{channel_list}')
    else:
        await event.respond('No channels added yet.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}")  # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern='/showlinks'))
async def show_links(event):
    """Shows the list of added text and links."""
    if text_links:
        link_list = "\n".join([f'{text}: {link}' for text, link in text_links.items()])
        await event.respond(f'Current links:\n{link_list}')
    else:
        await event.respond('No links added yet.')
    print(f"Current text_links: {text_links}")  # Debugging line: show current text_links

@client.on(events.NewMessage(pattern=r'/removechannel (-?\d+)'))
async def remove_channel(event):
    """Removes a channel from the list of monitored channels."""
    try:
        channel_id = int(event.pattern_match.group(1))
        if channel_id in CHANNEL_IDS:
            CHANNEL_IDS.remove(channel_id)
            save_data(CHANNEL_IDS, text_links)
            await event.respond(f'Channel ID {channel_id} removed! 👍')
        else:
             await event.respond(f'Channel ID {channel_id} not found! ⚠️')
    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}") # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern=r'/removelink (.+)'))
async def remove_link(event):
    """Removes a text-link pair from the dictionary."""
    text = event.pattern_match.group(1).strip()
    if text in text_links:
        del text_links[text]
        save_data(CHANNEL_IDS, text_links)
        await event.respond(f'Link with text "{text}" removed! 👍')
    else:
         await event.respond(f'Link with text "{text}" not found! ⚠️')
    print(f"Current text_links: {text_links}")  # Debugging line: show current text_links


@client.on(events.NewMessage())
async def add_links(event):
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
