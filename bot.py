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
           await event.edit(new_message_text)
