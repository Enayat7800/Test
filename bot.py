import os
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeeded, FloodWaitError
import asyncio

# Replace hardcoded values with environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
MY_CHANNEL_ID = int(os.getenv('MY_CHANNEL_ID'))  # Add your channel ID as an environment variable

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH)

# Dictionary to store user-specific data (channel ID and links)
user_data = {}

# /start command handler
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    await event.respond(
        "Welcome! This bot allows you to automatically add links to messages in your channel and copy gift codes to your channel.\n"
        "Please set up your channel and links using the following commands:\n"
        "/setchannel - Set your channel ID.\n"
        "/setlinks - Set your text-link pairs.\n"
        "/help - for more info"
        ,
        buttons=[
            [Button.inline("Set Channel", data="setchannel")],
            [Button.inline("Set Links", data="setlinks")],
             [Button.inline("Help", data="help")]
        ]
    )
    user_data[user_id] = {'channel_id': None, 'links': {}}

# /help command handler

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    
    help_message = (
        "Here are the available commands:\n\n"
        "/start - Start the bot and see the welcome message.\n"
        "/setchannel - Set the channel where you want the bot to operate. "
        "You need to add the bot to your channel as an admin with edit messages permission.\n"
        "/setlinks - Set the text-link pairs that the bot will use to replace text with links. "
        "Send each pair in the format 'text:link'.\n"
        "/showlinks - View your currently configured text-link pairs.\n"
        "/clearlnks - To clear all links and add links again.\n"
        "/help - Display this help message."
    )
    await event.respond(help_message)

#Inline query handler
@client.on(events.CallbackQuery)
async def callback_query_handler(event):
    query_data = event.data.decode()

    if query_data == "setchannel":
        await setchannel_inline(event)
    elif query_data == "setlinks":
        await setlinks_inline(event)
    elif query_data == "help":
        await help_inline(event)

# /setchannel command handler
# @client.on(events.NewMessage(pattern='/setchannel'))
async def setchannel_inline(event):
    user_id = event.sender_id
    await event.respond("Please send your channel ID (e.g., -100xxxxxxxxxx). "
                        "Make sure to add this bot to your channel as an admin with 'edit messages' permission.")
    user_data[user_id]['state'] = 'setting_channel'

# /setlinks command handler
# @client.on(events.NewMessage(pattern='/setlinks'))
async def setlinks_inline(event):
    user_id = event.sender_id
    await event.respond("Please send your text-link pairs, each on a new line, in the format 'text:link'. "
                        "For example:\n51game:https://51gameappinin.com\n82bet:https://82bet.com")
    user_data[user_id]['state'] = 'setting_links'

async def help_inline(event):
    user_id = event.sender_id
    help_message = (
        "Here are the available commands:\n\n"
        "/start - Start the bot and see the welcome message.\n"
        "/setchannel - Set the channel where you want the bot to operate. "
        "You need to add the bot to your channel as an admin with edit messages permission.\n"
        "/setlinks - Set the text-link pairs that the bot will use to replace text with links. "
        "Send each pair in the format 'text:link'.\n"
        "/showlinks - View your currently configured text-link pairs.\n"
        "/clearlnks - To clear all links and add links again.\n"
        "/help - Display this help message."
    )
    await event.respond(help_message)

# /showlinks command handler
@client.on(events.NewMessage(pattern='/showlinks'))
async def showlinks(event):
    user_id = event.sender_id
    if user_id in user_data and user_data[user_id]['links']:
        links_str = ""
        for text, link in user_data[user_id]['links'].items():
            links_str += f"{text}: {link}\n"
        await event.respond(f"Your current text-link pairs are:\n{links_str}")
    else:
        await event.respond("You haven't set any text-link pairs yet.")

@client.on(events.NewMessage(pattern='/clearlinks'))
async def clearlinks(event):
    user_id = event.sender_id
    if user_id in user_data:
        user_data[user_id]['links'] = {}
        await event.respond("All your links have been cleared.")
    else:
        await event.respond("You haven't set any links yet.")

# Message handler for setting channel ID and links
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    if user_id in user_data:
        state = user_data[user_id].get('state')

        if state == 'setting_channel':
            try:
                channel_id = int(event.message.message)
                # Try to get channel entity to verify the channel ID
                channel_entity = await client.get_entity(channel_id)

                # Check if the bot is an admin in the channel with edit messages permission
                bot_permissions = await client.get_permissions(channel_entity, client.uid)
                if not bot_permissions.is_admin or not bot_permissions.edit_messages:
                    await event.respond("I am not an admin with 'edit messages' permission in this channel. "
                                        "Please make me an admin and grant the necessary permission.")
                    return

                user_data[user_id]['channel_id'] = channel_id
                user_data[user_id]['state'] = None
                await event.respond(f"Channel ID set to {channel_id}")
            except ValueError:
                await event.respond("Invalid channel ID. Please send a valid integer.")
            except Exception as e:
                await event.respond(f"Error: {e}\n"
                                     "Make sure you have added the bot to your channel as admin with edit message permission.")

        elif state == 'setting_links':
            message_lines = event.message.message.strip().split('\n')
            new_links = {}
            for line in message_lines:
                try:
                    text, link = line.split(':', 1)
                    new_links[text.strip()] = link.strip()
                except ValueError:
                    await event.respond("Invalid format. Please use 'text:link' format for each line.")
                    return
            user_data[user_id]['links'].update(new_links)
            user_data[user_id]['state'] = None
            await event.respond("Text-link pairs added successfully.")

# Function to check if a string is a gift code (e.g., alphanumeric, uppercase, specific length)
def is_gift_code(text):
    # Customize this logic based on the gift code format
    return text.isalnum() and text.isupper() and len(text) >= 8

# New message handler for adding links in the user's channel and copying gift codes
@client.on(events.NewMessage(incoming=True))
async def handle_all_messages(event):
    
    # Copy gift codes logic (only if not from your channel to avoid loops)
    if event.chat_id != MY_CHANNEL_ID:
        message_text = event.message.message
        if is_gift_code(message_text):
            try:
                await client.send_message(MY_CHANNEL_ID, f"Gift Code found:\n{message_text}")
                print(f"Gift code '{message_text}' copied to your channel.")
            except FloodWaitError as e:
                print(f"FloodWaitError: Sleeping for {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"Error forwarding message: {e}")

    # Add links logic
    for user_id, data in user_data.items():
        channel_id = data.get('channel_id')
        links = data.get('links')

        if channel_id is None or links is None:
            continue  # Skip if channel ID or links are not set

        if event.chat_id == channel_id:
            message_text = event.message.message
            for text, link in links.items():
                if text in message_text and 'http' not in message_text:
                    new_message_text = message_text.replace(text, f"{text}\n{link}")
                    try:
                        await event.edit(new_message_text)
                    except Exception as e:
                        print(f"Error editing message in channel {channel_id}: {e}")
                    break

# Start the bot
async def start_bot():
    await client.start(bot_token=BOT_TOKEN)
    print("Bot started successfully!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())
