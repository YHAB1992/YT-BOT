import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
DAILY_LIMIT = 5
user_downloads = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 أهلاً! أرسل لي رابط يوتيوب وأحمله لك\n"
        "✅ مجاني: 5 تحميلات يومياً\n"
        "💎 مميز: اشتراك شهري بـ 10$"
    )

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    url = update.message.text

    # حد يومي
    count = user_downloads.get(user_id, 0)
    if count >= DAILY_LIMIT:
        await update.message.reply_text(
            "❌ وصلت الحد اليومي المجاني!\n"
            "💎 اشترك بـ 10$/شهر للتحميل بلا حدود\n"
            "تواصل: @your_username"
        )
        return

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("⚠️ أرسل رابط يوتيوب صحيح")
        return

    await update.message.reply_text("⏳ جاري التحميل...")

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو MP4", callback_data=f"video|{url}")],
        [InlineKeyboardButton("🎵 صوت MP3", callback_data=f"audio|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر نوع التحميل:", reply_markup=reply_markup)

    user_downloads[user_id] = count + 1

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    mode, url = data[0], data[1]

    ydl_opts = {
        'format': 'bestaudio/best' if mode == 'audio' else 'best[filesize<50M]',
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }] if mode == 'audio' else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if mode == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as f:
            if mode == 'audio':
                await query.message.reply_audio(f)
            else:
                await query.message.reply_video(f)
        os.remove(filename)
    except Exception as e:
        await query.message.reply_text(f"❌ فشل التحميل: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
