# api/vk_webhook.py
# Tula Key Bot — FIXED open_link buttons

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


def vk_get_user_name(user_id):
    try:
        params = {"user_ids": user_id, "fields": "first_name"}
        result = vk_api_call("users.get", params)
        if result and len(result) > 0:
            return result[0].get("first_name", "друг")
        return "друг"
    except Exception as e:
        logger.error(f"Failed to get user name: {e}")
        return "друг"


def get_random_id():
    return random.randint(0, 2000000000)


# ==================== KEYBOARD FUNCTIONS ====================

def get_button(label, payload='', color='primary'):
    """Обычная текстовая кнопка"""
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
    """Главное меню — ИСПРАВЛЕНО"""
    buttons = [
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('💰 Продать квартиру', {'cmd': 'sell'}, 'primary')],
        [get_button('📥 Получить чек-лист', {'cmd': 'checklist'}, 'secondary')],
        [get_button('📊 Инвестиции', {'cmd': 'invest'}, 'secondary')],
        [get_button('💬 Помощь и вопросы', {'cmd': 'help'}, 'secondary')],
        # ✅ Правильный open_link:
        [{
            "action": {
                "type": "open_link",
                "link": VK_GROUP_LINK.strip(),
                "label": "📢 Наш канал"
            }
        }]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def budget_keyboard():
    buttons = [
        [get_button('до 2 млн', {'cmd': 'budget', 'val': 'до 2 млн'}, 'secondary')],
        [get_button('2-3 млн', {'cmd': 'budget', 'val': '2-3 млн'}, 'primary')],
        [get_button('3-5 млн', {'cmd': 'budget', 'val': '3-5 млн'}, 'primary')],
        [get_button('5+ млн', {'cmd': 'budget', 'val': '5+ млн'}, 'primary')],
        [get_button('Нужна консультация', {'cmd': 'budget', 'val': 'Консультация'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def deadline_keyboard():
    buttons = [
        [get_button('🔥 Срочно (до недели)', {'cmd': 'deadline', 'val': 'Срочно'}, 'primary')],
        [get_button('📅 1-3 месяца', {'cmd': 'deadline', 'val': '1-3 месяца'}, 'primary')],
        [get_button('📅 3-6 месяцев', {'cmd': 'deadline', 'val': '3-6 месяцев'}, 'secondary')],
        [get_button('👀 Просто смотрю', {'cmd': 'deadline', 'val': 'Присматриваюсь'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def property_type_keyboard():
    buttons = [
        [get_button('🏢 Квартира', {'cmd': 'prop_type', 'val': 'Квартира'}, 'primary')],
        [get_button('🏡 Дом / Коттедж', {'cmd': 'prop_type', 'val': 'Дом'}, 'primary')],
        [get_button('🚪 Комната', {'cmd': 'prop_type', 'val': 'Комната'}, 'secondary')],
        [get_button('🏗️ Другое', {'cmd': 'prop_type', 'val': 'Другое'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def district_keyboard():
    buttons = [
        [get_button('🏛️ Центральный', {'cmd': 'district', 'val': 'Центральный'}, 'primary')],
        [get_button('🌳 Зареченский', {'cmd': 'district', 'val': 'Зареченский'}, 'primary')],
        [get_button('🏭 Пролетарский', {'cmd': 'district', 'val': 'Пролетарский'}, 'primary')],
        [get_button('🚉 Привокзальный', {'cmd': 'district', 'val': 'Привокзальный'}, 'secondary')],
        [get_button('🏘️ Советский', {'cmd': 'district', 'val': 'Советский'}, 'secondary')],
        [get_button('📍 Любой район', {'cmd': 'district', 'val': 'Любой'}, 'secondary')],
        [get_button('🌾 Тульская область', {'cmd': 'district', 'val': 'Область'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def invest_goal_keyboard():
    buttons = [
        [get_button('💵 Перепродажа', {'cmd': 'invest_goal', 'val': 'Перепродажа'}, 'primary')],
        [get_button('🏠 Аренда', {'cmd': 'invest_goal', 'val': 'Аренда'}, 'primary')],
        [get_button('📈 Долгосрок', {'cmd': 'invest_goal', 'val': 'Долгосрок'}, 'secondary')],
        [get_button('❓ Консультация', {'cmd': 'invest_goal', 'val': 'Консультация'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def invest_budget_keyboard():
    buttons = [
        [get_button('до 2 млн', {'cmd': 'invest_budget', 'val': 'до 2 млн'}, 'secondary')],
        [get_button('2-5 млн', {'cmd': 'invest_budget', 'val': '2-5 млн'}, 'primary')],
        [get_button('5-10 млн', {'cmd': 'invest_budget', 'val': '5-10 млн'}, 'primary')],
        [get_button('10+ млн', {'cmd': 'invest_budget', 'val': '10+ млн'}, 'primary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def phone_keyboard():
    return create_keyboard(one_time=True, buttons=[
        [get_button('🔙 В главное меню', {'cmd': 'menu'}, 'secondary')]
    ])


def checklist_keyboard():
    return create_keyboard(one_time=False, buttons=[
        # ✅ Правильный open_link:
        [{
            "action": {
                "type": "open_link",
                "link": (CHECKLIST_URL or VK_GROUP_LINK).strip(),
                "label": "📥 Скачать чек-лист"
            }
        }],
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ])


def help_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('❓ Как работает бот?', {'cmd': 'faq_bot'}, 'secondary')],
        [get_button('💰 Условия работы', {'cmd': 'faq_conditions'}, 'secondary')],
        [get_button('🏠 Как подобрать?', {'cmd': 'faq_buy'}, 'secondary')],
        [get_button('💰 Как продать?', {'cmd': 'faq_sell'}, 'secondary')],
        # ✅ Правильный open_link для связи:
        [{
            "action": {
                "type": "open_link",
                "link": f'https://vk.com/im?sel={VK_ADMIN_ID}'.strip() if VK_ADMIN_ID else VK_GROUP_LINK,
                "label": "✍️ Написать мне лично"
            }
        }],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ])


def vk_send_message(user_id, text, keyboard=None):
    params = {"user_id": user_id, "message": text, "random_id": get_random_id()}
    if keyboard:
        params["keyboard"] = keyboard
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
            sheet.append_row(['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_goal', 'invest_budget', 'phone', 'updated_at', 'status'])
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
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[12] if len(row) > 12 else ''
                if status == 'new':
                    row_idx = i
                    existing_data = {k: row[j] if len(row) > j else '' for j, k in enumerate(['goal','budget','deadline','prop_type','district','invest_goal','invest_budget'], 3)}
                    break
        merged = {**existing_data, **data}
        row_data = [str(chat_id), name or '', '', merged.get('goal',''), merged.get('budget',''), merged.get('deadline',''), merged.get('prop_type',''), merged.get('district',''), merged.get('invest_goal',''), merged.get('invest_budget',''), merged.get('phone',''), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'new']
        if row_idx:
            sheet.update(f'A{row_idx}:M{row_idx}', [row_data])
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
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[12] if len(row) > 12 else ''
                if status == 'new':
                    return {k: row[j] if len(row) > j else '' for j, k in enumerate(['chat_id','name','goal','budget','deadline','prop_type','district','invest_goal','invest_budget','phone','status'], 0)}
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
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[12] if len(row) > 12 else ''
                if status == 'new':
                    sheet.update_cell(i, 13, 'sent')
                    sheet.update_cell(i, 12, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    return True
        return False
    except:
        return False


def send_lead_to_admin(name, phone, user_id, state):
    goal = state.get('goal', '')
    emoji = {'buy': '🏠', 'sell': '💰', 'invest': '📊'}.get(goal, '❓')
    lines = [f"🔥 НОВЫЙ ЛИД | {emoji} {goal.upper()}", "━"*30, f"👤 {name}", f"📞 {phone}", f"🆔 VK: {user_id}"]
    if goal == 'buy':
        if state.get('budget'): lines.append(f"💰 Бюджет: {state['budget']}")
        if state.get('deadline'): lines.append(f"⏰ Срок: {state['deadline']}")
        if state.get('district'): lines.append(f"📍 Район: {state['district']}")
    elif goal == 'sell':
        if state.get('prop_type'): lines.append(f"🏠 Тип: {state['prop_type']}")
        if state.get('district'): lines.append(f"📍 Район: {state['district']}")
    elif goal == 'invest':
        if state.get('invest_goal'): lines.append(f"🎯 Цель: {state['invest_goal']}")
        if state.get('invest_budget'): lines.append(f"💵 Бюджет: {state['invest_budget']}")
    lines.append("━"*30)
    if VK_ADMIN_ID:
        vk_send_message(VK_ADMIN_ID, "\n".join(lines))


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    save_user_state(user_id, name, {'goal':'','budget':'','deadline':'','prop_type':'','district':'','invest_goal':'','invest_budget':'','phone':''})
    text = f"""✨ {name}, добро пожаловать в «Тульский ключ»!

Я здесь, чтобы исполнить ваше желание по недвижимости — без стресса и переплат.

🎁 **Ваш бонус:** Чек-лист «7 ошибок при покупке» — бесплатно!

🏠 **Что я умею:**
• Подобрать квартиру под ваш бюджет
• Помочь выгодно продать
• Подобрать объект для инвестиций

Выберите 👇"""
    vk_send_message(user_id, text, main_menu_keyboard())


def handle_checklist(user_id, name):
    text = f"""🎉 {name}, ваш чек-лист готов!

📄 «7 фатальных ошибок при покупке квартиры»

Этот чек-лист уже сэкономил моим клиентам более 2 млн ₽.

👇 **Скачивайте по кнопке!**"""
    vk_send_message(user_id, text, checklist_keyboard())


def handle_help(user_id, name):
    text = f"""💬 {name}, я с радостью помогу!

**Частые вопросы:**

❓ **Как работает бот?**
Просто отвечайте на вопросы — я подберу варианты.

❓ **Условия работы?**
Комиссия 2-3% только после сделки. Никаких предоплат.

❓ **Как подобрать/продать?**
Нажмите соответствующую кнопку в меню 👇

❓ **Личный вопрос?**
Кнопка «Написать мне лично» ниже 👇"""
    vk_send_message(user_id, text, help_keyboard())


def handle_faq(user_id, name, topic):
    faqs = {
        'faq_bot': "🤖 **Как работает бот?**\n1. Выберите цель\n2. Ответьте на вопросы\n3. Оставьте телефон\n4. Я свяжусь в течение 2 часов",
        'faq_conditions': "💰 **Условия:**\n• Комиссия: 2-3%\n• Оплата: после сделки\n• Сопровождение: полное",
        'faq_buy': "🏠 **Подбор:**\n1. Бюджет → 2. Район → 3. Телефон → 4. Показ вариантов (7-14 дней)",
        'faq_sell': "💰 **Продажа:**\n1. Оценка → 2. Фото → 3. Размещение → 4. Показы → 5. Сделка (2-4 недели)"
    }
    vk_send_message(user_id, faqs.get(topic, "Вопрос не найден."), help_keyboard())


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    if not name or name == "Пользователь":
        name = vk_get_user_name(user_id)
    state = get_user_state(user_id)
    
    # ГЛАВНОЕ МЕНЮ
    if cmd in ["начать","старт","/start","меню","🔙 в главное меню","🔙 в меню"]:
        handle_start(user_id, name); return
    if cmd in ["купить","подобрать квартиру","🏠 подобрать квартиру"]:
        save_user_state(user_id, name, {'goal':'buy'})
        vk_send_message(user_id, f"✨ {name}, помогу найти квартиру!\n\n1️⃣ Ваш бюджет?", budget_keyboard()); return
    if cmd in ["продать","продать квартиру","💰 продать квартиру"]:
        save_user_state(user_id, name, {'goal':'sell'})
        vk_send_message(user_id, f"💰 {name}, помогу продать!\n\n1️⃣ Тип объекта?", property_type_keyboard()); return
    if cmd in ["чек-лист","получить чек-лист","📥 получить чек-лист"]:
        handle_checklist(user_id, name); return
    if cmd in ["инвест","инвестиции","📊 инвестиции"]:
        save_user_state(user_id, name, {'goal':'invest'})
        vk_send_message(user_id, f"📊 {name}, инвестиции!\n\n💡 Цель?", invest_goal_keyboard()); return
    if cmd in ["помощь","помощь и вопросы","💬 помощь и вопросы"]:
        handle_help(user_id, name); return
    if cmd in ["faq_bot","❓ как работает бот?","как работает бот"]:
        handle_faq(user_id, name, 'faq_bot'); return
    if cmd in ["faq_conditions","💰 условия работы","условия работы"]:
        handle_faq(user_id, name, 'faq_conditions'); return
    if cmd in ["faq_buy","🏠 как подобрать?","как подобрать"]:
        handle_faq(user_id, name, 'faq_buy'); return
    if cmd in ["faq_sell","💰 как продать?","как продать"]:
        handle_faq(user_id, name, 'faq_sell'); return
    
    # ПОКУПКА
    if state and state.get('goal') == 'buy':
        if state.get('phone'): vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard()); return
        if not state.get('budget'):
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'budget': budget})
                vk_send_message(user_id, f"✅ {budget}₽\n\n📍 Район?", district_keyboard()); return
            else:
                vk_send_message(user_id, f"{name}, бюджет (3000000 или 3 млн)", budget_keyboard()); return
        if state.get('budget') and not state.get('district'):
            for k,v in [('центр','Центральный'),('зареч','Зареченский'),('пролетар','Пролетарский'),('привокзал','Привокзальный'),('совет','Советский'),('любой','Любой'),('област','Область')]:
                if k in cmd: save_user_state(user_id, name, {'district': v}); break
            else: vk_send_message(user_id, "Выберите район 👇", district_keyboard()); return
            vk_send_message(user_id, f"✅ {state.get('district')}\n\n⏰ Срок?", deadline_keyboard()); return
        if state.get('budget') and state.get('district') and not state.get('deadline'):
            for k,v in [('срочно','Срочно'),('неделю','Срочно'),('1-3','1-3 месяца'),('месяц','1-3 месяца'),('3-6','3-6 месяцев'),('смотр','Присматриваюсь')]:
                if k in cmd: save_user_state(user_id, name, {'deadline': v}); break
            else: vk_send_message(user_id, "Выберите срок 👇", deadline_keyboard()); return
            vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard()); return
        if state.get('budget') and state.get('district') and state.get('deadline') and not state.get('phone'):
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state); mark_lead_sent(user_id)
                vk_send_message(user_id, f"✅ {name}, спасибо!\n📞 {phone}\nСвяжусь в течение 2 часов!", main_menu_keyboard()); return
            else: vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard()); return
    
    # ПРОДАЖА
    if state and state.get('goal') == 'sell':
        if state.get('phone'): vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard()); return
        if not state.get('prop_type'):
            for k,v in [('квартира','Квартира'),('дом','Дом'),('коттедж','Дом'),('комната','Комната'),('другое','Другое')]:
                if k in cmd: save_user_state(user_id, name, {'prop_type': v}); break
            else: vk_send_message(user_id, "Выберите тип 👇", property_type_keyboard()); return
            vk_send_message(user_id, f"✅ {state.get('prop_type')}\n\n📍 Район?", district_keyboard()); return
        if state.get('prop_type') and not state.get('district'):
            for k,v in [('центр','Центральный'),('зареч','Зареченский'),('пролетар','Пролетарский'),('привокзал','Привокзальный'),('совет','Советский'),('любой','Любой'),('област','Область')]:
                if k in cmd: save_user_state(user_id, name, {'district': v}); break
            else: vk_send_message(user_id, "Выберите район 👇", district_keyboard()); return
            vk_send_message(user_id, f"🎉 Отлично!\n\n📞 Телефон:", phone_keyboard()); return
        if state.get('prop_type') and state.get('district') and not state.get('phone'):
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state); mark_lead_sent(user_id)
                vk_send_message(user_id, f"✅ {name}, спасибо!\n📞 {phone}\nСвяжусь в течение 2 часов!", checklist_keyboard()); return
            else: vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard()); return
    
    # ИНВЕСТИЦИИ
    if state and state.get('goal') == 'invest':
        if state.get('phone'): vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard()); return
        if not state.get('invest_goal'):
            for k,v in [('перепродаж','Перепродажа'),('флиппинг','Перепродажа'),('аренд','Аренда'),('долгосрок','Долгосрок'),('консультаци','Консультация')]:
                if k in cmd: save_user_state(user_id, name, {'invest_goal': v}); break
            else: vk_send_message(user_id, "Выберите цель 👇", invest_goal_keyboard()); return
            vk_send_message(user_id, f"✅ {state.get('invest_goal')}\n\n💵 Бюджет?", invest_budget_keyboard()); return
        if state.get('invest_goal') and not state.get('invest_budget'):
            budget = extract_budget(text)
            if budget: save_user_state(user_id, name, {'invest_budget': budget})
            elif 'до 2' in cmd: save_user_state(user_id, name, {'invest_budget': 'до 2 млн'})
            elif '2-5' in cmd: save_user_state(user_id, name, {'invest_budget': '2-5 млн'})
            elif '5-10' in cmd: save_user_state(user_id, name, {'invest_budget': '5-10 млн'})
            elif '10+' in cmd: save_user_state(user_id, name, {'invest_budget': '10+ млн'})
            else: vk_send_message(user_id, "Выберите бюджет 👇", invest_budget_keyboard()); return
            vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard()); return
        if state.get('invest_goal') and state.get('invest_budget') and not state.get('phone'):
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state); mark_lead_sent(user_id)
                vk_send_message(user_id, f"📊 {name}, спасибо!\n📞 {phone}\nСвяжусь в течение 2 часов!", main_menu_keyboard()); return
            else: vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard()); return
    
    vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard())


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        if data.get("type") == "confirmation": return VK_CONFIRMATION_TOKEN, 200
        obj = data.get("object", {})
        if data.get("type") == "message_new":
            msg = obj.get("message", {})
            user_id, name, text = msg.get("from_id"), msg.get("from_name",""), msg.get("text","")
            if user_id: handle_message(user_id, name, text)
            return "ok", 200
        return "ok", 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return "error", 500

@app.route('/health')
def health(): return "VK Bot OK v2.1", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
