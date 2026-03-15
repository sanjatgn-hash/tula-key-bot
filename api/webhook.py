# api/webhook.py
# Бот «Тульский ключ» — с умной валидацией телефона и сегментацией лидов

import os
import re
import json
import logging
import requests
from flask import Flask, request, jsonify

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== НАСТРОЙКИ ====================
RAW_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_TOKEN = "".join(RAW_TOKEN.split())

CHECKLIST_URL = os.getenv("CHECKLIST_URL", "https://t.me/tula_key_bot")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/tula_key_channel")
ADMIN_ID = os.getenv("ADMIN_ID", "")

if BOT_TOKEN:
    logger.info(f"✅ BOT_TOKEN loaded: {BOT_TOKEN[:10]}...")
else:
    logger.error("❌ BOT_TOKEN not set!")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ==================== TELEGRAM API ====================

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"❌ send_message error: {e}")
        return None


def answer_callback(callback_query_id, text=None):
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id, "show_alert": False}
    if text:
        data["text"] = text
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"❌ answer_callback error: {e}")
        return None


# ==================== ВАЛИДАЦИЯ ТЕЛЕФОНА ====================

def is_valid_phone(text):
    """
    Проверяет, похож ли текст на номер телефона.
    Поддерживает форматы:
    • +7 999 123-45-67
    • 8-999-123-45-67
    • 79991234567
    • 9991234567
    • +7(999)123-45-67
    """
    if not text:
        return False
    
    # Удаляем ВСЕ нецифровые символы кроме + в начале
    cleaned = re.sub(r'[^\d+]', '', text)
    
    # Убираем + если он не в начале
    if cleaned.startswith('++'):
        cleaned = '+' + cleaned.lstrip('+')
    
    # Паттерны для проверки:
    # 1. +7 + 10 цифр = 11 символов
    # 2. 7 + 10 цифр = 11 символов  
    # 3. 8 + 10 цифр = 11 символов
    # 4. 10 цифр (без кода страны)
    
    patterns = [
        r'^\+7\d{10}$',      # +79991234567
        r'^7\d{10}$',        # 79991234567
        r'^8\d{10}$',        # 89991234567
        r'^\d{10}$',         # 9991234567
        r'^\d{11}$',         # 79991234567 без +
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    
    return False


def normalize_phone(text):
    """Приводит телефон к единому формату: +79991234567"""
    cleaned = re.sub(r'[^\d+]', '', text)
    
    # Если начинается с 8 — меняем на +7
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    # Если начинается с 7 и 11 цифр — добавляем +
    elif cleaned.startswith('7') and len(cleaned) == 11 and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    # Если 10 цифр — добавляем +7
    elif cleaned.isdigit() and len(cleaned) == 10:
        cleaned = '+7' + cleaned
    
    return cleaned


# ==================== КЛАВИАТУРЫ ====================

def main_menu_kb():
    return {
        "inline_keyboard": [
            [{"text": "📥 Получить чек-лист", "callback_data": "get_checklist"}],
            [{"text": "🔍 Подобрать квартиру", "callback_data": "goal_buy"},
             {"text": "💰 Продать", "callback_data": "goal_sell"}],
            [{"text": "📊 Инвестиции", "callback_data": "goal_invest"},
             {"text": "💬 Задать вопрос", "callback_data": "faq"}],
            [{"text": "🎁 Пригласить друга", "callback_data": "referral"}]
        ]
    }


def budget_kb():
    return {
        "inline_keyboard": [
            [{"text": "до 3 млн", "callback_data": "budget_3m"},
             {"text": "3–5 млн", "callback_data": "budget_5m"}],
            [{"text": "5+ млн", "callback_data": "budget_5plus"},
             {"text": "Нужна помощь", "callback_data": "budget_help"}]
        ]
    }


def deadline_kb():
    return {
        "inline_keyboard": [
            [{"text": "🔥 Срочно", "callback_data": "deadline_urgent"}],
            [{"text": "📅 1-3 мес", "callback_data": "deadline_month"}],
            [{"text": "👀 Просто смотрю", "callback_data": "deadline_look"}]
        ]
    }


def property_type_kb():
    return {
        "inline_keyboard": [
            [{"text": "Квартира", "callback_data": "type_flat"},
             {"text": "Дом", "callback_data": "type_house"}],
            [{"text": "Комната", "callback_data": "type_room"},
             {"text": "Другое", "callback_data": "type_other"}]
        ]
    }


def district_kb():
    return {
        "inline_keyboard": [
            [{"text": "Центральный", "callback_data": "dist_center"},
             {"text": "Заречье", "callback_data": "dist_zarechye"}],
            [{"text": "Пролетарский", "callback_data": "dist_proletarsky"},
             {"text": "Любой", "callback_data": "dist_any"}]
        ]
    }


def invest_budget_kb():
    return {
        "inline_keyboard": [
            [{"text": "до 2 млн", "callback_data": "invest_2m"}],
            [{"text": "2–5 млн", "callback_data": "invest_5m"}],
            [{"text": "5+ млн", "callback_data": "invest_5plus"}]
        ]
    }


# ==================== ОТПРАВКА ЛИДА АДМИНУ ====================

def send_lead_to_admin(name, phone, user_data):
    """Отправляет сегментированный лид админу"""
    if not ADMIN_ID:
        return
    
    # Формируем текст лида
    goal_emoji = "🏠" if user_data.get('goal') == 'buy' else "💰" if user_data.get('goal') == 'sell' else "📊"
    
    lines = [
        f"🔥 НОВЫЙ ЛИД | {goal_emoji} {user_data.get('goal_text', '')}",
        f"━━━━━━━━━━━━━━",
        f"👤 Имя: {name}",
        f"📞 Телефон: {phone}",
        f"🆔 ID: {user_data.get('chat_id', '')}",
    ]
    
    # Добавляем параметры в зависимости от цели
    if user_data.get('goal') == 'buy':
        if user_data.get('budget'):
            lines.append(f"💰 Бюджет: {user_data['budget']}")
        if user_data.get('deadline'):
            lines.append(f"⏰ Срок: {user_data['deadline']}")
    
    elif user_data.get('goal') == 'sell':
        if user_data.get('prop_type'):
            lines.append(f"🏠 Тип: {user_data['prop_type']}")
        if user_data.get('district'):
            lines.append(f"📍 Район: {user_data['district']}")
    
    elif user_data.get('goal') == 'invest':
        if user_data.get('invest_budget'):
            lines.append(f"💵 Бюджет: {user_data['invest_budget']}")
    
    lines.append("━━━━━━━━━━━━━━")
    
    text = "\n".join(lines)
    
    try:
        send_message(ADMIN_ID, text)
        logger.info(f"📩 Lead notification sent to admin {ADMIN_ID}")
    except Exception as e:
        logger.error(f"❌ Failed to notify admin: {e}")


# ==================== ОБРАБОТЧИКИ ====================

def handle_start(chat_id, name):
    text = (
        f"🔑 Привет, {name}! Я — помощник «Тульского ключа»\n\n"
        f"Помогаю найти квартиру в Туле без стресса и переплат 🏠\n\n"
        f"🎁 Ваш подарок: чек-лист «7 ошибок при покупке жилья в Туле»\n"
        f"→ сэкономит от 100 000₽ и недели нервов"
    )
    send_message(chat_id, text, reply_markup=main_menu_kb())
    logger.info(f"📩 /start sent to {chat_id}")


def handle_callback(chat_id, callback_id, data, name, user_state):
    """Обработчик callback queries с сохранением состояния"""
    
    answer_callback(callback_id)
    
    if data == "get_checklist":
        text = (
            f"🎉 Готово!\n\n"
            f"📄 Чек-лист «7 ошибок при покупке»:\n{CHECKLIST_URL}\n\n"
            f"💡 Совет: сохраните ссылку в «Избранное» 📌\n\n"
            f"Чтобы я присылал только подходящие варианты, подскажите:"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🏠 Купить", "callback_data": "goal_buy"}],
                [{"text": "💰 Продать", "callback_data": "goal_sell"}],
                [{"text": "📊 Инвестировать", "callback_data": "goal_invest"}],
                [{"text": "🤔 Пока смотрю", "callback_data": "goal_browse"}]
            ]
        }
        send_message(chat_id, text, reply_markup=kb)
        logger.info(f"📥 Checklist sent to {chat_id}")
    
    # ==================== ПОКУПКА ====================
    elif data == "goal_buy":
        user_state['goal'] = 'buy'
        user_state['goal_text'] = 'Покупка'
        text = f"{name}, понял! 🔑 Чтобы подборка была точной:\n\n1️⃣ Ваш бюджет?"
        send_message(chat_id, text, reply_markup=budget_kb())
        logger.info(f"💾 User {chat_id} started BUY flow")
    
    elif data.startswith("budget_"):
        budget_map = {
            "budget_3m": "до 3 млн",
            "budget_5m": "3–5 млн",
            "budget_5plus": "5+ млн",
            "budget_help": "Нужна помощь"
        }
        user_state['budget'] = budget_map.get(data, "")
        text = "2️⃣ Когда планируете сделку?"
        send_message(chat_id, text, reply_markup=deadline_kb())
    
    elif data.startswith("deadline_"):
        deadline_map = {
            "deadline_urgent": "🔥 Срочно",
            "deadline_month": "📅 1-3 месяца",
            "deadline_look": "👀 Пока присматриваюсь"
        }
        user_state['deadline'] = deadline_map.get(data, "")
        
        if data == "deadline_urgent":
            # 🔥 Горячий лид — просим телефон
            text = (
                f"🔥 Вижу, вы ищете серьёзно!\n\n"
                f"📞 Напишите ваш номер телефона в любом формате:\n"
                f"• +7 999 123-45-67\n"
                f"• 8-999-123-45-67\n"
                f"• 9991234567\n"
                f"Я свяжусь с вами в течение 2 часов!"
            )
            send_message(chat_id, text)
            user_state['waiting_for_phone'] = True
        else:
            # 📅 Не срочно — показываем чек-лист и канал
            text = (
                f"✅ Понял, вы пока присматриваетесь!\n\n"
                f"📄 Если еще не скачали — получите чек-лист «7 ошибок при покупке»:\n"
                f"{CHECKLIST_URL}\n\n"
                f"📢 Подпишитесь на канал «Тульский ключ» — там лучшие предложения и новости:\n"
                f"{CHANNEL_LINK}\n\n"
                f"Когда будете готовы — просто напишите «ХОЧУ ПОДБОРКУ» или ваш номер телефона 🔑"
            )
            send_message(chat_id, text)
            logger.info(f"📬 Warm lead: {chat_id} — not urgent")
    
    # ==================== ПРОДАЖА ====================
    elif data == "goal_sell":
        user_state['goal'] = 'sell'
        user_state['goal_text'] = 'Продажа'
        text = f"{name}, помогу выгодно продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?"
        send_message(chat_id, text, reply_markup=property_type_kb())
        logger.info(f"💾 User {chat_id} started SELL flow")
    
    elif data.startswith("type_"):
        type_map = {
            "type_flat": "Квартира",
            "type_house": "Дом",
            "type_room": "Комната",
            "type_other": "Другое"
        }
        user_state['prop_type'] = type_map.get(data, "")
        text = "2️⃣ Район Тулы?"
        send_message(chat_id, text, reply_markup=district_kb())
    
    elif data.startswith("dist_"):
        district_map = {
            "dist_center": "Центральный",
            "dist_zarechye": "Заречье",
            "dist_proletarsky": "Пролетарский",
            "dist_any": "Любой"
        }
        user_state['district'] = district_map.get(data, "")
        
        text = (
            f"✅ Отлично! 🏡 Я подготовлю:\n"
            f"• Бесплатную оценку рыночной стоимости\n"
            f"• План продажи с прогнозом сроков\n"
            f"• Чек-лист «Как подготовить квартиру к продаже»\n\n"
            f"📞 Напишите ваш номер телефона в любом формате:\n"
            f"• +7 999 123-45-67\n"
            f"• 8-999-123-45-67\n"
            f"• 9991234567\n"
            f"Я свяжусь с вами в течение 2 часов!"
        )
        send_message(chat_id, text)
        user_state['waiting_for_phone'] = True
    
    # ==================== ИНВЕСТИЦИИ ====================
    elif data == "goal_invest":
        user_state['goal'] = 'invest'
        user_state['goal_text'] = 'Инвестиции'
        text = "📊 Калькулятор инвестора в недвижимость Тулы\n\nВыберите бюджет для расчёта:"
        send_message(chat_id, text, reply_markup=invest_budget_kb())
    
    elif data.startswith("invest_"):
        invest_map = {
            "invest_2m": "до 2 млн",
            "invest_5m": "2–5 млн",
            "invest_5plus": "5+ млн"
        }
        user_state['invest_budget'] = invest_map.get(data, "")
        
        calc = {
            "invest_2m": {"price": "2 000 000", "downpayment": "400 000", "monthly": "~18 000", "rent": "~15 000", "cashflow": "-3 000", "roi": "~8%"},
            "invest_5m": {"price": "5 000 000", "downpayment": "1 000 000", "monthly": "~45 000", "rent": "~35 000", "cashflow": "-10 000", "roi": "~10%"},
            "invest_5plus": {"price": "8 000 000+", "downpayment": "1 600 000+", "monthly": "~72 000+", "rent": "~55 000+", "cashflow": "-17 000+", "roi": "~12%"}
        }
        c = calc.get(data, calc["invest_2m"])
        text = (
            f"📈 Результаты расчёта:\n\n"
            f"🏢 Стоимость: {c['price']} ₽\n"
            f"💰 Первоначальный взнос: {c['downpayment']} ₽\n"
            f"📉 Платёж: {c['monthly']} ₽/мес\n"
            f"💵 Аренда: {c['rent']} ₽/мес\n"
            f"📦 Чистыми: {c['cashflow']} ₽/мес\n"
            f"📈 ROI: {c['roi']}\n\n"
            f"⚠️ Это ориентировочный расчёт.\n\n"
            f"💬 Хотите обсудить стратегию? Напишите ваш номер телефона 👇"
        )
        send_message(chat_id, text)
        user_state['waiting_for_phone'] = True
    
    # ==================== FAQ И ДРУГОЕ ====================
    elif data == "faq":
        text = (
            f"💬 Частые вопросы:\n\n"
            f"❓ Какая комиссия?\n"
            f"→ 2-3% от стоимости объекта, после сделки. Консультация — бесплатно 🔑\n\n"
            f"❓ Работаете с ипотекой?\n"
            f"→ Да! Со всеми банками Тулы. Есть партнёр-брокер — ставки ниже на 0.5-1% 📉\n\n"
            f"❓ Как проверить квартиру?\n"
            f"→ Проверяю юридическую чистоту, историю, обременения. Полный отчёт — перед сделкой ✅"
        )
        send_message(chat_id, text)
    
    elif data == "referral":
        text = (
            f"🤝 Приглашайте — получайте 15 000₽\n\n"
            f"Ваша ссылка:\n`https://t.me/tula_key_support_bot`\n\n"
            f"Отправьте другу — он получит чек-лист, а вы бонус после сделки! 💰"
        )
        send_message(chat_id, text)
    
    elif data == "goal_browse":
        text = (
            f"✅ Вы в списке рассылки!\n\n"
            f"📄 Пока ждёте — скачайте чек-лист «7 ошибок при покупке»:\n"
            f"{CHECKLIST_URL}\n\n"
            f"📢 И подпишитесь на канал с лучшими предложениями:\n"
            f"{CHANNEL_LINK}"
        )
        send_message(chat_id, text)
    
    logger.info(f"✅ Callback handled: {data} | State: {user_state}")


def handle_message(chat_id, text, name, user_state):
    """Обработчик текстовых сообщений (телефоны, вопросы)"""
    
    # Проверяем, ждём ли мы телефон от этого пользователя
    if user_state.get('waiting_for_phone') or is_valid_phone(text):
        if is_valid_phone(text):
            # Это телефон!
            phone = normalize_phone(text)
            
            # Отправляем подтверждение пользователю
            send_message(
                chat_id,
                f"✅ Спасибо, {name}! 🙏\n\n"
                f"Я получил ваш номер: {phone}\n"
                f"Свяжусь с вами в течение 2 часов!\n\n"
                f"А пока — посмотрите кейс: как я сэкономил клиенту 400 000₽ 👇\n"
                f"{CHANNEL_LINK}",
            )
            logger.info(f"📞 Phone received from {chat_id}: {phone}")
            
            # Отправляем сегментированный лид админу
            user_state['chat_id'] = chat_id
            user_state['phone'] = phone
            send_lead_to_admin(name, phone, user_state)
            
            # Сбрасываем состояние
            user_state.clear()
            return
    
    # Если не телефон — обычное сообщение
    send_message(
        chat_id,
        f"👋 Привет, {name}!\n\n"
        f"Если у вас есть вопрос — напишите его, я отвечу!\n\n"
        f"Или выберите действие:",
        reply_markup=main_menu_kb()
    )


def handle_update(update_data):
    """Главный обработчик обновлений"""
    update = update_data
    chat_id = None
    name = "Пользователь"
    
    # Извлекаем chat_id и name из любого типа обновления
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        name = message["from"].get("first_name", "Пользователь")
        text = message.get("text", "")
        
        if text == "/start":
            handle_start(chat_id, name)
        else:
            # Для текстовых сообщений создаём простое состояние
            user_state = {}
            handle_message(chat_id, text, name, user_state)
    
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_id = callback["id"]
        data = callback.get("data", "")
        name = callback["from"].get("first_name", "Пользователь")
        
        # Создаём состояние для отслеживания выбора пользователя
        user_state = {'chat_id': chat_id}
        handle_callback(chat_id, callback_id, data, name, user_state)


# ==================== РОУТЫ ====================

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("🏥 Health check requested")
    return "OK", 200


@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST']) if BOT_TOKEN else None
def webhook_handler():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set")
        return jsonify({"error": "Bot token not set"}), 500
    
    try:
        logger.info("📬 Webhook called!")
        
        update_data = request.get_json(force=True)
        logger.info(f"📩 Update received: {update_data.get('update_id')}")
        
        handle_update(update_data)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
