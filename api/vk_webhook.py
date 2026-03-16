# api/vk_webhook.py
# Бот ВКонтакте «Тульский ключ» — С ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ

import os
import json
import logging
import requests
from flask import Flask, request
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== НАСТРОЙКИ ====================
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN", "")
VK_ADMIN_ID = os.getenv("VK_ADMIN_ID", "")
CHECKLIST_URL = os.getenv("CHECKLIST_URL", "")
VK_GROUP_LINK = os.getenv("VK_GROUP_LINK", "https://vk.com/tula_key")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "tula_key_channel")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "")

logger.info(f"🔍 VK_TOKEN: {'✅' if VK_TOKEN else '❌'}")
logger.info(f"🔍 VK_GROUP_ID: {'✅' if VK_GROUP_ID else '❌'}")
logger.info(f"🔍 VK_ADMIN_ID: {'✅' if VK_ADMIN_ID else '❌'}")
logger.info(f"🔍 GOOGLE_SHEET_ID: {'✅' if GOOGLE_SHEET_ID else '❌'}")


# ==================== VK API ====================

def vk_api_call(method, params):
    logger.debug(f"🔍 vk_api_call: method={method}, params={params}")
    params.update({
        "access_token": VK_TOKEN,
        "v": "5.199",
        "group_id": VK_GROUP_ID
    })
    try:
        resp = requests.post(f"https://api.vk.com/method/{method}", data=params, timeout=10)
        logger.debug(f"📥 VK API raw response: {resp.text}")
        
        response_json = resp.json()
        logger.debug(f"📥 VK API parsed JSON: {response_json}")
        
        # ✅ ПРОВЕРЯЕМ НА ОШИБКУ
        if "error" in response_json:
            error = response_json["error"]
            logger.error(f"❌ VK API ERROR: error_code={error.get('error_code')}, error_msg={error.get('error_msg')}")
            logger.error(f"💡 Full error: {json.dumps(error, ensure_ascii=False)}")
            return None
        
        result = response_json.get("response", {})
        logger.debug(f"✅ VK API parsed response: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ VK API exception: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return None


def vk_send_message(user_id, text, buttons=None):
    logger.info(f"📤 vk_send_message called for user_id={user_id}")
    logger.debug(f"📝 Message text: {text[:100]}...")
    
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": 0
    }
    if buttons:
        params["keyboard"] = json.dumps(buttons, ensure_ascii=False)
        logger.debug(f"🔘 Keyboard attached")
    
    logger.info(f"🔍 Calling VK API messages.send...")
    result = vk_api_call("messages.send", params)
    
    # ✅ ДОБАВЛЕНО: подробный лог результата
    if result:
        logger.info(f"✅ Message sent successfully: message_id={result}")
    else:
        logger.error(f"❌ Failed to send message - vk_api_call returned None")
        logger.error(f"💡 Check VK_TOKEN permissions and user message settings")
    
    return result

def vk_send_file(user_id, file_url, caption, buttons=None):
    logger.info(f"📤 vk_send_file called for user_id={user_id}")
    text = f"{caption}\n\n📎 Файл: {file_url}"
    return vk_send_message(user_id, text, buttons)


# ==================== GOOGLE SHEETS ====================

def get_sheet():
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        
        if not GOOGLE_CREDS_JSON or not GOOGLE_SHEET_ID:
            logger.error("❌ Google Sheets credentials not set")
            return None
        
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        first_row = sheet.row_values(1)
        if not first_row or first_row[0] != 'chat_id':
            headers = ['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_budget', 'phone', 'updated_at', 'status']
            sheet.append_row(headers)
            logger.info("✅ Google Sheets headers created")
        
        return sheet
    except Exception as e:
        logger.error(f"❌ Google Sheets: {e}")
        return None


def save_user_state(chat_id, name, username, data):
    logger.debug(f"💾 save_user_state: chat_id={chat_id}, data={data}")
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
                    last_active_data = {
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_budget': row[8] if len(row) > 8 else '',
                    }
        
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
            logger.info(f"✅ Updated row {last_active_row}")
        else:
            sheet.append_row(row_data)
            logger.info(f"✅ Created NEW row for {chat_id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
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
        logger.error(f"❌ Get state error: {e}")
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
                    logger.info(f"✅ Marked row {i} as sent")
                    return True
        return False
    except Exception as e:
        logger.error(f"❌ Mark error: {e}")
        return False


def send_lead_to_admin(name, phone, chat_id, state):
    logger.info(f"📩 send_lead_to_admin: name={name}, phone={phone}")
    goal_code = state.get('goal', '')
    goal_map = {'buy': ('🏠', 'Покупка'), 'sell': ('💰', 'Продажа'), 'invest': ('📊', 'Инвестиции')}
    emoji, goal_text = goal_map.get(goal_code, ("❓", "Неизвестно"))
    
    lines = [
        f"🔥 НОВЫЙ ЛИД | {emoji} {goal_text}",
        "━━━━━━━━━━━━━━",
        f"👤 Имя: {name}",
        f"📞 Телефон: {phone}",
        f"🆔 VK: {chat_id}"
    ]
    
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
        logger.info(f"📩 Lead notification sent to VK admin {VK_ADMIN_ID}")


# ==================== КЛАВИАТУРЫ ====================

def main_menu_kb():
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "payload": json.dumps({"btn": "get_checklist"})}, "color": "primary", "title": "📥 Получить чек-лист"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "goal_buy"})}, "color": "primary", "title": "🔍 Подобрать квартиру"},
             {"action": {"type": "text", "payload": json.dumps({"btn": "goal_sell"})}, "color": "primary", "title": "💰 Продать"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "goal_invest"})}, "color": "primary", "title": "📊 Инвестиции"},
             {"action": {"type": "text", "payload": json.dumps({"btn": "faq"})}, "color": "primary", "title": "💬 Задать вопрос"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "referral"})}, "color": "primary", "title": "🎁 Пригласить друга"}]
        ]
    }


def budget_kb():
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "payload": json.dumps({"btn": "budget_3m"})}, "color": "primary", "title": "до 3 млн"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "budget_5m"})}, "color": "primary", "title": "3–5 млн"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "budget_5plus"})}, "color": "primary", "title": "5+ млн"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "budget_help"})}, "color": "primary", "title": "Нужна помощь"}]
        ]
    }


def deadline_kb(budget_code):
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"buy|{budget_code}|urgent"})}, "color": "primary", "title": "🔥 Срочно"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"buy|{budget_code}|month"})}, "color": "primary", "title": "📅 1-3 мес"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"buy|{budget_code}|look"})}, "color": "primary", "title": "👀 Просто смотрю"}]
        ]
    }


def property_type_kb():
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "payload": json.dumps({"btn": "sell|flat"})}, "color": "primary", "title": "Квартира"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "sell|house"})}, "color": "primary", "title": "Дом"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "sell|room"})}, "color": "primary", "title": "Комната"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": "sell|other"})}, "color": "primary", "title": "Другое"}]
        ]
    }


def district_kb(type_code):
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"sell|{type_code}|center"})}, "color": "primary", "title": "Центральный"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"sell|{type_code}|zarechye"})}, "color": "primary", "title": "Заречье"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"sell|{type_code}|proletarsky"})}, "color": "primary", "title": "Пролетарский"}],
            [{"action": {"type": "text", "payload": json.dumps({"btn": f"sell|{type_code}|any"})}, "color": "primary", "title": "Любой"}]
        ]
    }


def channel_kb():
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "open_link", "link": VK_GROUP_LINK}, "color": "primary", "title": "📢 Подписаться на группу"}]
        ]
    }


# ==================== МАППИНГИ ====================

BUDGET_MAP = {"budget_3m": "до 3 млн", "budget_5m": "3–5 млн", "budget_5plus": "5+ млн", "budget_help": "Нужна помощь"}
DEADLINE_MAP = {"urgent": "🔥 Срочно", "month": "📅 1-3 месяца", "look": "👀 Пока присматриваюсь"}
TYPE_MAP = {"flat": "Квартира", "house": "Дом", "room": "Комната", "other": "Другое"}
DISTRICT_MAP = {"center": "Центральный", "zarechye": "Заречье", "proletarsky": "Пролетарский", "any": "Любой"}
INVEST_MAP = {"i2": "до 2 млн", "i5": "2–5 млн", "i5p": "5+ млн"}


# ==================== ОБРАБОТЧИКИ ====================

def handle_start(user_id, name):
    logger.info(f"🚀 handle_start called for user_id={user_id}, name={name}")
    text = f"🔑 Привет, {name}! Я — помощник «Тульского ключа»\n\nПомогаю найти квартиру в Туле без стресса 🏠\n\n🎁 Подарок: чек-лист «7 ошибок при покупке»\n→ сэкономит от 100 000₽"
    logger.info(f"📤 Sending start message to {user_id}")
    response = vk_send_message(user_id, text, main_menu_kb())
    logger.info(f"📥 handle_start complete, response: {response}")


def handle_callback(user_id, name, btn_data):
    logger.info(f"🔘 handle_callback: user_id={user_id}, btn_data={btn_data}")
    
    if btn_data == "get_checklist":
        text = f"🎉 Готово!\n\n📄 <b>Чек-лист «7 ошибок при покупке»</b>\n\n💡 <a href='{CHECKLIST_URL}'>Скачать чек-лист</a> или откройте файл выше 📌\n\nЧтобы я присылал только подходящие варианты, подскажите:"
        vk_send_file(user_id, CHECKLIST_URL, text)
        vk_send_message(user_id, "Выберите цель:", main_menu_kb())
        return
    
    if btn_data == "goal_buy":
        save_user_state(user_id, name, '', {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, понял! 🔑 1️⃣ Ваш бюджет?", budget_kb())
        return
    
    if btn_data.startswith("budget_"):
        budget_text = BUDGET_MAP.get(btn_data, "")
        save_user_state(user_id, name, '', {'budget': budget_text})
        budget_code = btn_data.replace("budget_", "b")
        if budget_code == "3m": budget_code = "b3"
        elif budget_code == "5m": budget_code = "b5"
        elif budget_code == "5plus": budget_code = "b5p"
        elif budget_code == "help": budget_code = "bhelp"
        vk_send_message(user_id, "2️⃣ Когда планируете сделку?", deadline_kb(budget_code))
        return
    
    if btn_data.startswith("buy|"):
        parts = btn_data.split("|")
        if len(parts) == 3:
            deadline_text = DEADLINE_MAP.get(parts[2], "")
            save_user_state(user_id, name, '', {'deadline': deadline_text})
            if parts[2] == "urgent":
                vk_send_message(user_id, "🔥 Вижу, вы ищете серьёзно!\n\n📞 Напишите ваш номер телефона:\n• +7 999 123-45-67\n• 8-999-123-45-67\n• 9991234567")
            else:
                vk_send_message(user_id, f"✅ Понял, вы пока присматриваетесь!\n\n📄 Чек-лист:\n{CHECKLIST_URL}\n\n📢 Подпишитесь на канал:", channel_kb())
        return
    
    if btn_data == "goal_sell":
        save_user_state(user_id, name, '', {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, помогу продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?", property_type_kb())
        return
    
    if btn_data.startswith("sell|"):
        parts = btn_data.split("|")
        if len(parts) == 2:
            type_text = TYPE_MAP.get(parts[1], "")
            save_user_state(user_id, name, '', {'prop_type': type_text})
            vk_send_message(user_id, "2️⃣ Район Тулы?", district_kb(parts[1]))
        elif len(parts) == 3:
            district_text = DISTRICT_MAP.get(parts[2], "")
            save_user_state(user_id, name, '', {'district': district_text})
            vk_send_message(user_id, "✅ Отлично! 🏡 Я подготовлю оценку и план продажи.\n\n📞 Напишите ваш номер телефона:")
        return
    
    if btn_data == "goal_invest":
        save_user_state(user_id, name, '', {'goal': 'invest'})
        invest_kb = {
            "one_time": False,
            "inline": True,
            "buttons": [
                [{"action": {"type": "text", "payload": json.dumps({"btn": "invest|i2"})}, "color": "primary", "title": "до 2 млн"}],
                [{"action": {"type": "text", "payload": json.dumps({"btn": "invest|i5"})}, "color": "primary", "title": "2–5 млн"}],
                [{"action": {"type": "text", "payload": json.dumps({"btn": "invest|i5p"})}, "color": "primary", "title": "5+ млн"}]
            ]
        }
        vk_send_message(user_id, "📊 Калькулятор инвестора\n\nВыберите бюджет:", invest_kb)
        return
    
    if btn_data.startswith("invest|"):
        invest_text = INVEST_MAP.get(btn_data.split("|")[1], "")
        save_user_state(user_id, name, '', {'invest_budget': invest_text})
        vk_send_message(user_id, f"📈 Расчёт готов!\n\n💬 Хотите обсудить? Напишите ваш номер телефона 👇")
        return
    
    if btn_data == "faq":
        vk_send_message(user_id, "💬 Частые вопросы:\n\n❓ Комиссия? → 2-3%, после сделки\n❓ Ипотека? → Да, со всеми банками\n❓ Проверка? → Юридическая чистота + отчёт")
        return
    
    if btn_data == "referral":
        vk_send_message(user_id, f"🤝 Приглашайте — получайте 15 000₽\n\nВаша ссылка:\nvk.com/ваша_группа")
        return


def handle_message(user_id, name, text):
    logger.info(f"💬 handle_message: user_id={user_id}, text='{text}'")
    
    cleaned = ''.join(c for c in text if c.isdigit() or c == '+')
    if len(cleaned) >= 10 and (cleaned.startswith('+7') or cleaned.startswith('8') or cleaned.startswith('7') or len(cleaned) == 10):
        phone = cleaned
        if phone.startswith('8') and len(phone) == 11:
            phone = '+7' + phone[1:]
        elif phone.startswith('7') and len(phone) == 11:
            phone = '+' + phone
        elif len(phone) == 10:
            phone = '+7' + phone
        
        state = get_user_state(user_id)
        if state and state.get('goal'):
            send_lead_to_admin(name, phone, user_id, state)
            mark_lead_sent(user_id)
        elif VK_ADMIN_ID:
            vk_send_message(VK_ADMIN_ID, f"📞 КОНТАКТ!\n━━━━━━━━━━━━━━\n👤 {name}\n📞 {phone}\n🆔 VK: {user_id}")
        
        vk_send_message(user_id, f"✅ Спасибо, {name}! 🙏\n\nТелефон: {phone}\nСвяжусь в течение 2 часов!")
    else:
        vk_send_message(user_id, f"👋 {name}, выберите действие в меню:", main_menu_kb())


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"📬 VK webhook: type={data.get('type', 'unknown')}")
        logger.debug(f"📋 Full webhook  {json.dumps(data, ensure_ascii=False)[:500]}")
        
        if data.get("type") == "confirmation":
            logger.info(f"✅ Confirmation requested, returning: {VK_CONFIRMATION_TOKEN}")
            return VK_CONFIRMATION_TOKEN, 200
        
        obj = data.get("object", {})
        event_type = data.get("type", "")
        
        if event_type == "message_new":
            # ✅ VK передаёт сообщение внутри object.message
            message = obj.get("message", {})
            
            user_id = message.get("from_id")
            name = message.get("from_name", "Пользователь")
            text = message.get("text", "")
            
            logger.info(f"📩 Message received: user_id={user_id}, name={name}, text='{text}'")
            logger.debug(f"🔍 Full message: {json.dumps(message, ensure_ascii=False)[:300]}")
            
            if not user_id:
                logger.error(f"❌ user_id is None! Full obj: {json.dumps(obj, ensure_ascii=False)[:500]}")
                return "ok", 200
            
            if text in ["/start", "Начать", "Старт", "начать", "старт"]:
                logger.info(f"✅ Start command matched! Calling handle_start")
                handle_start(user_id, name)
            else:
                logger.info(f"⚠️ Not a start command, calling handle_message")
                handle_message(user_id, name, text)
        
        elif event_type == "message_event":
            # ✅ Обработка нажатий кнопок
            message = obj.get("message", {})
            payload = json.loads(obj.get("payload", "{}"))
            
            btn_data = payload.get("btn", "")
            user_id = message.get("from_id") or obj.get("user_id")
            name = message.get("from_name", "Пользователь")
            
            logger.info(f"🔘 Button click: user_id={user_id}, btn_data={btn_data}")
            
            if user_id:
                handle_callback(user_id, name, btn_data)
            else:
                logger.error(f"❌ user_id is None in message_event!")
        
        return "ok", 200
    
    except Exception as e:
        logger.error(f"❌ VK webhook error: {e}")
        import traceback
        logger.error(f"💡 Traceback: {traceback.format_exc()}")
        return "error", 500


@app.route('/health', methods=['GET'])
def health_check():
    return "VK Bot OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
