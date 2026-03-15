# api/webhook.py
# Бот «Тульский ключ» — сегментация через callback_data (работает в serverless!)

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
    if not text:
        return False
    cleaned = re.sub(r'[^\d+]', '', text)
    if cleaned.startswith('++'):
        cleaned = '+' + cleaned.lstrip('+')
    
    patterns = [
        r'^\+7\d{10}$', r'^7\d{10}$', r'^8\d{10}$', r'^\d{10}$', r'^\d{11}$',
    ]
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    return False


def normalize_phone(text):
    cleaned = re.sub(r'[^\d+]', '', text)
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11 and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    elif cleaned.isdigit() and len(cleaned) == 10:
        cleaned = '+7' + cleaned
    return cleaned


# ==================== КЛАВИАТУРЫ С КОНТЕКСТОМ ====================

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


def budget_kb(goal):
    """Кнопки бюджета с кодированием цели"""
    return {
        "inline_keyboard": [
            [{"text": "до 3 млн", "callback_data": f"{goal}|b3"}],
            [{"text": "3–5 млн", "callback_data": f"{goal}|b5"}],
            [{"text": "5+ млн", "callback_data": f"{goal}|b5p"}],
            [{"text": "Нужна помощь", "callback_data": f"{goal}|bhelp"}]
        ]
    }


def deadline_kb(goal, budget_code):
    """Кнопки срока с кодированием цели и бюджета"""
    return {
        "inline_keyboard": [
            [{"text": "🔥 Срочно", "callback_data": f"{goal}|{budget_code}|urgent"}],
            [{"text": "📅 1-3 мес", "callback_data": f"{goal}|{budget_code}|month"}],
            [{"text": "👀 Просто смотрю", "callback_data": f"{goal}|{budget_code}|look"}]
        ]
    }


def property_type_kb(goal):
    return {
        "inline_keyboard": [
            [{"text": "Квартира", "callback_data": f"{goal}|flat"}],
            [{"text": "Дом", "callback_data": f"{goal}|house"}],
            [{"text": "Комната", "callback_data": f"{goal}|room"}],
            [{"text": "Другое", "callback_data": f"{goal}|other"}]
        ]
    }


def district_kb(goal, type_code):
    return {
        "inline_keyboard": [
            [{"text": "Центральный", "callback_data": f"{goal}|{type_code}|center"}],
            [{"text": "Заречье", "callback_data": f"{goal}|{type_code}|zarechye"}],
            [{"text": "Пролетарский", "callback_data": f"{goal}|{type_code}|proletarsky"}],
            [{"text": "Любой", "callback_data": f"{goal}|{type_code}|any"}]
        ]
    }


def invest_budget_kb(goal):
    return {
        "inline_keyboard": [
            [{"text": "до 2 млн", "callback_data": f"{goal}|i2"}],
            [{"text": "2–5 млн", "callback_data": f"{goal}|i5"}],
            [{"text": "5+ млн", "callback_data": f"{goal}|i5p"}]
        ]
    }


# ==================== МАППИНГИ ДЛЯ ЧЕЛОВЕЧЕСКОГО ЧТЕНИЯ ====================

BUDGET_MAP = {
    "b3": "до 3 млн", "b5": "3–5 млн", "b5p": "5+ млн", "bhelp": "Нужна помощь"
}
DEADLINE_MAP = {
    "urgent": "🔥 Срочно", "month": "📅 1-3 месяца", "look": "👀 Пока присматриваюсь"
}
TYPE_MAP = {
    "flat": "Квартира", "house": "Дом", "room": "Комната", "other": "Другое"
}
DISTRICT_MAP = {
    "center": "Центральный", "zarechye": "Заречье", 
    "proletarsky": "Пролетарский", "any": "Любой"
}
INVEST_MAP = {
    "i2": "до 2 млн", "i5": "2–5 млн", "i5p": "5+ млн"
}
GOAL_MAP = {
    "buy": ("🏠", "Покупка"),
    "sell": ("💰", "Продажа"),
    "invest": ("📊", "Инвестиции")
}


# ==================== ОТПРАВКА ЛИДА АДМИНУ ====================

def send_lead_to_admin(name, phone, chat_id, goal_code, context):
    """Отправляет сегментированный лид админу"""
    if not ADMIN_ID:
        return
    
    emoji, goal_text = GOAL_MAP.get(goal_code, ("❓", "Неизвестно"))
    
    lines = [
        f"🔥 НОВЫЙ ЛИД | {emoji} {goal_text}",
        f"━━━━━━━━━━━━━━",
        f"👤 Имя: {name}",
        f"📞 Телефон: {phone}",
        f"🆔 ID: {chat_id}",
    ]
    
    # Добавляем контекст в зависимости от цели
    if goal_code == "buy":
        if context.get("budget"):
            lines.append(f"💰 Бюджет: {context['budget']}")
        if context.get("deadline"):
            lines.append(f"⏰ Срок: {context['deadline']}")
    
    elif goal_code == "sell":
        if context.get("prop_type"):
            lines.append(f"🏠 Тип: {context['prop_type']}")
        if context.get("district"):
            lines.append(f"📍 Район: {context['district']}")
    
    elif goal_code == "invest":
        if context.get("invest_budget"):
            lines.append(f"💵 Бюджет: {context['invest_budget']}")
    
    lines.append("━━━━━━━━━━━━━━")
    
    text = "\n".join(lines)
    
    try:
        send_message(ADMIN_ID, text)
        logger.info(f"📩 Lead sent to admin: {goal_text} | {name} | {phone}")
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


def handle_callback(chat_id, callback_id, data, name):
    """Обработчик callback queries с сегментацией через callback_data"""
    
    answer_callback(callback_id)
    
    # ==================== ГЛАВНОЕ МЕНЮ ====================
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
        return
    
    # ==================== ПОКУПКА ====================
    if data == "goal_buy":
        text = f"{name}, понял! 🔑 Чтобы подборка была точной:\n\n1️⃣ Ваш бюджет?"
        send_message(chat_id, text, reply_markup=budget_kb("buy"))
        logger.info(f"💾 User {chat_id} started BUY flow")
        return
    
    if data.startswith("buy|"):
        parts = data.split("|")
        
        # buy|b3 → выбор бюджета
        if len(parts) == 2 and parts[1].startswith("b"):
            budget_code = parts[1]
            budget_text = BUDGET_MAP.get(budget_code, "")
            text = f"2️⃣ Когда планируете сделку?"
            send_message(chat_id, text, reply_markup=deadline_kb("buy", budget_code))
            logger.info(f"💾 User {chat_id} selected budget: {budget_text}")
            return
        
        # buy|b3|urgent → выбор срока + горячий лид
        if len(parts) == 3:
            budget_code = parts[1]
            deadline_code = parts[2]
            budget_text = BUDGET_MAP.get(budget_code, "")
            deadline_text = DEADLINE_MAP.get(deadline_code, "")
            
            if deadline_code == "urgent":
                # 🔥 Горячий лид — отправляем уведомление и просим телефон
                context = {"budget": budget_text, "deadline": deadline_text}
                # Отправляем лид СЕЙЧАС (без телефона, добавим потом)
                send_lead_to_admin(name, "⏳ Ожидается", chat_id, "buy", context)
                
                text = (
                    f"🔥 Вижу, вы ищете серьёзно!\n\n"
                    f"📞 Напишите ваш номер телефона в любом формате:\n"
                    f"• +7 999 123-45-67\n"
                    f"• 8-999-123-45-67\n"
                    f"• 9991234567\n"
                    f"Я свяжусь с вами в течение 2 часов!"
                )
                send_message(chat_id, text)
                logger.info(f"🔥 HOT LEAD: buy | {budget_text} | {deadline_text} | {name}")
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
                logger.info(f"📬 Warm lead: buy | {budget_text} | {deadline_text}")
            return
    
    # ==================== ПРОДАЖА ====================
    if data == "goal_sell":
        text = f"{name}, помогу выгодно продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?"
        send_message(chat_id, text, reply_markup=property_type_kb("sell"))
        logger.info(f"💾 User {chat_id} started SELL flow")
        return
    
    if data.startswith("sell|"):
        parts = data.split("|")
        
        # sell|flat → выбор типа
        if len(parts) == 2:
            type_code = parts[1]
            type_text = TYPE_MAP.get(type_code, "")
            text = "2️⃣ Район Тулы?"
            send_message(chat_id, text, reply_markup=district_kb("sell", type_code))
            logger.info(f"💾 User {chat_id} selected type: {type_text}")
            return
        
        # sell|flat|center → выбор района + лид
        if len(parts) == 3:
            type_code = parts[1]
            district_code = parts[2]
            type_text = TYPE_MAP.get(type_code, "")
            district_text = DISTRICT_MAP.get(district_code, "")
            
            # 🔥 Отправляем лид СЕЙЧАС
            context = {"prop_type": type_text, "district": district_text}
            send_lead_to_admin(name, "⏳ Ожидается", chat_id, "sell", context)
            
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
            logger.info(f"🔥 HOT LEAD: sell | {type_text} | {district_text} | {name}")
            return
    
    # ==================== ИНВЕСТИЦИИ ====================
    if data == "goal_invest":
        text = "📊 Калькулятор инвестора в недвижимость Тулы\n\nВыберите бюджет для расчёта:"
        send_message(chat_id, text, reply_markup=invest_budget_kb("invest"))
        return
    
    if data.startswith("invest|"):
        parts = data.split("|")
        
        if len(parts) == 2:
            invest_code = parts[1]
            invest_text = INVEST_MAP.get(invest_code, "")
            
            calc = {
                "i2": {"price": "2 000 000", "downpayment": "400 000", "monthly": "~18 000", "rent": "~15 000", "cashflow": "-3 000", "roi": "~8%"},
                "i5": {"price": "5 000 000", "downpayment": "1 000 000", "monthly": "~45 000", "rent": "~35 000", "cashflow": "-10 000", "roi": "~10%"},
                "i5p": {"price": "8 000 000+", "downpayment": "1 600 000+", "monthly": "~72 000+", "rent": "~55 000+", "cashflow": "-17 000+", "roi": "~12%"}
            }
            c = calc.get(invest_code, calc["i2"])
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
            
            # 🔥 Отправляем лид для инвестиций
            context = {"invest_budget": invest_text}
            send_lead_to_admin(name, "⏳ Ожидается", chat_id, "invest", context)
            logger.info(f"🔥 LEAD: invest | {invest_text} | {name}")
            return
    
    # ==================== FAQ И ДРУГОЕ ====================
    if data == "faq":
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
        return
    
    if data == "referral":
        text = (
            f"🤝 Приглашайте — получайте 15 000₽\n\n"
            f"Ваша ссылка:\n`https://t.me/tula_key_support_bot`\n\n"
            f"Отправьте другу — он получит чек-лист, а вы бонус после сделки! 💰"
        )
        send_message(chat_id, text)
        return
    
    if data == "goal_browse":
        text = (
            f"✅ Вы в списке рассылки!\n\n"
            f"📄 Пока ждёте — скачайте чек-лист «7 ошибок при покупке»:\n"
            f"{CHECKLIST_URL}\n\n"
            f"📢 И подпишитесь на канал с лучшими предложениями:\n"
            f"{CHANNEL_LINK}"
        )
        send_message(chat_id, text)
        return
    
    logger.info(f"✅ Callback handled: {data}")


def handle_message(chat_id, text, name):
    """Обработчик текстовых сообщений (телефоны)"""
    
    if is_valid_phone(text):
        phone = normalize_phone(text)
        
        send_message(
            chat_id,
            f"✅ Спасибо, {name}! 🙏\n\n"
            f"Я получил ваш номер: {phone}\n"
            f"Свяжусь с вами в течение 2 часов!\n\n"
            f"А пока — посмотрите кейс: как я сэкономил клиенту 400 000₽ 👇\n"
            f"{CHANNEL_LINK}",
        )
        logger.info(f"📞 Phone received from {chat_id}: {phone}")
        
        # 🔥 Обновляем лид с телефоном (отправляем ещё одно уведомление)
        if ADMIN_ID:
            try:
                send_message(
                    ADMIN_ID,
                    f"📞 ТЕЛЕФОН ПОЛУЧЕН!\n"
                    f"👤 {name}\n"
                    f"📱 {phone}\n"
                    f"🆔 {chat_id}"
                )
            except Exception as e:
                logger.error(f"❌ Failed to send phone update: {e}")
    else:
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
    
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        name = message["from"].get("first_name", "Пользователь")
        text = message.get("text", "")
        
        if text == "/start":
            handle_start(chat_id, name)
        else:
            handle_message(chat_id, text, name)
    
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_id = callback["id"]
        data = callback.get("data", "")
        name = callback["from"].get("first_name", "Пользователь")
        
        handle_callback(chat_id, callback_id, data, name)


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
