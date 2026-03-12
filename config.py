# config.py
# Настройки бота «Тульский ключ»
# Все секреты задаются через переменные окружения Vercel

import os

# ==================== TELEGRAM ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# ==================== ССЫЛКИ ====================
CHECKLIST_URL = os.getenv("CHECKLIST_URL", "https://t.me/tula_key_bot")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/tula_key_channel")

# ==================== GOOGLE SHEETS ====================
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
# Credentials передаются как JSON-строка в переменной окружения
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# ==================== VERCEL ====================
VERCEL_URL = os.getenv("VERCEL_URL", "")
# Путь для webhook: /webhook/ВАШ_ТОКЕН
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}" if BOT_TOKEN else "/webhook"

# ==================== НАСТРОЙКИ ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
