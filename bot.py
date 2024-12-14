import os
from telethon import TelegramClient, events
import logging

# Logging setup for debugging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)  # set to DEBUG to see more info

# Initialize the client - client initialize
# we don't use API ID, API HASH and BOT TOKEN here
# since users will provide them
client = None

# Dictionary to store user configurations - user configuration store karne ke liye dictionary
user_configs = {}


# Function to handle the /start command - /start command ko handle karega
@events.register(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "Hi! I'm a bot that adds links to your messages. Use these commands to set the configuration:\n"
        "- `/set_api_id <api_id>`: Set your Telegram API ID\n"
        "- `/set_api_hash <api_hash>`: Set your Telegram API hash\n"
        "- `/set_bot_token <bot_token>`: Set your bot's token\n"
        "- `/set_channel_id <channel_id>`: Set the ID of the channel you want to use\n"
        "- `/set_link <text> <link>`: Set a link to add when 'text' is found in a message (e.g., `/set_link bswin https://your-link.com`)\n"
        "- `/get_config`: View current configuration\n"
        "After setting all configuration send messages in the channel you configured."
    )

# Function to handle the /help command - /help command ko handle karega
@events.register(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond("Okay, Here is the instruction:\n\n"
                         "1. Configure me using this commands:\n"
                         "- `/set_api_id <api_id>`: Set your Telegram API ID\n"
                         "- `/set_api_hash <api_hash>`: Set your Telegram API hash\n"
                         "- `/set_bot_token <bot_token>`: Set your bot's token\n"
                         "- `/set_channel_id <channel_id>`: Set the ID of the channel you want to use\n"
                         "- `/set_link <text> <link>`: Set a link to add when 'text' is found in a message (e.g., `/set_link bswin https://your-link.com`)\n"
                         "- `/get_config`: View current configuration\n\n"
                         "2. After setting the configuration, send messages in the channel you configured with `CHANNEL_ID`. The bot will automatically replace the text you defined in the variable with the specified link below it.\n"
                         "Example:\n"
                         "If you send this message 'Check bswin for more info' and set the environment variable 'LINK_bswin=https://your-link.com', then the bot will change the message to 'Check bswin\nhttps://your-link.com for more info'\n"
                        )

# Function to handle the /set_api_id command - /set_api_id command ko handle karega
@events.register(events.NewMessage(pattern='/set_api_id (.+)'))
async def set_api_id(event):
    user_id = event.sender_id
    api_id = event.pattern_match.group(1)
    try:
      api_id = int(api_id)
    except ValueError:
      await event.respond("Please input a valid number for API ID")
      return
    if user_id not in user_configs:
        user_configs[user_id] = {}
    user_configs[user_id]['api_id'] = api_id
    await event.respond(f"API ID set to: {api_id}")


# Function to handle the /set_api_hash command - /set_api_hash command ko handle karega
@events.register(events.NewMessage(pattern='/set_api_hash (.+)'))
async def set_api_hash(event):
    user_id = event.sender_id
    api_hash = event.pattern_match.group(1)
    if user_id not in user_configs:
        user_configs[user_id] = {}
    user_configs[user_id]['api_hash'] = api_hash
    await event.respond(f"API Hash set to: {api_hash}")


# Function to handle the /set_bot_token command - /set_bot_token command ko handle karega
@events.register(events.NewMessage(pattern='/set_bot_token (.+)'))
async def set_bot_token(event):
    user_id = event.sender_id
    bot_token = event.pattern_match.group(1)
    if user_id not in user_configs:
        user_configs[user_id] = {}
    user_configs[user_id]['bot_token'] = bot_token
    await event.respond(f"Bot Token set to: {bot_token}")

# Function to handle the /set_channel_id command - /set_channel_id command ko handle karega
@events.register(events.NewMessage(pattern='/set_channel_id (.+)'))
async def set_channel_id(event):
    user_id = event.sender_id
    channel_id = event.pattern_match.group(1)
    try:
        channel_id = int(channel_id)
    except ValueError:
        await event.respond("Please input a valid number for Channel ID")
        return

    if user_id not in user_configs:
        user_configs[user_id] = {}
    user_configs[user_id]['channel_id'] = channel_id
    await event.respond(f"Channel ID set to: {channel_id}")

# Function to handle the /set_link command - /set_link command ko handle karega
@events.register(events.NewMessage(pattern='/set_link (.+) (.+)'))
async def set_link(event):
    user_id = event.sender_id
    text = event.pattern_match.group(1)
    link = event.pattern_match.group(2)
    if user_id not in user_configs:
        user_configs[user_id] = {}
    if 'text_links' not in user_configs[user_id]:
      user_configs[user_id]['text_links'] = {}

    user_configs[user_id]['text_links'][text] = link
    await event.respond(f"Link for '{text}' set to: {link}")

# Function to handle the /get_config command - /get_config command ko handle karega
@events.register(events.NewMessage(pattern='/get_config'))
async def get_config(event):
  user_id = event.sender_id
  if user_id in user_configs:
    config = user_configs[user_id]
    config_str = "Current configuration:\n"
    for key, value in config.items():
        if key == 'text_links':
            config_str += f"  Text Links:\n"
            for text, link in value.items():
                config_str += f"    {text}: {link}\n"

        else:
          config_str += f"  {key}: {value}\n"
    await event.respond(config_str)

  else:
    await event.respond("No configuration found for this user. Please set the config using the `/set_*` commands.")

# Event handler to add links - links add karne ke liye event handler
@events.register(events.NewMessage())
async def add_links(event):
  user_id = event.sender_id
  if user_id not in user_configs or 'api_id' not in user_configs[user_id] or 'api_hash' not in user_configs[user_id] or 'bot_token' not in user_configs[user_id] or 'channel_id' not in user_configs[user_id]:
    await event.respond("Please set the configuration using the provided commands first. Use `/help` for instruction")
    return

  api_id = user_configs[user_id]['api_id']
  api_hash = user_configs[user_id]['api_hash']
  bot_token = user_configs[user_id]['bot_token']
  channel_id = user_configs[user_id]['channel_id']

  if client is None or not client.is_connected():
      try:
        # initialize the bot client
        client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

      except Exception as e:
        logging.error(f"Error initializing client: {e}")
        await event.respond(f"An error occurred initializing the bot. Please check your configurations. Error: {e}")
        return

  # Check if message is from the specified channel
  if event.chat_id != channel_id:
      return

  message_text = event.message.message
  new_message_text = message_text
  text_links = user_configs[user_id].get('text_links', {})

  for text, link in text_links.items():
    if text in message_text:
      new_message_text = new_message_text.replace(text, f"{text}\n{link}") # replaced the text with the link under the text

  if new_message_text != message_text:
    try:
        await event.edit(new_message_text, parse_mode=None) # edit message with link under it
    except Exception as e:
       logging.error(f"An error occurred while editing the message: {e}")
       await event.respond(f"An error occurred while editing the message. Error: {e}")

# Start the bot - bot start karega
if __name__ == '__main__':
    try:
        with TelegramClient('bot_session',  API_ID, API_HASH).start(bot_token=BOT_TOKEN) as client:
            client.run_until_disconnected()
    except Exception as e:
        logging.error(f"An error occurred while running the bot: {e}")
