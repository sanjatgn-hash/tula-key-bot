# lib/keyboards.py
# Клавиатуры для бота «Тульский ключ»

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню после команды /start"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📥 Получить чек-лист", callback_data="get_checklist"))
    builder.row(
        InlineKeyboardButton(text="🔍 Подобрать квартиру", callback_data="goal_buy"),
        InlineKeyboardButton(text="💰 Продать", callback_data="goal_sell")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Инвестиции", callback_data="goal_invest"),
        InlineKeyboardButton(text="💬 Задать вопрос", callback_data="faq")
    )
    builder.row(InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral"))
    return builder.as_markup()


def budget_kb() -> InlineKeyboardMarkup:
    """Выбор бюджета при покупке"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("до 3 млн", "budget_3m"),
        ("3–5 млн", "budget_5m"),
        ("5+ млн", "budget_5plus"),
        ("Нужна помощь", "budget_help")
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    builder.adjust(2)
    return builder.as_markup()


def deadline_kb() -> InlineKeyboardMarkup:
    """Выбор срока сделки"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🔥 Срочно", "deadline_urgent"),
        ("📅 1-3 мес", "deadline_month"),
        ("👀 Просто смотрю", "deadline_look")
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    return builder.as_markup()


def hot_lead_kb() -> InlineKeyboardMarkup:
    """Запрос контакта для горячего лида"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Поделиться контактом", request_contact=True)
    builder.button(text="✍️ Написать вручную", callback_data="phone_manual")
    builder.adjust(1)
    return builder.as_markup()


def invest_budget_kb() -> InlineKeyboardMarkup:
    """Выбор бюджета для калькулятора инвестиций"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("до 2 млн", "invest_2m"),
        ("2–5 млн", "invest_5m"),
        ("5+ млн", "invest_5plus")
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    builder.adjust(1)
    return builder.as_markup()


def back_kb(callback_data: str) -> InlineKeyboardMarkup:
    """Кнопка «Назад» с указанным callback_data"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=callback_data)
    return builder.as_markup()


def property_type_kb() -> InlineKeyboardMarkup:
    """Выбор типа объекта для продажи"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("Квартира", "type_flat"),
        ("Дом", "type_house"),
        ("Комната", "type_room"),
        ("Другое", "type_other")
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    builder.adjust(2)
    return builder.as_markup()


def district_kb() -> InlineKeyboardMarkup:
    """Выбор района Тулы"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("Центральный", "dist_center"),
        ("Заречье", "dist_zarechye"),
        ("Пролетарский", "dist_proletarsky"),
        ("Любой", "dist_any")
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    builder.adjust(2)
    return builder.as_markup()
