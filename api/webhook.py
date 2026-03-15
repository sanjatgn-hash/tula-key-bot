# api/webhook.py
# Бот «Тульский ключ» — Google Sheets (ИСПРАВЛЕННАЯ ВЕРСИЯ)

import os
import re
import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "".join(os.getenv("BOT_TOKEN", "").split())
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")
CHECKLIST_URL = os.getenv("CHECKLIST_URL", "https://t.me/tula_key_bot")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/tula_key_channel")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "tula_key_channel")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logger.info(f"🔍 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
logger.info(f"🔍 GOOGLE_SHEET_ID: {'✅' if GOOGLE_SHEET_ID else '❌'}")
logger.info(f"🔍 GOOGLE_CREDS_JSON: {'✅' if GOOGLE_CREDS_JSON else '❌'}")
logger.info(f"🔍 ADMIN_ID: {'✅' if ADMIN_ID else '❌'}")


# ==================== TELEGRAM ====================

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        return requests.post(url, json=data, timeout=10).json()
    except Exception as e:
        logger.error(f"❌ send_message: {e}")
        return None


def answer_callback(callback_query_id):
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    try:
        return requests.post(url, json={"callback_query_id": callback_query_id}, timeout=10).json()
    except:
        return None

# ==================== GOOGLE SHEETS — С СОХРАНЕНИЕМ ДЛЯ АНАЛИТИКИ ====================

def get_sheet():
    """Подключение к Google Sheets — БЕЗ дублирования заголовков"""
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        
        if not GOOGLE_CREDS_JSON or not GOOGLE_SHEET_ID:
            logger.error("❌ GOOGLE_CREDS_JSON или GOOGLE_SHEET_ID не заданы!")
            return None
        
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        # Проверяем ВСЮ первую строку (не только A1!)
        try:
            first_row = sheet.row_values(1)
            logger.info(f"🔍 First row: {first_row}")
            
            # Проверяем, есть ли правильные заголовки
            if first_row and first_row[0] == 'chat_id' and first_row[1] == 'name':
                logger.info("✅ Headers already exist — skipping creation")
            else:
                # Заголовков нет или неправильные — создаём
                logger.warning("⚠️ Headers missing or wrong, creating...")
                headers = ['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget', 'phone', 'updated_at', 'status']
                
                # Очищаем первую строку если там мусор
                if first_row:
                    sheet.clear()
                
                sheet.append_row(headers)
                logger.info("✅ Headers created successfully")
                
        except Exception as e:
            logger.error(f"❌ Error checking headers: {e}")
            # Если ошибка — пробуем создать заголовки
            try:
                headers = ['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget', 'phone', 'updated_at', 'status']
                sheet.append_row(headers)
                logger.info("✅ Headers created (fallback)")
            except Exception as e2:
                logger.error(f"❌ Failed to create headers: {e2}")
        
        logger.info("✅ Google Sheets connected")
        return sheet
        
    except Exception as e:
        logger.error(f"❌ Google Sheets connection error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return None


def save_user_state(chat_id, name, username, data):
    """Сохраняет состояние — ВСЕГДА создаёт НОВУЮ строку"""
    logger.info(f"💾 Saving state for {chat_id}: {data}")
    
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        # Читаем ПОСЛЕДНЮЮ активную заявку этого пользователя (если есть)
        all_values = sheet.get_all_values()
        last_active_row = None
        last_active_data = {}
        
        # Ищем последнюю строку с status='new' для этого chat_id
        for i, row in enumerate(all_values[1:], 2):  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    last_active_row = i
                    # Сохраняем существующие данные
                    last_active_data = {
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_budget': row[8] if len(row) > 8 else '',
                    }
        
        # Объединяем существующее с новым
        merged_data = {**last_active_data, **data}
        
        row_data = [
            str(chat_id),
            name or '',
            username or '',
            merged_data.get('goal', ''),
            merged_data.get('budget', ''),
            merged_data.get('deadline', ''),
            merged_data.get('prop_type', ''),
            merged_data.get('district', ''),
            merged_data.get('invest_budget', ''),
            merged_data.get('phone', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'new'  # Статус по умолчанию
        ]
        
        if last_active_row:
            # Обновляем СУЩЕСТВУЮЩУЮ активную заявку
            sheet.update(f'A{last_active_row}:L{last_active_row}', [row_data])
            logger.info(f"✅ Updated existing row {last_active_row}")
        else:
            # Создаём НОВУЮ заявку
            sheet.append_row(row_data)
            logger.info(f"✅ Created NEW row for {chat_id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return False


def get_user_state(chat_id):
    """Читает ПОСЛЕДНЮЮ активную заявку (status='new')"""
    logger.info(f"📖 Loading state for {chat_id}")
    
    sheet = get_sheet()
    if not sheet:
        return None
    
    try:
        all_values = sheet.get_all_values()
        
        # Ищем последнюю строку с status='new' для этого chat_id
        last_state = None
        for row in all_values[1:]:  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    # Сохраняем последнюю активную заявку
                    last_state = {
                        'chat_id': row[0] if len(row) > 0 else '',
                        'name': row[1] if len(row) > 1 else '',
                        'username': row[2] if len(row) > 2 else '',
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_budget': row[8] if len(row) > 8 else '',
                        'phone': row[9] if len(row) > 9 else '',
                        'status': status,
                    }
        
        if last_state:
            logger.info(f"✅ Active state loaded: {last_state}")
            return last_state
        else:
            logger.info(f"⚠️ No active state found for {chat_id}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Get state error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return None


def mark_lead_sent(chat_id):
    """Отмечает ПОСЛЕДНЮЮ активную заявку как отправленную"""
    logger.info(f"📝 Marking lead as sent: {chat_id}")
    
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        all_values = sheet.get_all_values()
        
        # Ищем последнюю строку с status='new'
        for i, row in enumerate(all_values[1:], 2):  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    # Обновляем статус и время
                    sheet.update_cell(i, 12, 'sent')  # Колонка L = status
                    sheet.update_cell(i, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # Колонка K = updated_at
                    logger.info(f"✅ Marked row {i} as sent")
                    return True
        
        logger.warning(f"⚠️ No active lead found for {chat_id}")
        return False
    except Exception as e:
        logger.error(f"❌ Mark error: {e}")
        return False
        

def mark_lead_sent(chat_id):
    """Отмечает лид как отправленный (НЕ удаляет!)"""
    logger.info(f"📝 Marking lead as sent: {chat_id}")
    
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        all_values = sheet.get_all_values()
        
        for i, row in enumerate(all_values[1:], 2):  # Пропускаем заголовки
            if len(row) > 0 and str(row[0]) == str(chat_id):
                # Обновляем только статус (колонка L)
                sheet.update_cell(i, 12, 'sent')
                sheet.update_cell(i, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                logger.info(f"✅ Marked row {i} as sent")
                return True
        
        logger.warning(f"⚠️ No record found for {chat_id}")
        return False
    except Exception as e:
        logger.error(f"❌ Mark error: {e}")
        return False


# ==================== ТЕЛЕФОН ====================

def is_valid_phone(text):
    if not text:
        return False
    cleaned = re.sub(r'[^\d+]', '', text)
    patterns = [r'^\+7\d{10}$', r'^7\d{10}$', r'^8\d{10}$', r'^\d{10}$', r'^\d{11}$']
    return any(re.match(p, cleaned) for p in patterns)


def normalize_phone(text):
    cleaned = re.sub(r'[^\d+]', '', text)
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11:
        cleaned = '+' + cleaned
    elif len(cleaned) == 10:
        cleaned = '+7' + cleaned
    return cleaned


# ==================== КЛАВИАТУРЫ ====================

def main_menu_kb():
    return {"inline_keyboard": [
        [{"text": "📥 Получить чек-лист", "callback_data": "get_checklist"}],
        [{"text": "🔍 Подобрать квартиру", "callback_data": "goal_buy"}, {"text": "💰 Продать", "callback_data": "goal_sell"}],
        [{"text": "📊 Инвестиции", "callback_data": "goal_invest"}, {"text": "💬 Задать вопрос", "callback_data": "faq"}],
        [{"text": "🎁 Пригласить друга", "callback_data": "referral"}]
    ]}


def budget_kb():
    return {"inline_keyboard": [
        [{"text": "до 3 млн", "callback_data": "buy|b3"}],
        [{"text": "3–5 млн", "callback_data": "buy|b5"}],
        [{"text": "5+ млн", "callback_data": "buy|b5p"}],
        [{"text": "Нужна помощь", "callback_data": "buy|bhelp"}]
    ]}


def deadline_kb(budget_code):
    return {"inline_keyboard": [
        [{"text": "🔥 Срочно", "callback_data": f"buy|{budget_code}|urgent"}],
        [{"text": "📅 1-3 мес", "callback_data": f"buy|{budget_code}|month"}],
        [{"text": "👀 Просто смотрю", "callback_data": f"buy|{budget_code}|look"}]
    ]}


def property_type_kb():
    return {"inline_keyboard": [
        [{"text": "Квартира", "callback_data": "sell|flat"}],
        [{"text": "Дом", "callback_data": "sell|house"}],
        [{"text": "Комната", "callback_data": "sell|room"}],
        [{"text": "Другое", "callback_data": "sell|other"}]
    ]}


def district_kb(type_code):
    return {"inline_keyboard": [
        [{"text": "Центральный", "callback_data": f"sell|{type_code}|center"}],
        [{"text": "Заречье", "callback_data": f"sell|{type_code}|zarechye"}],
        [{"text": "Пролетарский", "callback_data": f"sell|{type_code}|proletarsky"}],
        [{"text": "Любой", "callback_data": f"sell|{type_code}|any"}]
    ]}


def invest_budget_kb():
    return {"inline_keyboard": [
        [{"text": "до 2 млн", "callback_data": "invest|i2"}],
        [{"text": "2–5 млн", "callback_data": "invest|i5"}],
        [{"text": "5+ млн", "callback_data": "invest|i5p"}]
    ]}


def channel_kb():
    return {"inline_keyboard": [[{"text": "📢 Подписаться на канал", "url": f"https://t.me/{CHANNEL_USERNAME}"}]]}


# ==================== МАППИНГИ ====================

BUDGET_MAP = {"b3": "до 3 млн", "b5": "3–5 млн", "b5p": "5+ млн", "bhelp": "Нужна помощь"}
DEADLINE_MAP = {"urgent": "🔥 Срочно", "month": "📅 1-3 месяца", "look": "👀 Пока присматриваюсь"}
TYPE_MAP = {"flat": "Квартира", "house": "Дом", "room": "Комната", "other": "Другое"}
DISTRICT_MAP = {"center": "Центральный", "zarechye": "Заречье", "proletarsky": "Пролетарский", "any": "Любой"}
INVEST_MAP = {"i2": "до 2 млн", "i5": "2–5 млн", "i5p": "5+ млн"}
GOAL_MAP = {"buy": ("🏠", "Покупка"), "sell": ("💰", "Продажа"), "invest": ("📊", "Инвестиции")}


# ==================== ЛИДЫ ====================

def send_lead_to_admin(name, phone, chat_id, state):
    if not ADMIN_ID:
        return
    
    goal_code = state.get('goal', '')
    emoji, goal_text = GOAL_MAP.get(goal_code, ("❓", "Неизвестно"))
    
    lines = [f"🔥 НОВЫЙ ЛИД | {emoji} {goal_text}", "━━━━━━━━━━━━━━", f"👤 Имя: {name}", f"📞 Телефон: {phone}", f"🆔 ID: {chat_id}"]
    
    if goal_code == "buy":
        if state.get('budget'): lines.append(f"💰 Бюджет: {state['budget']}")
        if state.get('deadline'): lines.append(f"⏰ Срок: {state['deadline']}")
    elif goal_code == "sell":
        if state.get('prop_type'): lines.append(f"🏠 Тип: {state['prop_type']}")
        if state.get('district'): lines.append(f"📍 Район: {state['district']}")
    elif goal_code == "invest":
        if state.get('invest_budget'): lines.append(f"💵 Бюджет: {state['invest_budget']}")
    
    lines.append("━━━━━━━━━━━━━━")
    send_message(ADMIN_ID, "\n".join(lines))
    logger.info(f"📩 LEAD SENT: {goal_text} | {name}")


# ==================== ОБРАБОТЧИКИ ====================

def handle_start(chat_id, name, username):
    text = f"🔑 Привет, {name}! Я — помощник «Тульского ключа»\n\nПомогаю найти квартиру в Туле без стресса 🏠\n\n🎁 Подарок: чек-лист «7 ошибок при покупке»\n→ сэкономит от 100 000₽"
    send_message(chat_id, text, reply_markup=main_menu_kb())


def handle_callback(chat_id, callback_id, data, name, username):
    answer_callback(callback_id)
    
    if data == "get_checklist":
        send_message(chat_id, f"🎉 Готово!\n\n📄 Чек-лист:\n{CHECKLIST_URL}\n\n💡 Сохраните в «Избранное» 📌", reply_markup={"inline_keyboard": [[{"text": "🏠 Купить", "callback_data": "goal_buy"}, {"text": "💰 Продать", "callback_data": "goal_sell"}], [{"text": "📊 Инвестиции", "callback_data": "goal_invest"}, {"text": "🤔 Пока смотрю", "callback_data": "goal_browse"}]]})
        return
    
    if data == "goal_buy":
        save_user_state(chat_id, name, username, {'goal': 'buy'})
        send_message(chat_id, f"{name}, понял! 🔑 1️⃣ Ваш бюджет?", reply_markup=budget_kb())
        return
    
    if data.startswith("buy|"):
        parts = data.split("|")
        if len(parts) == 2:
            budget_text = BUDGET_MAP.get(parts[1], "")
            save_user_state(chat_id, name, username, {'budget': budget_text})
            send_message(chat_id, "2️⃣ Когда планируете сделку?", reply_markup=deadline_kb(parts[1]))
        elif len(parts) == 3:
            deadline_text = DEADLINE_MAP.get(parts[2], "")
            save_user_state(chat_id, name, username, {'deadline': deadline_text})
            if parts[2] == "urgent":
                send_message(chat_id, "🔥 Вижу, вы ищете серьёзно!\n\n📞 Напишите ваш номер телефона:\n• +7 999 123-45-67\n• 8-999-123-45-67\n• 9991234567")
            else:
                send_message(chat_id, f"✅ Понял, вы пока присматриваетесь!\n\n📄 Чек-лист:\n{CHECKLIST_URL}\n\n📢 Подпишитесь на канал:", reply_markup=channel_kb())
        return
    
    if data == "goal_sell":
        save_user_state(chat_id, name, username, {'goal': 'sell'})
        send_message(chat_id, f"{name}, помогу продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?", reply_markup=property_type_kb())
        return
    
    if data.startswith("sell|"):
        parts = data.split("|")
        if len(parts) == 2:
            type_text = TYPE_MAP.get(parts[1], "")
            save_user_state(chat_id, name, username, {'prop_type': type_text})
            send_message(chat_id, "2️⃣ Район Тулы?", reply_markup=district_kb(parts[1]))
        elif len(parts) == 3:
            district_text = DISTRICT_MAP.get(parts[2], "")
            save_user_state(chat_id, name, username, {'district': district_text})
            send_message(chat_id, "✅ Отлично! 🏡 Я подготовлю оценку и план продажи.\n\n📞 Напишите ваш номер телефона:")
        return
    
    if data == "goal_invest":
        save_user_state(chat_id, name, username, {'goal': 'invest'})
        send_message(chat_id, "📊 Калькулятор инвестора\n\nВыберите бюджет:", reply_markup=invest_budget_kb())
        return
    
    if data.startswith("invest|"):
        invest_text = INVEST_MAP.get(parts[1] if len(parts) > 1 else "", "")
        save_user_state(chat_id, name, username, {'invest_budget': invest_text})
        send_message(chat_id, f"📈 Расчёт готов!\n\n💬 Хотите обсудить? Напишите ваш номер телефона 👇")
        return
    
    if data == "faq":
        send_message(chat_id, "💬 Частые вопросы:\n\n❓ Комиссия? → 2-3%, после сделки\n❓ Ипотека? → Да, со всеми банками\n❓ Проверка? → Юридическая чистота + отчёт")
        return
    
    if data == "referral":
        send_message(chat_id, f"🤝 Приглашайте — получайте 15 000₽\n\nВаша ссылка:\n`t.me/tula_key_support_bot`")
        return
    
    if data == "goal_browse":
        send_message(chat_id, f"✅ Вы в списке!\n\n📄 Чек-лист:\n{CHECKLIST_URL}\n\n📢 Канал:", reply_markup=channel_kb())


def handle_message(chat_id, text, name, username):
    """Обработчик текстовых сообщений"""
    
    if is_valid_phone(text):
        phone = normalize_phone(text)
        state = get_user_state(chat_id)
        
        if state and state.get('goal'):
            # Отправляем лид
            send_lead_to_admin(name, phone, chat_id, state)
            # Отмечаем как отправленный (НЕ удаляем!)
            mark_lead_sent(chat_id)
            logger.info(f"✅ Lead sent and marked for {chat_id}")
        elif ADMIN_ID:
            # Нет контекста — просто контакт
            send_message(
                ADMIN_ID,
                f"📞 НОВЫЙ КОНТАКТ!\n"
                f"━━━━━━━━━━━━━━\n"
                f"👤 Имя: {name}\n"
                f"📞 Телефон: {phone}\n"
                f"🆔 ID: {chat_id}\n"
                f"━━━━━━━━━━━━━━\n"
                f"⚠️ Контекст неизвестен"
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
    if "message" in update_data:
        m = update_data["message"]
        chat_id = m["chat"]["id"]
        name = m["from"].get("first_name", "Пользователь")
        username = m["from"].get("username", "")
        text = m.get("text", "")
        
        if text == "/start":
            handle_start(chat_id, name, username)
        else:
            handle_message(chat_id, text, name, username)
    
    elif "callback_query" in update_data:
        cb = update_data["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        callback_id = cb["id"]
        data = cb.get("data", "")
        name = cb["from"].get("first_name", "Пользователь")
        username = cb["from"].get("username", "")
        
        handle_callback(chat_id, callback_id, data, name, username)


# ==================== РОУТЫ ====================

@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200


@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST']) if BOT_TOKEN else None
def webhook_handler():
    try:
        logger.info("📬 Webhook called!")
        update_data = request.get_json(force=True)
        logger.info(f"📩 Update: {update_data.get('update_id')}")
        handle_update(update_data)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
