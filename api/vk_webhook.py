# api/vk_webhook.py
# Tula Key Bot — VKontakte with Inline Buttons

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


# ==================== KEYBOARDS (VK FORMAT) ====================

def make_button(label, payload_dict):
    """Создаёт inline-кнопку в правильном формате VK"""
    return {
        "action": {
            "type": "text",
            "payload": json.dumps(payload_dict)
        },
        "label": label
    }


def main_menu_kb():
    """Главное меню"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("📥 Получить чек-лист", {"cmd": "checklist"})],
            [
                make_button("🔍 Подобрать квартиру", {"cmd": "buy"}),
                make_button("💰 Продать", {"cmd": "sell"})
            ],
            [
                make_button("📊 Инвестиции", {"cmd": "invest"}),
                make_button("💬 Помощь", {"cmd": "help"})
            ]
        ]
    }


def budget_kb():
    """Выбор бюджета"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("до 3 млн", {"cmd": "budget", "val": "до 3 млн"})],
            [make_button("3–5 млн", {"cmd": "budget", "val": "3–5 млн"})],
            [make_button("5+ млн", {"cmd": "budget", "val": "5+ млн"})],
            [make_button("Нужна помощь", {"cmd": "budget", "val": "Нужна помощь"})]
        ]
    }


def deadline_kb():
    """Выбор срока"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("🔥 Срочно", {"cmd": "deadline", "val": "🔥 Срочно"})],
            [make_button("📅 1-3 месяца", {"cmd": "deadline", "val": "📅 1-3 месяца"})],
            [make_button("👀 Присматриваюсь", {"cmd": "deadline", "val": "👀 Просто смотрю"})]
        ]
    }


def property_type_kb():
    """Тип недвижимости"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("Квартира", {"cmd": "prop_type", "val": "Квартира"})],
            [make_button("Дом", {"cmd": "prop_type", "val": "Дом"})],
            [make_button("Комната", {"cmd": "prop_type", "val": "Комната"})],
            [make_button("Другое", {"cmd": "prop_type", "val": "Другое"})]
        ]
    }


def district_kb():
    """Район"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("Центральный", {"cmd": "district", "val": "Центральный"})],
            [make_button("Заречье", {"cmd": "district", "val": "Заречье"})],
            [make_button("Пролетарский", {"cmd": "district", "val": "Пролетарский"})],
            [make_button("Любой", {"cmd": "district", "val": "Любой"})]
        ]
    }


def invest_budget_kb():
    """Бюджет инвестиций"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("до 2 млн", {"cmd": "invest_budget", "val": "до 2 млн"})],
            [make_button("2–5 млн", {"cmd": "invest_budget", "val": "2–5 млн"})],
            [make_button("5+ млн", {"cmd": "invest_budget", "val": "5+ млн"})]
        ]
    }


def back_menu_kb():
    """Кнопка назад в меню"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [make_button("🔙 В главное меню", {"cmd": "menu"})]
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

🎁 Чек-лист «7 ошибок при покупке»: {CHECKLIST_URL or 'после консультации'}

Выберите действие:"""
    vk_send_message(user_id, text, main_menu_kb())


def handle_callback(user_id, name, payload):
    cmd = payload.get("cmd")
    val = payload.get("val")
    state = get_user_state(user_id)
    
    logger.info(f"Callback: cmd={cmd}, val={val}, state={state}")
    
    # ГЛАВНОЕ МЕНЮ
    if cmd == "menu":
        handle_start(user_id, name)
        return
    
    # ЧЕК-ЛИСТ
    if cmd == "checklist":
        vk_send_message(user_id, f"📥 Чек-лист: {CHECKLIST_URL or 'доступен после консультации'}", main_menu_kb())
        return
    
    # ПОМОЩЬ
    if cmd == "help":
        vk_send_message(user_id, """💬 Частые вопросы:
❓ Комиссия: 2-3%
❓ Ипотека: да
❓ Проверка: юридическая чистота""", main_menu_kb())
        return
    
    # ПОКУПКА
    if cmd == "buy":
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, 1️⃣ Ваш бюджет?", budget_kb())
        return
    
    if cmd == "budget" and val and state and state.get('goal') == 'buy':
        save_user_state(user_id, name, {'budget': val})
        vk_send_message(user_id, f"✅ {val}\n\n2️⃣ Когда планируете?", deadline_kb())
        return
    
    if cmd == "deadline" and val and state and state.get('goal') == 'buy' and state.get('budget'):
        save_user_state(user_id, name, {'deadline': val})
        vk_send_message(user_id, "🔥 Отлично!\n\n📞 Напишите телефон:", back_menu_kb())
        return
    
    # ПРОДАЖА
    if cmd == "sell":
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, 1️⃣ Тип объекта?", property_type_kb())
        return
    
    if cmd == "prop_type" and val and state and state.get('goal') == 'sell':
        save_user_state(user_id, name, {'prop_type': val})
        vk_send_message(user_id, f"✅ {val}\n\n2️⃣ Район?", district_kb())
        return
    
    if cmd == "district" and val and state and state.get('goal') == 'sell' and state.get('prop_type'):
        save_user_state(user_id, name, {'district': val})
        vk_send_message(user_id, "✅ Готово!\n\n📞 Напишите телефон:", back_menu_kb())
        return
    
    # ИНВЕСТИЦИИ
    if cmd == "invest":
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, "📊 Ваш бюджет?", invest_budget_kb())
        return
    
    if cmd == "invest_budget" and val and state and state.get('goal') == 'invest':
        save_user_state(user_id, name, {'invest_budget': val})
        vk_send_message(user_id, f"✅ {val}\n\n📞 Напишите телефон:", back_menu_kb())
        return


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    state = get_user_state(user_id)
    
    # ТЕЛЕФОН (любой сценарий)
    if state and state.get('goal'):
        phone, valid = normalize_phone(text)
        if valid:
            save_user_state(user_id, name, {'phone': phone})
            send_lead_to_admin(name, phone, user_id, state)
            mark_lead_sent(user_id)
            vk_send_message(user_id, f"✅ Спасибо! Телефон: {phone}\nСвяжусь в течение 2 часов!", main_menu_kb())
            return
    
    # КОМАНДЫ ТЕКСТОМ
    if cmd in ["начать", "старт", "/start"]:
        handle_start(user_id, name)
        return
    
    if cmd == "купить":
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, 1️⃣ Бюджет?", budget_kb())
        return
    
    if cmd == "продать":
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, 1️⃣ Тип объекта?", property_type_kb())
        return
    
    if cmd == "инвест":
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, "📊 Бюджет?", invest_budget_kb())
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
        if any(x in cmd for x in ['срочно', 'неделю']):
            save_user_state(user_id, name, {'deadline': '🔥 Срочно'})
            vk_send_message(user_id, "🔥 Отлично!\n\n📞 Телефон:", back_menu_kb())
            return
        if any(x in cmd for x in ['месяц', '3 месяца']):
            save_user_state(user_id, name, {'deadline': '📅 1-3 месяца'})
            vk_send_message(user_id, "📅 Принято!\n\n📞 Телефон:", back_menu_kb())
            return
        if 'смотрю' in cmd:
            save_user_state(user_id, name, {'deadline': '👀 Просто смотрю'})
            vk_send_message(user_id, "👌 Понял!\n\n📞 Телефон:", back_menu_kb())
            return
    
    # ТИП ТЕКСТОМ (продажа)
    if state and state.get('goal') == 'sell' and not state.get('prop_type'):
        if 'квартира' in cmd:
            save_user_state(user_id, name, {'prop_type': 'Квартира'})
            vk_send_message(user_id, "✅ Квартира\n\n2️⃣ Район?", district_kb())
            return
        if 'дом' in cmd:
            save_user_state(user_id, name, {'prop_type': 'Дом'})
            vk_send_message(user_id, "✅ Дом\n\n2️⃣ Район?", district_kb())
            return
    
    # РАЙОН ТЕКСТОМ (продажа)
    if state and state.get('goal') == 'sell' and state.get('prop_type') and not state.get('district'):
        if any(x in cmd for x in ['центр', 'центральный']):
            save_user_state(user_id, name, {'district': 'Центральный'})
            vk_send_message(user_id, "✅ Центр\n\n📞 Телефон:", back_menu_kb())
            return
        if 'заречье' in cmd:
            save_user_state(user_id, name, {'district': 'Заречье'})
            vk_send_message(user_id, "✅ Заречье\n\n📞 Телефон:", back_menu_kb())
            return
        if 'пролетарский' in cmd:
            save_user_state(user_id, name, {'district': 'Пролетарский'})
            vk_send_message(user_id, "✅ Пролетарский\n\n📞 Телефон:", back_menu_kb())
            return
        if 'любой' in cmd:
            save_user_state(user_id, name, {'district': 'Любой'})
            vk_send_message(user_id, "✅ Любой\n\n📞 Телефон:", back_menu_kb())
            return
    
    # БЮДЖЕТ ИНВЕСТИЦИЙ ТЕКСТОМ
    if state and state.get('goal') == 'invest' and not state.get('invest_budget'):
        budget = extract_budget(text)
        if budget:
            save_user_state(user_id, name, {'invest_budget': budget})
            vk_send_message(user_id, f"✅ {budget}₽\n\n📞 Телефон:", back_menu_kb())
            return
    
    # НЕИЗВЕСТНОЕ
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
        
        if event_type == "message_new":
            msg = obj.get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name") or "Пользователь"
            text = msg.get("text", "")
            logger.info(f"Message: user={user_id}, name={name}, text='{text}'")
            if user_id:
                handle_message(user_id, name, text)
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
