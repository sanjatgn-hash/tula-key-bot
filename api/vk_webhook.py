# api/vk_webhook.py
# Tula Key Bot - VKontakte (FIXED v5)

import os
import json
import logging
import re
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
CHECKLIST_URL = os.getenv("CHECKLIST_URL", "https://t.me/tula_key_bot")
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
    """
    Извлекает бюджет из текста. Работает с форматами:
    - 5000000
    - 5 млн
    - 500 тыс
    - 5000000 руб
    - от 5 миллионов
    """
    text = text.lower().strip()
    
    # Извлекаем все цифры из текста
    digits = ''.join(c for c in text if c.isdigit())
    
    # Если есть цифры
    if digits:
        number = int(digits)
        
        # Проверяем на "млн" или "миллион"
        if 'млн' in text or 'миллион' in text:
            return str(number * 1000000)
        
        # Проверяем на "тыс" или "тысяч"
        if 'тыс' in text or 'тысяч' in text:
            return str(number * 1000)
        
        # Если число маленькое (1-99) и нет суффиксов — возможно это млн
        if number <= 99 and len(digits) <= 2:
            # Спрашиваем уточнение
            return None
        
        # Иначе возвращаем как есть
        return digits
    
    return None


def vk_api_call(method, params):
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
        params = {
            "user_ids": user_id,
            "fields": "first_name"
        }
        result = vk_api_call("users.get", params)
        if result and len(result) > 0:
            return result[0].get("first_name", "Пользователь")
        return "Пользователь"
    except Exception as e:
        logger.error(f"Failed to get user name: {e}")
        return "Пользователь"


def vk_send_message(user_id, text):
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": 0
    }
    result = vk_api_call("messages.send", params)
    if result:
        logger.info(f"Message sent to {user_id}")
    else:
        logger.error(f"Failed to send message to {user_id}")
    return result


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
            logger.info(f"Updated row {last_active_row}")
        else:
            sheet.append_row(row_data)
            logger.info(f"Created NEW row for {chat_id}")
        
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
                    logger.info(f"Marked row {i} as sent")
                    return True
        return False
    except Exception as e:
        logger.error(f"Mark error: {e}")
        return False


def send_lead_to_admin(name, phone, chat_id, state):
    goal_code = state.get('goal', '')
    goal_map = {'buy': ('🏠', 'Покупка'), 'sell': ('💰', 'Продажа'), 'invest': ('📊', 'Инвестиции')}
    emoji, goal_text = goal_map.get(goal_code, ('❓', 'Неизвестно'))
    
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
        logger.info(f"Lead notification sent to VK admin {VK_ADMIN_ID}")


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    # ✅ ПРОВЕРКА: Есть ли ссылка на чек-лист
    if not CHECKLIST_URL or CHECKLIST_URL == "https://t.me/tula_key_bot":
        checklist_text = f"📥 Чек-лист будет доступен после консультации"
    else:
        checklist_text = f"📥 Скачать: {CHECKLIST_URL}"
    
    text = f"""🔑 Привет, {name}! Я — помощник «Тульского ключа»

Помогаю найти квартиру в Туле без стресса 🏠

🎁 Подарок: чек-лист «7 ошибок при покупке»
{checklist_text}

📝 Напишите команду:
• купить — подобрать квартиру
• продать — продать недвижимость
• инвест — инвестиции
• помощь — частые вопросы
"""
    vk_send_message(user_id, text)


def handle_message(user_id, name, text):
    logger.info(f"Message: user_id={user_id}, name={name}, text='{text}'")
    
    cmd = text.strip().lower()
    
    # ✅ ПОЛУЧАЕМ ТЕКУЩЕЕ СОСТОЯНИЕ ПЕРВЫМ ДЕЛОМ
    state = get_user_state(user_id)
    
    # ============================================
    # ✅ ПРОВЕРКА: Пользователь в процессе ПОКУПКИ
    # ============================================
    if state and state.get('goal') == 'buy':
        
        # Шаг 1: Нет бюджета → извлекаем из ЛЮБОГО текста
        if not state.get('budget'):
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, '', {'budget': budget})
                vk_send_message(user_id, f"✅ Бюджет: {budget}₽ сохранён!\n\n2️⃣ Когда планируете сделку?\n\n• срочно — в течение недели\n• месяц — 1-3 месяца\n• смотрю — просто присматриваюсь")
                return
            else:
                # Если не удалось извлечь — принимаем любое число от 1 цифры
                digits = ''.join(c for c in text if c.isdigit())
                if len(digits) >= 1:
                    save_user_state(user_id, name, '', {'budget': digits})
                    vk_send_message(user_id, f"✅ Бюджет: {digits}₽ сохранён!\n\n2️⃣ Когда планируете сделку?\n\n• срочно — в течение недели\n• месяц — 1-3 месяца\n• смотрю — просто присматриваюсь")
                    return
                else:
                    vk_send_message(user_id, f"{name}, напишите бюджет (например: 5 млн, 5000000, 3000 тысяч)")
                    return
        
        # Шаг 2: Есть бюджет, нет срока → проверяем срок
        if state.get('budget') and not state.get('deadline'):
            deadline_map = {
                'срочно': '🔥 Срочно',
                'неделю': '🔥 Срочно',
                'быстро': '🔥 Срочно',
                'месяц': '📅 1-3 месяца',
                '3 месяца': '📅 1-3 месяца',
                'смотрю': '👀 Просто присматриваюсь',
                'присматриваюсь': '👀 Просто присматриваюсь',
                'думаю': '👀 Просто присматриваюсь'
            }
            deadline_text = None
            for key, value in deadline_map.items():
                if key in cmd:
                    deadline_text = value
                    break
            
            if deadline_text:
                save_user_state(user_id, name, '', {'deadline': deadline_text})
                vk_send_message(user_id, "🔥 Отлично!\n\n📞 Напишите ваш номер телефона для связи:\n\n+7 999 123-45-67\n8-999-123-45-67\n9991234567")
                return
            else:
                vk_send_message(user_id, "Напишите: срочно, месяц или смотрю")
                return
        
        # Шаг 3: Есть бюджет и срок → ждём телефон
        if state.get('budget') and state.get('deadline'):
            pass  # Проверка телефона ниже
    
    # ============================================
    # ✅ ПРОВЕРКА: Пользователь в процессе ПРОДАЖИ
    # ============================================
    if state and state.get('goal') == 'sell':
        
        # Шаг 1: Нет типа объекта
        if not state.get('prop_type'):
            prop_map = {
                'квартира': 'Квартира', 'квартиру': 'Квартира',
                'дом': 'Дом', 'дома': 'Дом',
                'комната': 'Комната', 'комнату': 'Комната',
                'гараж': 'Гараж',
                'участок': 'Участок', 'земля': 'Участок',
                'офис': 'Офис', 'помещение': 'Помещение'
            }
            prop_type = None
            for key, value in prop_map.items():
                if key in cmd:
                    prop_type = value
                    break
            
            if prop_type:
                save_user_state(user_id, name, '', {'prop_type': prop_type})
                vk_send_message(user_id, f"✅ Тип: {prop_type}\n\n2️⃣ Район Тулы?\n\n• центр — Центральный\n• заречье — Заречье\n• пролетарский — Пролетарский\n• любой — Любой район")
                return
            else:
                vk_send_message(user_id, f"{name}, напишите: квартира, дом, комната или участок")
                return
        
        # Шаг 2: Есть тип, нет района
        if state.get('prop_type') and not state.get('district'):
            district_map = {
                'центр': 'Центральный', 'центральный': 'Центральный',
                'заречье': 'Заречье',
                'пролетарский': 'Пролетарский',
                'привокзальный': 'Привокзальный',
                'любой': 'Любой', 'все равно': 'Любой'
            }
            district_text = None
            for key, value in district_map.items():
                if key in cmd:
                    district_text = value
                    break
            
            if district_text:
                save_user_state(user_id, name, '', {'district': district_text})
                vk_send_message(user_id, "✅ Отлично! 🏡 Я подготовлю оценку.\n\n📞 Напишите ваш номер телефона:")
                return
            else:
                vk_send_message(user_id, "Напишите: центр, заречье, пролетарский или любой")
                return
    
    # ============================================
    # ✅ ПРОВЕРКА: Пользователь в процессе ИНВЕСТИЦИЙ
    # ============================================
    if state and state.get('goal') == 'invest':
        
        # Шаг 1: Нет бюджета
        if not state.get('invest_budget'):
            invest_budget = extract_budget(text)
            if invest_budget:
                save_user_state(user_id, name, '', {'invest_budget': invest_budget})
                vk_send_message(user_id, f"📈 Бюджет: {invest_budget}₽\n\n💬 Хотите обсудить детали? Напишите ваш номер телефона 👇")
                return
            else:
                digits = ''.join(c for c in text if c.isdigit())
                if len(digits) >= 1:
                    save_user_state(user_id, name, '', {'invest_budget': digits})
                    vk_send_message(user_id, f"📈 Бюджет: {digits}₽\n\n💬 Хотите обсудить детали? Напишите ваш номер телефона 👇")
                    return
                else:
                    vk_send_message(user_id, "Напишите бюджет (например: 2 млн, 2000000)")
                    return
    
    # ============================================
    # ✅ ПРОВЕРКА: Новые команды (если нет активного сценария)
    # ============================================
    
    if cmd == "купить":
        save_user_state(user_id, name, '', {'goal': 'buy'})
        vk_send_message(user_id, f"{name}, понял! 🔑 1️⃣ Ваш бюджет? (напишите: 5 млн, 5000000, 3000 тысяч)")
        return
    
    if cmd == "продать":
        save_user_state(user_id, name, '', {'goal': 'sell'})
        vk_send_message(user_id, f"{name}, помогу продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта? (напишите: квартира, дом, комната)")
        return
    
    if cmd == "инвест":
        save_user_state(user_id, name, '', {'goal': 'invest'})
        vk_send_message(user_id, "📊 Инвестиции: напишите желаемый бюджет (например: 2 млн, 2000000)")
        return
    
    if cmd == "помощь":
        vk_send_message(user_id, """💬 Частые вопросы:

❓ Комиссия? → 2-3%, после сделки
❓ Ипотека? → Да, со всеми банками
❓ Проверка? → Юридическая чистота + отчёт""")
        return
    
    if cmd in ["начать", "старт", "/start", "start"]:
        handle_start(user_id, name)
        return
    
    # ============================================
    # ✅ ПРОВЕРКА ТЕЛЕФОНА
    # ============================================
    cleaned = ''.join(c for c in text if c.isdigit() or c == '+')
    
    if len(cleaned) >= 10 and state and state.get('goal'):
        phone = cleaned
        
        if phone.startswith('8') and len(phone) == 11:
            phone = '+7' + phone[1:]
        elif phone.startswith('7') and len(phone) == 11:
            phone = '+' + phone
        elif len(phone) == 10 and phone.isdigit():
            phone = '+7' + phone
        elif phone.startswith('+7') and len(phone) > 12:
            phone = '+7' + ''.join(c for c in phone[2:] if c.isdigit())
        
        if len(phone) >= 11 and phone.startswith('+'):
            if state.get('goal'):
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
            elif VK_ADMIN_ID:
                vk_send_message(VK_ADMIN_ID, f"📞 КОНТАКТ!\n━━━━━━━━━━━━━━\n👤 {name}\n📞 {phone}\n🆔 VK: {user_id}")
            
            vk_send_message(user_id, f"✅ Спасибо, {name}! 🙏\n\nТелефон: {phone}\nСвяжусь в течение 2 часов!\n\n📢 Наша группа: {VK_GROUP_LINK}")
            logger.info(f"Phone from {user_id}: {phone}")
            return
    
    # ❌ Неизвестная команда
    vk_send_message(user_id, f"👋 {name}, напишите команду:\n\n• купить\n• продать\n• инвест\n• помощь\n\nИли напишите ваш телефон для связи:")


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"VK webhook: type={data.get('type', 'unknown')}")
        
        if data.get("type") == "confirmation":
            logger.info(f"Confirmation requested, returning: {VK_CONFIRMATION_TOKEN}")
            return VK_CONFIRMATION_TOKEN, 200
        
        obj = data.get("object", {})
        event_type = data.get("type", "")
        
        if event_type == "message_new":
            message = obj.get("message", {})
            user_id = message.get("from_id")
            name = message.get("from_name", "")
            text = message.get("text", "")
            
            if not name or name == "":
                logger.info(f"Name not in message, fetching from VK API for user {user_id}")
                name = vk_get_user_name(user_id)
            
            logger.info(f"Message: user_id={user_id}, name={name}, text='{text}'")
            
            if not user_id:
                logger.error("user_id is None!")
                return "ok", 200
            
            handle_message(user_id, name, text)
        
        return "ok", 200
    
    except Exception as e:
        logger.error(f"VK webhook error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "error", 500


@app.route('/health', methods=['GET'])
def health_check():
    return "VK Bot OK v5", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
