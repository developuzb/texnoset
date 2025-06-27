from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler, ChosenInlineResultHandler
)
from telegram.constants import ParseMode
import json, os

TOKEN = "7742414096:AAGEZ9KYH1i4v4X3c6p3NZuj54c_10K8vWM"
ADMIN_ID = 6654453609
GROUP_ID = -4979712337
DATA_FILE = './database/services.json'
(ASK_ACTION, ASK_NAME, ASK_PRICE, ASK_PAYMENTS, ASK_DELETE_ID) = range(5)

DATA_FILE = './database/services.json'
ORDER_COUNTER_FILE = './database/order_counter.json'

# JSON fayl tayyorlash
os.makedirs('./database', exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)
        
if not os.path.exists(ORDER_COUNTER_FILE):
    with open(ORDER_COUNTER_FILE, 'w') as f:
        json.dump({"last": 172999}, f)


# START buyrug‘i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        keyboard = [["➕ Xizmat qo‘shish"], ["📋 Xizmatlar ro‘yxati"], ["🗑 Xizmatni o‘chirish"]]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 Assalomu alaykum, admin!\nAmallardan birini tanlang:", reply_markup=markup)
        return ASK_ACTION
    else:
        inline_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📲 Xizmatlardan foydalanish", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("☎️ Bog‘lanish", url="https://t.me/texnoset_bussines")]
        ])
        await update.message.reply_text(
            "👋 Assalomu alaykum!\nXizmatlarimizdan foydalanish yoki bog‘lanish uchun tugmani tanlang:",
            reply_markup=inline_markup
        )

# ADMIN menyu funksiyasi
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "➕ Xizmat qo‘shish":
        await update.message.reply_text("1/3: Xizmat nomini kiriting:", reply_markup=ReplyKeyboardRemove())
        return ASK_NAME
    elif text == "📋 Xizmatlar ro‘yxati":
        with open(DATA_FILE) as f:
            services = json.load(f)
        if not services:
            await update.message.reply_text("📭 Xizmatlar mavjud emas.")
            return ASK_ACTION
        msg = "📋 Mavjud xizmatlar:\n\n"
        for s in services:
            payments = ", ".join(s['payment_methods'])
            msg += (
                f"🔹 {s['id']} — {s['name']}\n"
                f"💰 {s['price']} so‘m\n"
                f"💳 To‘lov: {payments}\n\n"
            )
        await update.message.reply_text(msg)
        return ASK_ACTION
    elif text == "🗑 Xizmatni o‘chirish":
        await update.message.reply_text("O‘chirmoqchi bo‘lgan xizmat ID raqamini yuboring:", reply_markup=ReplyKeyboardRemove())
        return ASK_DELETE_ID

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("2/3: Narxini so‘mda kiriting:")
    return ASK_PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['price'] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Iltimos, raqam kiriting.")
        return ASK_PRICE
    keyboard = [["Click", "Payme"], ["Karta bilan"], ["Tugatish"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    context.user_data['payment_methods'] = []
    await update.message.reply_text("3/3: To‘lov usullarini yuboring. Tugatgach 'Tugatish' tugmasini bosing:", reply_markup=markup)
    return ASK_PAYMENTS

async def get_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Tugatish":
        with open(DATA_FILE) as f:
            services = json.load(f)
        new_id = max([s['id'] for s in services], default=172999) + 1
        service = {
            'id': new_id,
            'name': context.user_data['name'],
            'price': context.user_data['price'],
            'payment_methods': context.user_data['payment_methods']
        }
        services.append(service)
        with open(DATA_FILE, 'w') as f:
            json.dump(services, f, indent=2)
        await update.message.reply_text(f"✅ Xizmat qo‘shildi: {service['name']}", reply_markup=ReplyKeyboardRemove())
        return await start(update, context)
    context.user_data['payment_methods'].append(text)
    return ASK_PAYMENTS

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        service_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat ID raqamini yuboring.")
        return ASK_DELETE_ID
    with open(DATA_FILE) as f:
        services = json.load(f)
    updated_services = [s for s in services if s['id'] != service_id]
    with open(DATA_FILE, 'w') as f:
        json.dump(updated_services, f, indent=2)
    await update.message.reply_text("✅ O‘chirildi.")
    return await start(update, context)
    def get_next_order_number():
    with open(ORDER_COUNTER_FILE) as f:
        data = json.load(f)
    data['last'] += 1
    with open(ORDER_COUNTER_FILE, 'w') as f:
        json.dump(data, f)
    return data['last']

# MIJOZ OQIMI – xizmat tanlash → roziman → raqam → vaqt → guruhga yuborish
from telegram.ext import InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    results = []

    with open(DATA_FILE) as f:
        services = json.load(f)

    for s in services:
        if query in s['name'].lower():
            results.append(
                InlineQueryResultArticle(
                    id=str(s['id']),
                    title=s['name'],
                    input_message_content=InputTextMessageContent(f"{s['name']} xizmatini tanladingiz"),
                    description=f"{s['price']} so‘m - {'/'.join(s['payment_methods'])}"
                )
            )

    await update.inline_query.answer(results[:20])

async def chosen_inline_result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chosen_inline_result
    service_id = int(result.result_id)
    with open(DATA_FILE) as f:
        services = json.load(f)
    service = next((s for s in services if s['id'] == service_id), None)
    order_id = get_next_order_number()

    context.user_data['selected_service'] = service
    context.user_data['order_id'] = order_id

    text = (
        f"📌 <b>{service['name']}</b>\n"
        f"💰 {service['price']} so‘m\n"
        f"💳 To‘lov: {', '.join(service['payment_methods'])}\n"
        f"🧾 Buyurtma raqami: <b>#{order_id}</b>\n\n"
        "❗ Agar rozimisiz, pastdagi tugmani bosing."
    )

    buttons = [[InlineKeyboardButton("✅ Roziman", callback_data="confirm_service")]]
    if 'Click' in service['payment_methods']:
        click_url = create_click_url(order_id, service['price'])
        buttons.insert(0, [InlineKeyboardButton("💳 Click orqali to‘lash", url=click_url)])

    markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(result.from_user.id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML)

def create_click_url(order_id, amount):
    return f"https://my.click.uz/pay/?service_id=999999999&merchant_id=398062629&amount={amount}&transaction_param={order_id}"


async def roziman_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    markup = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await context.bot.send_message(query.from_user.id, "📞 Telefon raqamingizni yuboring:", reply_markup=markup)
    return 100

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    context.user_data['phone'] = contact.phone_number
    await update.message.reply_text("⏰ Qachon bog‘lanishimizni xohlaysiz?")
    return 101

async def receive_contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_time = update.message.text
    context.user_data['contact_time'] = contact_time
    service = context.user_data['selected_service']
    phone = context.user_data['phone']
    text = (
        f"📦 <b>Yangi buyurtma!</b>\n\n"
        f"🆔 Xizmat ID: <code>{service['id']}</code>\n"
        f"📌 Nomi: <b>{service['name']}</b>\n"
        f"📞 Raqam: <code>{phone}</code>\n"
        f"⏰ Aloqa vaqti: <i>{contact_time}</i>"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode=ParseMode.HTML)
    await update.message.reply_text("✅ Buyurtmangiz qabul qilindi. Tez orada bog‘lanamiz.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Botni ishga tushirish
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_ACTION: [MessageHandler(filters.TEXT, handle_action)],
        ASK_NAME: [MessageHandler(filters.TEXT, get_name)],
        ASK_PRICE: [MessageHandler(filters.TEXT, get_price)],
        ASK_PAYMENTS: [MessageHandler(filters.TEXT, get_payment)],
        ASK_DELETE_ID: [MessageHandler(filters.TEXT, confirm_delete)],
        100: [MessageHandler(filters.CONTACT, contact_handler)],
        101: [MessageHandler(filters.TEXT, receive_contact_time)],
    },
    fallbacks=[]
))

app.add_handler(CallbackQueryHandler(roziman_handler, pattern="^confirm_service$"))
app.add_handler(ChosenInlineResultHandler(chosen_inline_result_handler))
app.add_handler(InlineQueryHandler(inline_query_handler))


app.run_polling()
