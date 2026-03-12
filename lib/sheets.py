# lib/sheets.py
# Интеграция с Google Sheets для бота «Тульский ключ»

import logging
import json
import os
import gspread
from google.oauth2.service_account import Credentials

# Локальный импорт config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def get_sheet():
    """
    Инициализация подключения к Google Sheets.
    Возвращает объект листа или None при ошибке.
    """
    try:
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Вариант 1: credentials из переменной окружения (для Vercel)
        if config.GOOGLE_CREDS_JSON:
            creds_info = json.loads(config.GOOGLE_CREDS_JSON)
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        
        # Вариант 2: credentials из файла (для локальной отладки)
        elif os.path.exists("credentials.json"):
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        
        else:
            logger.error("❌ Google credentials not found!")
            return None
        
        # Авторизация и получение листа
        client = gspread.authorize(creds)
        sheet = client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
        logger.info("✅ Google Sheets connected")
        return sheet
        
    except Exception as e:
        logger.error(f"❌ Google Sheets connection error: {e}")
        return None


def save_lead( dict):
    """
    Сохранение данных лида в таблицу Google Sheets.
    
    Args:
        data: dict с ключами: date, name, phone, goal, budget, district, deadline, user_id
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        sheet.append_row([
            data.get('date', ''),
            data.get('name', ''),
            data.get('phone', ''),
            data.get('goal', ''),
            data.get('budget', ''),
            data.get('district', ''),
            data.get('deadline', ''),
            str(data.get('user_id', ''))
        ])
        logger.info(f"✅ Lead saved: {data.get('name')} | {data.get('phone')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Save lead error: {e}")
        return False


async def notify_admin(bot, text: str):
    """
    Отправка уведомления администратору в Telegram.
    
    Args:
        bot: объект aiogram Bot
        text: текст сообщения
    """
    if not config.ADMIN_ID:
        logger.warning("⚠️ ADMIN_ID not set, skipping notification")
        return
    
    try:
        await bot.send_message(chat_id=config.ADMIN_ID, text=text)
        logger.info(f"✅ Notification sent to admin {config.ADMIN_ID}")
    except Exception as e:
        logger.error(f"❌ Notify admin error: {e}")
