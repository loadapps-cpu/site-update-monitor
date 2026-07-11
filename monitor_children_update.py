import os
import re
from pathlib import Path
from datetime import datetime

import requests
from playwright.sync_api import sync_playwright


URL = (
    "https://xn--b1agisfqlc7e.xn--p1ai/"
    "children?page=1&limit=6&ageFrom=0&ageTo=17"
)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

LAST_DATE_FILE = Path("last_update_date.txt")
LOG_FILE = Path("update_dates_log.txt")

# Для быстрой проверки оставь True.
# После получения тестового сообщения обязательно поменяй на False.
TEST_MODE = True


def get_page_text():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"],
        )

        page = browser.new_page()

        try:
            print("Перехожу на страницу...")

            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=120_000,
            )

            # Даём странице время загрузить динамические данные
            page.wait_for_timeout(10_000)

            text = page.locator("body").inner_text(timeout=30_000)

            print("Страница успешно загружена.")
            return text

        finally:
            browser.close()

def extract_update_date(text):
    # Заменяем неразрывные пробелы обычными
    normalized_text = text.replace("\xa0", " ")

    months = (
        "января|февраля|марта|апреля|мая|июня|июля|"
        "августа|сентября|октября|ноября|декабря"
    )

    pattern = rf"на\s+\d{{1,2}}\s+(?:{months})\s+\d{{4}}\s+года"

    match = re.search(
        pattern,
        normalized_text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError("Не удалось найти дату обновления на странице")

    return match.group(0).strip()


def send_telegram(message):
    telegram_url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )

    response.raise_for_status()


def read_last_date():
    if not LAST_DATE_FILE.exists():
        return ""

    return LAST_DATE_FILE.read_text(encoding="utf-8").strip()


def save_new_date(new_date):
    LAST_DATE_FILE.write_text(
        new_date,
        encoding="utf-8",
    )

    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{datetime.now().isoformat(timespec='seconds')} | "
            f"{new_date}\n"
        )


def check_once():
    print("Открываю страницу...")

    page_text = get_page_text()
    current_date = extract_update_date(page_text)

    if TEST_MODE:
        # Искусственно задаём старую дату для проверки уведомления
        previous_date = "на 1 января 2000 года"
    else:
        previous_date = read_last_date()

    print(f"Дата на сайте: {current_date}")
    print(f"Предыдущая дата: {previous_date or 'ещё не записана'}")

    if current_date == previous_date:
        print("Дата не изменилась. Уведомление не требуется.")
        return

    save_new_date(current_date)

    if TEST_MODE:
        message = (
            "✅ Тест GitHub Actions успешно выполнен!\n\n"
            f"Дата на сайте: {current_date}\n"
            f"Тестовая предыдущая дата: {previous_date}\n\n"
            f"{URL}"
        )
    else:
        message = (
            "🔔 На сайте изменилась дата обновления!\n\n"
            f"Было: {previous_date or 'предыдущей записи не было'}\n"
            f"Стало: {current_date}\n\n"
            f"{URL}"
        )

    send_telegram(message)
    print("Сообщение отправлено в Telegram.")


if __name__ == "__main__":
    try:
        check_once()
    except Exception as error:
        print(f"Ошибка: {error}")
        raise
