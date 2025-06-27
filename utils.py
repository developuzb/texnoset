import re
import pytz
from datetime import datetime, time
from PIL import Image, ImageDraw, ImageFont
import io
import difflib

def is_working_hours():
    now = datetime.now(pytz.timezone('Asia/Tashkent')).time()
    return time(8, 30) <= now <= time(19, 30)

def create_receipt_image(order, amount, confirmation_time):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_body = ImageFont.truetype("arial.ttf", 18)
        font_stamp = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_stamp = ImageFont.load_default()

    draw.text((50, 50), "To‘lov cheki", font=font_title, fill='black')
    draw.text((50, 90), "Texnoset Xizmatlari", font=font_body, fill='gray')
    draw.text((50, 110), "Bank operatsiyasi", font=font_body, fill='gray')

    y = 150
    draw.text((50, y), f"Buyurtma raqami: #{order['order_id']}", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Xizmat turi: {order['service_name']}", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Summa: {amount} so‘m", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Boshlangan vaqti: {order['timestamp']}", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Tasdiqlangan vaqti: {confirmation_time}", font=font_body, fill='black')
    y += 60

    draw.text((50, y), "To‘lov ma'lumotlari:", font=font_body, fill='black')
    y += 40
    draw.text((50, y), "Karta raqami: 8600 3104 7319 9081", font=font_body, fill='black')
    y += 40
    draw.text((50, y), "Holati: To‘landi", font=font_body, fill='green')

    stamp_x, stamp_y = 550, 400
    draw.rectangle((stamp_x, stamp_y, stamp_x + 200, stamp_y + 100), outline='red', width=2)
    draw.text((stamp_x + 20, stamp_y + 20), "TO‘LANDI", font=font_stamp, fill='red')
    draw.text((stamp_x + 20, stamp_y + 60), confirmation_time.split()[0], font=font_stamp, fill='red')

    draw.text((50, height - 50), "Texnoset – Ishonchli xizmat!", font=font_body, fill='gray')

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def create_invoice_image(order, amount):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_body = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    draw.text((50, 50), "To‘lov uchun invoys", font=font_title, fill='black')
    draw.text((50, 90), "Texnoset Xizmatlari", font=font_body, fill='gray')

    y = 150
    draw.text((50, y), f"Buyurtma raqami: #{order['order_id']}", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Xizmat turi: {order['service_name']}", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Narxi: {amount} so‘m", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Boshlangan vaqti: {order['timestamp']}", font=font_body, fill='black')
    y += 60

    draw.text((50, y), "To‘lov ma'lumotlari:", font=font_body, fill='black')
    y += 40
    draw.text((50, y), "Karta raqami: 8600 3104 7319 9081", font=font_body, fill='black')
    y += 40
    draw.text((50, y), f"Summa: {amount} so‘m", font=font_body, fill='black')

    draw.text((50, height - 50), "Texnoset – Ishonchli xizmat!", font=font_body, fill='gray')

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def transliterate(text, to_latin=True):
    replacements = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j',
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e',
        'ю': 'yu', 'я': 'ya', 'қ': 'q', 'ҳ': 'h', 'ғ': 'g‘', 'ў': 'o‘',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J',
        'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
        'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts',
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh', 'Ъ': '', 'Ы': 'I', 'Ь': '', 'Э': 'E',
        'Ю': 'Yu', 'Я': 'Ya', 'Қ': 'Q', 'Ҳ': 'H', 'Ғ': 'G‘', 'Ў': 'O‘'
    }
    if not to_latin:
        replacements = {v: k for k, v in replacements.items() if v}
    return ''.join(replacements.get(c, c) for c in text)

def is_match(query, name):
    query_l = query.lower()
    name_l = name.lower()
    if query_l in name_l or transliterate(query_l) in name_l or query_l in transliterate(name_l, False):
        return True
    return bool(difflib.get_close_matches(query_l, [name_l], cutoff=0.7))

def create_click_url(order_id, amount):
    return f"https://my.click.uz/pay/?service_id=999999999&merchant_id=398062629&amount={amount}&transaction_param={order_id}"