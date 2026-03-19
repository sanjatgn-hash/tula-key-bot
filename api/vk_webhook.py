# api/vk_webhook.py
# Tula Key Bot — FAQ COMMANDS ADDED v3.0

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


def get_link_button(label, url):
    clean_url = url.strip()
    return {"action": {"type": "open_link", "link": clean_url, "label": label}}


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


def help_keyboard():
    """✅ ДОБАВЛЕНЫ: Кнопки для подробной информации о подборе и продаже"""
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
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
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
            logger.info("✅ Created/Reset Google Sheets headers")
        
        return sheet
    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        return None


def save_user_state(chat_id, name, data):
    sheet = get_sheet()
    if not sheet:
        logger.error("❌ Sheet is None in save_user_state")
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
                    existing_data = {
                        'goal': row[3].strip() if len(row) > 3 and row[3].strip() else '',
                        'budget': row[4].strip() if len(row) > 4 and row[4].strip() else '',
                        'deadline': row[5].strip() if len(row) > 5 and row[5].strip() else '',
                        'prop_type': row[6].strip() if len(row) > 6 and row[6].strip() else '',
                        'district': row[7].strip() if len(row) > 7 and row[7].strip() else '',
                        'invest_goal': row[8].strip() if len(row) > 8 and row[8].strip() else '',
                        'invest_budget': row[9].strip() if len(row) > 9 and row[9].strip() else '',
                    }
                    break
        
        merged = {**existing_data, **data}
        
        row_data = [
            str(chat_id).strip(),
            (name or '').strip(),
            '',
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
        
        if row_idx:
            sheet.update(f'A{row_idx}:M{row_idx}', [row_data])
            logger.info(f"✅ Updated row {row_idx}")
        else:
            sheet.append_row(row_data)
            logger.info(f"✅ Created new row")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_user_state(chat_id):
    sheet = get_sheet()
    if not sheet:
        return None
    
    try:
        for row in sheet.get_all_values()[1:]:
            if row and len(row) > 0:
                if str(row[0]).strip() == str(chat_id).strip():
                    status = row[12].strip() if len(row) > 12 else ''
                    if status == 'new':
                        return {
                            'chat_id': row[0].strip() if len(row) > 0 else '',
                            'name': row[1].strip() if len(row) > 1 else '',
                            'goal': row[3].strip() if len(row) > 3 and row[3].strip() else '',
                            'budget': row[4].strip() if len(row) > 4 and row[4].strip() else '',
                            'deadline': row[5].strip() if len(row) > 5 and row[5].strip() else '',
                            'prop_type': row[6].strip() if len(row) > 6 and row[6].strip() else '',
                            'district': row[7].strip() if len(row) > 7 and row[7].strip() else '',
                            'invest_goal': row[8].strip() if len(row) > 8 and row[8].strip() else '',
                            'invest_budget': row[9].strip() if len(row) > 9 and row[9].strip() else '',
                            'phone': row[10].strip() if len(row) > 10 and row[10].strip() else '',
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


def clear_user_state(chat_id):
    return save_user_state(chat_id, "", {
        'goal': '', 'budget': '', 'deadline': '',
        'prop_type': '', 'district': '',
        'invest_goal': '', 'invest_budget': '', 'phone': ''
    })


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
    text = f"""✨ {name}, добро пожаловать в «Тульский ключ»!

🎁 Бонус: Чек-лист «7 ошибок» — бесплатно!

🏠 **Что я умею:**
• Подобрать квартиру под ваш бюджет
• Помочь выгодно продать объект
• Подобрать инвестиции в недвижимость

Выберите, что вас интересует 👇"""
    vk_send_message(user_id, text, main_menu_keyboard())


def handle_checklist(user_id, name):
    text = f"""🎉 {name}, чек-лист готов!

📄 «7 ошибок при покупке»

👇 Скачивайте по кнопке!"""
    vk_send_message(user_id, text, checklist_keyboard())


def handle_help(user_id, name):
    text = f"""💬 {name}, помогу!

Выберите вопрос ниже 👇"""
    vk_send_message(user_id, text, help_keyboard())


def handle_faq(user_id, name, topic):
    """✅ ДОБАВЛЕНЫ: faq_buy и faq_sell"""
    faqs = {
        'faq_bot': f"""🤖 {name}, я — ваш универсальный помощник по недвижимости в Туле!

Я ещё учусь и становлюсь лучше с каждым днём, но уже сейчас умею:

✅ Подбирать квартиры под ваш бюджет и район
✅ Помогать с продажей недвижимости
✅ Консультировать по инвестициям
✅ Отвечать на частые вопросы

Просто выберите, что вас интересует, и я проведу вас по всем шагам!

💡 Бот работает 24/7, но если нужен человек — нажмите «Написать лично» 👇""",
        
        'faq_conditions': f"""🤝 {name}, наши условия просты и прозрачны:

📋 **Как мы работаем:**
1. Вы оставляете заявку — я изучаю ваш запрос
2. Веду переговоры от вашего имени
3. Сопровождаю сделку от начала до конца

💰 **Оплата:**
Только ПОСЛЕ успешного перехода права собственности!

📊 **Комиссия:**
2-3% от стоимости объекта — зависит от сложности.

🎯 **Моя цель:**
Лучший результат с минимальными затратами времени и нервов!

Есть вопросы? Напишите мне лично 👇""",
        
        'faq_buy': """🏠 **Подобрать квартиру:**

1️⃣ Бюджет → 2️⃣ Район → 3️⃣ Срок → 4️⃣ Телефон

📋 **Что я делаю:**
• Анализирую 100+ объектов
• Отбираю 3-5 лучших вариантов
• Организую просмотры
• Веду переговоры о цене
• Проверяю документы собственников
• Готовлю документы для сделки
• Поздравляю с успешной сделкой 🤝

⏱️ **Срок:** от 2-ух до 14-ти дней в среднем (индивидуально)

🚀 Хотите начать? Нажмите «Подобрать квартиру» 👇""",
        
        'faq_sell': """💰 **Продать недвижимость:**

1️⃣ Тип объекта → 2️⃣ Район → 3️⃣ Телефон

📋 **Что я делаю:**
• Бесплатный анализ рынка, чтобы быть в курсе актуальной цены
• Профессиональные фото (по желанию) от нашего фотографа 
• Размещение на всех площадках (VK, Циан, Авито и другие), чаты риелторов и инвесторов 
• Организация показов потенциальным покупателям
• Ведение переговоров и торг за Вас
• Генерация входящего потока благодаря использованию всех доступных инструментов (Расклейка, платное продвижение и многое другое)
• Полное сопровождение сделки от Здравствуйте, меня зовут... до Александр, огромное спасибо за сделку, я порекомендую вас своим знакомым
• Отслеживание статистики
• Поздравляю с успешной сделкой 🤝

⏱️ **Срок:** 1-3 месяца в среднем

🚀 Хотите начать? Нажмите «Продажа объекта» 👇"""
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
    logger.info(f"State: {state}")
    
    # ========================================
    # 🔘 ГЛАВНОЕ МЕНЮ И СБРОС
    # ========================================
    
    if cmd in ["начать", "старт", "/start"]:
        handle_start(user_id, name)
        return
    
    if cmd in ["меню", "🔙 в меню", "🔙 в главное меню"]:
        clear_user_state(user_id)
        handle_start(user_id, name)
        return
    
    if cmd.startswith("restart_"):
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
    
    # Запуск сценариев (сброс перед стартом)
    if cmd in ["купить", "подобрать квартиру", "🏠 подобрать квартиру"]:
        clear_user_state(user_id)
        save_user_state(user_id, name, {'goal': 'buy'})
        vk_send_message(user_id, f"✨ {name}, 1️⃣ Ваш бюджет?", budget_keyboard())
        return
    
    if cmd in ["продать", "продажа объекта", "💰 продажа объекта"]:
        clear_user_state(user_id)
        save_user_state(user_id, name, {'goal': 'sell'})
        vk_send_message(user_id, f"💰 {name}, 1️⃣ Тип объекта?", property_type_keyboard())
        return
    
    if cmd in ["инвест", "инвестиции", "📊 инвестиции"]:
        clear_user_state(user_id)
        save_user_state(user_id, name, {'goal': 'invest'})
        vk_send_message(user_id, f"📊 {name}, 💡 Цель?", invest_goal_keyboard())
        return
    
    if cmd in ["чек-лист", "получить чек-лист", "📥 получить чек-лист"]:
        handle_checklist(user_id, name)
        return
    
    if cmd in ["помощь", "помощь и вопросы", "💬 помощь и вопросы"]:
        handle_help(user_id, name)
        return
    
    # ========================================
    # ✅ FAQ — УНИКАЛЬНЫЕ КОМАНДЫ (ПОСЛЕ СЦЕНАРИЕВ)
    # ========================================
    if cmd in ["инфо покупка", "как купить", "про подбор", "ℹ️ подробнее о подборе", "как подбирают квартиру"]:
        handle_faq(user_id, name, 'faq_buy')
        return
    
    if cmd in ["инфо продажа", "как продать", "про продажу", "ℹ️ подробнее о продаже", "как продают недвижимость"]:
        handle_faq(user_id, name, 'faq_sell')
        return
    
    # Остальные FAQ
    if cmd in ["faq_bot", "❓ как работает бот?", "как работает бот"]:
        handle_faq(user_id, name, 'faq_bot')
        return
    if cmd in ["faq_conditions", "🤝 условия работы", "условия"]:
        handle_faq(user_id, name, 'faq_conditions')
        return
    
    # ========================================
    # 🏠 ПОКУПКА
    # ========================================
    if state and state.get('goal') == 'buy':
        logger.info(f"🔄 In BUY scenario")
        
        if state.get('phone'):
            vk_send_message(user_id, f"""👋 {name}, вы уже оставили заявку на покупку!

✅ Ваши данные сохранены — я свяжусь с вами.

💡 Что можно сделать:
• Создать новую заявку
• Написать мне лично
• Вернуться в меню""", final_keyboard('buy'))
            return
        
        if not state.get('budget'):
            logger.info("BUY Step 1: Getting budget")
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'budget': budget})
                vk_send_message(user_id, f"✅ {budget}₽\n\n📍 Район?", district_keyboard())
                return
            vk_send_message(user_id, f"{name}, напишите бюджет (3000000 или 3 млн)", budget_keyboard())
            return
        
        if not state.get('district'):
            logger.info("BUY Step 2: Getting district")
            district_map = {'центр': 'Центральный', 'зареч': 'Зареченский', 'пролетар': 'Пролетарский',
                          'привокзал': 'Привокзальный', 'совет': 'Советский', 'любой': 'Любой', 'област': 'Область'}
            for k, v in district_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'district': v})
                    vk_send_message(user_id, f"✅ {v}\n\n⏰ Срок?", deadline_keyboard())
                    return
            vk_send_message(user_id, "Выберите район из кнопок 👇", district_keyboard())
            return
        
        if not state.get('deadline'):
            logger.info("BUY Step 3: Getting deadline")
            deadline_map = {'срочно': 'Срочно', 'неделю': 'Срочно', '1-3': '1-3 месяца',
                          'месяц': '1-3 месяца', '3-6': '3-6 месяцев', 'смотр': 'Присматриваюсь'}
            for k, v in deadline_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'deadline': v})
                    vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard())
                    return
            vk_send_message(user_id, "Выберите срок из кнопок 👇", deadline_keyboard())
            return
        
        if state.get('budget') and state.get('district') and state.get('deadline') and not state.get('phone'):
            logger.info("BUY Step 4: Getting phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"""🎉 {name}, заявка принята!

✅ **Вы указали:**
• Бюджет: {state.get('budget')}
• Район: {state.get('district')}
• Срок: {state.get('deadline')}
• Телефон: {phone}

📋 **Что дальше:**
1. Я изучу ваш запрос (15-30 мин)
2. Подберу лучшие варианты
3. Свяжусь с вами в ближайшее время

📞 **Можно позвонить прямо сейчас:** {VK_ADMIN_PHONE}
✍️ Или напишите в личные сообщения""", final_keyboard('buy'))
                logger.info("✅ BUY scenario completed with final message")
                return
            vk_send_message(user_id, f"⚠️ {name}, это не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    # ========================================
    # 💰 ПРОДАЖА
    # ========================================
    if state and state.get('goal') == 'sell':
        logger.info(f"🔄 In SELL scenario")
        
        if state.get('phone'):
            vk_send_message(user_id, f"""👋 {name}, вы уже оставили заявку на продажу!

✅ Ваши данные сохранены — я свяжусь с вами.

💡 Что можно сделать:
• Создать новую заявку
• Написать мне лично
• Вернуться в меню""", final_keyboard('sell'))
            return
        
        if not state.get('prop_type'):
            logger.info("SELL Step 1: Getting prop_type")
            prop_map = {'квартира': 'Квартира', 'дом': 'Дом', 'коттедж': 'Дом',
                       'комната': 'Комната', 'другое': 'Другое'}
            for k, v in prop_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'prop_type': v})
                    vk_send_message(user_id, f"✅ {v}\n\n📍 Район?", district_keyboard())
                    return
            vk_send_message(user_id, "Выберите тип из кнопок 👇", property_type_keyboard())
            return
        
        if not state.get('district'):
            logger.info("SELL Step 2: Getting district")
            district_map = {'центр': 'Центральный', 'зареч': 'Зареченский', 'пролетар': 'Пролетарский',
                          'привокзал': 'Привокзальный', 'совет': 'Советский', 'любой': 'Любой', 'област': 'Область'}
            for k, v in district_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'district': v})
                    vk_send_message(user_id, f"🎉 Отлично!\n\n📞 Телефон:", phone_keyboard())
                    return
            vk_send_message(user_id, "Выберите район из кнопок 👇", district_keyboard())
            return
        
        if state.get('prop_type') and state.get('district') and not state.get('phone'):
            logger.info("SELL Step 3: Getting phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"""🎉 {name}, заявка принята!

✅ **Вы указали:**
• Тип: {state.get('prop_type')}
• Район: {state.get('district')}
• Телефон: {phone}

📋 **Что дальше:**
1. Изучу ваш объект (30-60 мин)
2. Подготовлю оценку рынка
3. Свяжусь в ближайшее время

📞 **Можно позвонить прямо сейчас:** {VK_ADMIN_PHONE}
✍️ Или напишите в личные сообщения""", final_keyboard('sell'))
                logger.info("✅ SELL scenario completed with final message")
                return
            vk_send_message(user_id, f"⚠️ {name}, это не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    # ========================================
    # 📊 ИНВЕСТИЦИИ
    # ========================================
    if state and state.get('goal') == 'invest':
        logger.info(f"🔄 In INVEST scenario")
        
        if state.get('phone'):
            vk_send_message(user_id, f"""👋 {name}, вы уже оставили заявку на инвестиции!

✅ Ваши данные сохранены — я свяжусь с вами.

💡 Что можно сделать:
• Создать новую заявку
• Написать мне лично
• Вернуться в меню""", final_keyboard('invest'))
            return
        
        if not state.get('invest_goal'):
            logger.info("INVEST Step 1: Getting invest_goal")
            goal_map = {'перепродаж': 'Перепродажа', 'флиппинг': 'Перепродажа',
                       'аренд': 'Аренда', 'долгосрок': 'Долгосрок', 'консультаци': 'Консультация'}
            for k, v in goal_map.items():
                if k in cmd:
                    save_user_state(user_id, name, {'invest_goal': v})
                    vk_send_message(user_id, f"✅ {v}\n\n💵 Бюджет?", invest_budget_keyboard())
                    return
            vk_send_message(user_id, "Выберите цель из кнопок 👇", invest_goal_keyboard())
            return
        
        if not state.get('invest_budget'):
            logger.info("INVEST Step 2: Getting invest_budget")
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
                vk_send_message(user_id, "Выберите бюджет из кнопок 👇", invest_budget_keyboard())
                return
            vk_send_message(user_id, f"🎉 Почти готово!\n\n📞 Телефон:", phone_keyboard())
            return
        
        if state.get('invest_goal') and state.get('invest_budget') and not state.get('phone'):
            logger.info("INVEST Step 3: Getting phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                vk_send_message(user_id, f"""🎉 {name}, заявка принята!

✅ **Вы указали:**
• Цель: {state.get('invest_goal')}
• Бюджет: {state.get('invest_budget')}
• Телефон: {phone}

📋 **Что дальше:**
1. Проанализирую рынок (1-2 часа)
2. Подберу объекты с лучшей доходностью
3. Подготовлю расчёт ROI
4. Свяжусь в ближайшее время

📞 **Можно позвонить прямо сейчас:** {VK_ADMIN_PHONE}
✍️ Или напишите в личные сообщения""", final_keyboard('invest'))
                logger.info("✅ INVEST scenario completed with final message")
                return
            vk_send_message(user_id, f"⚠️ {name}, это не телефон. Попробуйте: +7 999 123-45-67", phone_keyboard())
            return
    
    # ========================================
    # ❌ НЕИЗВЕСТНАЯ КОМАНДА
    # ========================================
    vk_send_message(user_id, f"""👋 {name}, выберите действие:

🏠 Подобрать квартиру
💰 Продажа объекта  
📊 Инвестиции
📥 Чек-лист
💬 Помощь

Или напишите «начать» для главного меню 👇""", main_menu_keyboard())


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
    return "VK Bot OK v3.0", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
