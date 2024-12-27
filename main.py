import logging
import asyncio
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import instaloader

# Initialize the bot with your bot's token
bot_token = "7713676691:AAEGcDNTL0_UFZ9ub1UTo9sW8e2lVKTcwTo"

# Kanal va Admin ID
CHANNEL_USERNAME = 'istoriya_videos'
ADMIN_USER_ID = 6879273956  # Admin foydalanuvchi ID sini kiriting

# Foydalanuvchilar ro'yxatini saqlash (faqat xususiy saqlash uchun)
users = set()

# Instaloader media olish funksiyasi
def download_instagram_media(url):
    L = instaloader.Instaloader()

    try:
        shortcode = url.split('/')[-2]  # Instagram post shortcode
    except IndexError:
        return {'error': "URL noto'g'ri formatda."}

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        media_urls = []

        # Agar post karusel bo'lsa (bir nechta rasm yoki video), barchasini olish
        if post.get_sidecar_nodes():  # Karusel bo'lsa
            for node in post.get_sidecar_nodes():
                media_url = node.display_url if not node.is_video else node.video_url
                media_type = 'image' if not node.is_video else 'video'
                media_urls.append({'type': media_type, 'url': media_url})
        else:  # Bitta rasm yoki video bo'lsa
            media_url = post.url if not post.is_video else post.video_url
            media_type = 'image' if not post.is_video else 'video'
            media_urls.append({'type': media_type, 'url': media_url})

        # Check if it's a Reel (Reels can be fetched just like posts, just need the shortcode)
        if post.is_video:
            media_urls = [{'type': 'video', 'url': post.video_url}]

        return media_urls
    except Exception as e:
        return {'error': f"Xatolik yuz berdi: {str(e)}"}


# Telegram botning start komandi
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    users.add(user_id)  # Foydalanuvchini ro'yxatga qo'shish
    await update.message.reply_text('Salom! Instagram postining linkini yuboring.')


# Admin komandasi
async def admin(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Siz admin emassiz.")
        return

    keyboard = [
        [InlineKeyboardButton("Botning statistikasi", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Admin paneli:", reply_markup=reply_markup)


# Botning statistikasi
async def show_stats(update: Update, context: CallbackContext) -> None:
    if update.callback_query.from_user.id != ADMIN_USER_ID:
        return

    user_count = len(users)
    await update.callback_query.message.edit_text(f"Botning foydalanuvchilari soni: {user_count}")


# Instagram linkini qayta ishlash va media yuborish
async def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text  # Foydalanuvchidan linkni olish
    result = download_instagram_media(url)

    if 'error' in result:
        await update.message.reply_text(result['error'])
        return

    # "Yuklanmoqda" deb xabar yuborish
    loading_message = await update.message.reply_text("☕️")

    # Agar karusel (bir nechta rasm yoki video) bo'lsa, ularni ketma-ket yuborish
    for media in result:
        if media['type'] == 'image':
            keyboard = [[InlineKeyboardButton("Kanalimizga obuna bo'ling", url=f"https://t.me/{CHANNEL_USERNAME}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Send image with caption
            await update.message.reply_photo(media['url'], caption="Rasm yuklandi✅", reply_markup=reply_markup)
        elif media['type'] == 'video':
            keyboard = [[InlineKeyboardButton("Kanalimizga obuna bo'ling", url=f"https://t.me/{CHANNEL_USERNAME}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                # Send video with caption
                await update.message.reply_video(media['url'], caption="Video yuklandi✅", reply_markup=reply_markup)
            except Exception as e:
                # Error handling for video download
                await update.message.reply_text(f"Video yuborishda xatolik yuz berdi: {str(e)}")

    # "Uploading..." xabarini o'chirish
    await loading_message.delete()


# Callback so'rovini qayta ishlash
async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    callback_query = update.callback_query
    if callback_query:
        chat_id = callback_query.message.chat.id
        callback_data = callback_query.data

        if callback_data == 'stats' and chat_id == ADMIN_USER_ID:
            user_count = len(users)
            await callback_query.message.edit_text(f"Bot statistikasi:\nFoydalanuvchilar soni: {user_count}")


# Botni ishga tushirish
def main():
    # Application yaratish (v20 va yuqori versiya uchun)
    application = Application.builder().token(bot_token).build()

    # Handlerlar: /start, /admin komandi va linkni tekshirish
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Botni ishga tushurish
    application.run_polling()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s -%(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler("bot.log"),
                            logging.StreamHandler(sys.stdout)  # This is to log to console as well
                        ])
    asyncio.run(main())
