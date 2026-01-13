import os
import feedparser
import json
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
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
    # Читаем RSS из bills.txt
    urls = []
    try:
        with open('bills.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except:
        print("❌ bills.txt не найден")
        return []
    
    state = load_state()
    new_events = []
    
    for url in urls:
        bill_num = url.split('/bill/')[1].split('/')[0]
        print(f"🔍 {bill_num}")
        
        feed = feedparser.parse(url)
        if not feed.entries:
            continue
            
        last_guids = state.get(bill_num, [])
        
        for entry in feed.entries[:3]:
            guid = entry.get('guid') or entry.link
            if guid not in last_guids:
                title = entry.title.replace('[CDATA[', '').replace(']]>', '').strip(' ()')
                link = entry.link
                new_events.append(f"📄 <b>{title}</b>\n🔗 <a href='{link}'>Открыть</a>")
        
        state[bill_num] = [e.get('guid') or e.link for e in feed.entries[:5]]
    
    save_state(state)
    return new_events

if __name__ == "__main__":
    print("🚀 Bill RSS Tracker запущен")
    events = check_rss()
    
    if events:
        msg = "🔔 <b>НОВЫЕ СОБЫТИЯ ПО ЗАКОНОПРОЕКТАМ:</b>\n\n" + "\n\n".join(events)
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        print(f"✅ Отправлено {len(events)} событий")
    else:
        print("ℹ️ Нет новых событий")
