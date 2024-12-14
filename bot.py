import os
from telethon import TelegramClient, events
import re
import json

# एनवायरनमेंट वेरिएबल से वैल्यू लोड करें
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# डेटा को स्टोर करने के लिए एक फ़ाइल (आप डेटाबेस का उपयोग भी कर सकते हैं)
DATA_FILE = 'bot_data.json'

# लोड करने के लिए फ़ंक्शन
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'channels': {}, 'text_links': {}}

# सेव करने के लिए फंक्शन
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# क्लाइंट को इनिशियलाइज़ करें
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# डेटा लोड करें
data = load_data()

# /start कमांड को हैंडल करें
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """यह फंक्शन /start कमांड का जवाब देता है।"""
    await event.respond('नमस्ते! मैं एक बोट हूँ जो मैसेज में लिंक्स जोड़ता है।\n\n'
                        'उपलब्ध कमांड:\n'
                        '/setchannel <channel_id> - चैनल आईडी सेट करें\n'
                        '/addlink <text> <link> - एक नया लिंक जोड़ें\n'
                        '/removelink <text> - एक लिंक हटाएं\n'
                        '/listlinks - सभी सेट लिंक देखें')

# /setchannel कमांड को हैंडल करें
@client.on(events.NewMessage(pattern='/setchannel'))
async def set_channel_handler(event):
    """यह फंक्शन चैनल आईडी सेट करने की अनुमति देता है।"""
    try:
        channel_id = int(event.text.split(' ', 1)[1])
        user_id = event.sender_id
        data['channels'][user_id] = channel_id
        save_data(data)
        await event.respond(f'चैनल आईडी {channel_id} सेट किया गया।')
    except (IndexError, ValueError):
        await event.respond('गलत फॉर्मेट। सही फॉर्मेट: /setchannel <channel_id>')

# /addlink कमांड को हैंडल करें
@client.on(events.NewMessage(pattern='/addlink'))
async def add_link_handler(event):
    """यह फंक्शन टेक्स्ट और लिंक को जोड़ने की अनुमति देता है।"""
    try:
        parts = event.text.split(' ', 2)
        text = parts[1]
        link = parts[2]
        user_id = event.sender_id
        if user_id not in data['text_links']:
           data['text_links'][user_id] = {}
        data['text_links'][user_id][text] = link
        save_data(data)
        await event.respond(f'लिंक `{link}` को टेक्स्ट `{text}` के लिए जोड़ा गया।')
    except IndexError:
        await event.respond('गलत फॉर्मेट। सही फॉर्मेट: /addlink <text> <link>')


# /removelink कमांड को हैंडल करें
@client.on(events.NewMessage(pattern='/removelink'))
async def remove_link_handler(event):
    """यह फंक्शन टेक्स्ट और लिंक को हटाने की अनुमति देता है।"""
    try:
        text = event.text.split(' ', 1)[1]
        user_id = event.sender_id
        if user_id in data['text_links'] and text in data['text_links'][user_id]:
            del data['text_links'][user_id][text]
            save_data(data)
            await event.respond(f'लिंक टेक्स्ट `{text}` से हटाया गया।')
        else:
            await event.respond('लिंक टेक्स्ट नहीं मिला।')
    except IndexError:
        await event.respond('गलत फॉर्मेट। सही फॉर्मेट: /removelink <text>')


# /listlinks कमांड को हैंडल करें
@client.on(events.NewMessage(pattern='/listlinks'))
async def list_links_handler(event):
    """यह फंक्शन सभी लिंक्स की सूची दिखाता है।"""
    user_id = event.sender_id
    if user_id in data['text_links'] and data['text_links'][user_id]:
        links_list = "\n".join([f"{text}: {link}" for text, link in data['text_links'][user_id].items()])
        await event.respond(f'सेव किए गए लिंक्स:\n{links_list}')
    else:
        await event.respond('कोई लिंक सेव नहीं किया गया।')


# चैनल में नए मैसेज आने पर लिंक्स जोड़ने का फंक्शन
@client.on(events.NewMessage)
async def add_links(event):
    """यह फंक्शन चैनल के मैसेज में टेक्स्ट के अनुसार लिंक्स जोड़ता है।"""
    user_id = event.sender_id
    if user_id in data['channels'] and event.chat_id == data['channels'][user_id]:
      message_text = event.message.message
      new_message_text = message_text
      if user_id in data['text_links']:
        for text, link in data['text_links'][user_id].items():
            # केस-इनसेंसिटिव मैचिंग के लिए regex pattern
            pattern = re.compile(r'(?i)' + re.escape(text))
            match = pattern.search(message_text)
            if match:
               # मैसेज में पहले टेक्स्ट को लिंक के साथ बदलें
               new_message_text = re.sub(pattern, f"{text}\n{link}", new_message_text, 1)
      
      # अगर मैसेज में बदलाव हुआ है तो मैसेज एडिट करें
      if new_message_text != message_text:
         await event.edit(new_message_text, parse_mode=None)

# बॉट को शुरू करें
with client:
    print("बॉट चल रहा है...")  # बॉट के चलने की पुष्टि करें
    client.run_until_disconnected()
