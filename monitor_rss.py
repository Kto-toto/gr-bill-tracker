import os
import feedparser
import json
import asyncio
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # 1691411641 из вашего curl!

bot = Bot(token=TELEGRAM_TOKEN)

STATE_FILE = '/tmp/rss_state.json'

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def check_rss():
    urls = []
    try:
        with open('bills.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except:
        return ["❌ <b>bills.txt</b> не найден"]
    
    state = load_state()
    messages = []
    
    for url in urls:
        bill_num = url.split('/bill/')[1].split('/')[0] if '/bill/' in url else 'неизвестно'
        print(f"🔍 {bill_num}")
        
        feed = feedparser.parse(url)
        if not feed.entries:
            messages.append(f"📄 <b>{bill_num}</b>\n⚠️ RSS пустой")
            continue
        
        last_guids = state.get(bill_num, [])
        changes = []
        
        for entry in feed.entries[:3]:
            guid = entry.get('guid') or entry.link
            if guid not in last_guids:
                title = entry.title.replace('[CDATA[', '').replace(']]>', '').strip(' ()')
                changes.append(title)
        
        if changes:
            status_msg = f"🔄 <b>{bill_num}</b> изменился!\n" + "\n".join(changes)
        else:
            status_msg = f"📄 <b>{bill_num}</b>\n✅ Изменений нет"
        
        messages.append(status_msg)
        state[bill_num] = [e.get('guid') or e.link for e in feed.entries[:5]]
    
    save_state(state)
    return messages

async def main():
    print("🚀 Bill RSS Tracker запущен")
    messages = check_rss()
    
    report = "📊 <b>ОТЧЕТ МОНИТОРИНГА:</b>\n\n" + "\n\n".join(messages)
    await bot.send_message(chat_id=CHAT_ID, text=report, parse_mode='HTML')
    print(f"✅ Отчет отправлен ({len(messages)} законопроектов)")

if __name__ == "__main__":
    asyncio.run(main())
