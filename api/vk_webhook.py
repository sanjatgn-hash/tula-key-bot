# api/vk_webhook.py
# Tula Key Bot — VKontakte with CALLBACK Buttons (WORKING)

import os
import json
import logging
import requests
from flask import Flask, request
from datetime import datetime

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


def vk_send_message(user_id, text, keyboard=None):
    params = {"user_id": user_id, "message": text, "random_id": 0}
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    result = vk_api_call("messages.send", params)
    logger.info(f"Message sent to {user_id}" if result else f"Failed to send to {user_id}")
    return result


def send_callback_answer(event_id, user_id, event_data):
    """Ответ на callback кнопку"""
    params = {
        "event_id": event_id,
        "user_id": user_id,
        "event_data": json.dumps(event_data)
    }
    return vk_api_call("messages.sendMessageEventAnswer", params)


# ==================== KEYBOARDS (CALLBACK TYPE - NO EMOJI IN LABEL) ====================

def main_menu_kb():
    """Главное меню — БЕЗ ЭМОДЗИ в label (VK требует!)"""
    return {
        "inline": True,
        "buttons": [
            [
                {"action": {"type": "callback", "payload": "{\"cmd\":\"buy\"}"}, "label": "Подобрать квартиру"}
            ],
            [
                {"action": {"type": "callback", "payload": "{\"cmd\":\"sell\"}"}, "label": "Продать"}
            ],
            [
                {"action": {"type": "callback", "payload": "{\"cmd\":\"invest\"}"}, "label": "Инвестиции"}
            ],
            [
                {"action": {"type": "callback", "payload": "{\"cmd\":\"help\"}"}, "label": "Помощь"}
            ]
        ]
    }


def budget_kb():
    return {
        "inline": True,
        "buttons": [
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"budget\",\"val\":\"do3\"}"}, "label": "до 3 млн"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"budget\",\"val\":\"3-5\"}"}, "label": "3-5 млн"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"budget\",\"val\":\"5plus\"}"}, "label": "5+ млн"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"budget\",\"val\":\"help\"}"}, "label": "Нужна помощь"}]
        ]
    }


def deadline_kb():
    return {
        "inline": True,
        "buttons": [
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"deadline\",\"val\":\"urgent\"}"}, "label": "Срочно"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"deadline\",\"val\":\"month\"}"}, "label": "1-3 месяца"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"deadline\",\"val\":\"looking\"}"}, "label": "Присматриваюсь"}]
        ]
    }


def property_type_kb():
    return {
        "inline": True,
        "buttons": [
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"prop_type\",\"val\":\"flat\"}"}, "label": "Квартира"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"prop_type\",\"val\":\"house\"}"}, "label": "Дом"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"prop_type\",\"val\":\"room\"}"}, "label": "Комната"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"prop_type\",\"val\":\"other\"}"}, "label": "Другое"}]
        ]
    }


def district_kb():
    return {
        "inline": True,
        "buttons": [
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"district\",\"val\":\"center\"}"}, "label": "Центральный"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"district\",\"val\":\"zarechye\"}"}, "label": "Заречье"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"district\",\"val\":\"proletarsky\"}"}, "label": "Пролетарский"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"district\",\"val\":\"any\"}"}, "label": "Любой"}]
        ]
    }


def invest_budget_kb():
    return {
        "inline": True,
        "buttons": [
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"invest_budget\",\"val\":\"do2\"}"}, "label": "до 2 млн"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"invest_budget\",\"val\":\"2-5\"}"}, "label": "2-5 млн"}],
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"invest_budget\",\"val\":\"5plus\"}"}, "label": "5+ млн"}]
        ]
    }


def back_menu_kb():
    return {
        "inline": True,
        "buttons": [
            [{"action": {"type": "callback", "payload": "{\"cmd\":\"menu\"}"}, "label": "В меню"}]
        ]
    }


# ==================== GOOGLE SHEETS ====================

def get_sheet():
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        if not GOOGLE_CREDS_JSON or not GOOGLE_SHEET_ID:
            return None
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        if not sheet.row_values(1) or sheet.row_values(1)[0] != 'chat_id':
            sheet.append_row(['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget', 'phone', 'updated_at', 'status'])
        return sheet
    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        return None


def save_user_state(chat_id, name, data):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        rows = sheet.get_all_values()
        row_idx = None
        existing_data = {}
        for i, row in enumerate(rows[1:], 2):
            if row and str(row[0]) == str(chat_id) and (len(row) > 11 and row[11] == 'new'):
                row_idx = i
                existing_data = {'goal': row[3], 'budget': row[4], 'deadline': row[5], 'prop_type': row[6], 'district': row[7], 'invest_budget': row[8]}
                break
        merged = {**existing_data, **data}
        row_data = [str(chat_id), name or '', '', merged.get('goal',''), merged.get('budget',''), merged.get('deadline',''), merged.get('prop_type',''), merged.get('district',''), merged.get('invest_budget',''), merged.get('phone',''), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'new']
        if row_idx:
            sheet.update(f'A{row_idx}:L{row_idx}', [row_data])
        else:
            sheet.append_row(row_data)
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False


def get_user_state(chat_id):
    sheet = get_sheet()
    if not sheet:
        return None
    try:
        for row in sheet.get_all_values()[1:]:
            if row and str(row[0]) == str(chat_id) and (len(row) > 11 and row[11] == 'new'):
                return {'chat_id': row[0], 'name': row[1], 'goal': row[3], 'budget': row[4], 'deadline': row[5], 'prop_type': row[6], 'district': row[7], 'invest_budget': row[8], 'phone': row[9], 'status': row[11]}
        return None
    except:
        return None


def mark_lead_sent(chat_id):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        rows = sheet.get_all_values()
        for i, row in enumerate(rows[1:], 2):
            if row and str(row[0]) == str(chat_id) and (len(row) > 11 and row[11] == 'new'):
                sheet.update_cell(i, 12, 'sent')
                sheet.update_cell(i, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                return True
        return False
    except:
        return False


def send_lead_to_admin(name, phone, user_id, state):
    goal = state.get('goal', '')
    emoji = {'buy': '🏠', 'sell': '💰', 'invest': '📊'}.get(goal, '❓')
    lines = [f"🔥 НОВЫЙ ЛИД | {emoji} {goal.upper()}", "━" * 30, f"👤 {name}", f"📞 {phone}", f"🆔 VK: {user_id}"]
    if goal == 'buy' and state.get('budget'): lines.append(f"💰 {state['budget']}")
    if goal == 'sell' and state.get('prop_type'): lines.append(f"🏠 {state['prop_type']}")
    if VK_ADMIN_ID:
        vk_send_message(VK_ADMIN_ID, "\n".join(lines))


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    text = f"""🔑 Привет, {name}! Я — помощник «Тульского ключа»

🎁 Чек-лист: {CHECKLIST_URL or 'после консультации'}

Выберите действие:"""
    vk_send_message(user_id, text, main_menu_kb())


def handle_callback(user_id, name, payload, event_id):
    cmd = payload.get("cmd")
    val = payload.get("val")
    state = get_user_state(user_id)
    
    logger.info(f"Callback: cmd={cmd}, val={val}")
    
    # Ответ VK что кнопка нажата
    send_callback_answer(event_id, user_id, {"type": "show_snackbar", "text": "Загрузка..."})
    
    if cmd == "menu":
        handle_start(user_id, name)
        return
    
    if cmd == "buy":
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, 1️⃣ Ваш бюджет?", budget_kb())
        return
    
    if cmd == "budget" and val:
        budget_map = {"do3": "до 3 млн", "3-5": "3-5 млн", "5plus": "5+ млн", "help": "Нужна помощь"}
        budget_text = budget_map.get(val, val)
        save_user_state(user_id, name, {'budget': budget_text})
        vk_send_message(user_id, f"✅ {budget_text}\n\n2️⃣ Когда планируете?", deadline_kb())
        return
    
    if cmd == "deadline" and val:
        deadline_map = {"urgent": "Срочно", "month": "1-3 месяца", "looking": "Присматриваюсь"}
        deadline_text = deadline_map.get(val, val)
        save_user_state(user_id, name, {'deadline': deadline_text})
        vk_send_message(user_id, "🔥 Отлично!\n\n📞 Напишите телефон:", back_menu_kb())
        return
    
    if cmd == "sell":
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, 1️⃣ Тип объекта?", property_type_kb())
        return
    
    if cmd == "prop_type" and val:
        prop_map = {"flat": "Квартира", "house": "Дом", "room": "Комната", "other": "Другое"}
        prop_text = prop_map.get(val, val)
        save_user_state(user_id, name, {'prop_type': prop_text})
        vk_send_message(user_id, f"✅ {prop_text}\n\n2️⃣ Район?", district_kb())
        return
    
    if cmd == "district" and val:
        district_map = {"center": "Центральный", "zarechye": "Заречье", "proletarsky": "Пролетарский", "any": "Любой"}
        district_text = district_map.get(val, val)
        save_user_state(user_id, name, {'district': district_text})
        vk_send_message(user_id, "✅ Готово!\n\n📞 Напишите телефон:", back_menu_kb())
        return
    
    if cmd == "invest":
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, "📊 Ваш бюджет?", invest_budget_kb())
        return
    
    if cmd == "invest_budget" and val:
        invest_map = {"do2": "до 2 млн", "2-5": "2-5 млн", "5plus": "5+ млн"}
        invest_text = invest_map.get(val, val)
        save_user_state(user_id, name, {'invest_budget': invest_text})
        vk_send_message(user_id, f"✅ {invest_text}\n\n📞 Напишите телефон:", back_menu_kb())
        return
    
    if cmd == "help":
        vk_send_message(user_id, """💬 Частые вопросы:
❓ Комиссия: 2-3%
❓ Ипотека: да
❓ Проверка: юридическая чистота""", main_menu_kb())
        return


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    state = get_user_state(user_id)
    
    # ТЕЛЕФОН
    if state and state.get('goal'):
        phone, valid = normalize_phone(text)
        if valid:
            save_user_state(user_id, name, {'phone': phone})
            send_lead_to_admin(name, phone, user_id, state)
            mark_lead_sent(user_id)
            vk_send_message(user_id, f"✅ Спасибо! Телефон: {phone}\nСвяжусь в течение 2 часов!", main_menu_kb())
            return
    
    # КОМАНДЫ
    if cmd in ["начать", "старт", "/start"]:
        handle_start(user_id, name)
        return
    
    # БЮДЖЕТ ТЕКСТОМ
    if state and state.get('goal') == 'buy' and not state.get('budget'):
        budget = extract_budget(text)
        if budget:
            save_user_state(user_id, name, {'budget': budget})
            vk_send_message(user_id, f"✅ {budget}₽\n\n2️⃣ Срок?", deadline_kb())
            return
    
    # СРОК ТЕКСТОМ
    if state and state.get('goal') == 'buy' and state.get('budget') and not state.get('deadline'):
        if 'срочно' in cmd:
            save_user_state(user_id, name, {'deadline': 'Срочно'})
            vk_send_message(user_id, "🔥 Принято!\n\n📞 Телефон:", back_menu_kb())
            return
        if 'месяц' in cmd:
            save_user_state(user_id, name, {'deadline': '1-3 месяца'})
            vk_send_message(user_id, "📅 Принято!\n\n📞 Телефон:", back_menu_kb())
            return
    
    vk_send_message(user_id, f"👋 {name}, выберите действие:", main_menu_kb())


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
        
        # СООБЩЕНИЕ (текст)
        if event_type == "message_new":
            msg = obj.get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name") or "Пользователь"
            text = msg.get("text", "")
            logger.info(f"Message: user={user_id}, name={name}, text='{text}'")
            if user_id:
                handle_message(user_id, name, text)
            return "ok", 200
        
        # НАЖАТИЕ КНОПКИ (callback)
        if event_type == "message_event":
            msg = obj.get("message", {})
            user_id = msg.get("from_id") or obj.get("user_id")
            name = msg.get("from_name") or "Пользователь"
            payload = json.loads(obj.get("payload", "{}"))
            event_id = obj.get("event_id")
            logger.info(f"Callback: user={user_id}, payload={payload}, event_id={event_id}")
            if user_id:
                handle_callback(user_id, name, payload, event_id)
            return "ok", 200
        
        return "ok", 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "error", 500


@app.route('/health', methods=['GET'])
def health_check():
    return "VK Bot OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
