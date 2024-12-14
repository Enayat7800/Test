import os
from telethon import TelegramClient, events
from pymongo import MongoClient

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGODB_URL = os.getenv('MONGODB_URL')  # MongoDB connection string from environment variable

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Initialize MongoDB Client and database
mongo_client = MongoClient(MONGODB_URL)
db = mongo_client.get_default_database() # Or specify database: mongo_client['your_database_name']
text_links_collection = db['text_links']

# Other code (start, help, addchannel functions etc....)

@client.on(events.NewMessage(pattern=r'/addlink (.+) (https?://[^\s]+)'))
async def add_link(event):
  """Adds a text and link pair to the database."""
  text = event.pattern_match.group(1).strip()
  link = event.pattern_match.group(2)

  text_links_collection.insert_one({'text': text, 'link': link}) # Store in MongoDB
  await event.respond(f'Text "{text}" aur link "{link}" database mein add ho gaya! 👍')
  print(f"Added to database text: {text}, link: {link}")

@client.on(events.NewMessage())
async def add_links(event):
  if event.is_channel and event.chat_id in CHANNEL_IDS:
    print(f"Message received from channel ID: {event.chat_id}")
    message_text = event.message.message
    
    # Find data from MongoDB
    for item in text_links_collection.find():
       text, link = item['text'], item['link']
       if message_text.strip() == text:
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
