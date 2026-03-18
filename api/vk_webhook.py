# api/vk_webhook.py
# Tula Key Bot — ENGAGING VERSION v2.0

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
logger.info(f"VK_ADMIN_ID: {'OK' if VK_ADMIN_ID else 'MISSING'}")


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
    return {
        'action': {
            'type': 'text',
            'payload': json.dumps(payload, ensure_ascii=False),
            'label': label
        },
        'color': color
    }


def get_link_button(label, url):
    return {
        'action': {
            'type': 'open_link',
            'link': url
        },
        'label': label
    }


def create_keyboard(one_time=False, buttons=None):
    if buttons is None:
        buttons = []
    keyboard = {'one_time': one_time, 'buttons': buttons}
    return json.dumps(keyboard, ensure_ascii=False)


def main_menu_keyboard():
    """Главное меню — ПРОДАЮЩЕЕ"""
    buttons = [
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('💰 Продать квартиру', {'cmd': 'sell'}, 'primary')],
        [get_button('📥 Получить чек-лист', {'cmd': 'checklist'}, 'secondary')],
        [get_button('📊 Инвестиции', {'cmd': 'invest'}, 'secondary')],
        [get_button('💬 Помощь и вопросы', {'cmd': 'help'}, 'secondary')],
        [get_link_button('📢 Наш канал', VK_GROUP_LINK, )]
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
    """Все районы Тулы"""
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
    """Цель инвестиций"""
    buttons = [
        [get_button('💵 Перепродажа (флиппинг)', {'cmd': 'invest_goal', 'val': 'Перепродажа'}, 'primary')],
        [get_button('🏠 Сдача в аренду', {'cmd': 'invest_goal', 'val': 'Аренда'}, 'primary')],
        [get_button('📈 Долгосрочные вложения', {'cmd': 'invest_goal', 'val': 'Долгосрок'}, 'secondary')],
        [get_button('❓ Нужна консультация', {'cmd': 'invest_goal', 'val': 'Консультация'}, 'secondary')]
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
    buttons = [
        [get_button('🔙 В главное меню', {'cmd': 'menu'}, 'secondary')]
    ]
    return create_keyboard(one_time=True, buttons=buttons)


def contact_keyboard():
    """Кнопка связи с админом"""
    buttons = [
        [get_link_button('✍️ Написать мне лично', f'https://vk.com/im?sel={VK_ADMIN_ID}')],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
    ]
    return create_keyboard(one_time=True, buttons=buttons)


def help_keyboard():
    buttons = [
        [get_button('❓ Как работает бот?', {'cmd': 'faq_bot'}, 'secondary')],
        [get_button('💰 Условия работы', {'cmd': 'faq_conditions'}, 'secondary')],
        [get_button('🏠 Как подобрать квартиру?', {'cmd': 'faq_buy'}, 'secondary')],
        [get_button('💰 Как продать?', {'cmd': 'faq_sell'}, 'secondary')],
        [get_button('✍️ Связаться со мной', {'cmd': 'contact'}, 'primary')],
        [get_button('🔙 В главное меню', {'cmd': 'menu'}, 'secondary')]
    ]
    return create_keyboard(one_time=False, buttons=buttons)


def checklist_keyboard():
    buttons = [
        [get_link_button('📥 Скачать чек-лист', CHECKLIST_URL or VK_GROUP_LINK)],
        [get_button('🏠 Подобрать квартиру', {'cmd': 'buy'}, 'primary')],
        [get_button('📢 Подписаться на канал', VK_GROUP_LINK, ), get_link_button('📢 Канал', VK_GROUP_LINK)],
        [get_button('🔙 В меню', {'cmd': 'menu'}, 'secondary')]
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
            logger.error("Google Sheets credentials not set")
            return None
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        first_row = sheet.row_values(1)
        if not first_row or first_row[0] != 'chat_id':
            sheet.append_row(['chat_id', 'name', 'username', 'goal', 'budget', 'deadline', 'prop_type', 'district', 'invest_goal', 'invest_budget', 'phone', 'updated_at', 'status'])
            logger.info("Created Google Sheets headers")
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
                    existing_data = {
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_goal': row[8] if len(row) > 8 else '',
                        'invest_budget': row[9] if len(row) > 9 else '',
                    }
                    break
        
        merged = {**existing_data, **data}
        row_data = [
            str(chat_id), name or '', '',
            merged.get('goal', ''), merged.get('budget', ''),
            merged.get('deadline', ''), merged.get('prop_type', ''),
            merged.get('district', ''), merged.get('invest_goal', ''),
            merged.get('invest_budget', ''), merged.get('phone', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'new'
        ]
        
        if row_idx:
            sheet.update(f'A{row_idx}:M{row_idx}', [row_data])
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
    sheet = get_sheet()
    if not sheet:
        return None
    try:
        for row in sheet.get_all_values()[1:]:
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[12] if len(row) > 12 else ''
                if status == 'new':
                    return {
                        'chat_id': row[0],
                        'name': row[1],
                        'goal': row[3] if len(row) > 3 else '',
                        'budget': row[4] if len(row) > 4 else '',
                        'deadline': row[5] if len(row) > 5 else '',
                        'prop_type': row[6] if len(row) > 6 else '',
                        'district': row[7] if len(row) > 7 else '',
                        'invest_goal': row[8] if len(row) > 8 else '',
                        'invest_budget': row[9] if len(row) > 9 else '',
                        'phone': row[10] if len(row) > 10 else '',
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
        rows = sheet.get_all_values()
        for i, row in enumerate(rows[1:], 2):
            if row and len(row) > 0 and str(row[0]) == str(chat_id):
                status = row[12] if len(row) > 12 else ''
                if status == 'new':
                    sheet.update_cell(i, 13, 'sent')
                    sheet.update_cell(i, 12, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
    
    if goal == 'buy':
        if state.get('budget'):
            lines.append(f"💰 Бюджет: {state['budget']}")
        if state.get('deadline'):
            lines.append(f"⏰ Срок: {state['deadline']}")
        if state.get('district'):
            lines.append(f"📍 Район: {state['district']}")
    elif goal == 'sell':
        if state.get('prop_type'):
            lines.append(f"🏠 Тип: {state['prop_type']}")
        if state.get('district'):
            lines.append(f"📍 Район: {state['district']}")
    elif goal == 'invest':
        if state.get('invest_goal'):
            lines.append(f"🎯 Цель: {state['invest_goal']}")
        if state.get('invest_budget'):
            lines.append(f"💵 Бюджет: {state['invest_budget']}")
    
    lines.append("━" * 30)
    
    if VK_ADMIN_ID:
        vk_send_message(VK_ADMIN_ID, "\n".join(lines))
        logger.info(f"Lead sent to admin {VK_ADMIN_ID}")


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    # Очищаем состояние
    save_user_state(user_id, name, {
        'goal': '', 'budget': '', 'deadline': '',
        'prop_type': '', 'district': '', 
        'invest_goal': '', 'invest_budget': '', 'phone': ''
    })
    
    text = f"""✨ {name}, добро пожаловать в «Тульский ключ»!

Я здесь, чтобы исполнить ваше желание по недвижимости — без стресса, обмана и переплат.

🎁 **Ваш приветственный бонус:**
Чек-лист «7 фатальных ошибок при покупке квартиры» — скачайте бесплатно!

🏠 **Что я умею:**
• Подобрать квартиру под ваш бюджет
• Помочь выгодно продать недвижимость
• Подобрать объект для инвестиций
• Ответить на любые вопросы

Выберите, что вас интересует 👇"""
    
    vk_send_message(user_id, text, main_menu_keyboard())


def handle_checklist(user_id, name):
    text = f"""🎉 {name}, ваш чек-лист готов!

📄 **«7 фатальных ошибок при покупке квартиры»**

Этот чек-лист уже сэкономил моим клиентам более 2 млн рублей на неудачных сделках.

⚠️ **Внимание:** информация в чек-листе актуальна для рынка Тулы 2026 года.

👇 **Скачивайте по кнопке ниже!**

💡 **Кстати:** пока изучаете чек-лист, могу подобрать для вас 3-5 квартир по вашим критериям — бесплатно!"""
    
    vk_send_message(user_id, text, checklist_keyboard())


def handle_help(user_id, name):
    text = f"""💬 {name}, я с радостью помогу!

**Частые вопросы:**

❓ **Как работает бот?**
Просто отвечайте на вопросы — я подберу варианты под ваши критерии.

❓ **Условия работы?**
Комиссия 2-3% только после успешной сделки. Никаких предоплат.

❓ **Как подобрать квартиру?**
Нажмите «Подобрать квартиру» → укажите бюджет → выберите район → оставьте телефон.

❓ **Как продать?**
Нажмите «Продать квартиру» → укажите тип → район → телефон. Я оценю и найду покупателя.

❓ **Можно ли задать личный вопрос?**
Конечно! Кнопка «Связаться со мной» ниже 👇

Выберите тему или напишите свой вопрос 👇"""
    
    vk_send_message(user_id, text, help_keyboard())


def handle_faq(user_id, name, topic):
    faqs = {
        'faq_bot': """🤖 **Как работает бот?**

1. Выберите цель (купить/продать/инвест)
2. Ответьте на 3-4 вопроса
3. Оставьте телефон
4. Я свяжусь в течение 2 часов

Это бесплатно и ни к чему не обязывает! 🎁""",
        
        'faq_conditions': """💰 **Условия работы:**

• Комиссия: 2-3% от стоимости
• Оплата: только после сделки
• Сопровождение: полное (юрист, банк, МФЦ)
• Гарантия: юридическая чистота

Никаких скрытых платежей! ✅""",
        
        'faq_buy': """🏠 **Как подобрать квартиру:**

1. Определяем бюджет
2. Выбираем район
3. Учитываем пожелания (этаж, площадь, ремонт)
4. Показываю 3-5 лучших вариантов
5. Помогаю с торгом и оформлением

Средний срок подбора: 7-14 дней ⏱️""",
        
        'faq_sell': """💰 **Как продать квартиру:**

1. Бесплатная оценка объекта
2. Профессиональные фото
3. Размещение на всех площадках
4. Показы потенциальным покупателям
5. Сопровождение сделки

Средний срок продажи: 2-4 недели 📅"""
    }
    
    text = faqs.get(topic, "Вопрос не найден. Нажмите «Связаться со мной» для личного вопроса.")
    vk_send_message(user_id, text, help_keyboard())


def handle_contact(user_id, name):
    text = f"""✍️ {name}, я на связи!

Нажмите кнопку ниже — откроется диалог со мной в личных сообщениях.

Отвечаю в течение 2 часов (в рабочее время 9:00-20:00) 🕐"""
    
    vk_send_message(user_id, text, contact_keyboard())


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    
    # Получаем имя из VK API если не передано
    if not name or name == "Пользователь":
        name = vk_get_user_name(user_id)
        logger.info(f"Resolved name: {name}")
    
    state = get_user_state(user_id)
    
    logger.info(f"=== MESSAGE START ===")
    logger.info(f"User: {user_id}, Name: {name}, Text: '{text}'")
    logger.info(f"Current state: {state}")
    
    # ============================================
    # ✅ 1. КНОПКИ ГЛАВНОГО МЕНЮ
    # ============================================
    
    if cmd in ["начать", "старт", "/start", "меню", "🔙 в главное меню", "🔙 в меню"]:
        handle_start(user_id, name)
        return
    
    if cmd in ["купить", "подобрать квартиру", "🏠 подобрать квартиру"]:
        save_user_state(user_id, name, {'goal': 'buy'})
        text = f"""✨ Отлично, {name}! Помогу найти квартиру мечты в Туле!

🏠 **Подбор квартиры — это просто:**
1. Указываем бюджет
2. Выбираем район
3. Оставляем телефон

Начнём? 👇

💡 *Пока вы выбираете, я уже ищу лучшие варианты!*"""
        vk_send_message(user_id, text, budget_keyboard())
        return
    
    if cmd in ["продать", "продать квартиру", "💰 продать квартиру"]:
        save_user_state(user_id, name, {'goal': 'sell'})
        text = f"""💰 {name}, помогу продать вашу недвижимость выгодно!

🏠 **Продажа с «Тульский ключ»:**
• Бесплатная оценка
• Профессиональные фото
• Покупатели уже ждут

Что продаём? 👇"""
        vk_send_message(user_id, text, property_type_keyboard())
        return
    
    if cmd in ["чек-лист", "получить чек-лист", "📥 получить чек-лист"]:
        handle_checklist(user_id, name)
        return
    
    if cmd in ["инвест", "инвестиции", "📊 инвестиции"]:
        save_user_state(user_id, name, {'goal': 'invest'})
        text = f"""📊 {name}, инвестиции в недвижимость — это надёжно!

💡 **Цель инвестиций?**

• **Перепродажа** — купил дешевле, продал дороже (6-12 месяцев)
• **Аренда** — пассивный доход ежемесячно
• **Долгосрок** — сохранение капитала на годы

Что вас интересует? 👇"""
        vk_send_message(user_id, text, invest_goal_keyboard())
        return
    
    if cmd in ["помощь", "помощь и вопросы", "💬 помощь и вопросы"]:
        handle_help(user_id, name)
        return
    
    if cmd in ["канал", "наш канал", "📢 наш канал", "подписаться"]:
        text = f"""📢 {name}, рад что хотите быть в курсе!

В нашем канале:
• Горячие предложения (эксклюзивы)
• Изменения рынка Тулы
• Советы по недвижимости
• Акции и скидки

Подписывайтесь 👇"""
        vk_send_message(user_id, text, main_menu_keyboard())
        return
    
    # FAQ кнопки
    if cmd in ["faq_bot", "❓ как работает бот?", "как работает бот"]:
        handle_faq(user_id, name, 'faq_bot')
        return
    if cmd in ["faq_conditions", "💰 условия работы", "условия работы"]:
        handle_faq(user_id, name, 'faq_conditions')
        return
    if cmd in ["faq_buy", "🏠 как подобрать квартиру?", "как подобрать квартиру"]:
        handle_faq(user_id, name, 'faq_buy')
        return
    if cmd in ["faq_sell", "💰 как продать?", "как продать"]:
        handle_faq(user_id, name, 'faq_sell')
        return
    if cmd in ["contact", "связаться со мной", "✍️ связаться со мной", "написать мне лично"]:
        handle_contact(user_id, name)
        return
    
    # ============================================
    # ✅ 2. СЦЕНАРИЙ ПОКУПКИ
    # ============================================
    if state and state.get('goal') == 'buy':
        logger.info("In BUY scenario")
        
        if state.get('phone'):
            vk_send_message(user_id, f"👋 {name}, выберите действие:", main_menu_keyboard())
            return
        
        if not state.get('budget'):
            logger.info("Step 1: No budget")
            budget = extract_budget(text)
            if budget:
                save_user_state(user_id, name, {'budget': budget})
                text = f"""✅ Бюджет {budget}₽ — отлично!

📍 **Теперь выберите район:**

• Центральный — жизнь в центре событий
• Зареченский — тихо, зелёно, семейно
• Пролетарский — развитая инфраструктура
• Привокзальный — удобная транспортная доступность
• Советский — новый район, современно

Или «Любой район» если открыты к вариантам 👇"""
                vk_send_message(user_id, text, district_keyboard())
                return
            else:
                vk_send_message(user_id, f"{name}, напишите бюджет (например: 3000000 или 3 млн)\n\n💡 *Средний бюджет для 1-к в Туле: 2.5-3 млн ₽*", budget_keyboard())
                return
        
        if state.get('budget') and not state.get('district'):
            logger.info("Step 2: Need district")
            if 'центр' in cmd:
                save_user_state(user_id, name, {'district': 'Центральный'})
            elif 'зареч' in cmd:
                save_user_state(user_id, name, {'district': 'Зареченский'})
            elif 'пролетар' in cmd:
                save_user_state(user_id, name, {'district': 'Пролетарский'})
            elif 'привокзал' in cmd:
                save_user_state(user_id, name, {'district': 'Привокзальный'})
            elif 'совет' in cmd:
                save_user_state(user_id, name, {'district': 'Советский'})
            elif 'любой' in cmd:
                save_user_state(user_id, name, {'district': 'Любой'})
            elif 'област' in cmd:
                save_user_state(user_id, name, {'district': 'Область'})
            else:
                vk_send_message(user_id, f"{name}, выберите район из кнопок 👇", district_keyboard())
                return
            
            text = f"""✅ {state.get('district')} — отличный выбор!

⏰ **Когда планируете сделку?**

🔥 Срочно — уже на этой неделе
📅 1-3 месяца — есть время на подбор
📅 3-6 месяцев — спокойно выбираем
👀 Просто смотрю — изучаю рынок

💡 *Чем точнее срок — тем лучше подберу варианты!*"""
            vk_send_message(user_id, text, deadline_keyboard())
            return
        
        if state.get('budget') and state.get('district') and not state.get('deadline'):
            logger.info("Step 3: Need deadline")
            if 'срочно' in cmd or 'неделю' in cmd:
                save_user_state(user_id, name, {'deadline': 'Срочно'})
            elif '1-3' in cmd or 'месяц' in cmd:
                save_user_state(user_id, name, {'deadline': '1-3 месяца'})
            elif '3-6' in cmd:
                save_user_state(user_id, name, {'deadline': '3-6 месяцев'})
            elif 'смотр' in cmd or 'присматриваюсь' in cmd:
                save_user_state(user_id, name, {'deadline': 'Присматриваюсь'})
            else:
                vk_send_message(user_id, "Выберите срок из кнопок 👇", deadline_keyboard())
                return
            
            text = f"""🎉 Почти готово, {name}!

📞 **Оставьте телефон** — я свяжусь в течение 2 часов и:
• Подберу 3-5 квартир под ваш запрос
• Организую просмотры в удобное время
• Помогу с торгом и оформлением

🔒 *Телефон не передаётся третьим лицам*"""
            vk_send_message(user_id, text, phone_keyboard())
            return
        
        if state.get('budget') and state.get('district') and state.get('deadline') and not state.get('phone'):
            logger.info("Step 4: Need phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                text = f"""🎉 {name}, спасибо! Вы сделали первый шаг к квартире мечты!

✅ **Что дальше:**
1. Я изучу ваш запрос (15 минут)
2. Подберу 3-5 лучших вариантов
3. Свяжусь с вами в течение 2 часов
4. Договоримся о просмотрах

📞 Телефон: {phone}

🎁 **Бонус:** пока жду звонка, загляните в наш канал — там эксклюзивные предложения!"""
                vk_send_message(user_id, text, main_menu_keyboard())
                return
            else:
                vk_send_message(user_id, f"⚠️ {name}, это не похоже на телефон.\n\nПопробуйте ещё раз:\n+7 999 123-45-67", phone_keyboard())
                return
    
    # ============================================
    # ✅ 3. СЦЕНАРИЙ ПРОДАЖИ
    # ============================================
    if state and state.get('goal') == 'sell':
        logger.info("In SELL scenario")
        
        if state.get('phone'):
            vk_send_message(user_id, f"👋 {name}, выберите действие:", main_menu_keyboard())
            return
        
        if not state.get('prop_type'):
            logger.info("Step 1: No prop_type")
            if 'квартира' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Квартира'})
            elif 'дом' in cmd or 'коттедж' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Дом'})
            elif 'комната' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Комната'})
            elif 'другое' in cmd:
                save_user_state(user_id, name, {'prop_type': 'Другое'})
            else:
                vk_send_message(user_id, f"{name}, выберите тип недвижимости 👇", property_type_keyboard())
                return
            
            text = f"""✅ {state.get('prop_type')} — понял!

📍 **В каком районе находится объект?**

Это поможет мне оценить стоимость и найти покупателей 👇"""
            vk_send_message(user_id, text, district_keyboard())
            return
        
        if state.get('prop_type') and not state.get('district'):
            logger.info("Step 2: Need district")
            if 'центр' in cmd:
                save_user_state(user_id, name, {'district': 'Центральный'})
            elif 'зареч' in cmd:
                save_user_state(user_id, name, {'district': 'Зареченский'})
            elif 'пролетар' in cmd:
                save_user_state(user_id, name, {'district': 'Пролетарский'})
            elif 'привокзал' in cmd:
                save_user_state(user_id, name, {'district': 'Привокзальный'})
            elif 'совет' in cmd:
                save_user_state(user_id, name, {'district': 'Советский'})
            elif 'любой' in cmd:
                save_user_state(user_id, name, {'district': 'Любой'})
            elif 'област' in cmd:
                save_user_state(user_id, name, {'district': 'Область'})
            else:
                vk_send_message(user_id, "Выберите район из кнопок 👇", district_keyboard())
                return
            
            text = f"""🎉 Отлично, {name}!

📞 **Оставьте телефон** — я:
• Бесплатно оценю ваш объект
• Расскажу о сроках продажи
• Подготовлю план действий

🔒 *Конфиденциально*"""
            vk_send_message(user_id, text, phone_keyboard())
            return
        
        if state.get('prop_type') and state.get('district') and not state.get('phone'):
            logger.info("Step 3: Need phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                text = f"""✅ {name}, спасибо!

📊 **Что дальше:**
1. Изучу ваш объект (30 минут)
2. Подготовлю оценку рынка
3. Свяжусь в течение 2 часов
4. Обсудим стратегию продажи

📞 Телефон: {phone}

💡 *Пока жду звонка, скачайте чек-лист — там советы по предпродажной подготовке!*"""
                vk_send_message(user_id, text, checklist_keyboard())
                return
            else:
                vk_send_message(user_id, f"⚠️ {name}, это не телефон.\n\nПопробуйте: +7 999 123-45-67", phone_keyboard())
                return
    
    # ============================================
    # ✅ 4. СЦЕНАРИЙ ИНВЕСТИЦИЙ
    # ============================================
    if state and state.get('goal') == 'invest':
        logger.info("In INVEST scenario")
        
        if state.get('phone'):
            vk_send_message(user_id, f"👋 {name}, выберите действие:", main_menu_keyboard())
            return
        
        if not state.get('invest_goal'):
            logger.info("Step 1: No invest_goal")
            if 'перепродаж' in cmd or 'флиппинг' in cmd:
                save_user_state(user_id, name, {'invest_goal': 'Перепродажа'})
            elif 'аренд' in cmd:
                save_user_state(user_id, name, {'invest_goal': 'Аренда'})
            elif 'долгосрок' in cmd or 'долгосрочн' in cmd:
                save_user_state(user_id, name, {'invest_goal': 'Долгосрок'})
            elif 'консультаци' in cmd:
                save_user_state(user_id, name, {'invest_goal': 'Консультация'})
            else:
                vk_send_message(user_id, "Выберите цель инвестиций 👇", invest_goal_keyboard())
                return
            
            text = f"""✅ {state.get('invest_goal')} — отличный выбор!

💵 **Какой бюджет рассматриваете?**

💡 *Для перепродажи: от 2 млн ₽*\n*Для аренды: от 3 млн ₽*"""
            vk_send_message(user_id, text, invest_budget_keyboard())
            return
        
        if state.get('invest_goal') and not state.get('invest_budget'):
            logger.info("Step 2: Need invest_budget")
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
                vk_send_message(user_id, "Выберите бюджет или напишите цифрами 👇", invest_budget_keyboard())
                return
            
            text = f"""🎉 {name}, почти готово!

📞 **Оставьте телефон** — я:
• Подберу объекты с доходностью 8-12%
• Рассчитаю ROI для каждого варианта
• Покажу прогноз роста стоимости

🔒 *Конфиденциально*"""
            vk_send_message(user_id, text, phone_keyboard())
            return
        
        if state.get('invest_goal') and state.get('invest_budget') and not state.get('phone'):
            logger.info("Step 3: Need phone")
            phone, valid = normalize_phone(text)
            if valid:
                save_user_state(user_id, name, {'phone': phone})
                send_lead_to_admin(name, phone, user_id, state)
                mark_lead_sent(user_id)
                text = f"""📊 {name}, спасибо за интерес к инвестициям!

✅ **Что дальше:**
1. Проанализирую рынок (1 час)
2. Подберу 3-5 объектов с лучшей доходностью
3. Подготовлю расчёт ROI
4. Свяжусь в течение 2 часов

📞 Телефон: {phone}

💡 *Инвестиции в недвижимость Тулы: 8-12% годовых*"""
                vk_send_message(user_id, text, main_menu_keyboard())
                return
            else:
                vk_send_message(user_id, f"⚠️ {name}, это не телефон.\n\nПопробуйте: +7 999 123-45-67", phone_keyboard())
                return
    
    # ============================================
    # ✅ 5. НЕИЗВЕСТНАЯ КОМАНДА
    # ============================================
    vk_send_message(user_id, f"👋 {name}, выберите действие:", main_menu_keyboard())
    logger.info("=== MESSAGE END ===")


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
            name = msg.get("from_name", "")
            text = msg.get("text", "")
            logger.info(f"Message: user={user_id}, name='{name}', text='{text}'")
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
    return "VK Bot OK v2.0", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
