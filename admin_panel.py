# admin_panel.py (to‘liq yangilangan)
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from utils import get_services, save_services, ADMIN_ID, is_match

logger = logging.getLogger(__name__)

# Holatlar
(ADD_SERVICE_ID, ADD_SERVICE_NAME, ADD_SERVICE_PRICE, ADD_SERVICE_PAYMENTS, ADD_SERVICE_IMAGE,
 ADD_SERVICE_CATEGORY, EDIT_SERVICE_ID, EDIT_SERVICE_FIELD, EDIT_SERVICE_NAME, EDIT_SERVICE_PRICE,
 EDIT_SERVICE_PAYMENTS, EDIT_SERVICE_IMAGE, EDIT_SERVICE_CATEGORY, DELETE_SERVICE_ID, SEARCH_SERVICE,
 TOGGLE_VISIBILITY_ID, GROUP_BY_CATEGORY) = range(5, 22)

async def admin_main_menu(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={user_id}")
        return

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Xizmatlar", callback_data="admin_services"),
            InlineKeyboardButton("📋 Buyurtmalar", callback_data="admin_orders")
        ],
        [
            InlineKeyboardButton("💸 To‘lovlar", callback_data="admin_payments"),
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin_settings")
        ]
    ])

    await update.message.reply_text(
        "👋 <b>Admin panel</b>\n\nSifatli xizmat – oson boshqaruv!\nQuyidagi bo‘limlardan birini tanlang:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ Admin panel bosh menyusi ochildi: user_id={user_id}")

# Qolgan funksiyalar o‘zgarmaydi, faqat import va holatlar yangilandi
# Yuqoridagi `get_price` va boshqa funksiyalar oldingi versiyada to‘g‘ri

  
async def admin_services_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Yangi xizmat", callback_data="add_service"),
            InlineKeyboardButton("📋 Ro‘yxat", callback_data="list_services")
        ],
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data="edit_service"),
            InlineKeyboardButton("🗑 O‘chirish", callback_data="delete_service")
        ],
        [
            InlineKeyboardButton("🔍 Qidirish", callback_data="search_service"),
            InlineKeyboardButton("📦 Toifalar", callback_data="group_by_category")
        ],
        [
            InlineKeyboardButton("🔄 Faollik", callback_data="toggle_service_visibility"),
            InlineKeyboardButton("⬅️ Bosh sahifa", callback_data="admin_main")
        ]
    ])

    await query.edit_message_text(
        "📦 <b>Xizmatlar bo‘limi</b>\n\nTez va sifatli xizmatlarni boshqaring:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ Xizmatlar menyusi ochildi: user_id={query.from_user.id}")
    return None

async def add_service_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    context.user_data['service_action'] = 'add'
    await query.message.reply_text(
        "➕ <b>Yangi xizmat qo‘shish</b>\n\n1/6: Xizmat ID raqamini yozing (masalan, 123):",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"✅ Yangi xizmat qo‘shish boshlandi: user_id={query.from_user.id}")
    return ADD_SERVICE_ID

async def get_service_id(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        service_id = int(update.message.text.strip())
        services = get_services(admin=True)
        if any(s['id'] == service_id for s in services):
            await update.message.reply_text("❌ Bu ID allaqachon mavjud. Boshqa ID kiriting:")
            logger.warning(f"❌ Dublikat ID kiritildi: user_id={update.effective_user.id}, id={service_id}")
            return ADD_SERVICE_ID
        context.user_data['id'] = service_id
        await update.message.reply_text("2/6: Xizmat nomini kiriting:")
        logger.info(f"✅ Xizmat ID kiritildi: user_id={update.effective_user.id}, id={service_id}")
        return ADD_SERVICE_NAME
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting (masalan, 123). Qayta urining:")
        logger.error(f"❌ Noto‘g‘ri ID formati: user_id={update.effective_user.id}, input={update.message.text}")
        return ADD_SERVICE_ID

async def get_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Xizmat nomi bo‘sh bo‘lmasligi kerak. Qayta kiriting:")
        return ADD_SERVICE_NAME
    context.user_data['name'] = name
    await update.message.reply_text("3/6: Narxini so‘mda kiriting (masalan, 10000):")
    logger.info(f"✅ Xizmat nomi kiritildi: user_id={update.effective_user.id}, name={name}")
    return ADD_SERVICE_PRICE

async def get_price(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.strip())
        if price <= 0:
            await update.message.reply_text("❌ Narx musbat bo‘lishi kerak. Qayta kiriting:")
            return ADD_SERVICE_PRICE
        context.user_data['price'] = price
        keyboard = [["Click", "Payme"], ["Karta bilan"], ["Tugatish"]]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        context.user_data['payment_methods'] = []
        await update.message.reply_text(
            "4/6: To‘lov usullarini tanlang. 'Tugatish' bosilgach rasm so‘raladi:",
            reply_markup=markup
        )
        logger.info(f"✅ Xizmat narxi kiritildi: user_id={update.effective_user.id}, price={price}")
        return ADD_SERVICE_PAYMENTS
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting (masalan, 10000). Qayta urining:")
        logger.error(f"❌ Noto‘g‘ri narx formati: user_id={update.effective_user.id}, input={update.message.text}")
        return ADD_SERVICE_PRICE
        
async def get_payment(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() == "tugatish":
        if not context.user_data['payment_methods']:
            await update.message.reply_text("❌ Kamida bitta to‘lov usuli tanlanishi kerak. Qayta tanlang:")
            return ADD_SERVICE_PAYMENTS
        await update.message.reply_text(
            "5/6: Xizmat rasmini yuboring yoki 'Rasm yo‘q' deb yozing:",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"✅ To‘lov usullari tanlandi: user_id={update.effective_user.id}, methods={context.user_data['payment_methods']}")
        return ADD_SERVICE_IMAGE
    context.user_data['payment_methods'].append(text)
    logger.info(f"✅ To‘lov usuli qo‘shildi: user_id={update.effective_user.id}, method={text}")
    return ADD_SERVICE_PAYMENTS

async def get_image(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() in ["yo‘q", "yoq", "rasm yo‘q"]:
        context.user_data['image'] = None
        logger.info(f"✅ Rasm yo‘q deb tanlandi: user_id={update.effective_user.id}")
    elif update.message.photo:
        context.user_data['image'] = update.message.photo[-1].file_id
        logger.info(f"✅ Rasm kiritildi: user_id={update.effective_user.id}, file_id={context.user_data['image']}")
    else:
        await update.message.reply_text("❌ Iltimos, rasm yuboring yoki 'Rasm yo‘q' deb yozing.")
        return ADD_SERVICE_IMAGE

    await update.message.reply_text("6/6: Xizmat toifasini kiriting (masalan, Print, Foto):")
    return ADD_SERVICE_CATEGORY

async def get_category(update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text.strip()
    if not category:
        await update.message.reply_text("❌ Toifa bo‘sh bo‘lmasligi kerak. Qayta kiriting:")
        return ADD_SERVICE_CATEGORY
    context.user_data['category'] = category

    services = get_services(admin=True)
    new_service = {
        'id': context.user_data['id'],
        'name': context.user_data['name'],
        'price': context.user_data['price'],
        'payment_methods': context.user_data['payment_methods'],
        'image': context.user_data['image'],
        'category': context.user_data['category'],
        'active': True
    }
    services.append(new_service)
    save_services(services)
    context.bot_data['services'] = services

    await update.message.reply_text(
        f"✅ Yangi xizmat qo‘shildi: {new_service['name']} ({new_service['category']})",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Yangi xizmat saqlandi: user_id={update.effective_user.id}, id={new_service['id']}, name={new_service['name']}")
    context.user_data.clear()
    return ConversationHandler.END

async def list_services_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    services = get_services(admin=True)
    if not services:
        await query.edit_message_text(
            "📭 Hozirda xizmatlar mavjud emas.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.info(f"ℹ Xizmatlar ro‘yxati bo‘sh: user_id={query.from_user.id}")
        return ConversationHandler.END

    text = "📋 <b>Xizmatlar ro‘yxati</b>\n\n"
    for s in services:
        status = "✅ Faol" if s.get('active', True) else "❌ NoFaol"
        text += (
            f"🆔 ID: {s['id']}\n"
            f"📌 Nomi: {s['name']}\n"
            f"💰 Narxi: {s['price']} so‘m\n"
            f"💳 To‘lov: {', '.join(s['payment_methods'])}\n"
            f"📦 Toifa: {s.get('category', 'Belgilanmagan')}\n"
            f"🔄 Holati: {status}\n"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_service_{s['id']}"),
                InlineKeyboardButton("🗑 O‘chirish", callback_data=f"delete_service_{s['id']}")
            ]
        ])
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        text = ""

    await query.message.reply_text(
        "⬆️ Yuqoridagi xizmatlar ro‘yxati.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Xizmatlar ro‘yxati ko‘rsatildi: user_id={query.from_user.id}, count={len(services)}")
    return ConversationHandler.END

async def edit_service_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    data = query.data
    if data.startswith("edit_service_") and data != "edit_service":
        service_id = int(data.replace("edit_service_", ""))
        context.user_data['edit_service_id'] = service_id
        return await select_edit_field(update, context)

    context.user_data['service_action'] = 'edit'
    await query.edit_message_text(
        "✏️ <b>Xizmatni tahrirlash</b>\n\nTahrir qilmoqchi bo‘lgan xizmat ID raqamini yozing:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Xizmat tahrirlash boshlandi: user_id={query.from_user.id}")
    return EDIT_SERVICE_ID

async def get_edit_service_id(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        service_id = int(update.message.text.strip())
        services = get_services(admin=True)
        service = next((s for s in services if s['id'] == service_id), None)
        if not service:
            await update.message.reply_text(
                "❌ Bunday ID topilmadi. Qayta kiriting:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
                ])
            )
            logger.error(f"❌ Xizmat topilmadi: user_id={update.effective_user.id}, service_id={service_id}")
            return EDIT_SERVICE_ID
        context.user_data['edit_service_id'] = service_id
        return await select_edit_field(update, context)
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam kiriting (masalan, 123). Qayta urining:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.error(f"❌ Noto‘g‘ri ID formati: user_id={update.effective_user.id}, input={update.message.text}")
        return EDIT_SERVICE_ID
        
async def select_edit_field(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    service_id = context.user_data['edit_service_id']
    services = get_services(admin=True)
    service = next((s for s in services if s['id'] == service_id), None)
    
    if not service:
        await (query.message.reply_text if query else update.message.reply_text)(
            "❌ Xizmat topilmadi. Qaytadan boshlang.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        context.user_data.clear()
        return ConversationHandler.END

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📌 Nomi", callback_data="edit_name"),
            InlineKeyboardButton("💰 Narxi", callback_data="edit_price")
        ],
        [
            InlineKeyboardButton("💳 To‘lov usullari", callback_data="edit_payments"),
            InlineKeyboardButton("📎 Rasm", callback_data="edit_image")
        ],
        [
            InlineKeyboardButton("📦 Toifa", callback_data="edit_category"),
            InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")
        ]
    ])

    text = (
        f"✅ Xizmat topildi: {service['name']}\n\n"
        f"Nimalarni tahrir qilmoqchisiz?"
    )
    if query:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
    logger.info(f"✅ Tahrirlash maydonlari ko‘rsatildi: user_id={update.effective_user.id}, service_id={service_id}")
    return EDIT_SERVICE_FIELD

async def edit_service_field(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    field = query.data
    context.user_data['edit_field'] = field
    field_names = {
        "edit_name": "xizmat nomini",
        "edit_price": "narxini",
        "edit_payments": "to‘lov usullarini (vergul bilan ajrating, masalan: Click, Payme)",
        "edit_image": "rasmni",
        "edit_category": "toifani"
    }
    await query.edit_message_text(
        f"✏️ Yangi {field_names[field]} kiriting:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="select_edit_field")]
        ])
    )
    logger.info(f"✅ Tahrirlash uchun maydon tanlandi: user_id={query.from_user.id}, field={field}")
    return {
        "edit_name": EDIT_SERVICE_NAME,
        "edit_price": EDIT_SERVICE_PRICE,
        "edit_payments": EDIT_SERVICE_PAYMENTS,
        "edit_image": EDIT_SERVICE_IMAGE,
        "edit_category": EDIT_SERVICE_CATEGORY
    }[field]

async def edit_service_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Nomi bo‘sh bo‘lmasligi kerak. Qayta kiriting:")
        return EDIT_SERVICE_NAME
    return await save_edited_field(update, context, 'name', name)

async def edit_service_price(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.strip())
        if price <= 0:
            await update.message.reply_text("❌ Narx musbat bo‘lishi kerak. Qayta kiriting:")
            return EDIT_SERVICE_PRICE
        return await save_edited_field(update, context, 'price', price)
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting (masalan, 10000). Qayta kiriting:")
        return EDIT_SERVICE_PRICE

async def edit_service_payments(update, context: ContextTypes.DEFAULT_TYPE):
    payments = [p.strip() for p in update.message.text.strip().split(',') if p.strip()]
    if not payments:
        await update.message.reply_text("❌ Kamida bitta to‘lov usuli kiritilishi kerak. Qayta kiriting:")
        return EDIT_SERVICE_PAYMENTS
    return await save_edited_field(update, context, 'payment_methods', payments)

async def edit_service_image(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() in ["yo‘q", "yoq", "rasm yo‘q"]:
        value = None
    elif update.message.photo:
        value = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("❌ Iltimos, rasm yuboring yoki 'Rasm yo‘q' deb yozing.")
        return EDIT_SERVICE_IMAGE
    return await save_edited_field(update, context, 'image', value)

async def edit_service_category(update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text.strip()
    if not category:
        await update.message.reply_text("❌ Toifa bo‘sh bo‘lmasligi kerak. Qayta kiriting:")
        return EDIT_SERVICE_CATEGORY
    return await save_edited_field(update, context, 'category', category)

async def save_edited_field(update, context: ContextTypes.DEFAULT_TYPE, field, value):
    service_id = context.user_data['edit_service_id']
    services = get_services(admin=True)
    service = next((s for s in services if s['id'] == service_id), None)
    
    if not service:
        await update.message.reply_text(
            "❌ Xizmat topilmadi. Qaytadan boshlang.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        context.user_data.clear()
        return ConversationHandler.END

    service[field] = value
    save_services(services)
    context.bot_data['services'] = services

    await update.message.reply_text(
        f"✅ Xizmatning {field} maydoni yangilandi: {service['name']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Yana tahrirlash", callback_data="select_edit_field"),
             InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Xizmat tahrirlandi: user_id={update.effective_user.id}, service_id={service_id}, field={field}")
    return EDIT_SERVICE_FIELD

async def delete_service_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    data = query.data
    if data.startswith("delete_service_") and data != "delete_service":
        service_id = int(data.replace("delete_service_", ""))
        context.user_data['delete_service_id'] = service_id
        services = get_services(admin=True)
        service = next((s for s in services if s['id'] == service_id), None)
        if not service:
            await query.edit_message_text(
                "❌ Xizmat topilmadi. Qaytadan boshlang.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
                ])
            )
            return ConversationHandler.END
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_delete_{service_id}"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_services")
            ]
        ])
        await query.edit_message_text(
            f"🗑 <b>Xizmatni o‘chirish</b>\n\nO‘chirmoqchi bo‘lgan xizmat: {service['name']} (ID: {service_id})\nTasdiqlaysizmi?",
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        logger.info(f"✅ Xizmat o‘chirish tasdiqlash so‘raldi: user_id={query.from_user.id}, service_id={service_id}")
        return DELETE_SERVICE_ID

    context.user_data['service_action'] = 'delete'
    await query.edit_message_text(
        "🗑 <b>Xizmatni o‘chirish</b>\n\nO‘chirmoqchi bo‘lgan xizmat ID raqamini yozing:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Xizmat o‘chirish boshlandi: user_id={query.from_user.id}")
    return DELETE_SERVICE_ID

async def confirm_delete(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    if query:
        await query.answer()
        data = query.data
        if not data.startswith("confirm_delete_"):
            await query.edit_message_text(
                "❌ Noto‘g‘ri tasdiqlash amali.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
                ])
            )
            return ConversationHandler.END
        service_id = int(data.replace("confirm_delete_", ""))
    else:
        try:
            service_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ Faqat raqam kiriting (masalan, 123). Qayta urining:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
                ])
            )
            logger.error(f"❌ Noto‘g‘ri ID formati: user_id={update.effective_user.id}, input={update.message.text}")
            return DELETE_SERVICE_ID

    services = get_services(admin=True)
    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        text = "❌ Bunday ID topilmadi."
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
        if query:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        logger.error(f"❌ Xizmat topilmadi: user_id={update.effective_user.id}, service_id={service_id}")
        return ConversationHandler.END if query else DELETE_SERVICE_ID

    services = [s for s in services if s['id'] != service_id]
    save_services(services)
    context.bot_data['services'] = services
    context.user_data.clear()

    text = f"✅ Xizmat o‘chirildi: {service['name']} (ID: {service_id})"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
    ])
    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    logger.info(f"✅ Xizmat o‘chirildi: user_id={update.effective_user.id}, service_id={service_id}")
    return ConversationHandler.END

async def search_service_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    context.user_data['service_action'] = 'search'
    await query.edit_message_text(
        "🔍 <b>Xizmat qidirish</b>\n\nXizmat nomining bir qismini yozing:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Xizmat qidirish boshlandi: user_id={query.from_user.id}")
    return SEARCH_SERVICE

async def search_service(update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip().lower()
    services = get_services(admin=True)
    matches = [s for s in services if is_match(query_text, s['name'])]

    if not matches:
        await update.message.reply_text(
            "❌ Hech qanday xizmat topilmadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Qayta qidirish", callback_data="search_service"),
                 InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.info(f"ℹ Qidiruv natijasiz: user_id={update.effective_user.id}, query={query_text}")
        return SEARCH_SERVICE

    text = f"🔍 <b>Qidiruv natijalari</b> ({len(matches)} ta xizmat):\n\n"
    for s in matches:
        status = "✅ Faol" if s.get('active', True) else "❌ NoFaol"
        text += (
            f"🆔 ID: {s['id']}\n"
            f"📌 Nomi: {s['name']}\n"
            f"💰 Narxi: {s['price']} so‘m\n"
            f"📦 Toifa: {s.get('category', 'Belgilanmagan')}\n"
            f"🔄 Holati: {status}\n"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_service_{s['id']}"),
                InlineKeyboardButton("🗑 O‘chirish", callback_data=f"delete_service_{s['id']}")
            ]
        ])
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        text = ""

    await update.message.reply_text(
        "⬆️ Yuqoridagi qidiruv natijalari.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Qayta qidirish", callback_data="search_service"),
             InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Qidiruv natijalari ko‘rsatildi: user_id={update.effective_user.id}, query={query_text}, count={len(matches)}")
    return SEARCH_SERVICE

async def group_by_category_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    services = get_services(admin=True)
    categories = sorted(set(s.get('category', 'Belgilanmagan') for s in services))
    if not categories:
        await query.edit_message_text(
            "📭 Hozirda toifalar mavjud emas.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.info(f"ℹ Toifalar bo‘sh: user_id={query.from_user.id}")
        return ConversationHandler.END

    buttons = []
    for i in range(0, len(categories), 2):
        row = [InlineKeyboardButton(categories[i], callback_data=f"view_category_{categories[i]}")]
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i + 1], callback_data=f"view_category_{categories[i + 1]}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")])

    await query.edit_message_text(
        "📦 <b>Toifalar bo‘yicha ko‘rish</b>\n\nQuyidagi toifalardan birini tanlang:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    logger.info(f"✅ Toifalar ro‘yxati ko‘rsatildi: user_id={query.from_user.id}, count={len(categories)}")
    return GROUP_BY_CATEGORY

async def view_category(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    category = query.data.replace("view_category_", "")
    services = get_services(admin=True)
    category_services = [s for s in services if s.get('category', 'Belgilanmagan') == category]

    if not category_services:
        await query.edit_message_text(
            f"📭 {category} toifasida xizmatlar mavjud emas.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Toifalarga", callback_data="group_by_category"),
                 InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.info(f"ℹ Toifa bo‘sh: user_id={query.from_user.id}, category={category}")
        return ConversationHandler.END

    text = f"📦 <b>{category} toifasidagi xizmatlar</b>\n\n"
    for s in category_services:
        status = "✅ Faol" if s.get('active', True) else "❌ NoFaol"
        text += (
            f"🆔 ID: {s['id']}\n"
            f"📌 Nomi: {s['name']}\n"
            f"💰 Narxi: {s['price']} so‘m\n"
            f"🔄 Holati: {status}\n"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_service_{s['id']}"),
                InlineKeyboardButton("🗑 O‘chirish", callback_data=f"delete_service_{s['id']}")
            ]
        ])
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        text = ""

    await query.message.reply_text(
        "⬆️ Yuqoridagi toifa xizmatlari.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Toifalarga", callback_data="group_by_category"),
             InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Toifa xizmatlari ko‘rsatildi: user_id={query.from_user.id}, category={category}, count={len(category_services)}")
    return ConversationHandler.END

async def toggle_service_visibility_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    context.user_data['service_action'] = 'toggle_visibility'
    await query.edit_message_text(
        "🔄 <b>Faollikni o‘zgartirish</b>\n\nFaollik holatini o‘zgartirmoqchi bo‘lgan xizmat ID raqamini yozing:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
        ])
    )
    logger.info(f"✅ Faollik o‘zgartirish boshlandi: user_id={query.from_user.id}")
    return TOGGLE_VISIBILITY_ID

async def toggle_visibility(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        service_id = int(update.message.text.strip())
        services = get_services(admin=True)
        service = next((s for s in services if s['id'] == service_id), None)
        if not service:
            await update.message.reply_text(
                "❌ Bunday ID topilmadi. Qayta kiriting:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
                ])
            )
            logger.error(f"❌ Xizmat topilmadi: user_id={update.effective_user.id}, service_id={service_id}")
            return TOGGLE_VISIBILITY_ID

        service['active'] = not service.get('active', True)
        save_services(services)
        context.bot_data['services'] = services
        status = "Faol" if service['active'] else "NoFaol"
        await update.message.reply_text(
            f"✅ Xizmat holati o‘zgartirildi: {service['name']} — {status}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.info(f"✅ Xizmat faolligi o‘zgartirildi: user_id={update.effective_user.id}, service_id={service_id}, status={status}")
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam kiriting (masalan, 123). Qayta urining:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar menyusiga", callback_data="admin_services")]
            ])
        )
        logger.error(f"❌ Noto‘g‘ri ID formati: user_id={update.effective_user.id}, input={update.message.text}")
        return TOGGLE_VISIBILITY_ID

async def admin_orders_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🆕 Yangi", callback_data="orders_new"),
            InlineKeyboardButton("✅ Bajarilgan", callback_data="orders_done")
        ],
        [
            InlineKeyboardButton("❌ Bekor qilingan", callback_data="orders_cancelled"),
            InlineKeyboardButton("🔍 Qidirish", callback_data="orders_search")
        ],
        [
            InlineKeyboardButton("⬅️ Bosh sahifaga", callback_data="admin_main")
        ]
    ])

    await query.edit_message_text(
        "📋 <b>Buyurtmalar bo‘limi</b>\n\nBuyurtmalarni samarali boshqaring:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ Buyurtmalar menyusi ochildi: user_id={query.from_user.id}")
    return None

async def admin_payments_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧾 Kelgan cheklar", callback_data="payments_checks"),
            InlineKeyboardButton("✅ Tasdiqlangan", callback_data="payments_approved")
        ],
        [
            InlineKeyboardButton("❌ Rad etilgan", callback_data="payments_rejected"),
            InlineKeyboardButton("⬅️ Bosh sahifaga", callback_data="admin_main")
        ]
    ])

    await query.edit_message_text(
        "💸 <b>To‘lovlar bo‘limi</b>\n\nTo‘lov jarayonlarini nazorat qiling:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ To‘lovlar menyusi ochildi: user_id={query.from_user.id}")
    return None

async def admin_users_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Ro‘yxat", callback_data="users_list"),
            InlineKeyboardButton("🔍 Qidirish", callback_data="users_search")
        ],
        [
            InlineKeyboardButton("⬅️ Bosh sahifaga", callback_data="admin_main")
        ]
    ])

    await query.edit_message_text(
        "👥 <b>Foydalanuvchilar bo‘limi</b>\n\nMijozlaringizni boshqaring:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ Foydalanuvchilar menyusi ochildi: user_id={query.from_user.id}")
    return None

async def admin_stats_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📈 Bugungi soni", callback_data="stats_today"),
            InlineKeyboardButton("🔝 Eng mashhur xizmat", callback_data="stats_top")
        ],
        [
            InlineKeyboardButton("📆 7 kunlik graf", callback_data="stats_week"),
            InlineKeyboardButton("⬅️ Bosh sahifaga", callback_data="admin_main")
        ]
    ])

    await query.edit_message_text(
        "📊 <b>Statistika bo‘limi</b>\n\nXizmatlaringiz faoliyatini tahlil qiling:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ Statistika menyusi ochildi: user_id={query.from_user.id}")
    return None

async def admin_settings_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Bu funksiya faqat adminlar uchun!")
        logger.warning(f"❌ Noto‘g‘ri admin kirish urinishi: user_id={update.effective_user.id}")
        return ConversationHandler.END

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💳 To‘lov kartasi", callback_data="settings_card"),
            InlineKeyboardButton("🕒 Ish vaqti", callback_data="settings_hours")
        ],
        [
            InlineKeyboardButton("📢 Kanal havolasi", callback_data="settings_channel"),
            InlineKeyboardButton("👑 Admin ID", callback_data="settings_admin")
        ],
        [
            InlineKeyboardButton("⬅️ Bosh sahifaga", callback_data="admin_main")
        ]
    ])

    await query.edit_message_text(
        "⚙️ <b>Sozlamalar bo‘limi</b>\n\nBot sozlamalarini moslashtiring:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    logger.info(f"✅ Sozlamalar menyusi ochildi: user_id={query.from_user.id}")
    return None