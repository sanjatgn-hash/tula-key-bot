# api/vk_webhook.py
# Tula Key Bot — FIXED STATE MANAGEMENT v2.3

import os
import json
import logging
import requests
from flask import Flask, request
from datetime import datetime
import random
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
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

logger.info("=" * 50)
logger.info(f"VK_TOKEN: {'✅' if VK_TOKEN else '❌'}")
logger.info(f"VK_GROUP_ID: {'✅' if VK_GROUP_ID else '❌'}")
logger.info(f"GOOGLE_SHEET_ID: {'✅' if GOOGLE_SHEET_ID else '❌'}")
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


def create_keyboard(one_time=False, buttons=None):
    if buttons is None:
        buttons = []
    return json.dumps({'one_time': one_time, 'buttons': buttons}, ensure_ascii=False)


def main_menu_keyboard():
    return create_keyboard(one_time=False, buttons=[
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('💰 Продать квартиру', {'cmd': 'sell'}, 'primary')],
        [get_button('📥 Получить чек-лист', {'cmd': 'checklist'}, 'secondary')],
        [get_button('📊 Инвестиции', {'cmd': 'invest'}, 'secondary')],
        [get_button('💬 Помощь и вопросы', {'cmd': 'help'}, 'secondary')],
        [{"action": {"type": "open_link", "link": VK_GROUP_LINK.strip(), "label": "📢 Наш канал"}}]
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
        [{"action": {"type": "open_link", "link": link, "label": "📥 Скачать чек-лист"}}],
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ])


def help_keyboard():
    admin_link = f'https://vk.com/im?sel={VK_ADMIN_ID}' if VK_ADMIN_ID else VK_GROUP_LINK
    return create_keyboard(one_time=False, buttons=[
        [get_button('❓ Как работает бот?', {'cmd': 'faq_bot'}, 'secondary')],
        [get_button('💰 Условия', {'cmd': 'faq_conditions'}, 'secondary')],
        [get_button('🏠 Подобрать', {'cmd': 'faq_buy'}, 'secondary')],
        [get_button('💰 Продать', {'cmd': 'faq_sell'}, 'secondary')],
        [{"action": {"type": "open_link", "link": admin_link, "label": "✍️ Написать лично"}}],
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


# ==================== GOOGLE SHEETS — ИСПРАВЛЕНО! ====================

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
        
        # Проверка/создание заголовков
        first_row = sheet.row_values(1)
        expected_headers = ['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 
                          'prop_type', 'district', 'invest_goal', 'invest_budget', 
                          'phone', 'updated_at', 'status']
        
        if not first_row or first_row[:len(expected_headers)] != expected_headers:
            sheet.clear()
            sheet.append_row(expected_headers)
            logger.info("✅ Created/Reset Google Sheets headers")
        
        return sheet
    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        return None


def save_user_state(chat_id, name, data):
    """✅ ИСПРАВЛЕНО: Правильное сохранение состояния"""
    sheet = get_sheet()
    if not sheet:
        logger.error("❌ Sheet is None in save_user_state")
        return False
    
    try:
        rows = sheet.get_all_values()
        logger.info(f"📊 Total rows: {len(rows)}")
        
        # Ищем существующую запись
        row_idx = None
        existing_data = {}
        
        for i, row in enumerate(rows[1:], 2):  # Пропускаем заголовок
            if row and len(row) > 0 and str(row[0]).strip() == str(chat_id).strip():
                status = row[12].strip() if len(row) > 12 else ''
                logger.info(f"🔍 Found user {chat_id} at row {i}, status: {status}")
                if status == 'new':
                    row_idx = i
                    existing_data = {
                        'goal': row[3].strip() if len(row) > 3 else '',
                        'budget': row[4].strip() if len(row) > 4 else '',
                        'deadline': row[5].strip() if len(row) > 5 else '',
                        'prop_type': row[6].strip() if len(row) > 6 else '',
                        'district': row[7].strip() if len(row) > 7 else '',
                        'invest_goal': row[8].strip() if len(row) > 8 else '',
                        'invest_budget': row[9].strip() if len(row) > 9 else '',
                    }
                    logger.info(f"📋 Existing data: {existing_data}")
                    break
        
        # Объединяем данные
        merged = {**existing_data, **data}
        logger.info(f"💾 Merged data: {merged}")
        
        # Создаём строку
        row_data = [
            str(chat_id).strip(),
            (name or '').strip(),
            '',  # username
            merged.get('goal', '').strip(),
            merged.get('budget', '').strip(),
            merged.get('deadline', '').strip(),
            merged.get('prop_type', '').strip(),
            merged.get('district', '').strip(),
            merged.get('invest_goal', '').strip(),
            merged.get('invest_budget', '').strip(),
            merged.get('phone', '').strip(),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'new'
        ]
        
        # Обновляем или создаём
        if row_idx:
            sheet.update(f'A{row_idx}:M{row_idx}', [row_data])
            logger.info(f"✅ Updated row {row_idx}")
        else:
            sheet.append_row(row_data)
            logger.info(f"✅ Created new row")
        
        # ✅ ПРОВЕРКА: Сразу читаем обратно чтобы убедиться
        verify_state = get_user_state(chat_id)
        logger.info(f"🔎 Verification after save: {verify_state}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_user_state(chat_id):
    """✅ ИСПРАВЛЕНО: Правильное получение состояния"""
    sheet = get_sheet()
    if not sheet:
        logger.error("❌ Sheet is None in get_user_state")
        return None
    
    try:
        rows = sheet.get_all_values()
        logger.info(f"📊 get_user_state: {len(rows)} rows")
        
        for row in rows[1:]:  # Пропускаем заголовок
            if row and len(row) > 0:
                row_chat_id = str(row[0]).strip()
                if row_chat_id == str(chat_id).strip():
                    status = row[12].strip() if len(row) > 12 else ''
                    logger.info(f"🔍 Found row, status: {status}")
                    if status == 'new':
                        state = {
                            'chat_id': row[0].strip() if len(row) > 0 else '',
                            'name': row[1].strip() if len(row) > 1 else '',
                            'goal': row[3].strip() if len(row) > 3 else '',
                            'budget': row[4].strip() if len(row) > 4 else '',
                            'deadline': row[5].strip() if len(row) > 5 else '',
                            'prop_type': row[6].strip() if len(row) > 6 else '',
                            'district': row[7].strip() if len(row) > 7 else '',
                            'invest_goal': row[8].strip() if len(row) > 8 else '',
                            'invest_budget': row[9].strip() if len(row) > 9 else '',
                            'phone': row[10].strip() if len(row) > 10 else '',
                            'status': status,
                        }
                        logger.info(f"✅ Got state: {state}")
                        return state
        
        logger.info(f"⚠️ No state found for {chat_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Get state error: {e}")
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
            if row and len(row) > 0 and str(row[0]).strip() == str(chat_id).strip():
                status = row[12].strip() if len(row) > 12 else ''
                if status == 'new':
                    sheet.update_cell(i, 13, 'sent')
                    sheet.update_cell(i, 12, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    logger.info(f"✅ Marked {chat_id} as sent")
                    return True
        return False
    except Exception as e:
        logger.error(f"❌ Mark error: {e}")
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
    logger.info(f"🎬 handle_start: {name} ({user_id})")
    save_user_state(user_id, name, {
        'goal': '', 'budget': '', 'deadline': '',
        'prop_type': '', 'district': '',
        'invest_goal': '', 'invest_budget': '', 'phone': ''
    })
    text = f"""✨ {name}, добро пожаловать в «Тульский ключ»!

🎁 Бонус: Чек-лист «7 ошибок» — бесплатно!

Выберите 👇"""
    vk_send_message(user_id, text, main_menu_keyboard())


def handle_checklist(user_id, name):
    text = f"""🎉 {name}, чек-лист готов!

📄 «7 ошибок при покупке»

👇 Скачивайте!"""
    vk_send_message(user_id, text, checklist_keyboard())


def handle_help(user_id, name):
    text = f"""💬 {name}, помогу!

❓ Как работает? — Отвечайте на вопросы
❓ Условия? — 2-3% после сделки
❓ Личный вопрос? — Кнопка ниже 👇"""
    vk_send_message(user_id, text, help_keyboard())


def handle_faq(user_id, name, topic):
    faqs = {
        'faq_bot': "🤖 Выберите цель → Ответьте на вопросы → Оставьте телефон → Я свяжусь!",
        'faq_conditions': "💰 Комиссия 2-3% только после сделки. Без предоплат!",
        'faq_buy': "🏠 Бюджет → Район → Срок → Телефон → Подберу за 7-14 дней!",
        'faq_sell': "💰 Оценка → Фото → Размещение → Показы → Сделка за 2-4 недели!"
    }
    vk_send_message(user_id, faqs.get(topic, "Вопрос не найден."), help_keyboard())


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    
    if not name or name == "Пользователь" or name == "":
        name = vk_get_user_name(user_id)
    
    state = get_user_state(user_id)
    
    logger.info("=" * 50)
    logger.info(f"User: {user_id}, Name: {name}, Text: '{text}'")
    logger.info(f"State: {state}")
    
    # ГЛАВНОЕ МЕНЮ
    if cmd in ["начать", "старт", "/start", "меню", "🔙 в меню", "🔙 в главное меню"]:
        handle_start(user_id, name)
        return
    
    if cmd in ["купить", "подобрать квартиру", "🏠 подобрать квартиру"]:
        logger.info("🏠 BUY scenario START")
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"✨ {name}, 1️⃣ Ваш бюджет?", budget_keyboard())
        return
    
    if cmd in ["продать", "продать квартиру", "💰 продать квартиру"]:
        logger.info("💰 SELL scenario START")
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"💰 {name}, 1️⃣ Тип объекта?", property_type_keyboard())
        return
    
    if cmd in ["чек-лист", "получить чек-лист", "📥 получить чек-лист"]:
        handle_checklist(user_id, name)
        return
    
    if cmd in ["инвест", "инвестиции", "📊 инвестиции"]:
        logger.info("📊 INVEST scenario START")
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, f"📊 {name}, 💡 Цель?", invest_goal_keyboard())
        return
    
    if cmd in ["помощь", "помощь и вопросы", "💬 помощь и вопросы"]:
        handle_help(user_id, name)
        return
    
    if cmd in ["faq_bot", "❓ как работает бот?", "как работает бот"]:
        handle_faq(user_id, name, 'faq_bot')
        return
    if cmd in ["faq_conditions", "💰 условия", "условия работы"]:
        handle_faq(user_id, name, 'faq_conditions')
        return
    if cmd in ["faq_buy", "🏠 как подобрать?", "как подобрать"]:
        handle_faq(user_id, name, 'faq_buy')
        return
    if cmd in ["faq_sell", "💰 как продать?", "как продать"]:
        handle_faq(user_id, name, 'faq_sell')
        return
    
    # ПОКУПКА
    if state and state.get('goal') == 'buy':
        logger.info(f"🔄 In BUY: goal={state.get('goal')}, budget={state.get('budget')}, district={state.get('district')}")
        
        if state.get('phone'):
            vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard())
            return
        
        if not state.get('budget'):
            logger.info("BUY Step 1: Budget")
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'budget': budget})
                vk_send_message(user_id, f"✅ {budget}₽\n\n📍 Район?", district_keyboard())
                return
            vk_send_message(user_id, f"{name}, бюджет (3000000 или 3 млн)", budget_keyboard())
            return
        
        if state.get('budget') and not state.get('district'):
            logger.info("BUY Step 2: District")
            district_map = {'центр': 'Центральный', 'зареч': 'Зареченский', 'пролетар': 'Пролетарский',
                          'привокзал': 'Привокзальный', 'совет': 'Советский', 'любой': 'Любой', 'област': 'Область'}
            for k, v in district_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'district': v})
                    vk_send_message(user_id, f"✅ {v}\n\n⏰ Срок?", deadline_keyboard())
                    return
            vk_send_message(user_id, "Выберите район 👇", district_keyboard())
            return
        
        if state.get('budget') and state.get('district') and not state.get('deadline'):
            logger.info("BUY Step 3: Deadline")
            deadline_map = {'срочно': 'Срочно', 'неделю': 'Срочно', '1-3': '1-3 месяца',
                          'месяц': '1-3 месяца', '3-6': '3-6 месяцев', 'смотр': 'Присматриваюсь'}
            for k, v in deadline_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'deadline': v})
                    vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard())
                    return
            vk_send_message(user_id, "Выберите срок 👇", deadline_keyboard())
            return
        
        if state.get('budget') and state.get('district') and state.get('deadline') and not state.get('phone'):
            logger.info("BUY Step 4: Phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"✅ {name}, спасибо!\n📞 {phone}\nСвяжусь в течение 2 часов!", main_menu_keyboard())
                return
            vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    # ПРОДАЖА
    if state and state.get('goal') == 'sell':
        logger.info(f"🔄 In SELL: goal={state.get('goal')}, prop_type={state.get('prop_type')}, district={state.get('district')}")
        
        if state.get('phone'):
            vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard())
            return
        
        if not state.get('prop_type'):
            logger.info("SELL Step 1: Prop Type")
            prop_map = {'квартира': 'Квартира', 'дом': 'Дом', 'коттедж': 'Дом',
                       'комната': 'Комната', 'другое': 'Другое'}
            for k, v in prop_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'prop_type': v})
                    vk_send_message(user_id, f"✅ {v}\n\n📍 Район?", district_keyboard())
                    return
            vk_send_message(user_id, "Выберите тип 👇", property_type_keyboard())
            return
        
        if state.get('prop_type') and not state.get('district'):
            logger.info("SELL Step 2: District")
            district_map = {'центр': 'Центральный', 'зареч': 'Зареченский', 'пролетар': 'Пролетарский',
                          'привокзал': 'Привокзальный', 'совет': 'Советский', 'любой': 'Любой', 'област': 'Область'}
            for k, v in district_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'district': v})
                    vk_send_message(user_id, f"🎉 Отлично!\n\n📞 Телефон:", phone_keyboard())
                    return
            vk_send_message(user_id, "Выберите район 👇", district_keyboard())
            return
        
        if state.get('prop_type') and state.get('district') and not state.get('phone'):
            logger.info("SELL Step 3: Phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"✅ {name}, спасибо!\n📞 {phone}\nСвяжусь в течение 2 часов!", checklist_keyboard())
                return
            vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    # ИНВЕСТИЦИИ
    if state and state.get('goal') == 'invest':
        logger.info(f"🔄 In INVEST: goal={state.get('goal')}, invest_goal={state.get('invest_goal')}, invest_budget={state.get('invest_budget')}")
        
        if state.get('phone'):
            vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard())
            return
        
        if not state.get('invest_goal'):
            logger.info("INVEST Step 1: Goal")
            goal_map = {'перепродаж': 'Перепродажа', 'флиппинг': 'Перепродажа',
                       'аренд': 'Аренда', 'долгосрок': 'Долгосрок', 'консультаци': 'Консультация'}
            for k, v in goal_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'invest_goal': v})
                    vk_send_message(user_id, f"✅ {v}\n\n💵 Бюджет?", invest_budget_keyboard())
                    return
            vk_send_message(user_id, "Выберите цель 👇", invest_goal_keyboard())
            return
        
        if state.get('invest_goal') and not state.get('invest_budget'):
            logger.info("INVEST Step 2: Budget")
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
            logger.info("INVEST Step 3: Phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"📊 {name}, спасибо!\n📞 {phone}\nСвяжусь в течение 2 часов!", main_menu_keyboard())
                return
            vk_send_message(user_id, f"⚠️ Не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    vk_send_message(user_id, f"👋 {name}, выберите:", main_menu_keyboard())


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
        return "error", 500

@app.route('/health')
def health():
    return "VK Bot OK v2.3", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
