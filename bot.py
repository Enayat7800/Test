import os
from telethon import TelegramClient, events

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize with an empty list of channel IDs
CHANNEL_IDS = []

# Dictionary of text and links (initially empty)
text_links = {}

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    await event.respond('Namaste! 🙏  Bot mein aapka swagat hai! \n\n'
                        'Ye bot aapke messages mein automatically links add kar dega.\n\n'
                        'Agar aapko koi problem ho ya help chahiye, to /help command use karein.\n\n'
                        'Naye channel add karne ke liye, /addchannel command use karein (jaise: /addchannel -100123456789).\n\n'
                        'Text aur link add karne ke liye /addlink command use karein (jaise: /addlink text link).')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Provides help and contact information."""
    await event.respond('Aapko koi bhi problem ho, to mujhe yahaan contact karein: @captain_stive')

@client.on(events.NewMessage(pattern=r'/addchannel (-?\d+)'))
async def add_channel(event):
    """Adds a channel ID to the list of monitored channels."""
    channel_id = int(event.pattern_match.group(1))
    if channel_id not in CHANNEL_IDS:
        CHANNEL_IDS.append(channel_id)
        await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
    else:
        await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}") # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern=r'/addlink (.+) (https?://[^\s]+)'))
async def add_link(event):
    """Adds a text and link pair to the dictionary."""
    text = event.pattern_match.group(1)
    link = event.pattern_match.group(2)
    text_links[text] = link
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    print(f"Current text_links: {text_links}") # Debugging line: show current text_links


@client.on(events.NewMessage())
async def add_links(event):
    if event.is_channel and event.chat_id in CHANNEL_IDS:
        print(f"Message received from channel ID: {event.chat_id}")
        message_text = event.message.message
        for text, link in text_links.items():
            if message_text == text:
                new_message_text = f"{text}\n{link}"
                await event.edit(new_message_text)
                print(f"Edited message in channel ID: {event.chat_id}")
                break


# Start the bot
with client:
    client.run_until_disconnected()
