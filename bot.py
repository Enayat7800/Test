import os
from telethon import TelegramClient, events

# Replace hardcoded values with environment variables
API_ID = int(os.getenv('API_ID'))  # Set in Railway environment variables
API_HASH = os.getenv('API_HASH')  # Set in Railway environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN'))  # Set in Railway environment variables
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Set your channel ID in Railway environment variables

# Dictionary of text and links
text_links = {
    '51game': 'https://51gameappinin.com/#/register?invitationCode=83363102977',
    'bswin': 'https://bslotto.com/#/register?invitationCode=86787104955',
    '82bet': 'https://82bet.com/#/register?invitationCode=583873088657',
    'okwin': 'https://www.okwin.la/#/register?invitationCode=715142961253',
    'Deltin': 'http://deltin.bet/register?key=1000277575',
    'Raja luck': 'https://rajaluck.com/#/register?invitationCode=tleWe85176',
    'In99': 'https://in999.club/#/register?invitationCode=13587102403',
    'sonsy': 'https://www.sonsy1.in/#/register?invitationCode=58334104548',
    '1010game': 'https://1014game.in/#/register?invitationCode=372441180074',
    'Diuwin': 'https://diuwin.bet/#/register?invitationCode=88112104612',
    'Biliwin': 'https://biliwin.in/#/register?invitationCode=68853114831',
    'Big mumbai': 'https://mumbaibig.in/#/register?invitationCode=755462848654',
    'Aviator god': 'https://aviatorgod3.in/#/register?invitationCode=31232118241',
    'Lottery 7': 'https://www.9999lottery.com/#/register?invitationCode=684231384630',
    'Tpplay': 'https://tpplay.in/#/register?invitationCode=85536323165',
    'Lucknow game': 'https://www.lucknowgames.in/register?share_reg_type=fissionRoulette&invite_code=3C0A48982150',
    'Tiranga': 'https://tirangagames.top/#/register?invitationCode=374254902621',
    '91club': 'https://91appa.com/#/register?invitationCode=136124853496',
    'Bounty game': 'https://bountygame.biz/#/register?invitationCode=63717296105',
    'Kwg game': 'https://kwggame.com/#/register?invitationCode=422B567414',
    'Lucky11': 'https://lucky11a.in/#/register?invitationCode=58385216389',
    'Win101': 'https://Win101.bet/#/register?invitationCode=31831271287',
    'Sikkim': 'https://sikkim1.com/#/register?invitationCode=25621112253',
    'NN game': 'https://nngames.in/#/register?invitationCode=47257104541',
    'Raja wager': 'https://rajawager.com/#/register?invitationCode=3637791430',
    'Goa game': 'https://goa888.vip/#/register?invitationCode=576654552342',
    'Tc lottery': 'https://9987up.co/#/register?invitationCode=582475880239',
    '55club': 'https://55club08.in/#/register?invitationCode=25173833647',
    'Dream99': 'https://dream99.info/#/register?invitationCode=58173619026',
}

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    await event.respond('Namaste! 🙏  Bot mein aapka swagat hai! \n\n'
                        'Ye bot aapke messages mein automatically links add kar dega.\n\n'
                        'Agar aapko koi problem ho ya help chahiye, to /help command use karein.')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Provides help and contact information."""
    await event.respond('Aapko koi bhi problem ho, to mujhe yahaan contact karein: @captain_stive')

@client.on(events.NewMessage(chats=CHANNEL_ID))
async def add_links(event):
    message_text = event.message.message
    for text, link in text_links.items():
        if message_text == text:
            new_message_text = f"{text}\n{link}"
            await event.edit(new_message_text, parse_mode=None)  # Removed 'html' parse mode
            break

# Start the bot
with client:
    client.run_until_disconnected()
