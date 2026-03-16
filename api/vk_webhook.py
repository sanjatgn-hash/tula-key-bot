# api/vk_webhook.py
# Tula Key Bot — FIXED STATE MANAGEMENT

import os
import json
import logging
import requests
from flask import Flask, request
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== SETTINGS ====================
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN", "")
VK_ADMIN_ID = os.getenv("VK_ADMIN_ID", "")
CHECKLIST_URL = os.getenv("CHECKLIST_URL", "")
VK_GROUP_LINK = os.getenv("VK_GROUP_LINK", "https://vk.com/tula_key")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "")

logger.info(f"VK_TOKEN: {'OK' if VK_TOKEN else 'MISSING'}")
logger.info(f"VK_GROUP_ID: {'OK' if VK_GROUP_ID else 'MISSING'}")


# ==================== VK API ====================

def vk_api_call(method, params):
    params.update({"access_token": VK_TOKEN, "v": "5.199", "group_id": VK_GROUP_ID})
    try:
        resp = requests.post(f"https://api.vk.com/method/{method}", data=params, timeout=10)
        result = resp.json()
        if "error" in result:
            logger.error(f"VK API ERROR: {result['error']}")
            return None
        return result.get("response", {})
    except Exception as e:
        logger.error(f"VK API exception: {e}")
        return None


def get_random_id():
    return random.randint(0, 2000000000)


# ==================== KEYBOARD FUNCTIONS ====================

def get_button(label, payload='', color='primary'):
    return {
        'action': {
            'type': 'text',
            'payload': json.dumps(payload, ensure_ascii=False),
            'label': label
        },
        'color': color
    }


def create_keyboard(one_time=False, buttons=None):
    if buttons is None:
        buttons = []
    keyboard = {'one_time': one_time, 'buttons': buttons}
    return json.dumps(keyboard, ensure_ascii=False)


def main_menu_keyboard():
    buttons = [
        [get_button('🔍 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('💰 Продать', {'cmd': 'sell'}, 'primary')],
        [get_button('📊 Инвестиции', {'cmd': 'invest'}, 'primary')],
        [get_button('💬 Помощь', {'cmd': 'help'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def budget_keyboard():
    buttons = [
        [get_button('до 3 млн', {'cmd': 'budget', 'val': 'до 3 млн'}, 'primary')],
        [get_button('3-5 млн', {'cmd': 'budget', 'val': '3-5 млн'}, 'primary')],
        [get_button('5+ млн', {'cmd': 'budget', 'val': '5+ млн'}, 'primary')],
        [get_button('Нужна помощь', {'cmd': 'budget', 'val': 'help'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def deadline_keyboard():
    buttons = [
        [get_button('🔥 Срочно', {'cmd': 'deadline', 'val': 'Срочно'}, 'primary')],
        [get_button('📅 1-3 месяца', {'cmd': 'deadline', 'val': '1-3 месяца'}, 'primary')],
        [get_button('👀 Присматриваюсь', {'cmd': 'deadline', 'val': 'Присматриваюсь'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def property_type_keyboard():
    buttons = [
        [get_button('Квартира', {'cmd': 'prop_type', 'val': 'Квартира'}, 'primary')],
        [get_button('Дом', {'cmd': 'prop_type', 'val': 'Дом'}, 'primary')],
        [get_button('Комната', {'cmd': 'prop_type', 'val': 'Комната'}, 'primary')],
        [get_button('Другое', {'cmd': 'prop_type', 'val': 'Другое'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def district_keyboard():
    buttons = [
        [get_button('Центральный', {'cmd': 'district', 'val': 'Центральный'}, 'primary')],
        [get_button('Заречье', {'cmd': 'district', 'val': 'Заречье'}, 'primary')],
        [get_button('Пролетарский', {'cmd': 'district', 'val': 'Пролетарский'}, 'primary')],
        [get_button('Любой', {'cmd': 'district', 'val': 'Любой'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def invest_budget_keyboard():
    buttons = [
        [get_button('до 2 млн', {'cmd': 'invest_budget', 'val': 'до 2 млн'}, 'primary')],
        [get_button('2-5 млн', {'cmd': 'invest_budget', 'val': '2-5 млн'}, 'primary')],
        [get_button('5+ млн', {'cmd': 'invest_budget', 'val': '5+ млн'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def back_menu_keyboard():
    buttons = [
        [get_button('🔙 В главное меню', {'cmd': 'menu'}, 'secondary')]
    ]
    return create_keyboard(one_time=True, buttons=buttons)


def vk_send_message(user_id, text, keyboard=None):
    params = {"user_id": user_id, "message": text, "random_id": get_random_id()}
    if keyboard:
        params["keyboard"] = keyboard
        logger.info(f"Keyboard: {keyboard[:150]}")
    result = vk_api_call("messages.send", params)
    logger.info(f"Sent to {user_id}" if result else f"Failed {user_id}")
    return result


# ==================== HELPER FUNCTIONS ====================

def extract_budget(text):
    text = text.lower().strip()
    digits = ''.join(c for c in text if c.isdigit())
    if not digits:
        return None
    number = int(digits)
    if number >= 100000:
        return str(number)
    if 'млн' in text:
        return str(number * 1000000)
    if 'тыс' in text:
        return str(number * 1000)
    return digits if number > 99 else None


def normalize_phone(text):
    cleaned = ''.join(c for c in text if c.isdigit() or c == '+')
    if len(cleaned) < 10:
        return None, False
    if cleaned.startswith('8') and len(cleaned) == 11:
        return '+7' + cleaned[1:], True
    if cleaned.startswith('7') and len(cleaned) == 11:
        return '+' + cleaned, True
    if len(cleaned) == 10:
        return '+7' + cleaned, True
    if cleaned.startswith('+7') and len(cleaned) == 12:
        return cleaned, True
    return None, False


# ==================== GOOGLE SHEETS ====================

def get_sheet():
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        if not GOOGLE_CREDS_JSON or not GOOGLE_SHEET_ID:
            logger.error("Google Sheets credentials not set")
            return None
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        first_row = sheet.row_values(1)
        if not first_row or first_row[0] != 'chat_id':
            sheet.append_row(['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget', 'phone', 'updated_at', 'status'])
            logger.info("Created Google Sheets headers")
        return sheet
    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        return None


def save_user_state(chat_id, name, data):
    """Сохраняет состояние пользователя"""
    sheet = get_sheet()
    if not sheet:
        logger.error("Sheet is None")
        return False
    
    try:
        rows = sheet.get_all_values()
        logger.info(f"Total rows in sheet: {len(rows)}")
        
        # Ищем существующую запись
        row_idx = None
        existing_data = {}
        
        for i, row in enumerate(rows[1:], 2):  # Пропускаем заголовок
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                logger.info(f"Found user {chat_id} at row {i}, status: {status}")
                if status == 'new':
                    row_idx = i
                    # Извлекаем существующие данные
                    existing_data = {
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_budget': row[8] if len(row) > 8 else '',
                    }
                    logger.info(f"Existing data: {existing_data}")
                    break
        
        # Объединяем данные
        merged = {**existing_data, **data}
        logger.info(f"Merged data: {merged}")
        
        # Создаём строку данных
        row_data = [
            str(chat_id),
            name or '',
            '',  # username
            merged.get('goal', ''),
            merged.get('budget', ''),
            merged.get('deadline', ''),
            merged.get('prop_type', ''),
            merged.get('district', ''),
            merged.get('invest_budget', ''),
            merged.get('phone', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'new'
        ]
        
        # Обновляем или создаём
        if row_idx:
            sheet.update(f'A{row_idx}:L{row_idx}', [row_data])
            logger.info(f"Updated row {row_idx}")
        else:
            sheet.append_row(row_data)
            logger.info(f"Created new row for {chat_id}")
        
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_user_state(chat_id):
    """Получает состояние пользователя"""
    sheet = get_sheet()
    if not sheet:
        logger.error("Sheet is None in get_user_state")
        return None
    
    try:
        rows = sheet.get_all_values()
        logger.info(f"get_user_state: {len(rows)} rows total")
        
        for row in rows[1:]:  # Пропускаем заголовок
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    state = {
                        'chat_id': row[0] if len(row) > 0 else '',
                        'name': row[1] if len(row) > 1 else '',
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_budget': row[8] if len(row) > 8 else '',
                        'phone': row[9] if len(row) > 9 else '',
                        'status': status,
                    }
                    logger.info(f"Found state for {chat_id}: {state}")
                    return state
        
        logger.info(f"No state found for {chat_id}")
        return None
    except Exception as e:
        logger.error(f"Get state error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def mark_lead_sent(chat_id):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        rows = sheet.get_all_values()
        for i, row in enumerate(rows[1:], 2):
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    sheet.update_cell(i, 12, 'sent')
                    sheet.update_cell(i, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    logger.info(f"Marked {chat_id} as sent")
                    return True
        return False
    except Exception as e:
        logger.error(f"Mark error: {e}")
        return False


def send_lead_to_admin(name, phone, user_id, state):
    goal = state.get('goal', '')
    emoji = {'buy': '🏠', 'sell': '💰', 'invest': '📊'}.get(goal, '❓')
    lines = [f"🔥 НОВЫЙ ЛИД | {emoji} {goal.upper()}", "━" * 30, f"👤 {name}", f"📞 {phone}", f"🆔 VK: {user_id}"]
    if goal == 'buy' and state.get('budget'):
        lines.append(f"💰 Бюджет: {state['budget']}")
    if goal == 'sell' and state.get('prop_type'):
        lines.append(f"🏠 Тип: {state['prop_type']}")
    if VK_ADMIN_ID:
        vk_send_message(VK_ADMIN_ID, "\n".join(lines))


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    # Очищаем старое состояние при новом старте
    save_user_state(user_id, name, {'goal': '', 'budget': '', 'deadline': '', 'prop_type': '', 'district': '', 'invest_budget': '', 'phone': ''})
    
    text = f"""🔑 Привет, {name}! Я — помощник «Тульского ключа»

Помогаю найти квартиру в Туле без стресса 🏠

🎁 Чек-лист: {CHECKLIST_URL or 'после консультации'}

Выберите действие:"""
    vk_send_message(user_id, text, main_menu_keyboard())


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    
    # ✅ ВАЖНО: Получаем состояние КАЖДЫЙ РАЗ
    state = get_user_state(user_id)
    
    logger.info(f"=== MESSAGE START ===")
    logger.info(f"User: {name}, Text: '{text}'")
    logger.info(f"Current state: {state}")
    
    # ============================================
    # ✅ ТЕЛЕФОН (любой сценарий)
    # ============================================
    if state and state.get('goal') and not state.get('phone'):
        phone, valid = normalize_phone(text)
        if valid:
            save_user_state(user_id, name, {'phone': phone})
            send_lead_to_admin(name, phone, user_id, state)
            mark_lead_sent(user_id)
            vk_send_message(user_id, f"✅ Спасибо, {name}! 🙏\n\nТелефон: {phone}\nСвяжусь в течение 2 часов!", main_menu_keyboard())
            logger.info(f"Phone saved: {phone}")
            return
        else:
            # ❌ Неверный телефон — просим ещё раз, НЕ сбрасываем!
            vk_send_message(user_id, f"⚠️ {name}, это не похоже на номер телефона.\n\nПожалуйста, попробуйте ещё раз:\n+7 999 123-45-67", back_menu_keyboard())
            logger.info("Invalid phone, asking again")
            return
    
    # ============================================
    # ✅ КНОПКИ ГЛАВНОГО МЕНЮ
    # ============================================
    if cmd in ["купить", "подобрать квартиру", "🔍 подобрать квартиру"]:
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, понял! 🔑\n\n1️⃣ Ваш бюджет?", budget_keyboard())
        return
    
    if cmd in ["продать", "💰 продать"]:
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, помогу продать! 🏡\n\n1️⃣ Тип объекта?", property_type_keyboard())
        return
    
    if cmd in ["инвест", "инвестиции", "📊 инвестиции"]:
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, "📊 Инвестиции:\n\nВаш бюджет?", invest_budget_keyboard())
        return
    
    if cmd in ["помощь", "💬 помощь"]:
        vk_send_message(user_id, """💬 Частые вопросы:

❓ Комиссия? → 2-3%, после сделки
❓ Ипотека? → Да, со всеми банками
❓ Проверка? → Юридическая чистота + отчёт""", main_menu_keyboard())
        return
    
    if cmd in ["начать", "старт", "/start", "меню", "🔙 в главное меню"]:
        handle_start(user_id, name)
        return
    
    # ============================================
    # ✅ СЦЕНАРИЙ ПОКУПКИ
    # ============================================
    if state and state.get('goal') == 'buy':
        logger.info(f"In BUY scenario, budget={state.get('budget')}, deadline={state.get('deadline')}")
        
        # Шаг 1: Нет бюджета
        if not state.get('budget'):
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'budget': budget})
                vk_send_message(user_id, f"✅ Бюджет: {budget}₽\n\n2️⃣ Когда планируете?", deadline_keyboard())
                logger.info(f"Budget saved: {budget}")
                return
            else:
                vk_send_message(user_id, f"{name}, напишите бюджет цифрами (например: 5000000 или 5 млн)", budget_keyboard())
                logger.info("Invalid budget, asking again")
                return
        
        # Шаг 2: Есть бюджет, нет срока
        if state.get('budget') and not state.get('deadline'):
            if 'срочно' in cmd or 'неделю' in cmd:
                save_user_state(user_id, name, {'deadline': 'Срочно'})
                vk_send_message(user_id, "🔥 Отлично!\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            if 'месяц' in cmd or '3 месяца' in cmd:
                save_user_state(user_id, name, {'deadline': '1-3 месяца'})
                vk_send_message(user_id, "📅 Принято!\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            if 'смотр' in cmd or 'присматриваюсь' in cmd:
                save_user_state(user_id, name, {'deadline': 'Присматриваюсь'})
                vk_send_message(user_id, "👌 Понял!\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            else:
                vk_send_message(user_id, "Напишите: срочно, месяц или смотрю", deadline_keyboard())
                logger.info("Invalid deadline, asking again")
                return
    
    # ============================================
    # ✅ СЦЕНАРИЙ ПРОДАЖИ
    # ============================================
    if state and state.get('goal') == 'sell':
        logger.info(f"In SELL scenario, prop_type={state.get('prop_type')}, district={state.get('district')}")
        
        # Шаг 1: Нет типа
        if not state.get('prop_type'):
            if 'квартира' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Квартира'})
                vk_send_message(user_id, "✅ Квартира\n\n2️⃣ Район?", district_keyboard())
                return
            if 'дом' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Дом'})
                vk_send_message(user_id, "✅ Дом\n\n2️⃣ Район?", district_keyboard())
                return
            if 'комната' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Комната'})
                vk_send_message(user_id, "✅ Комната\n\n2️⃣ Район?", district_keyboard())
                return
            if 'другое' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Другое'})
                vk_send_message(user_id, "✅ Другое\n\n2️⃣ Район?", district_keyboard())
                return
            else:
                vk_send_message(user_id, f"{name}, напишите: квартира, дом, комната или другое", property_type_keyboard())
                logger.info("Invalid prop_type, asking again")
                return
        
        # Шаг 2: Есть тип, нет района
        if state.get('prop_type') and not state.get('district'):
            if 'центр' in cmd:
                save_user_state(user_id, name, {'district': 'Центральный'})
                vk_send_message(user_id, "✅ Центр\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            if 'заречье' in cmd:
                save_user_state(user_id, name, {'district': 'Заречье'})
                vk_send_message(user_id, "✅ Заречье\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            if 'пролетарский' in cmd:
                save_user_state(user_id, name, {'district': 'Пролетарский'})
                vk_send_message(user_id, "✅ Пролетарский\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            if 'любой' in cmd:
                save_user_state(user_id, name, {'district': 'Любой'})
                vk_send_message(user_id, "✅ Любой\n\n📞 Напишите телефон:", back_menu_keyboard())
                return
            else:
                vk_send_message(user_id, "Напишите: центр, заречье, пролетарский или любой", district_keyboard())
                logger.info("Invalid district, asking again")
                return
    
    # ============================================
    # ✅ СЦЕНАРИЙ ИНВЕСТИЦИЙ
    # ============================================
    if state and state.get('goal') == 'invest':
        logger.info(f"In INVEST scenario, invest_budget={state.get('invest_budget')}")
        
        if not state.get('invest_budget'):
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'invest_budget': budget})
                vk_send_message(user_id, f"📈 Бюджет: {budget}₽\n\n💬 Напишите телефон:", back_menu_keyboard())
                logger.info(f"Invest budget saved: {budget}")
                return
            else:
                vk_send_message(user_id, "Напишите бюджет (например: 2000000 или 2 млн)", invest_budget_keyboard())
                logger.info("Invalid invest budget, asking again")
                return
    
    # ============================================
    # ❌ НЕИЗВЕСТНОЕ — показываем меню
    # ============================================
    vk_send_message(user_id, f"👋 {name}, выберите действие:", main_menu_keyboard())
    logger.info("Unknown command, showing menu")
    logger.info(f"=== MESSAGE END ===")


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"VK webhook: type={data.get('type')}")
        
        if data.get("type") == "confirmation":
            return VK_CONFIRMATION_TOKEN, 200
        
        obj = data.get("object", {})
        event_type = data.get("type")
        
        if event_type == "message_new":
            msg = obj.get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name", "Пользователь")
            text = msg.get("text", "")
            logger.info(f"Message: {user_id}, {name}, '{text}'")
            if user_id:
                handle_message(user_id, name, text)
            return "ok", 200
        
        return "ok", 200
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "error", 500


@app.route('/health')
def health():
    return "VK Bot OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
