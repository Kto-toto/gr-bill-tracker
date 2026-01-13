# GR Bill Tracker Bot

Telegram-бот для мониторинга законопроектов Госдумы.

## Развертывание

1. Создайте бота у @BotFather, получите TOKEN.
2. Узнайте свой CHAT_ID через @userinfobot.
3. `pip install -r requirements.txt`
4. `export TELEGRAM_TOKEN=your_token`
5. `python main.py`

## GitHub Actions (cron каждые 2 часа)
Создайте `.github/workflows/monitor.yml`:
```yaml
name: Check Bills
on:
  schedule:
    - cron: '0 */2 * * *'
  workflow_dispatch:
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: python check_updates.py  # Отдельный скрипт без polling
      env:
        TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
