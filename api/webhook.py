# api/webhook.py
# Бот «Тульский ключ» — с обработкой телефонов

import os
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

# Загрузка токена
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
    """Обработчик callback queries"""
    
    answer_callback(callback_id)
    
    if data == "get_checklist":
        text = (
            f"🎉 Готово!\n\n"
            f"📄 Чек-лист:\n{CHECKLIST_URL}\n\n"
            f"💡 Сохраните ссылку в «Избранное» 📌\n\n"
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
    
    elif data == "goal_buy":
        text = f"{name}, понял! 🔑 Чтобы подборка была точной:\n\n1️⃣ Ваш бюджет?"
        send_message(chat_id, text, reply_markup=budget_kb())
        # Сохраняем состояние в БД (пока просто лог)
        logger.info(f"💾 User {chat_id} started BUY flow")
    
    elif data.startswith("budget_"):
        text = "2️⃣ Когда планируете сделку?"
        send_message(chat_id, text, reply_markup=deadline_kb())
    
    elif data.startswith("deadline_"):
        if data == "deadline_urgent":
            text = f"🔥 Вижу, вы ищете серьёзно!\n\n📞 Напишите ваш номер телефона:\n(например: +79991234567)"
        else:
            text = f"✅ Отлично! Буду присылать лучшие варианты 📬\n\nЕсли захотите срочную подборку — напишите «ХОЧУ ПОДБОРКУ»"
        send_message(chat_id, text)
    
    elif data == "goal_sell":
        text = f"{name}, помогу выгодно продать недвижимость в Туле 🏡\n\n1️⃣ Тип объекта?"
        send_message(chat_id, text, reply_markup=property_type_kb())
        logger.info(f"💾 User {chat_id} started SELL flow")
    
    elif data.startswith("type_"):
        text = "2️⃣ Район Тулы?"
        send_message(chat_id, text, reply_markup=district_kb())
    
    elif data.startswith("dist_"):
        text = "✅ Отлично! 🏡 Я подготовлю:\n• Бесплатную оценку\n• План продажи\n• Чек-лист «Как подготовить квартиру»\n\n📞 Напишите ваш номер телефона:\n(например: +79991234567)"
        send_message(chat_id, text)
    
    elif data == "goal_invest":
        text = "📊 Калькулятор инвестора в недвижимость Тулы\n\nВыберите бюджет для расчёта:"
        send_message(chat_id, text, reply_markup=invest_budget_kb())
    
    elif data.startswith("invest_"):
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
            f"⚠️ Это ориентировочный расчёт."
        )
        send_message(chat_id, text)
    
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
        send_message(chat_id, "✅ Вы в списке рассылки! Буду присылать лучшие предложения Тулы 📬")
    
    logger.info(f"✅ Callback handled: {data}")


def handle_message(chat_id, text, name):
    """Обработчик текстовых сообщений (телефоны, вопросы)"""
    
    # Проверка на телефон (простая валидация)
    if text and (text.startswith("+7") or text.startswith("8")) and len(text.replace(" ", "").replace("-", "")) >= 10:
        # Это телефон!
        send_message(
            chat_id,
            f"✅ Спасибо, {name}! 🙏\n\n"
            f"Я получил ваш номер: {text}\n"
            f"Свяжусь с вами в течение 2 часов!\n\n"
            f"А пока — посмотрите кейс: как я сэкономил клиенту 400 000₽ 👇\n"
            f"{CHANNEL_LINK}",
        )
        logger.info(f"📞 Phone received from {chat_id}: {text}")
        
        # Отправка уведомления админу (если ADMIN_ID задан)
        if ADMIN_ID:
            try:
                send_message(
                    ADMIN_ID,
                    f"🔥 НОВЫЙ ЛИД!\n\n"
                    f"👤 Имя: {name}\n"
                    f"📞 Телефон: {text}\n"
                    f"🆔 ID: {chat_id}"
                )
                logger.info(f"📩 Notification sent to admin {ADMIN_ID}")
            except Exception as e:
                logger.error(f"❌ Failed to notify admin: {e}")
    else:
        # Обычное сообщение
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
    
    # Обработка сообщений (текст)
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        name = message["from"].get("first_name", "Пользователь")
        
        if text == "/start":
            handle_start(chat_id, name)
        else:
            handle_message(chat_id, text, name)
    
    # Обработка callback queries (кнопки)
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
