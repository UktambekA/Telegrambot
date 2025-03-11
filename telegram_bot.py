
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import pandas as pd
import os
from datetime import datetime

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot holatlari
PRODUCT_NAME, PRODUCT_QUANTITY, PRODUCT_PRICE = range(3)

# Foydalanuvchilar ma'lumotlarini saqlash uchun lug'at
user_data_dict = {}

# Asosiy menu klaviaturasini yaratish funksiyasi
def get_main_keyboard():
    keyboard = [
        ['🛒 Mahsulot qo\'shish'],
        ['📥 Excel yuklab olish', '🗑 Ma\'lumotlarni tozalash']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start komandasi uchun funksiya
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_text(
        f"Salom, {user.first_name}! Men mahsulot ma'lumotlarini Excel formatiga saqlaydigan botman.\n"
        "Pastdagi tugmalardan foydalanib ma'lumotlarni boshqarishingiz mumkin.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# Mahsulot qo'shish komandasi
async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Mahsulot nomini kiriting:", 
        reply_markup=ReplyKeyboardMarkup([['❌ Bekor qilish']], resize_keyboard=True)
    )
    return PRODUCT_NAME

# Mahsulot nomini olish
async def get_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    
    if text == '❌ Bekor qilish':
        await update.message.reply_text(
            "Mahsulot qo'shish bekor qilindi.", 
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    if user_id not in user_data_dict:
        user_data_dict[user_id] = []
    
    context.user_data['product_name'] = text
    await update.message.reply_text(
        "Mahsulot miqdorini kiriting (faqat raqamlar):",
        reply_markup=ReplyKeyboardMarkup([['❌ Bekor qilish']], resize_keyboard=True)
    )
    return PRODUCT_QUANTITY

# # Mahsulot miqdorini olish
# async def get_product_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     text = update.message.text
    
#     if text == '❌ Bekor qilish':
#         await update.message.reply_text(
#             "Mahsulot qo'shish bekor qilindi.", 
#             reply_markup=get_main_keyboard()
#         )
#         return ConversationHandler.END
    
#     try:
#         quantity = float(text)
#         context.user_data['product_quantity'] = quantity
#         await update.message.reply_text(
#             "Mahsulot narxini kiriting (faqat raqamlar):",
#             reply_markup=ReplyKeyboardMarkup([['❌ Bekor qilish']], resize_keyboard=True)
#         )
#         return PRODUCT_PRICE
#     except ValueError:
#         await update.message.reply_text(
#             "Iltimos, faqat raqamlarni kiriting. Qaytadan urinib ko'ring:",
#             reply_markup=ReplyKeyboardMarkup([['❌ Bekor qilish']], resize_keyboard=True)
#         )
#         return PRODUCT_QUANTITY

# Mahsulot narxini olish
async def get_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    
    if text == '❌ Bekor qilish':
        await update.message.reply_text(
            "Mahsulot qo'shish bekor qilindi.", 
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    
    try:
        price = float(text)
        product_name = context.user_data['product_name']
        product_quantity = context.user_data['product_quantity']
        
        # Mahsulot ma'lumotlarini saqlash
        user_data_dict[user_id].append({
            'nomi': product_name,
            # 'miqdori': product_quantity,
            'narxi': price
        })
        
        await update.message.reply_text(
            f"✅ Mahsulot qo'shildi!\n\n🏷️ Nomi: {product_name}\n💰 Narxi: {price}",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "Iltimos, faqat raqamlarni kiriting. Qaytadan urinib ko'ring:",
            reply_markup=ReplyKeyboardMarkup([['❌ Bekor qilish']], resize_keyboard=True)
        )
        return PRODUCT_PRICE

# Ma'lumotlarni Excel formatida yuborish
async def export_to_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id not in user_data_dict or not user_data_dict[user_id]:
        await update.message.reply_text(
            "Hozircha hech qanday ma'lumot kiritilmagan. Mahsulot qo'shish tugmasini bosing.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # DataFrame yaratish
    df = pd.DataFrame(user_data_dict[user_id])
    
    # Vaqt formatidagi fayl nomi
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"mahsulotlar_{timestamp}.xlsx"
    
    # Excel faylini saqlash
    df.to_excel(file_name, index=False)
    
    # Faylni yuborish
    await update.message.reply_document(
        document=open(file_name, 'rb'),
        filename=file_name,
        caption="📊 Mahsulot ma'lumotlari"
    )
    
    # Faylni o'chirish
    os.remove(file_name)

# Bekor qilish funksiyasi
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Jarayon bekor qilindi.", 
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# Ma'lumotlarni tozalash funksiyasi
async def clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_data_dict:
        user_data_dict[user_id] = []
    await update.message.reply_text(
        "🗑 Barcha ma'lumotlar o'chirildi.",
        reply_markup=get_main_keyboard()
    )

# Tugmalardan kelgan buyruqlarni qayta ishlash
async def handle_button_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    
    if text == '🛒 Mahsulot qo\'shish':
        return await add_product(update, context)
    elif text == '📥 Excel yuklab olish':
        return await export_to_excel(update, context)
    elif text == '🗑 Ma\'lumotlarni tozalash':
        return await clear_data(update, context)

def main() -> None:
    # Bot tokenini shu yerga kiriting
    application = Application.builder().token("8126996910:AAGcidCXkjc53ONoGv681Q_c4jEDdQwDvOc").build()
    
    # Suhbat oqimi uchun handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_product),
            MessageHandler(filters.Text(['🛒 Mahsulot qo\'shish']), add_product)
        ],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_name)],
            # PRODUCT_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_quantity)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_price)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Text(['❌ Bekor qilish']), cancel)
        ],
    )
    
    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("export", export_to_excel))
    application.add_handler(CommandHandler("clear", clear_data))
    application.add_handler(MessageHandler(
        filters.Text(['📥 Excel yuklab olish', '🗑 Ma\'lumotlarni tozalash']), 
        handle_button_messages
    ))
    
    # Botni ishga tushirish
    application.run_polling()

if __name__ == "__main__":
    main()
