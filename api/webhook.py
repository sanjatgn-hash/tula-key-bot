# api/webhook.py
# Бот «Тульский ключ» — Flask + aiogram для Vercel

import os
import json
import logging
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем корень проекта в путь для импортов
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from lib.handlers import register_handlers

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
app = Flask(__name__)

# Загрузка и очистка токена
RAW_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_TOKEN = "".join(RAW_TOKEN.split())  # Удаляем ВСЕ пробелы

if BOT_TOKEN:
    logger.info(f"✅ BOT_TOKEN loaded: {BOT_TOKEN[:10]}...")
else:
    logger.error("❌ BOT_TOKEN not set!")

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
storage = MemoryStorage()
dp = Dispatcher(storage=storage) if bot else None

# Регистрация обработчиков
if dp:
    register_handlers(dp)
    logger.info("✅ Handlers registered")


# ==================== РОУТЫ FLASK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("🏥 Health check requested")
    return "OK", 200


@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST']) if BOT_TOKEN else None
def webhook_handler():
    """Обработчик webhook от Telegram"""
    if not bot or not dp:
        logger.error("❌ Bot not initialized")
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        logger.info("📬 Webhook called!")
        
        # Получаем обновление от Telegram
        update_data = request.get_json(force=True)
        update = types.Update(**update_data)
        
        # Обрабатываем через aiogram (в том же потоке для serverless)
        import asyncio
        asyncio.run(dp.feed_update(bot, update))
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ==================== ЗАПУСК (для локального теста) ====================
if __name__ == '__main__':
    # Только для локального запуска, не для Vercel
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
