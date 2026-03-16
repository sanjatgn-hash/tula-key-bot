# api/vk_webhook.py
# Tula Key Bot — MINIMAL TEST

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
logger.info(f"VK_GROUP_ID: {'OK' if VK_GROUP_ID else 'MISSING'}")


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
        # ✅ БЕЗ ensure_ascii - пробуем стандартную кодировку
        params["keyboard"] = json.dumps(keyboard)
        logger.info(f"Keyboard JSON: {json.dumps(keyboard)}")
    result = vk_api_call("messages.send", params)
    logger.info(f"Sent: {user_id}" if result else f"Failed: {user_id}")
    return result


# ==================== MINIMAL KEYBOARD ====================

def minimal_kb():
    """Абсолютно минимальная клавиатура"""
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "{}"
                    },
                    "label": "A"
                }
            ]
        ]
    }


# ==================== HANDLERS ====================

def handle_start(user_id, name):
    vk_send_message(user_id, f"Hi {name}! Test:", minimal_kb())


def handle_message(user_id, name, text):
    if text.lower() in ["start", "начать", "тест", "test"]:
        handle_start(user_id, name)
        return
    vk_send_message(user_id, f"Echo: {text}", minimal_kb())


# ==================== WEBHOOK ====================

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"VK webhook: type={data.get('type')}")
        
        if data.get("type") == "confirmation":
            return VK_CONFIRMATION_TOKEN, 200
        
        if data.get("type") == "message_new":
            msg = data.get("object", {}).get("message", {})
            user_id = msg.get("from_id")
            name = msg.get("from_name", "User")
            text = msg.get("text", "")
            logger.info(f"Message: {user_id}, {name}, '{text}'")
            if user_id:
                handle_message(user_id, name, text)
            return "ok", 200
        
        return "ok", 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return "error", 500


@app.route('/health')
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
