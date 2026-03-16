# api/vk_bot.py
# Tula Key Bot — VKontakte with Callback Buttons

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
logger.info(f"VK_ADMIN_ID: {'OK' if VK_ADMIN_ID else 'MISSING'}")
logger.info(f"CHECKLIST_URL: {'OK' if CHECKLIST_URL else 'MISSING'}")
logger.info(f"GOOGLE_SHEET_ID: {'OK' if GOOGLE_SHEET_ID else 'MISSING'}")


# ==================== HELPER FUNCTIONS ====================

def extract_budget(text):
    """Извлекает бюджет из текста: 5 млн → 5000000"""
    text = text.lower().strip()
    digits = ''.join(c for c in text if c.isdigit())
    if not digits:
        return None
    number = int(digits)
    if number >= 100000:
        return str(number)
    if 'млн' in text or 'миллион' in text:
        return str(number * 1000000)
    if 'тыс' in text or 'тысяч' in text:
        return str(number * 1000)
    if number <= 99:
        return None
    return digits


def normalize_phone(text):
    """Нормализует телефон: возвращает (phone, is_valid)"""
    cleaned = ''.join(c for c in text if c.isdigit() or c == '+')
    if len(cleaned) < 10:
        return None, False
    phone = cleaned
    if phone.startswith('+7') and len(phone) == 12:
        return phone, True
    if phone.startswith('8') and len(phone) == 11:
        return '+7' + phone[1:], True
    if phone.startswith('7') and len(phone) == 11:
        return '+' + phone, True
    if len(phone) == 10 and phone.isdigit():
        return '+7' + phone, True
    if phone.startswith('+7') and len(phone) > 12:
        phone = '+7' + ''.join(c for c in phone[2:] if c.isdigit())
        if len(phone) == 12:
            return phone, True
    return None, False


def vk_api_call(method, params):
    """Вызов VK API"""
    params.update({
        "access_token": VK_TOKEN,
        "v": "5.199",
        "group_id": VK_GROUP_ID
    })
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


def vk_get_user_name(user_id):
    """Получаем имя пользователя из VK API"""
    try:
        params = {"user_ids": user_id, "fields": "first_name"}
        result = vk_api_call("users.get", params)
        if result and len(result) > 0:
            return result[0].get("first_name", "Пользователь")
        return "Пользователь"
    except Exception as e:
        logger.error(f"Failed to get user name: {e}")
        return "Пользователь"


def vk_send_message(user_id, text, keyboard=None):
    """Отправка сообщения с опциональной клавиатурой"""
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": 0
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    result = vk_api_call("messages.send", params)
    if result:
        logger.info(f"Message sent to {user_id}")
    else:
        logger.error(f"Failed to send message to {user_id}")
    return result


def vk_edit_message(user_id, conversation_message_id, text, keyboard=None):
    """Редактирование сообщения (для callback кнопок)"""
    params = {
        "peer_id": user_id,
        "conversation_message_id": conversation_message_id,
        "message": text,
        "keep_forward_messages": 0
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    result = vk_api_call("messages.edit", params)
    if result:
        logger.info(f"Message edited for {user_id}")
    else:
        logger.error(f"Failed to edit message for {user_id}")
    return result


def send_callback_answer(event_id, user_id, event_data):
    """Ответ на нажатие callback-кнопки"""
    params = {
        "event_id": event_id,
        "user_id": user_id,
        "event_data": json.dumps(event_data)
    }
    return vk_api_call("messages.sendMessageEventAnswer", params)


# ==================== KEYBOARDS (VK CALLBACK FORMAT) ====================

def make_callback_btn(label, cmd, **extra):
    """Создаёт callback-кнопку в формате VK"""
    payload = {"cmd": cmd, **extra}
    return {
        "action": {
            "type": "callback",
            "payload": json.dumps(payload)
        },
        "label": label
    }


def make_link_btn(label, url):
    """Создаёт кнопку-ссылку"""
    return {
        "action": {
            "type": "open_link",
            "link": url
        },
        "label": label
    }


def main_menu_kb():
    """Главное меню"""
    return {
        "inline": True,
        "buttons": [
            [make_callback_btn("📥 Получить чек-лист", "get_checklist")],
            [
                make_callback_btn("🔍 Подобрать квартиру", "goal_buy"),
                make_callback_btn("💰 Продать", "goal_sell")
            ],
            [
                make_callback_btn("📊 Инвестиции", "goal_invest"),
                make_callback_btn("💬 Задать вопрос", "faq")
            ],
            [make_callback_btn("🎁 Пригласить друга", "referral")]
        ]
    }


def budget_kb():
    """Выбор бюджета"""
    return {
        "inline": True,
        "buttons": [
            [make_callback_btn("до 3 млн", "budget", value="до 3 млн")],
            [make_callback_btn("3–5 млн", "budget", value="3–5 млн")],
            [make_callback_btn("5+ млн", "budget", value="5+ млн")],
            [make_callback_btn("Нужна помощь", "budget", value="Нужна помощь")]
        ]
    }


def deadline_kb():
    """Выбор срока"""
    return {
        "inline": True,
        "buttons": [
            [make_callback_btn("🔥 Срочно", "deadline", value="🔥 Срочно")],
            [make_callback_btn("📅 1-3 месяца", "deadline", value="📅 1-3 месяца")],
            [make_callback_btn("👀 Просто смотрю", "deadline", value="👀 Просто присматриваюсь")]
        ]
    }


def property_type_kb():
    """Тип недвижимости"""
    return {
        "inline": True,
        "buttons": [
            [make_callback_btn("Квартира", "prop_type", value="Квартира")],
            [make_callback_btn("Дом", "prop_type", value="Дом")],
            [make_callback_btn("Комната", "prop_type", value="Комната")],
            [make_callback_btn("Другое", "prop_type", value="Другое")]
        ]
    }


def district_kb():
    """Район"""
    return {
        "inline": True,
        "buttons": [
            [make_callback_btn("Центральный", "district", value="Центральный")],
            [make_callback_btn("Заречье", "district", value="Заречье")],
            [make_callback_btn("Пролетарский", "district", value="Пролетарский")],
            [make_callback_btn("Любой", "district", value="Любой")]
        ]
    }


def invest_budget_kb():
    """Бюджет инвестиций"""
    return {
        "inline": True,
        "buttons": [
            [make_callback_btn("до 2 млн", "invest_budget", value="до 2 млн")],
            [make_callback_btn("2–5 млн", "invest_budget", value="2–5 млн")],
            [make_callback_btn("5+ млн", "invest_budget", value="5+ млн")]
        ]
    }


def phone_request_kb():
    """Кнопка для отправки телефона"""
    return {
        "inline": True,
        "buttons": [
            [make_link_btn("📞 Написать в ЛС", VK_GROUP_LINK)]
        ]
    }


def channel_kb():
    """Подписка на группу"""
    return {
        "inline": True,
        "buttons": [
            [make_link_btn("📢 Подписаться на группу", VK_GROUP_LINK)]
        ]
    }


# ==================== GOOGLE SHEETS ====================

def get_sheet():
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        
        if not GOOGLE_CREDS_JSON or not GOOGLE_SHEET_ID:
            logger.error("Google Sheets credentials not set")
            return None
        
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        first_row = sheet.row_values(1)
        if not first_row or first_row[0] != 'chat_id':
            headers = ['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget', 'phone', 'updated_at', 'status']
            sheet.append_row(headers)
            logger.info("Google Sheets headers created")
        
        return sheet
    except Exception as e:
        logger.error(f"Google Sheets: {e}")
        return None


def save_user_state(chat_id, name, username, data):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        all_values = sheet.get_all_values()
        last_active_row = None
        last_active_data = {}
        for i, row in enumerate(all_values[1:], 2):
            if len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    last_active_row = i
                    last_active_data = {k: row[j] if len(row) > j else '' for j, k in enumerate(['goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget'], 3)}
        merged_data = {**last_active_data, **data}
        row_data = [
            str(chat_id), name or '', username or '',
            merged_data.get('goal', ''), merged_data.get('budget', ''),
            merged_data.get('deadline', ''), merged_data.get('prop_type', ''),
            merged_data.get('district', ''), merged_data.get('invest_budget', ''),
            merged_data.get('phone', ''), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'new'
        ]
        if last_active_row:
            sheet.update(f'A{last_active_row}:L{last_active_row}', [row_data])
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
        all_values = sheet.get_all_values()
        for row in all_values[1:]:
            if len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    return {
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
        return None
    except Exception as e:
        logger.error(f"Get state error: {e}")
        return None


def mark_lead_sent(chat_id):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        all_values = sheet.get_all_values()
        for i, row in enumerate(all_values[1:], 2):
            if len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[11] if len(row) > 11 else ''
                if status == 'new':
                    sheet.update_cell(i, 12, 'sent')
                    sheet.update_cell(i, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    return True
        return False
    except Exception as e:
        logger.error(f"Mark error: {e}")
        return False


def send_lead_to_admin(name, phone, chat_id, state):
    goal_code = state.get('goal', '')
    goal_map = {'buy': ('🏠', 'Покупка'), 'sell': ('💰', 'Продажа'), 'invest': ('📊', 'Инвестиции')}
    emoji, goal_text = goal_map.get(goal_code, ('❓', 'Неизвестно'))
    lines = [f"🔥 НОВЫЙ ЛИД | {emoji} {goal_text}", "━━━━━━━━━━━━━━", f"👤 Имя: {name}", f"📞 Телефон: {phone}", f"🆔 VK: {chat_id}"]
    if goal_code == "buy":
        if state.get('budget'): lines.append(f"💰 Бюджет: {state['budget']}")
        if state.get('deadline'): lines.append(f"⏰ Срок: {state['deadline']}")
    elif goal_code == "sell":
        if state.get('prop_type'): lines.append(f"🏠 Тип: {state['prop_type']}")
        if state.get('district'): lines.append(f"📍 Район: {state['district']}")
    elif goal_code == "invest":
        if state.get('invest_budget'): lines.append(f"💵 Бюджет: {state['invest_budget']}")
    lines.append("━━━━━━━━━━━━━━")
    if VK_ADMIN_ID:
        vk_send_message(VK_ADMIN_ID, "\n".join(lines))


# ==================== HANDLERS ====================

def handle_start(user_id, name, conversation_message_id=None):
    checklist = f"📥 Скачать: {CHECKLIST_URL}" if CHECKLIST_URL else "📥 Чек-лист после консультации"
    text = f"""🔑 Привет, {name}! Я — помощник «Тульского ключа»

Помогаю найти квартиру в Туле без стресса 🏠

🎁 Подарок: чек-лист «7 ошибок при покупке»
{checklist}

📝 Выберите действие:"""
    if conversation_message_id:
        vk_edit_message(user_id, conversation_message_id, text, main_menu_kb())
    else:
        vk_send_message(user_id, text, main_menu_kb())


def handle_callback(user_id, name, payload, conversation_message_id=None):
    cmd = payload.get("cmd")
    value = payload.get("value")
    logger.info(f"Callback: cmd={cmd}, value={value}")
    
    state = get_user_state(user_id)
    
    # ✅ ПОКУПКА
    if cmd == "goal_buy" or (state and state.get('goal') == 'buy' and cmd == "budget"):
        if cmd == "goal_buy":
            save_user_state(user_id, name, '', {'goal': 'buy'})
            text = f"{name}, понял! 🔑 1️⃣ Ваш бюджет?"
            vk_send_message(user_id, text, budget_kb())
            send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Выберите бюджет 👇"})
            return
        if cmd == "budget" and value:
            save_user_state(user_id, name, '', {'budget': value})
            text = f"✅ Бюджет: {value}\n\n2️⃣ Когда планируете сделку?"
            vk_send_message(user_id, text, deadline_kb())
            send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Выберите срок 👇"})
            return
    
    # СРОК ПОКУПКИ
    if state and state.get('goal') == 'buy' and state.get('budget') and cmd == "deadline" and value:
        save_user_state(user_id, name, '', {'deadline': value})
        text = "🔥 Отлично!\n\n📞 Напишите ваш номер телефона:"
        vk_send_message(user_id, text, phone_request_kb())
        send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Ждём ваш телефон 👇"})
        return
    
    # ✅ ПРОДАЖА
    if cmd == "goal_sell" or (state and state.get('goal') == 'sell' and cmd == "prop_type"):
        if cmd == "goal_sell":
            save_user_state(user_id, name, '', {'goal': 'sell'})
            text = f"{name}, помогу продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?"
            vk_send_message(user_id, text, property_type_kb())
            send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Выберите тип 👇"})
            return
        if cmd == "prop_type" and value:
            save_user_state(user_id, name, '', {'prop_type': value})
            text = f"✅ Тип: {value}\n\n2️⃣ Район Тулы?"
            vk_send_message(user_id, text, district_kb())
            send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Выберите район 👇"})
            return
    
    # РАЙОН ПРОДАЖИ
    if state and state.get('goal') == 'sell' and state.get('prop_type') and cmd == "district" and value:
        save_user_state(user_id, name, '', {'district': value})
        text = "✅ Отлично! 🏡 Я подготовлю оценку.\n\n📞 Напишите ваш номер телефона:"
        vk_send_message(user_id, text, phone_request_kb())
        send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Ждём ваш телефон 👇"})
        return
    
    # ✅ ИНВЕСТИЦИИ
    if cmd == "goal_invest" or (state and state.get('goal') == 'invest' and cmd == "invest_budget"):
        if cmd == "goal_invest":
            save_user_state(user_id, name, '', {'goal': 'invest'})
            text = "📊 Инвестиции: выберите бюджет"
            vk_send_message(user_id, text, invest_budget_kb())
            send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Выберите бюджет 👇"})
            return
        if cmd == "invest_budget" and value:
            save_user_state(user_id, name, '', {'invest_budget': value})
            text = f"📈 Бюджет: {value}₽\n\n💬 Напишите ваш номер телефона для обсуждения:"
            vk_send_message(user_id, text, phone_request_kb())
            send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Ждём ваш телефон 👇"})
            return
    
    # ✅ ЧЕК-ЛИСТ
    if cmd == "get_checklist":
        text = f"🎉 Готово!\n\n📄 Чек-лист «7 ошибок при покупке»\n💡 {CHECKLIST_URL or 'Доступен после консультации'}"
        vk_send_message(user_id, text, channel_kb())
        send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Чек-лист отправлен 📥"})
        return
    
    # ✅ FAQ
    if cmd == "faq":
        text = """💬 Частые вопросы:

❓ Комиссия? → 2-3%, после сделки
❓ Ипотека? → Да, со всеми банками
❓ Проверка? → Юридическая чистота + отчёт"""
        vk_send_message(user_id, text, main_menu_kb())
        send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Показываю ответы 💬"})
        return
    
    # ✅ РЕФЕРАЛКА
    if cmd == "referral":
        text = f"🤝 Приглашайте — получайте 15 000₽\n\nВаша ссылка:\n{VK_GROUP_LINK}"
        vk_send_message(user_id, text, main_menu_kb())
        send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Ваша ссылка скопирована 🎁"})
        return
    
    # Fallback
    send_callback_answer(payload.get("event_id"), user_id, {"type": "show_snackbar", "text": "Команда принята ✅"})


def handle_message(user_id, name, text):
    logger.info(f"Text message: '{text}'")
    cmd = text.strip().lower()
    state = get_user_state(user_id)
    
    # ✅ ТЕЛЕФОН (любой сценарий)
    if state and state.get('goal'):
        phone, is_valid = normalize_phone(text)
        if is_valid:
            save_user_state(user_id, name, '', {'phone': phone})
            send_lead_to_admin(name, phone, user_id, state)
            mark_lead_sent(user_id)
            vk_send_message(user_id, f"✅ Спасибо, {name}! 🙏\n\nТелефон: {phone}\nСвяжусь в течение 2 часов!\n\n📢 {VK_GROUP_LINK}")
            return
    
    # ✅ КОМАНДЫ ТЕКСТОМ (для веб-версии)
    if cmd in ["начать", "старт", "/start"]:
        handle_start(user_id, name)
        return
    if cmd == "купить":
        save_user_state(user_id, name, '', {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, понял! 🔑 1️⃣ Ваш бюджет? (напишите: 5 млн или 5000000)", budget_kb())
        return
    if cmd == "продать":
        save_user_state(user_id, name, '', {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, помогу продать! 🏡 1️⃣ Тип объекта?", property_type_kb())
        return
    if cmd == "инвест":
        save_user_state(user_id, name, '', {'goal': 'invest'})
        vk_send_message(user_id, "📊 Инвестиции: выберите бюджет", invest_budget_kb())
        return
    if cmd == "помощь":
        vk_send_message(user_id, """💬 Частые вопросы:
❓ Комиссия? → 2-3%
❓ Ипотека? → Да
❓ Проверка? → Юридическая чистота""", main_menu_kb())
        return
    
    # ✅ БЮДЖЕТ ТЕКСТОМ (если в сценарии покупки)
    if state and state.get('goal') == 'buy' and not state.get('budget'):
        budget = extract_budget(text)
        if budget:
            save_user_state(user_id, name, '', {'budget': budget})
            vk_send_message(user_id, f"✅ Бюджет: {budget}₽\n\n2️⃣ Когда планируете сделку?", deadline_kb())
            return
    
    # ❌ НЕИЗВЕСТНОЕ
    vk_send_message(user_id, f"👋 {name}, выберите действие в меню:", main_menu_kb())


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
        
        # ✅ СООБЩЕНИЕ (текст)
        if event_type == "message_new":
            message = obj.get("message", {})
            user_id = message.get("from_id")
            name = message.get("from_name", "") or vk_get_user_name(user_id)
            text = message.get("text", "")
            conv_id = message.get("conversation_message_id")
            logger.info(f"Message: user={user_id}, name={name}, text='{text}'")
            if user_id:
                handle_message(user_id, name, text)
            return "ok", 200
        
        # ✅ НАЖАТИЕ КНОПКИ (callback)
        if event_type == "message_event":
            message = obj.get("message", {})
            user_id = message.get("from_id") or obj.get("user_id")
            name = message.get("from_name", "") or vk_get_user_name(user_id)
            payload = json.loads(obj.get("payload", "{}"))
            payload["event_id"] = obj.get("event_id")
            conv_id = message.get("conversation_message_id")
            logger.info(f"Callback: user={user_id}, payload={payload}")
            if user_id:
                handle_callback(user_id, name, payload, conv_id)
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
