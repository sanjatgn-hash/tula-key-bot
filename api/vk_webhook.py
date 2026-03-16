# api/vk_webhook.py
# Tula Key Bot — TEST VERSION with simple keyboard

import os
import json
import logging
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


def vk_send_message(user_id, text, keyboard=None):
    params = {"user_id": user_id, "message": text, "random_id": 0}
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
        logger.info(f"Sending keyboard: {json.dumps(keyboard, ensure_ascii=False)}")
    result = vk_api_call("messages.send", params)
    logger.info(f"Message sent to {user_id}" if result else f"Failed to send to {user_id}")
    return result


# ==================== TEST KEYBOARD ====================

def test_keyboard():
    """Простейшая клавиатура — 1 кнопка"""
    return {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "{\"test\":\"button1\"}"
                    },
                    "label": "Test Button"
                }
            ]
        ]
    }


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    text = f"""🔑 Привет, {name}!

🧪 ТЕСТОВАЯ ВЕРСИЯ БОТА

Нажмите кнопку ниже чтобы проверить работу клавиатуры:"""
    vk_send_message(user_id, text, test_keyboard())


def handle_message(user_id, name, text):
    cmd = text.strip().lower()
    
    logger.info(f"Message from {name}: '{text}'")
    
    # Команды
    if cmd in ["начать", "старт", "/start", "test"]:
        handle_start(user_id, name)
        return
    
    # Если нажал на кнопку
    if "test" in cmd or "button" in cmd:
        vk_send_message(user_id, f"✅ КНОПКА РАБОТАЕТ!\n\n{name}, вы нажали на тестовую кнопку.\n\nТеперь бот готов к работе!", test_keyboard())
        return
    
    # Любое другое сообщение
    vk_send_message(user_id, f"👋 {name}, вы написали: {text}\n\nНапишите 'тест' чтобы проверить клавиатуру.", test_keyboard())


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"VK webhook: type={data.get('type')}")
        
        if data.get("type") == "confirmation":
            logger.info(f"Confirmation requested, returning: {VK_CONFIRMATION_TOKEN}")
            return VK_CONFIRMATION_TOKEN, 200
        
        obj = data.get("object", {})
        event_type = data.get("type")
        
        if event_type == "message_new":
            msg = obj.get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name", "Пользователь")
            text = msg.get("text", "")
            
            logger.info(f"Message: user={user_id}, name={name}, text='{text}'")
            
            if user_id:
                handle_message(user_id, name, text)
            
            return "ok", 200
        
        return "ok", 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "error", 500


@app.route('/health', methods=['GET'])
def health_check():
    return "VK Bot TEST OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
