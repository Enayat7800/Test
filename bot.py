import os
from telethon import TelegramClient, events
import logging

# Logging setup for debugging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING) # set to DEBUG to see more info

# Get environment variables - environment variables se data fetch karenge
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')


# Function to load text_links from env - text_links ko environment variables se load karega
def load_text_links():
    text_links = {}
    for key, value in os.environ.items():
        if key.startswith('LINK_'):  # Environment variables 'LINK_key=value' format mein honge
            link_key = key[5:].lower()  # Remove 'LINK_' and convert to lower
            text_links[link_key] = value  # Key aur value ko dictionary mein store kare
    return text_links


# Initialize the client - client initialize
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# Function to handle the /start command - /start command ko handle karega
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Hi! I'm a bot that adds links to your messages.\n\n"
                         "To use me, set the following environment variables:\n"
                         "  - `API_ID`: Your Telegram API ID\n"
                         "  - `API_HASH`: Your Telegram API hash\n"
                         "  - `BOT_TOKEN`: Your bot's token\n"
                         "  - `CHANNEL_ID`: The ID of the channel you want to use\n"
                         "  - `LINK_text1`: The link you want to add when 'text1' is found in a message (replace text1 with your word)\n"
                         "  - `LINK_text2`: Another link (as needed)\n"
                         "  ...\n\n"
                         "For example:\n"
                         "  `LINK_bswin=https://your-link.com`\n\n"
                         "After setting the environment variables, send `/help` to see more instructions.")


# Function to handle the /help command - /help command ko handle karega
@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond("Okay, Here is the instruction:\n\n"
                         "1. First, set the required Environment variables:\n"
                         "   - `API_ID`: Your Telegram API ID\n"
                         "   - `API_HASH`: Your Telegram API hash\n"
                         "   - `BOT_TOKEN`: Your bot's token\n"
                         "   - `CHANNEL_ID`: The ID of the channel you want to use\n"
                         "   - `LINK_text1`: The link you want to add when 'text1' is found in a message (replace text1 with your word)\n"
                         "   - `LINK_text2`: Another link (as needed)\n"
                         "   ...\n\n"
                         "2. After setting the variables, send messages in the channel you configured with `CHANNEL_ID`. The bot will automatically replace the text you defined in the variable with the specified link below it.\n"
                         "Example:\n"
                         "If you send this message 'Check bswin for more info' and set the environment variable 'LINK_bswin=https://your-link.com', then the bot will change the message to 'Check bswin\nhttps://your-link.com for more info'\n"
                        )

# Event handler to add links - links add karne ke liye event handler
@client.on(events.NewMessage()) # removed chats=CHANNEL_ID because we check inside the function now
async def add_links(event):
    # get the channel_id from environment variable
    try:
      channel_id = int(os.getenv('CHANNEL_ID'))
    except TypeError:
      logging.error("No channel id was found. Please set up CHANNEL_ID as an environment variable.")
      return
    except ValueError:
      logging.error("The channel id must be a number. Please review your CHANNEL_ID variable.")
      return

    # Check if message is from the specified channel
    if event.chat_id != channel_id:
        return

    message_text = event.message.message
    new_message_text = message_text
    text_links = load_text_links()  # text_links ko environment se load kiya

    for text, link in text_links.items():
      if text in message_text:
        new_message_text = new_message_text.replace(text, f"{text}\n{link}") # replaced the text with the link under the text

    if new_message_text != message_text:
      await event.edit(new_message_text, parse_mode=None) # edit message with link under it

# Start the bot - bot start karega
with client:
    client.run_until_disconnected()
