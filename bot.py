import os
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelInvalidError


# Environment variables se values load karo
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Channel IDs ko ek list mein store karenge
CHANNEL_IDS = list(map(int, os.getenv('CHANNEL_IDS', '').split(','))) if os.getenv('CHANNEL_IDS') else []

# Text aur links ka dictionary
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

# Client initialize karo
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def is_valid_channel(channel_id):
    try:
        channel = await client(GetFullChannelRequest(channel_id))
        return True
    except ChannelInvalidError:
        return False
    except Exception as e:
        print(f"Error checking channel {channel_id}: {e}")
        return False


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcome message."""
    await event.respond('Namaste! 🙏  Bot mein aapka swagat hai! \n\n'
                        'Ye bot aapke messages mein automatically links add kar dega.\n\n'
                        'Agar aapko koi problem ho ya help chahiye, to /help command use karein.')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Help aur contact information."""
    await event.respond('Aapko koi bhi problem ho, to mujhe yahaan contact karein: @captain_stive\n\n'
                       'Commands:\n'
                       '/add_channel <channel_id> - Channel add karein.\n'
                       '/remove_channel <channel_id> - Channel remove karein.\n'
                       '/list_channels - Added channels dekhein.')

@client.on(events.NewMessage(pattern=r'/add_channel (.*)'))
async def add_channel(event):
    """Channel add karein."""
    try:
        channel_id = int(event.pattern_match.group(1))
        if await is_valid_channel(channel_id):
            if channel_id not in CHANNEL_IDS:
                CHANNEL_IDS.append(channel_id)
                await event.respond(f'Channel ID {channel_id} add ho gaya! ✅')
            else:
                await event.respond(f'Channel ID {channel_id} already added hai. ⚠️')
        else:
             await event.respond(f'Invalid channel ID: {channel_
