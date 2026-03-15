# api/webhook.py
# Бот «Тульский ключ» — с Google Sheets для сохранения состояния

import os
import re
import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== НАСТРОЙКИ ====================
RAW_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_TOKEN = "".join(RAW_TOKEN.split())

CHECKLIST_URL = os.getenv("CHECKLIST_URL", "https://t.me/tula_key_bot")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/tula_key_channel")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "tula_key_channel")
ADMIN_ID = os.getenv("ADMIN_ID", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "")

if BOT_TOKEN:
    logger.info(f"✅ BOT_TOKEN loaded: {BOT_TOKEN[:10]}...")
else:
    logger.error("❌ BOT_TOKEN not set!")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ==================== TELEGRAM API ====================

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"❌ send_message error: {e}")
        return None


def answer_callback(callback_query_id, text=None):
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id, "show_alert": False}
    if text:
        data["text"] = text
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"❌ answer_callback error: {e}")
        return None


# ==================== GOOGLE SHEETS — ИСПРАВЛЕННЫЕ ФУНКЦИИ ====================

def get_sheet():
    """Подключение к Google Sheets"""
    logger.info("🔍 Attempting to connect to Google Sheets...")
    
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        
        logger.info("✅ Google libraries imported successfully")
        
        if not GOOGLE_CREDS_JSON:
            logger.error("❌ GOOGLE_CREDS_JSON is empty!")
            return None
        
        if not GOOGLE_SHEET_ID:
            logger.error("❌ GOOGLE_SHEET_ID is empty!")
            return None
        
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        logger.info("🔍 Parsing credentials JSON...")
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        logger.info(f"✅ Credentials parsed. Email: {creds_info.get('client_email', 'unknown')}")
        
        logger.info("🔍 Authorizing...")
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        logger.info(f"🔍 Opening sheet: {GOOGLE_SHEET_ID}")
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        sheet = spreadsheet.sheet1
        
        # Проверяем заголовки
        headers = sheet.row_values(1)
        logger.info(f"🔍 Sheet headers: {headers}")
        
        if not headers or len(headers) < 1:
            logger.error("❌ Headers row is empty!")
            return None
        
        logger.info("✅ Google Sheets connected successfully!")
        return sheet
        
    except ImportError as e:
        logger.error(f"❌ ImportError (missing libraries): {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Google Sheets error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return None


def save_user_state(chat_id, name, username, data):
    """Сохраняет состояние пользователя в таблицу"""
    logger.info(f"💾 Saving state for chat_id: {chat_id}")
    logger.info(f"💾 Data: {data}")
    
    sheet = get_sheet()
    if not sheet:
        logger.error("❌ Failed to get sheet, skipping save")
        return False
    
    try:
        # Проверяем заголовки
        headers = sheet.row_values(1)
        logger.info(f"🔍 Sheet headers: {headers}")
        
        # Если таблица пустая — создаём заголовки
        expected_headers = ['chat_id', 'name', 'username', 'goal', 'budget', 
                          'deadline', 'prop_type', 'district', 'invest_budget', 
                          'phone', 'updated_at']
        
        if not headers or headers[0] != 'chat_id':
            logger.warning("⚠️ Headers missing or wrong, creating headers...")
            sheet.append_row(expected_headers)
            headers = expected_headers
            logger.info(f"✅ Headers created: {headers}")
        
        # Ищем существующую запись
        all_values = sheet.get_all_values()
        logger.info(f"🔍 Total rows in sheet: {len(all_values)}")
        
        existing_row = None
        for i, row in enumerate(all_values[1:], 2):  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                existing_row = i
                logger.info(f"🔍 Found existing record at row {existing_row}")
                break
        
        # Данные для сохранения
        row_data = {
            'chat_id': str(chat_id),
            'name': name or '',
            'username': username or '',
            'goal': data.get('goal', ''),
            'budget': data.get('budget', ''),
            'deadline': data.get('deadline', ''),
            'prop_type': data.get('prop_type', ''),
            'district': data.get('district', ''),
            'invest_budget': data.get('invest_budget', ''),
            'phone': data.get('phone', ''),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if existing_row:
            # Обновляем существующую запись
            logger.info(f"🔍 Updating row {existing_row}")
            for col_idx, header in enumerate(headers, 1):
                if header in row_data and col_idx <= len(row_data):
                    try:
                        sheet.update_cell(existing_row, col_idx, row_data.get(header, ''))
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update {header}: {e}")
        else:
            # Новая запись
            logger.info("🔍 Creating new row")
            new_row = [
                row_data['chat_id'],
                row_data['name'],
                row_data['username'],
                row_data['goal'],
                row_data['budget'],
                row_data['deadline'],
                row_data['prop_type'],
                row_data['district'],
                row_data['invest_budget'],
                row_data['phone'],
                row_data['updated_at']
            ]
            sheet.append_row(new_row)
            logger.info(f"✅ New row appended")
        
        logger.info(f"✅ State saved successfully for chat_id: {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Save state error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return False


def get_user_state(chat_id):
    """Читает состояние пользователя из таблицы"""
    logger.info(f"📖 Loading state for chat_id: {chat_id}")
    
    sheet = get_sheet()
    if not sheet:
        logger.error("❌ Sheet connection failed")
        return None
    
    try:
        # Используем get_all_values() вместо get_all_records() — надёжнее
        all_values = sheet.get_all_values()
        logger.info(f"🔍 Total rows in sheet: {len(all_values)}")
        
        if len(all_values) < 2:
            logger.info("⚠️ No data rows in sheet (headers only)")
            return None
        
        # Заголовки в первой строке
        headers = all_values[0]
        logger.info(f"🔍 Headers: {headers}")
        
        # Ищем запись с matching chat_id
        for row in all_values[1:]:  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                # Преобразуем в словарь
                state = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        state[header] = row[i]
                    else:
                        state[header] = ''
                
                logger.info(f"✅ State loaded: {state}")
                return state
        
        logger.info(f"⚠️ No state found for chat_id: {chat_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Get state error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return None


def delete_user_state(chat_id):
    """Удаляет состояние после отправки лида"""
    logger.info(f"🗑️ Deleting state for chat_id: {chat_id}")
    
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        all_values = sheet.get_all_values()
        
        for i, row in enumerate(all_values[1:], 2):  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                sheet.delete_rows(i)
                logger.info(f"✅ State deleted for chat_id: {chat_id}")
                return True
        
        logger.warning(f"⚠️ No record found to delete for chat_id: {chat_id}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Delete state error: {e}")
        return False
        
# ==================== ВАЛИДАЦИЯ ТЕЛЕФОНА ====================

def is_valid_phone(text):
    if not text:
        return False
    cleaned = re.sub(r'[^\d+]', '', text)
    if cleaned.startswith('++'):
        cleaned = '+' + cleaned.lstrip('+')
    
    patterns = [
        r'^\+7\d{10}$', r'^7\d{10}$', r'^8\d{10}$', r'^\d{10}$', r'^\d{11}$',
    ]
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    return False


def normalize_phone(text):
    cleaned = re.sub(r'[^\d+]', '', text)
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11 and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    elif cleaned.isdigit() and len(cleaned) == 10:
        cleaned = '+7' + cleaned
    return cleaned


# ==================== КЛАВИАТУРЫ ====================

def main_menu_kb():
    return {
        "inline_keyboard": [
            [{"text": "📥 Получить чек-лист", "callback_data": "get_checklist"}],
            [{"text": "🔍 Подобрать квартиру", "callback_data": "goal_buy"},
             {"text": "💰 Продать", "callback_data": "goal_sell"}],
            [{"text": "📊 Инвестиции", "callback_data": "goal_invest"},
             {"text": "💬 Задать вопрос", "callback_data": "faq"}],
            [{"text": "🎁 Пригласить друга", "callback_data": "referral"}]
        ]
    }


def budget_kb():
    return {
        "inline_keyboard": [
            [{"text": "до 3 млн", "callback_data": "buy|b3"}],
            [{"text": "3–5 млн", "callback_data": "buy|b5"}],
            [{"text": "5+ млн", "callback_data": "buy|b5p"}],
            [{"text": "Нужна помощь", "callback_data": "buy|bhelp"}]
        ]
    }


def deadline_kb(budget_code):
    return {
        "inline_keyboard": [
            [{"text": "🔥 Срочно", "callback_data": f"buy|{budget_code}|urgent"}],
            [{"text": "📅 1-3 мес", "callback_data": f"buy|{budget_code}|month"}],
            [{"text": "👀 Просто смотрю", "callback_data": f"buy|{budget_code}|look"}]
        ]
    }


def property_type_kb():
    return {
        "inline_keyboard": [
            [{"text": "Квартира", "callback_data": "sell|flat"}],
            [{"text": "Дом", "callback_data": "sell|house"}],
            [{"text": "Комната", "callback_data": "sell|room"}],
            [{"text": "Другое", "callback_data": "sell|other"}]
        ]
    }


def district_kb(type_code):
    return {
        "inline_keyboard": [
            [{"text": "Центральный", "callback_data": f"sell|{type_code}|center"}],
            [{"text": "Заречье", "callback_data": f"sell|{type_code}|zarechye"}],
            [{"text": "Пролетарский", "callback_data": f"sell|{type_code}|proletarsky"}],
            [{"text": "Любой", "callback_data": f"sell|{type_code}|any"}]
        ]
    }


def invest_budget_kb():
    return {
        "inline_keyboard": [
            [{"text": "до 2 млн", "callback_data": "invest|i2"}],
            [{"text": "2–5 млн", "callback_data": "invest|i5"}],
            [{"text": "5+ млн", "callback_data": "invest|i5p"}]
        ]
    }


def channel_kb():
    return {
        "inline_keyboard": [
            [{"text": "📢 Подписаться на канал", "url": f"https://t.me/{CHANNEL_USERNAME}"}]
        ]
    }


# ==================== МАППИНГИ ====================

BUDGET_MAP = {
    "b3": "до 3 млн", "b5": "3–5 млн", "b5p": "5+ млн", "bhelp": "Нужна помощь"
}
DEADLINE_MAP = {
    "urgent": "🔥 Срочно", "month": "📅 1-3 месяца", "look": "👀 Пока присматриваюсь"
}
TYPE_MAP = {
    "flat": "Квартира", "house": "Дом", "room": "Комната", "other": "Другое"
}
DISTRICT_MAP = {
    "center": "Центральный", "zarechye": "Заречье", 
    "proletarsky": "Пролетарский", "any": "Любой"
}
INVEST_MAP = {
    "i2": "до 2 млн", "i5": "2–5 млн", "i5p": "5+ млн"
}
GOAL_MAP = {
    "buy": ("🏠", "Покупка"),
    "sell": ("💰", "Продажа"),
    "invest": ("📊", "Инвестиции")
}


# ==================== ОТПРАВКА ЛИДА ====================

def send_lead_to_admin(name, phone, chat_id, state):
    """Отправляет ПОЛНЫЙ лид с сегментацией после получения телефона"""
    if not ADMIN_ID:
        logger.warning("❌ ADMIN_ID not set!")
        return
    
    goal_code = state.get('goal', '')
    emoji, goal_text = GOAL_MAP.get(goal_code, ("❓", "Неизвестно"))
    
    lines = [
        f"🔥 НОВЫЙ ЛИД | {emoji} {goal_text}",
        f"━━━━━━━━━━━━━━",
        f"👤 Имя: {name}",
        f"📞 Телефон: {phone}",
        f"🆔 ID: {chat_id}",
    ]
    
    # Добавляем сегментацию
    if goal_code == "buy":
        if state.get('budget'):
            lines.append(f"💰 Бюджет: {state['budget']}")
        if state.get('deadline'):
            lines.append(f"⏰ Срок: {state['deadline']}")
    
    elif goal_code == "sell":
        if state.get('prop_type'):
            lines.append(f"🏠 Тип: {state['prop_type']}")
        if state.get('district'):
            lines.append(f"📍 Район: {state['district']}")
    
    elif goal_code == "invest":
        if state.get('invest_budget'):
            lines.append(f"💵 Бюджет: {state['invest_budget']}")
    
    lines.append("━━━━━━━━━━━━━━")
    
    text = "\n".join(lines)
    
    try:
        send_message(ADMIN_ID, text)
        logger.info(f"📩 LEAD SENT: {goal_text} | {name} | {phone}")
    except Exception as e:
        logger.error(f"❌ Failed to send lead: {e}")


# ==================== ОБРАБОТЧИКИ ====================

def handle_start(chat_id, name, username):
    text = (
        f"🔑 Привет, {name}! Я — помощник «Тульского ключа»\n\n"
        f"Помогаю найти квартиру в Туле без стресса и переплат 🏠\n\n"
        f"🎁 Ваш подарок: чек-лист «7 ошибок при покупке жилья в Туле»\n"
        f"→ сэкономит от 100 000₽ и недели нервов"
    )
    send_message(chat_id, text, reply_markup=main_menu_kb())
    logger.info(f"📩 /start sent to {chat_id}")


def handle_callback(chat_id, callback_id, data, name, username):
    """Обработчик callback queries с сохранением в Google Sheets"""
    
    answer_callback(callback_id)
    
    # ==================== ГЛАВНОЕ МЕНЮ ====================
    if data == "get_checklist":
        text = (
            f"🎉 Готово!\n\n"
            f"📄 Чек-лист «7 ошибок при покупке»:\n{CHECKLIST_URL}\n\n"
            f"💡 Совет: сохраните ссылку в «Избранное» 📌\n\n"
            f"Чтобы я присылал только подходящие варианты, подскажите:"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🏠 Купить", "callback_data": "goal_buy"}],
                [{"text": "💰 Продать", "callback_data": "goal_sell"}],
                [{"text": "📊 Инвестировать", "callback_data": "goal_invest"}],
                [{"text": "🤔 Пока смотрю", "callback_data": "goal_browse"}]
            ]
        }
        send_message(chat_id, text, reply_markup=kb)
        logger.info(f"📥 Checklist sent to {chat_id}")
        return
    
    # ==================== ПОКУПКА ====================
    if data == "goal_buy":
        # Сохраняем цель
        save_user_state(chat_id, name, username, {'goal': 'buy'})
        
        text = f"{name}, понял! 🔑 Чтобы подборка была точной:\n\n1️⃣ Ваш бюджет?"
        send_message(chat_id, text, reply_markup=budget_kb())
        logger.info(f"💾 User {chat_id} started BUY flow")
        return
    
    if data.startswith("buy|"):
        parts = data.split("|")
        
        # buy|b3 → выбор бюджета
        if len(parts) == 2 and parts[1].startswith("b"):
            budget_code = parts[1]
            budget_text = BUDGET_MAP.get(budget_code, "")
            
            # Сохраняем бюджет
            save_user_state(chat_id, name, username, {'budget': budget_text})
            
            text = "2️⃣ Когда планируете сделку?"
            send_message(chat_id, text, reply_markup=deadline_kb(budget_code))
            return
        
        # buy|b3|urgent → выбор срока
        if len(parts) == 3:
            budget_code = parts[1]
            deadline_code = parts[2]
            budget_text = BUDGET_MAP.get(budget_code, "")
            deadline_text = DEADLINE_MAP.get(deadline_code, "")
            
            # Сохраняем срок
            save_user_state(chat_id, name, username, {'deadline': deadline_text})
            
            if deadline_code == "urgent":
                # 🔥 ГОРЯЧИЙ лид — просим телефон
                text = (
                    f"🔥 Вижу, вы ищете серьёзно!\n\n"
                    f"📞 Напишите ваш номер телефона в любом формате:\n"
                    f"• +7 999 123-45-67\n"
                    f"• 8-999-123-45-67\n"
                    f"• 9991234567\n"
                    f"Я свяжусь с вами в течение 2 часов!"
                )
                send_message(chat_id, text)
                logger.info(f"🔥 Waiting for phone: buy | {budget_text} | {deadline_text}")
            else:
                # 📅 НЕ срочно — НЕ отправляем лид
                text = (
                    f"✅ Понял, вы пока присматриваетесь!\n\n"
                    f"📄 Если еще не скачали — получите чек-лист «7 ошибок при покупке»:\n"
                    f"{CHECKLIST_URL}\n\n"
                    f"📢 Подпишитесь на канал «Тульский ключ» — там лучшие предложения:\n"
                )
                send_message(chat_id, text, reply_markup=channel_kb())
                logger.info(f"📬 Warm lead (NO LEAD): buy | {budget_text} | {deadline_text}")
            return
    
    # ==================== ПРОДАЖА ====================
    if data == "goal_sell":
        # Сохраняем цель
        save_user_state(chat_id, name, username, {'goal': 'sell'})
        
        text = f"{name}, помогу выгодно продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?"
        send_message(chat_id, text, reply_markup=property_type_kb())
        logger.info(f"💾 User {chat_id} started SELL flow")
        return
    
    if data.startswith("sell|"):
        parts = data.split("|")
        
        # sell|flat → выбор типа
        if len(parts) == 2:
            type_code = parts[1]
            type_text = TYPE_MAP.get(type_code, "")
            
            # Сохраняем тип
            save_user_state(chat_id, name, username, {'prop_type': type_text})
            
            text = "2️⃣ Район Тулы?"
            send_message(chat_id, text, reply_markup=district_kb(type_code))
            return
        
        # sell|flat|center → выбор района
        if len(parts) == 3:
            type_code = parts[1]
            district_code = parts[2]
            type_text = TYPE_MAP.get(type_code, "")
            district_text = DISTRICT_MAP.get(district_code, "")
            
            # Сохраняем район
            save_user_state(chat_id, name, username, {'district': district_text})
            
            text = (
                f"✅ Отлично! 🏡 Я подготовлю:\n"
                f"• Бесплатную оценку рыночной стоимости\n"
                f"• План продажи с прогнозом сроков\n"
                f"• Чек-лист «Как подготовить квартиру к продаже»\n\n"
                f"📞 Напишите ваш номер телефона в любом формате:\n"
                f"• +7 999 123-45-67\n"
                f"• 8-999-123-45-67\n"
                f"• 9991234567\n"
                f"Я свяжусь с вами в течение 2 часов!"
            )
            send_message(chat_id, text)
            logger.info(f"🔥 Waiting for phone: sell | {type_text} | {district_text}")
            return
    
    # ==================== ИНВЕСТИЦИИ ====================
    if data == "goal_invest":
        # Сохраняем цель
        save_user_state(chat_id, name, username, {'goal': 'invest'})
        
        text = "📊 Калькулятор инвестора в недвижимость Тулы\n\nВыберите бюджет для расчёта:"
        send_message(chat_id, text, reply_markup=invest_budget_kb())
        return
    
    if data.startswith("invest|"):
        parts = data.split("|")
        
        if len(parts) == 2:
            invest_code = parts[1]
            invest_text = INVEST_MAP.get(invest_code, "")
            
            # Сохраняем бюджет инвестиций
            save_user_state(chat_id, name, username, {'invest_budget': invest_text})
            
            calc = {
                "i2": {"price": "2 000 000", "downpayment": "400 000", "monthly": "~18 000", "rent": "~15 000", "cashflow": "-3 000", "roi": "~8%"},
                "i5": {"price": "5 000 000", "downpayment": "1 000 000", "monthly": "~45 000", "rent": "~35 000", "cashflow": "-10 000", "roi": "~10%"},
                "i5p": {"price": "8 000 000+", "downpayment": "1 600 000+", "monthly": "~72 000+", "rent": "~55 000+", "cashflow": "-17 000+", "roi": "~12%"}
            }
            c = calc.get(invest_code, calc["i2"])
            text = (
                f"📈 Результаты расчёта:\n\n"
                f"🏢 Стоимость: {c['price']} ₽\n"
                f"💰 Первоначальный взнос: {c['downpayment']} ₽\n"
                f"📉 Платёж: {c['monthly']} ₽/мес\n"
                f"💵 Аренда: {c['rent']} ₽/мес\n"
                f"📦 Чистыми: {c['cashflow']} ₽/мес\n"
                f"📈 ROI: {c['roi']}\n\n"
                f"⚠️ Это ориентировочный расчёт.\n\n"
                f"💬 Хотите обсудить стратегию? Напишите ваш номер телефона 👇"
            )
            send_message(chat_id, text)
            logger.info(f"🔥 Waiting for phone: invest | {invest_text}")
            return
    
    # ==================== FAQ И ДРУГОЕ ====================
    if data == "faq":
        text = (
            f"💬 Частые вопросы:\n\n"
            f"❓ Какая комиссия?\n"
            f"→ 2-3% от стоимости объекта, после сделки. Консультация — бесплатно 🔑\n\n"
            f"❓ Работаете с ипотекой?\n"
            f"→ Да! Со всеми банками Тулы. Есть партнёр-брокер — ставки ниже на 0.5-1% 📉\n\n"
            f"❓ Как проверить квартиру?\n"
            f"→ Проверяю юридическую чистоту, историю, обременения. Полный отчёт — перед сделкой ✅"
        )
        send_message(chat_id, text)
        return
    
    if data == "referral":
        text = (
            f"🤝 Приглашайте — получайте 15 000₽\n\n"
            f"Ваша ссылка:\n`https://t.me/tula_key_support_bot`\n\n"
            f"Отправьте другу — он получит чек-лист, а вы бонус после сделки! 💰"
        )
        send_message(chat_id, text)
        return
    
    if data == "goal_browse":
        text = (
            f"✅ Вы в списке рассылки!\n\n"
            f"📄 Пока ждёте — скачайте чек-лист «7 ошибок при покупке»:\n"
            f"{CHECKLIST_URL}\n\n"
            f"📢 Подпишитесь на канал с лучшими предложениями:\n"
        )
        send_message(chat_id, text, reply_markup=channel_kb())
        return
    
    logger.info(f"✅ Callback handled: {data}")


def handle_message(chat_id, text, name, username):
    """Обработчик текстовых сообщений (телефоны)"""
    
    if is_valid_phone(text):
        phone = normalize_phone(text)
        
        # 🔥 ЧИТАЕМ состояние из Google Sheets
        state = get_user_state(chat_id)
        
        if state:
            # Отправляем ПОЛНЫЙ лид с сегментацией
            send_lead_to_admin(name, phone, chat_id, state)
            
            # Удаляем состояние после отправки лида
            delete_user_state(chat_id)
        else:
            # Состояния нет — отправляем просто контакт
            if ADMIN_ID:
                send_message(
                    ADMIN_ID,
                    f"📞 НОВЫЙ КОНТАКТ!\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"👤 Имя: {name}\n"
                    f"📞 Телефон: {phone}\n"
                    f"🆔 ID: {chat_id}\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"⚠️ Контекст неизвестен (клиент просто написал номер)"
                )
        
        # Ответ пользователю
        send_message(
            chat_id,
            f"✅ Спасибо, {name}! 🙏\n\n"
            f"Я получил ваш номер: {phone}\n"
            f"Свяжусь с вами в течение 2 часов!\n\n"
            f"А пока — посмотрите кейс: как я сэкономил клиенту 400 000₽ 👇\n"
            f"{CHANNEL_LINK}",
        )
        logger.info(f"📞 Phone received from {chat_id}: {phone}")
    else:
        send_message(
            chat_id,
            f"👋 Привет, {name}!\n\n"
            f"Если у вас есть вопрос — напишите его, я отвечу!\n\n"
            f"Или выберите действие:",
            reply_markup=main_menu_kb()
        )


def handle_update(update_data):
    """Главный обработчик обновлений"""
    update = update_data
    
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        name = message["from"].get("first_name", "Пользователь")
        username = message["from"].get("username", "")
        text = message.get("text", "")
        
        if text == "/start":
            handle_start(chat_id, name, username)
        else:
            handle_message(chat_id, text, name, username)
    
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_id = callback["id"]
        data = callback.get("data", "")
        name = callback["from"].get("first_name", "Пользователь")
        username = callback["from"].get("username", "")
        
        handle_callback(chat_id, callback_id, data, name, username)


# ==================== РОУТЫ ====================

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("🏥 Health check requested")
    return "OK", 200


@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST']) if BOT_TOKEN else None
def webhook_handler():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set")
        return jsonify({"error": "Bot token not set"}), 500
    
    try:
        logger.info("📬 Webhook called!")
        
        update_data = request.get_json(force=True)
        logger.info(f"📩 Update received: {update_data.get('update_id')}")
        
        handle_update(update_data)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
