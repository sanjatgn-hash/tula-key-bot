# api/vk_webhook.py
# Tula Key Bot — FAQ DEBUG v3.1

import os
import json
import logging
import requests
from flask import Flask, request
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== SETTINGS ====================
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN", "")
VK_ADMIN_ID = os.getenv("VK_ADMIN_ID", "")
VK_ADMIN_PHONE = os.getenv("VK_ADMIN_PHONE", "+79991234567")
CHECKLIST_URL = os.getenv("CHECKLIST_URL", "")
VK_GROUP_LINK = os.getenv("VK_GROUP_LINK", "https://vk.com/tula_key").strip()
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "")

logger.info("=" * 50)
logger.info(f"VK_TOKEN: {'✅' if VK_TOKEN else '❌'}")
logger.info(f"VK_GROUP_ID: {'✅' if VK_GROUP_ID else '❌'}")
logger.info("=" * 50)


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
    except:
        return "друг"


def get_random_id():
    return random.randint(0, 2000000000)


# ==================== KEYBOARDS ====================

def get_button(label, payload='', color='primary'):
    return {
        'action': {'type': 'text', 'payload': json.dumps(payload, ensure_ascii=False), 'label': label},
        'color': color
    }


def get_link_button(label, url):
    return {"action": {"type": "open_link", "link": url.strip(), "label": label}}


def create_keyboard(one_time=False, buttons=None):
    if buttons is None:
        buttons = []
    return json.dumps({'one_time': one_time, 'buttons': buttons}, ensure_ascii=False)


def main_menu_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('💰 Продажа объекта', {'cmd': 'sell'}, 'primary')],
        [get_button('📥 Получить чек-лист', {'cmd': 'checklist'}, 'secondary')],
        [get_button('📊 Инвестиции', {'cmd': 'invest'}, 'secondary')],
        [get_button('💬 Помощь и вопросы', {'cmd': 'help'}, 'secondary')],
        [get_link_button('📢 Наш канал', VK_GROUP_LINK)]
    ])


def budget_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('до 2 млн', {'cmd': 'budget', 'val': 'до 2 млн'}, 'secondary')],
        [get_button('2-3 млн', {'cmd': 'budget', 'val': '2-3 млн'}, 'primary')],
        [get_button('3-5 млн', {'cmd': 'budget', 'val': '3-5 млн'}, 'primary')],
        [get_button('5+ млн', {'cmd': 'budget', 'val': '5+ млн'}, 'primary')],
        [get_button('Нужна консультация', {'cmd': 'budget', 'val': 'Консультация'}, 'secondary')]
    ])


def deadline_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('🔥 Срочно', {'cmd': 'deadline', 'val': 'Срочно'}, 'primary')],
        [get_button('📅 1-3 месяца', {'cmd': 'deadline', 'val': '1-3 месяца'}, 'primary')],
        [get_button('📅 3-6 месяцев', {'cmd': 'deadline', 'val': '3-6 месяцев'}, 'secondary')],
        [get_button('👀 Просто смотрю', {'cmd': 'deadline', 'val': 'Присматриваюсь'}, 'secondary')]
    ])


def property_type_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('🏢 Квартира', {'cmd': 'prop_type', 'val': 'Квартира'}, 'primary')],
        [get_button('🏡 Дом', {'cmd': 'prop_type', 'val': 'Дом'}, 'primary')],
        [get_button('🚪 Комната', {'cmd': 'prop_type', 'val': 'Комната'}, 'secondary')],
        [get_button('🏗️ Другое', {'cmd': 'prop_type', 'val': 'Другое'}, 'secondary')]
    ])


def district_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('🏛️ Центральный', {'cmd': 'district', 'val': 'Центральный'}, 'primary')],
        [get_button('🌳 Зареченский', {'cmd': 'district', 'val': 'Зареченский'}, 'primary')],
        [get_button('🏭 Пролетарский', {'cmd': 'district', 'val': 'Пролетарский'}, 'primary')],
        [get_button('🚉 Привокзальный', {'cmd': 'district', 'val': 'Привокзальный'}, 'secondary')],
        [get_button('🏘️ Советский', {'cmd': 'district', 'val': 'Советский'}, 'secondary')],
        [get_button('📍 Любой район', {'cmd': 'district', 'val': 'Любой'}, 'secondary')],
        [get_button('🌾 Область', {'cmd': 'district', 'val': 'Область'}, 'secondary')]
    ])


def invest_goal_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('💵 Перепродажа', {'cmd': 'invest_goal', 'val': 'Перепродажа'}, 'primary')],
        [get_button('🏠 Аренда', {'cmd': 'invest_goal', 'val': 'Аренда'}, 'primary')],
        [get_button('📈 Долгосрок', {'cmd': 'invest_goal', 'val': 'Долгосрок'}, 'secondary')],
        [get_button('❓ Консультация', {'cmd': 'invest_goal', 'val': 'Консультация'}, 'secondary')]
    ])


def invest_budget_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('до 2 млн', {'cmd': 'invest_budget', 'val': 'до 2 млн'}, 'secondary')],
        [get_button('2-5 млн', {'cmd': 'invest_budget', 'val': '2-5 млн'}, 'primary')],
        [get_button('5-10 млн', {'cmd': 'invest_budget', 'val': '5-10 млн'}, 'primary')],
        [get_button('10+ млн', {'cmd': 'invest_budget', 'val': '10+ млн'}, 'primary')]
    ])


def phone_keyboard():
    return create_keyboard(one_time=True, buttons=[
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ])


def checklist_keyboard():
    link = (CHECKLIST_URL or VK_GROUP_LINK).strip()
    return create_keyboard(one_time=False, buttons=[
        [get_link_button('📥 Скачать чек-лист', link)],
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ])


# ✅ ВОТ ЗДЕСЬ НОВЫЕ КНОПКИ FAQ
def help_keyboard():
    admin_link = f'https://vk.com/im?sel={VK_ADMIN_ID}'.strip() if VK_ADMIN_ID else VK_GROUP_LINK
    return create_keyboard(one_time=False, buttons=[
        [get_button('❓ Как работает бот?', {'cmd': 'faq_bot'}, 'secondary')],
        [get_button('🤝 Условия работы', {'cmd': 'faq_conditions'}, 'secondary')],
        [get_button('ℹ️ Как подбирают квартиру?', {'cmd': 'инфо покупка'}, 'secondary')],  # ✅ НОВАЯ
        [get_button('ℹ️ Как продают недвижимость?', {'cmd': 'инфо продажа'}, 'secondary')],  # ✅ НОВАЯ
        [get_link_button('✍️ Написать лично', admin_link)],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ])


def final_keyboard(goal=''):
    goal_labels = {'buy': 'покупку', 'sell': 'продажу', 'invest': 'инвестиции'}
    goal_label = goal_labels.get(goal, 'заявку')
    admin_link = f'https://vk.com/im?sel={VK_ADMIN_ID}'.strip() if VK_ADMIN_ID else VK_GROUP_LINK
    
    buttons = [
        [get_link_button('✍️ Написать в ЛС', admin_link)],
        [get_button(f'🔄 Новая заявка на {goal_label}', {'cmd': f'restart_{goal}'}, 'primary')],
        [get_button('🔙 В главное меню', {'cmd': 'menu'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


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
            return None
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        first_row = sheet.row_values(1)
        expected_headers = ['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 
                          'prop_type', 'district', 'invest_goal', 'invest_budget', 
                          'phone', 'updated_at', 'status']
        
        if not first_row or first_row[:len(expected_headers)] != expected_headers:
            sheet.clear()
            sheet.append_row(expected_headers)
        
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
            if row and len(row) > 0 and str(row[0]).strip() == str(chat_id).strip():
                status = row[12].strip() if len(row) > 12 else ''
                if status == 'new':
                    row_idx = i
                    existing_data = {k: row[j].strip() if len(row) > j and row[j].strip() else '' for j, k in enumerate(['goal','budget','deadline','prop_type','district','invest_goal','invest_budget'], 3)}
                    break
        
        merged = {**existing_data, **data}
        row_data = [str(chat_id).strip(), (name or '').strip(), '', merged.get('goal','').strip(), merged.get('budget','').strip(), merged.get('deadline','').strip(), merged.get('prop_type','').strip(), merged.get('district','').strip(), merged.get('invest_goal','').strip(), merged.get('invest_budget','').strip(), merged.get('phone','').strip(), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'new']
        
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
            if row and len(row) > 0 and str(row[0]).strip() == str(chat_id).strip():
                status = row[12].strip() if len(row) > 12 else ''
                if status == 'new':
                    return {k: row[j].strip() if len(row) > j and row[j].strip() else '' for j, k in enumerate(['chat_id','name','goal','budget','deadline','prop_type','district','invest_goal','invest_budget','phone','status'], 0)}
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
            if row and len(row) > 0 and str(row[0]).strip() == str(chat_id).strip():
                status = row[12].strip() if len(row) > 12 else ''
                if status == 'new':
                    sheet.update_cell(i, 13, 'sent')
                    sheet.update_cell(i, 12, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    return True
        return False
    except:
        return False


def clear_user_state(chat_id):
    return save_user_state(chat_id, "", {'goal':'','budget':'','deadline':'','prop_type':'','district':'','invest_goal':'','invest_budget':'','phone':''})


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
    clear_user_state(user_id)
    vk_send_message(user_id, f"✨ {name}, добро пожаловать в «Тульский ключ»!\n\n🎁 Бонус: Чек-лист «7 ошибок» — бесплатно!\n\nВыберите 👇", main_menu_keyboard())


def handle_checklist(user_id, name):
    vk_send_message(user_id, f"🎉 {name}, чек-лист готов!\n\n📄 «7 ошибок при покупке»\n\n👇 Скачивайте!", checklist_keyboard())


def handle_help(user_id, name):
    vk_send_message(user_id, f"💬 {name}, помогу!\n\nВыберите вопрос 👇", help_keyboard())


def handle_faq(user_id, name, topic):
    logger.info(f"📚 FAQ TOPIC: {topic}")  # ✅ ЛОГ ДЛЯ ОТЛАДКИ
    faqs = {
        'faq_bot': f"🤖 {name}, я — ваш помощник по недвижимости в Туле!\n\n✅ Подбирать квартиры\n✅ Помогать с продажей\n✅ Консультировать по инвестициям\n\n💡 Нажмите «Написать лично» если нужен человек 👇",
        'faq_conditions': f"🤝 {name}, наши условия:\n\n📋 Оплата ТОЛЬКО после сделки!\n📊 Комиссия: 2-3%\n\n🎯 Лучший результат с минимальными нервами!",
        'faq_buy': "🏠 **Подобрать квартиру:**\n\n1️⃣ Бюджет → 2️⃣ Район → 3️⃣ Срок → 4️⃣ Телефон\n\n📋 **Что делаю:**\n• Анализирую 100+ объектов\n• Отбираю 3-5 лучших\n• Организую просмотры\n• Веду переговоры\n• Проверяю документы\n• Готовлю сделку\n• Поздравляю 🤝\n\n⏱️ **Срок:** 2-14 дней\n\n🚀 Нажмите «Подобрать квартиру» чтобы начать 👇",
        'faq_sell': "💰 **Продать недвижимость:**\n\n1️⃣ Тип → 2️⃣ Район → 3️⃣ Телефон\n\n📋 **Что делаю:**\n• Анализ рынка\n• Фото от фотографа\n• Размещение везде (VK, Циан, Авито)\n• Показы покупателям\n• Торг за Вас\n• Расклейка, продвижение\n• Полное сопровождение\n• Поздравляю 🤝\n\n⏱️ **Срок:** 1-3 месяца\n\n🚀 Нажмите «Продажа объекта» чтобы начать 👇"
    }
    
    keyboard = help_keyboard() if topic in ['faq_bot', 'faq_conditions'] else main_menu_keyboard()
    vk_send_message(user_id, faqs.get(topic, "Вопрос не найден."), keyboard)


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    
    if not name or name == "Пользователь" or name == "":
        name = vk_get_user_name(user_id)
    
    state = get_user_state(user_id)
    
    logger.info("=" * 50)
    logger.info(f"User: {user_id}, Name: {name}, Text: '{text}'")
    logger.info(f"Cmd: '{cmd}'")  # ✅ ЛОГ КОМАНДЫ
    logger.info(f"State: {state}")
    
    # ГЛАВНОЕ МЕНЮ
    if cmd in ["начать", "старт", "/start"]:
        logger.info("📍 Command: START")
        handle_start(user_id, name)
        return
    
    if cmd in ["меню", "🔙 в меню", "🔙 в главное меню"]:
        logger.info("📍 Command: MENU")
        clear_user_state(user_id)
        handle_start(user_id, name)
        return
    
    if cmd.startswith("restart_"):
        logger.info(f"📍 Command: RESTART {cmd}")
        goal = cmd.replace("restart_", "")
        clear_user_state(user_id)
        if goal == "buy":
            save_user_state(user_id, name, {'goal': 'buy'})
            vk_send_message(user_id, f"✨ {name}, 1️⃣ Ваш бюджет?", budget_keyboard())
        elif goal == "sell":
            save_user_state(user_id, name, {'goal': 'sell'})
            vk_send_message(user_id, f"💰 {name}, 1️⃣ Тип объекта?", property_type_keyboard())
        elif goal == "invest":
            save_user_state(user_id, name, {'goal': 'invest'})
            vk_send_message(user_id, f"📊 {name}, 💡 Цель?", invest_goal_keyboard())
        return
    
    # СЦЕНАРИИ (сброс перед стартом)
    if cmd in ["купить", "подобрать квартиру", "🏠 подобрать квартиру"]:
        logger.info("📍 Command: BUY SCENARIO")
        clear_user_state(user_id)
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"✨ {name}, 1️⃣ Ваш бюджет?", budget_keyboard())
        return
    
    if cmd in ["продать", "продажа объекта", "💰 продажа объекта"]:
        logger.info("📍 Command: SELL SCENARIO")
        clear_user_state(user_id)
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"💰 {name}, 1️⃣ Тип объекта?", property_type_keyboard())
        return
    
    if cmd in ["инвест", "инвестиции", "📊 инвестиции"]:
        logger.info("📍 Command: INVEST SCENARIO")
        clear_user_state(user_id)
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, f"📊 {name}, 💡 Цель?", invest_goal_keyboard())
        return
    
    if cmd in ["чек-лист", "получить чек-лист", "📥 получить чек-лист"]:
        logger.info("📍 Command: CHECKLIST")
        handle_checklist(user_id, name)
        return
    
    if cmd in ["помощь", "помощь и вопросы", "💬 помощь и вопросы"]:
        logger.info("📍 Command: HELP")
        handle_help(user_id, name)
        return
    
    # ✅ FAQ — ПЕРЕД СЦЕНАРИЯМИ!
    if cmd in ["инфо покупка", "как купить", "про подбор", "как подбирают квартиру"]:
        logger.info("📍 Command: FAQ BUY")  # ✅ ЛОГ
        handle_faq(user_id, name, 'faq_buy')
        return
    
    if cmd in ["инфо продажа", "как продать", "про продажу", "как продают недвижимость"]:
        logger.info("📍 Command: FAQ SELL")  # ✅ ЛОГ
        handle_faq(user_id, name, 'faq_sell')
        return
    
    if cmd in ["faq_bot", "❓ как работает бот?", "как работает бот"]:
        handle_faq(user_id, name, 'faq_bot')
        return
    
    if cmd in ["faq_conditions", "🤝 условия работы", "условия"]:
        handle_faq(user_id, name, 'faq_conditions')
        return
    
    # СЦЕНАРИИ (продолжение)
    if state and state.get('goal') == 'buy' and not state.get('phone'):
        if not state.get('budget'):
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'budget': budget})
                vk_send_message(user_id, f"✅ {budget}₽\n\n📍 Район?", district_keyboard())
                return
            vk_send_message(user_id, f"{name}, бюджет (3000000 или 3 млн)", budget_keyboard())
            return
        
        if not state.get('district'):
            district_map = {'центр': 'Центральный', 'зареч': 'Зареченский', 'пролетар': 'Пролетарский', 'привокзал': 'Привокзальный', 'совет': 'Советский', 'любой': 'Любой', 'област': 'Область'}
            for k, v in district_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'district': v})
                    vk_send_message(user_id, f"✅ {v}\n\n⏰ Срок?", deadline_keyboard())
                    return
            vk_send_message(user_id, "Выберите район 👇", district_keyboard())
            return
        
        if not state.get('deadline'):
            deadline_map = {'срочно': 'Срочно', 'неделю': 'Срочно', '1-3': '1-3 месяца', 'месяц': '1-3 месяца', '3-6': '3-6 месяцев', 'смотр': 'Присматриваюсь'}
            for k, v in deadline_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'deadline': v})
                    vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard())
                    return
            vk_send_message(user_id, "Выберите срок 👇", deadline_keyboard())
            return
        
        if state.get('budget') and state.get('district') and state.get('deadline') and not state.get('phone'):
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"🎉 {name}, заявка принята!\n\n✅ Бюджет: {state.get('budget')}\n✅ Район: {state.get('district')}\n✅ Срок: {state.get('deadline')}\n✅ Телефон: {phone}\n\n📞 Позвонить: {VK_ADMIN_PHONE}\n✍️ Или напишите в ЛС", final_keyboard('buy'))
                return
            vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    if state and state.get('goal') == 'sell' and not state.get('phone'):
        if not state.get('prop_type'):
            prop_map = {'квартира': 'Квартира', 'дом': 'Дом', 'коттедж': 'Дом', 'комната': 'Комната', 'другое': 'Другое'}
            for k, v in prop_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'prop_type': v})
                    vk_send_message(user_id, f"✅ {v}\n\n📍 Район?", district_keyboard())
                    return
            vk_send_message(user_id, "Выберите тип 👇", property_type_keyboard())
            return
        
        if not state.get('district'):
            district_map = {'центр': 'Центральный', 'зареч': 'Зареченский', 'пролетар': 'Пролетарский', 'привокзал': 'Привокзальный', 'совет': 'Советский', 'любой': 'Любой', 'област': 'Область'}
            for k, v in district_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'district': v})
                    vk_send_message(user_id, f"🎉 Отлично!\n\n📞 Телефон:", phone_keyboard())
                    return
            vk_send_message(user_id, "Выберите район 👇", district_keyboard())
            return
        
        if state.get('prop_type') and state.get('district') and not state.get('phone'):
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"🎉 {name}, заявка принята!\n\n✅ Тип: {state.get('prop_type')}\n✅ Район: {state.get('district')}\n✅ Телефон: {phone}\n\n📞 Позвонить: {VK_ADMIN_PHONE}\n✍️ Или напишите в ЛС", final_keyboard('sell'))
                return
            vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    if state and state.get('goal') == 'invest' and not state.get('phone'):
        if not state.get('invest_goal'):
            goal_map = {'перепродаж': 'Перепродажа', 'флиппинг': 'Перепродажа', 'аренд': 'Аренда', 'долгосрок': 'Долгосрок', 'консультаци': 'Консультация'}
            for k, v in goal_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'invest_goal': v})
                    vk_send_message(user_id, f"✅ {v}\n\n💵 Бюджет?", invest_budget_keyboard())
                    return
            vk_send_message(user_id, "Выберите цель 👇", invest_goal_keyboard())
            return
        
        if not state.get('invest_budget'):
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'invest_budget': budget})
            elif 'до 2' in cmd:
                save_user_state(user_id, name, {'invest_budget': 'до 2 млн'})
            elif '2-5' in cmd:
                save_user_state(user_id, name, {'invest_budget': '2-5 млн'})
            elif '5-10' in cmd:
                save_user_state(user_id, name, {'invest_budget': '5-10 млн'})
            elif '10+' in cmd:
                save_user_state(user_id, name, {'invest_budget': '10+ млн'})
            else:
                vk_send_message(user_id, "Выберите бюджет 👇", invest_budget_keyboard())
                return
            vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard())
            return
        
        if state.get('invest_goal') and state.get('invest_budget') and not state.get('phone'):
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"🎉 {name}, заявка принята!\n\n✅ Цель: {state.get('invest_goal')}\n✅ Бюджет: {state.get('invest_budget')}\n✅ Телефон: {phone}\n\n📞 Позвонить: {VK_ADMIN_PHONE}\n✍️ Или напишите в ЛС", final_keyboard('invest'))
                return
            vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    if state and state.get('phone'):
        goal = state.get('goal', '')
        goal_name = {'buy': 'покупку', 'sell': 'продажу', 'invest': 'инвестиции'}.get(goal, 'заявку')
        vk_send_message(user_id, f"👋 {name}, вы уже оставили заявку на {goal_name}!\n\n✅ Данные сохранены — свяжусь с вами.\n\n💡 Можно: новая заявка, написать лично, меню", final_keyboard(goal))
        return
    
    vk_send_message(user_id, f"👋 {name}, выберите действие:\n\n🏠 Подобрать квартиру\n💰 Продажа объекта\n📊 Инвестиции\n📥 Чек-лист\n💬 Помощь\n\nИли «начать» для меню 👇", main_menu_keyboard())


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        if data.get("type") == "confirmation":
            return VK_CONFIRMATION_TOKEN, 200
        obj = data.get("object", {})
        if data.get("type") == "message_new":
            msg = obj.get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name", "")
            text = msg.get("text", "")
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
    return "VK Bot OK v3.1", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
