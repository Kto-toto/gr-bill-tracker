#!/usr/bin/env python3
import feedparser, json, os, requests
from datetime import datetime
import telegram

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = telegram.Bot(TELEGRAM_TOKEN)

def load_bills():
    try:
        with open("bills.txt") as f:
            return [l.strip() for l in f if l.strip()]
    except: return []

state = {}
try:
    with open(".bill_status.json") as f:
        state = json.load(f)
except: pass

messages = []
for url in load_bills():
    num = url.split('/bill/')[1].split('/')[0]
    resp = requests.get(url)
    feed = feedparser.parse(resp.content)
    
    if not feed.entries:
        messages.append(f"📄 <b>{num}</b> Нет событий")
        continue
    
    cnt = len(feed.entries)
    if num not in state:
        messages.append(f"🔥 <b>{num}</b> НОВЫЙ! {cnt} событий")
        state[num] = {"events": cnt}
    elif cnt > state[num]["events"]:
        messages.append(f"🔔 <b>{num}</b> +{cnt-state[num]['events']} событий")
        state[num]["events"] = cnt

with open(".bill_status.json", "w") as f:
    json.dump(state, f)

if messages:
    report = f"📊 {datetime.now().strftime('%H:%M')}\n\n" + "\n".join(messages)
    bot.send_message(CHAT_ID, report, parse_mode="HTML")
