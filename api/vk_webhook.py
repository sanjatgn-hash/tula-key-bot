# api/vk_webhook.py
# Tula Key Bot — CALLBACK BUTTONS (WORKING)

import os
import json
import logging
import requests
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN", "")

logger.info(f"VK_TOKEN: {'OK' if VK_TOKEN else 'MISSING'}")


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
        params["keyboard"] = json.dumps(keyboard)
    result = vk_api_call("messages.send", params)
    logger.info(f"Sent: {user_id}" if result else f"Failed: {user_id}")
    return result


def send_callback_answer(event_id, user_id, event_data):
    """ОБЯЗАТЕЛЬНО для callback кнопок!"""
    params = {
        "event_id": event_id,
        "user_id": user_id,
        "event_data": json.dumps(event_data)
    }
    return vk_api_call("messages.sendMessageEventAnswer", params)


# ==================== CALLBACK KEYBOARD ====================

def test_kb():
    """Callback клавиатура — ПРАВИЛЬНЫЙ ФОРМАТ"""
    return {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": json.dumps({"test": "1"})
                    },
                    "label": "Test"
                }
            ]
        ]
    }


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    vk_send_message(user_id, f"Hi {name}! Click button:", test_kb())


def handle_callback(user_id, name, payload, event_id):
    """Обработка нажатия callback кнопки"""
    logger.info(f"Callback received: {payload}")
    
    # ✅ ОБЯЗАТЕЛЬНО: ответить VK что кнопка нажата
    send_callback_answer(event_id, user_id, {
        "type": "show_snackbar",
        "text": "Button clicked!"
    })
    
    # Отправить сообщение
    vk_send_message(user_id, f"✅ Button works! Payload: {payload}", test_kb())


def handle_message(user_id, name, text):
    if text.lower() in ["start", "начать", "тест"]:
        handle_start(user_id, name)
        return
    vk_send_message(user_id, f"Echo: {text}", test_kb())


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
        
        # ✅ СООБЩЕНИЕ (текст)
        if event_type == "message_new":
            msg = obj.get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name", "User")
            text = msg.get("text", "")
            logger.info(f"Message: {user_id}, {name}, '{text}'")
            if user_id:
                handle_message(user_id, name, text)
            return "ok", 200
        
        # ✅ НАЖАТИЕ КНОПКИ (callback)
        if event_type == "message_event":
            msg = obj.get("message", {})
            user_id = msg.get("from_id") or obj.get("user_id")
            name = msg.get("from_name", "User")
            payload = json.loads(obj.get("payload", "{}"))
            event_id = obj.get("event_id")
            logger.info(f"Callback: {user_id}, payload={payload}, event_id={event_id}")
            if user_id:
                handle_callback(user_id, name, payload, event_id)
            return "ok", 200
        
        return "ok", 200
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "error", 500


@app.route('/health')
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
