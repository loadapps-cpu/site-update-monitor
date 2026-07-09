name: Check children update

on:
  schedule:
    - cron: "0 */4 * * *"   # каждые 4 часа
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install playwright requests

      - run: playwright install chromium

      - run: python monitor_children_update.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
