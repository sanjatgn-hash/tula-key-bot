# lib/handlers.py
# Обработчики сообщений для бота «Тульский ключ»

import logging
from aiogram import F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Локальные импорты
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from .keyboards import *
from .sheets import save_lead, notify_admin

logger = logging.getLogger(__name__)


# ==================== СОСТОЯНИЯ FSM ====================

class UserForm(StatesGroup):
    """Состояния для сбора данных пользователя"""
    waiting_for_phone = State()
    waiting_for_sell_contact = State()


# ==================== ГЛАВНОЕ МЕНЮ ====================

async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    name = message.from_user.first_name or "Пользователь"
    
    await message.answer(
        f"🔑 Привет, {name}! Я — помощник «Тульского ключа»\n\n"
        f"Помогаю найти квартиру в Туле без стресса и переплат 🏠\n\n"
        f"🎁 Ваш подарок: чек-лист «7 ошибок при покупке жилья в Туле»\n"
        f"→ сэкономит от 100 000₽ и недели нервов",
        reply_markup=main_menu_kb()
    )
    logger.info(f"📩 /start from: {message.from_user.id} ({name})")


async def send_checklist(callback: types.CallbackQuery):
    """Выдача чек-листа и выбор цели"""
    await callback.answer()
    
    await callback.message.answer(
        f"🎉 Готово!\n\n"
        f"📄 Чек-лист «7 ошибок при покупке»:\n{config.CHECKLIST_URL}\n\n"
        f"💡 Совет: сохраните ссылку в «Избранное» 📌\n\n"
        f"Чтобы я присылал только подходящие варианты, подскажите:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Купить", callback_data="goal_buy")],
            [InlineKeyboardButton(text="💰 Продать", callback_data="goal_sell")],
            [InlineKeyboardButton(text="📊 Инвестировать", callback_data="goal_invest")],
            [InlineKeyboardButton(text="🤔 Пока смотрю", callback_data="goal_browse")]
        ])
    )
    logger.info(f"📥 Checklist sent to: {callback.from_user.id}")


# ==================== ВЕТКА «КУПИТЬ» ====================

async def goal_buy(callback: types.CallbackQuery):
    """Начало ветки покупки — запрос бюджета"""
    await callback.answer()
    
    await callback.message.answer(
        f"{callback.from_user.first_name}, понял! 🔑 Чтобы подборка была точной:\n\n"
        f"1️⃣ Ваш бюджет?",
        reply_markup=budget_kb()
    )


async def set_budget(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение бюджета и запрос срока"""
    await callback.answer()
    
    budget_map = {
        "budget_3m": "до 3 млн",
        "budget_5m": "3–5 млн", 
        "budget_5plus": "5+ млн",
        "budget_help": "Нужна помощь"
    }
    budget = budget_map.get(callback.data, "")
    await state.update_data(budget=budget)
    
    await callback.message.answer(
        f"2️⃣ Когда планируете сделку?",
        reply_markup=deadline_kb()
    )


async def set_deadline(callback: types.CallbackQuery, state: FSMContext):
    """Обработка срока + ветвление на горячий/тёплый лид"""
    await callback.answer()
    
    deadline_map = {
        "deadline_urgent": "Срочно",
        "deadline_month": "1-3 мес",
        "deadline_look": "Просто смотрю"
    }
    deadline = deadline_map.get(callback.data, "")
    await state.update_data(deadline=deadline)
    
    data = await state.get_data()
    budget = data.get("budget", "")
    
    # 🔥 Горячий лид: срочно + конкретный бюджет
    if deadline == "Срочно" and budget not in ["Нужна помощь", ""]:
        await callback.message.answer(
            f"🔥 Вижу, вы ищете серьёзно! У меня есть варианты под ваши параметры.\n\n"
            f"Как удобнее получить подборку?",
            reply_markup=hot_lead_kb()
        )
        logger.info(f"🔥 HOT LEAD: {callback.from_user.id} | {budget} | {deadline}")
    else:
        # Тёплый/холодный лид — подписка на рассылку
        await callback.message.answer(
            f"Отлично! Я подготовлю подборку и буду присылать лучшие варианты 📬\n\n"
            f"Как с вами связаться, если появится срочное предложение?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Написать в ЛС", callback_data="contact_later")],
                [InlineKeyboardButton(text="🔕 Только в боте", callback_data="contact_bot_only")]
            ])
        )
        logger.info(f"📬 WARM LEAD: {callback.from_user.id} | {budget} | {deadline}")


async def handle_contact(message: types.Message, state: FSMContext):
    """Обработка полученного контакта (кнопка «Поделиться»)"""
    if not message.contact:
        return
    
    phone = message.contact.phone_number
    data = await state.get_data()
    
    user_data = {
        'date': message.date.strftime("%Y-%m-%d %H:%M"),
        'name': message.from_user.first_name,
        'phone': phone,
        'goal': 'Купить',
        'budget': data.get('budget', ''),
        'district': data.get('district', ''),
        'deadline': data.get('deadline', ''),
        'user_id': message.from_user.id
    }
    
    # Сохранение в Google Sheets
    save_lead(user_data)
    
    # Уведомление админу
    await notify_admin(
        message.bot,
        f"🔥 НОВЫЙ ЛИД | Купить\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 {user_data['name']}\n"
        f"📞 {phone}\n"
        f"💰 Бюджет: {user_data['budget']}\n"
        f"⏰ Срок: {user_data['deadline']}\n"
        f"━━━━━━━━━━━━━━"
    )
    
    # Ответ пользователю
    await message.answer(
        f"Спасибо, {message.from_user.first_name}! 🙏\n\n"
        f"Я свяжусь с вами в течение 2 часов.\n\n"
        f"А пока — посмотрите кейс: как я сэкономил клиенту 400 000₽ 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Читать кейс", url=config.CHANNEL_LINK)]
        ])
    )
    
    await state.clear()
    logger.info(f"✅ Contact saved: {message.from_user.id} | {phone}")


async def ask_phone_manual(callback: types.CallbackQuery, state: FSMContext):
    """Запрос телефона вручную (если пользователь не хочет делиться контактом)"""
    await callback.answer()
    await callback.message.answer("✍️ Напишите ваш номер телефона:")
    await state.set_state(UserForm.waiting_for_phone)


async def save_phone_manual(message: types.Message, state: FSMContext):
    """Сохранение телефона, введённого вручную"""
    phone = message.text.strip()
    
    # Простая валидация телефона
    if len(phone) < 10:
        await message.answer("⚠️ Похоже, номер введён неверно. Попробуйте ещё раз:")
        return
    
    data = await state.get_data()
    
    user_data = {
        'date': message.date.strftime("%Y-%m-%d %H:%M"),
        'name': message.from_user.first_name,
        'phone': phone,
        'goal': 'Купить',
        'budget': data.get('budget', ''),
        'district': data.get('district', ''),
        'deadline': data.get('deadline', ''),
        'user_id': message.from_user.id
    }
    
    save_lead(user_data)
    
    await notify_admin(
        message.bot,
        f"🔥 ЛИД (ручной) | Купить\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 {user_data['name']}\n"
        f"📞 {phone}\n"
        f"💰 {user_data['budget']}"
    )
    
    await message.answer(
        f"Принято! 🙏 Свяжусь в течение 2 часов.\n"
        f"А пока — кейс: экономия 400 000₽ 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Читать кейс", url=config.CHANNEL_LINK)]
        ])
    )
    
    await state.clear()
    logger.info(f"✅ Manual phone saved: {message.from_user.id} | {phone}")


# ==================== ВЕТКА «ПРОДАТЬ» ====================

async def goal_sell(callback: types.CallbackQuery):
    """Начало ветки продажи — запрос типа объекта"""
    await callback.answer()
    
    await callback.message.answer(
        f"{callback.from_user.first_name}, помогу выгодно продать недвижимость в Туле 🏡\n\n"
        f"1️⃣ Тип объекта?",
        reply_markup=property_type_kb()
    )


async def set_property_type(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение типа объекта и запрос района"""
    await callback.answer()
    
    type_map = {
        "type_flat": "Квартира",
        "type_house": "Дом",
        "type_room": "Комната",
        "type_other": "Другое"
    }
    prop_type = type_map.get(callback.data, "")
    await state.update_data(prop_type=prop_type)
    
    await callback.message.answer(
        f"2️⃣ Район Тулы?",
        reply_markup=district_kb()
    )


async def set_district(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение района + запрос контакта для связи"""
    await callback.answer()
    
    district_map = {
        "dist_center": "Центральный",
        "dist_zarechye": "Заречье",
        "dist_proletarsky": "Пролетарский",
        "dist_any": "Любой"
    }
    district = district_map.get(callback.data, "")
    await state.update_data(district=district)
    
    await callback.message.answer(
        f"Отлично! 🏡 Я подготовлю для вас:\n"
        f"• Бесплатную оценку рыночной стоимости\n"
        f"• План продажи с прогнозом сроков\n"
        f"• Чек-лист «Как подготовить квартиру к продаже»\n\n"
        f"Как вам удобнее получить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📩 В ЛС", callback_data="send_to_dm")],
            [InlineKeyboardButton(text="📞 Перезвоните", callback_data="call_me_sell")]
        ])
    )


# ==================== ВЕТКА «ИНВЕСТИЦИИ» ====================

async def goal_invest(callback: types.CallbackQuery):
    """Калькулятор инвестиций — выбор бюджета"""
    await callback.answer()
    
    await callback.message.answer(
        f"📊 Калькулятор инвестора в недвижимость Тулы\n\n"
        f"Выберите бюджет для расчёта:",
        reply_markup=invest_budget_kb()
    )


async def calculate_invest(callback: types.CallbackQuery):
    """Расчёт инвестиций (упрощённые готовые значения)"""
    await callback.answer()
    
    # Готовые расчёты для 3 диапазонов бюджета
    calculations = {
        "invest_2m": {
            "price": "2 000 000", "downpayment": "400 000", "monthly": "~18 000",
            "rent": "~15 000", "cashflow": "-3 000", "growth_5y": "+600 000", "roi": "~8%"
        },
        "invest_5m": {
            "price": "5 000 000", "downpayment": "1 000 000", "monthly": "~45 000",
            "rent": "~35 000", "cashflow": "-10 000", "growth_5y": "+1 500 000", "roi": "~10%"
        },
        "invest_5plus": {
            "price": "8 000 000+", "downpayment": "1 600 000+", "monthly": "~72 000+",
            "rent": "~55 000+", "cashflow": "-17 000+", "growth_5y": "+2 400 000+", "roi": "~12%"
        }
    }
    
    calc = calculations.get(callback.data, calculations["invest_2m"])
    
    await callback.message.answer(
        f"📈 Результаты расчёта:\n\n"
        f"🏢 Стоимость: {calc['price']} ₽\n"
        f"💰 Первоначальный взнос (20%): {calc['downpayment']} ₽\n"
        f"📉 Платёж по ипотеке: {calc['monthly']} ₽/мес\n"
        f"💵 Арендный доход: {calc['rent']} ₽/мес\n"
        f"📦 Чистый поток: {calc['cashflow']} ₽/мес\n\n"
        f"📈 Прогноз через 5 лет:\n"
        f"• Рост стоимости: {calc['growth_5y']}\n"
        f"• ROI: {calc['roi']} годовых\n\n"
        f"⚠️ Это ориентировочный расчёт. Точные цифры зависят от объекта.\n\n"
        f"👇 Что дальше?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Обсудить стратегию", callback_data="consult_invest")],
            [InlineKeyboardButton(text="🔁 Пересчитать", callback_data="goal_invest")]
        ])
    )


async def consult_invest(callback: types.CallbackQuery, state: FSMContext):
    """Запрос консультации по инвестициям"""
    await callback.answer()
    await state.update_data(goal="Инвестиции")
    
    await callback.message.answer(
        f"🔥 Хотите обсудить инвестиционную стратегию лично?\n\n"
        f"Это бесплатно и ни к чему не обязывает.\n"
        f"Нажмите кнопку — я получу ваш контакт:",
        reply_markup=hot_lead_kb()
    )


# ==================== РЕФЕРАЛКА ====================

async def referral_program(callback: types.CallbackQuery):
    """Программа «Приведи друга»"""
    await callback.answer()
    
    # Формируем реферальную ссылку
    referral_link = f"https://t.me/{callback.bot.me.username}?start=ref_{callback.from_user.id}"
    
    await callback.message.answer(
        f"🤝 Приглашайте — получайте 15 000₽\n\n"
        f"Как это работает:\n"
        f"1️⃣ Нажмите «Поделиться»\n"
        f"2️⃣ Отправьте ссылку другу\n"
        f"3️⃣ Друг получит чек-лист и подборку\n"
        f"4️⃣ Вы получите бонус, когда он станет клиентом 💰\n\n"
        f"Ваша ссылка:\n`{referral_link}`\n\n"
        f"Нажмите, чтобы скопировать 👇",
        parse_mode="Markdown"
    )


# ==================== FAQ ====================

async def show_faq(callback: types.CallbackQuery):
    """Частые вопросы"""
    await callback.answer()
    
    await callback.message.answer(
        f"💬 Частые вопросы:\n\n"
        f"❓ Какая комиссия?\n"
        f"→ 2-3% от стоимости объекта, после сделки. Консультация — бесплатно 🔑\n\n"
        f"❓ Работаете с ипотекой?\n"
        f"→ Да! Со всеми банками Тулы. Есть партнёр-брокер — ставки ниже на 0.5-1% 📉\n\n"
        f"❓ Как проверить квартиру?\n"
        f"→ Проверяю юридическую чистоту, историю объекта, обременения. Полный отчёт — перед сделке ✅\n\n"
        f"Есть ещё вопрос? Напишите — отвечу лично 👇",
        reply_markup=back_kb("main_menu_stub")
    )


# ==================== ЗАГЛУШКИ И ВСПОМОГАТЕЛЬНЫЕ ====================

async def handle_browse(callback: types.CallbackQuery):
    """Обработка выбора «Пока смотрю»"""
    await callback.answer()
    await callback.message.answer("✅ Вы в списке рассылки! Буду присылать лучшие предложения Тулы 📬")


async def handle_contact_later(callback: types.CallbackQuery):
    """Пользователь хочет, чтобы написали позже"""
    await callback.answer()
    await callback.message.answer("✅ Договорились! Буду на связи. Если появятся вопросы — пишите в любой момент 🔑")


async def handle_bot_only(callback: types.CallbackQuery):
    """Пользователь хочет общаться только в боте"""
    await callback.answer()
    await callback.message.answer("✅ Ок, буду писать только в боте. Следите за уведомлениями 📬")


async def handle_send_to_dm(callback: types.CallbackQuery):
    """Отправка информации продавцу в ЛС"""
    await callback.answer()
    await callback.message.answer("✅ Отправлю оценку и чек-лист в ЛС в ближайшее время 📩")


async def handle_call_me_sell(callback: types.CallbackQuery, state: FSMContext):
    """Запрос телефона для продавца"""
    await callback.answer()
    await callback.message.answer("✍️ Напишите ваш номер телефона для связи:")
    await state.set_state(UserForm.waiting_for_sell_contact)


async def save_sell_phone(message: types.Message, state: FSMContext):
    """Сохранение телефона продавца"""
    phone = message.text.strip()
    data = await state.get_data()
    
    user_data = {
        'date': message.date.strftime("%Y-%m-%d %H:%M"),
        'name': message.from_user.first_name,
        'phone': phone,
        'goal': 'Продать',
        'budget': '',
        'district': data.get('district', ''),
        'deadline': '',
        'user_id': message.from_user.id
    }
    
    save_lead(user_data)
    
    await notify_admin(
        message.bot,
        f"🏡 ЛИД | Продать\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 {user_data['name']}\n"
        f"📞 {phone}\n"
        f"🏠 Тип: {data.get('prop_type', '')}\n"
        f"📍 Район: {data.get('district', '')}"
    )
    
    await message.answer(
        f"Спасибо! 🙏 Свяжусь с вами в течение 2 часов для оценки объекта."
    )
    await state.clear()


async def handle_main_menu_stub(callback: types.CallbackQuery):
    """Заглушка для кнопки «Назад» из FAQ"""
    await callback.answer()
    # Можно отправить главное меню, но чтобы не спамить — просто подтверждение
    await callback.message.answer("✅ Вернулся в главное меню. Выберите действие:", reply_markup=main_menu_kb())


# ==================== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ====================

def register_handlers(dp):
    """
    Регистрация всех обработчиков в диспетчере aiogram.
    Вызывается при инициализации бота.
    """
    
    # --- Команды ---
    dp.message(Command("start"))(cmd_start)
    
    # --- Главное меню ---
    dp.callback_query(F.data == "get_checklist")(send_checklist)
    dp.callback_query(F.data == "goal_buy")(goal_buy)
    dp.callback_query(F.data == "goal_sell")(goal_sell)
    dp.callback_query(F.data == "goal_invest")(goal_invest)
    dp.callback_query(F.data == "goal_browse")(handle_browse)
    dp.callback_query(F.data == "faq")(show_faq)
    dp.callback_query(F.data == "referral")(referral_program)
    
    # --- Ветка «Купить» ---
    dp.callback_query(F.data.startswith("budget_"))(set_budget)
    dp.callback_query(F.data.startswith("deadline_"))(set_deadline)
    dp.message(F.contact)(handle_contact)
    dp.callback_query(F.data == "phone_manual")(ask_phone_manual)
    dp.message(UserForm.waiting_for_phone)(save_phone_manual)
    
    # --- Ветка «Продать» ---
    dp.callback_query(F.data.startswith("type_"))(set_property_type)
    dp.callback_query(F.data.startswith("dist_"))(set_district)
    dp.callback_query(F.data == "send_to_dm")(handle_send_to_dm)
    dp.callback_query(F.data == "call_me_sell")(handle_call_me_sell)
    dp.message(UserForm.waiting_for_sell_contact)(save_sell_phone)
    
    # --- Ветка «Инвестиции» ---
    dp.callback_query(F.data.startswith("invest_"))(calculate_invest)
    dp.callback_query(F.data == "consult_invest")(consult_invest)
    
    # --- Заглушки для кнопок ---
    dp.callback_query(F.data == "main_menu_stub")(handle_main_menu_stub)
    dp.callback_query(F.data == "contact_later")(handle_contact_later)
    dp.callback_query(F.data == "contact_bot_only")(handle_bot_only)
