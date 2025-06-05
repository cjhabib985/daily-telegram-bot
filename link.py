import os
import sqlite3
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
JOIN_LINK = os.getenv("JOIN_LINK")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not BOT_TOKEN:
    print("توکن ربات پیدا نشد! لطفا فایل .env رو چک کن.")
    exit(1)

DB_PATH = "usage.db"
MAX_DAILY_UPLOADS = 5

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usage (
            user_id INTEGER,
            date TEXT,
            count INTEGER,
            PRIMARY KEY(user_id, date)
        )
        """
    )
    conn.commit()
    conn.close()

def can_upload(user_id):
    from datetime import date
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM usage WHERE user_id=? AND date=?", (user_id, today))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] < MAX_DAILY_UPLOADS
    return True

def increment_usage(user_id):
    from datetime import date
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM usage WHERE user_id=? AND date=?", (user_id, today))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE usage SET count=count+1 WHERE user_id=? AND date=?", (user_id, today))
    else:
        cursor.execute("INSERT INTO usage (user_id, date, count) VALUES (?, ?, 1)", (user_id, today))
    conn.commit()
    conn.close()

async def is_user_member(update: Update, user_id: int) -> bool:
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! فایل بفرست تا لینک دانلود بگیر."
    )

# تابع retry برای آپلود فایل با 3 تلاش و فاصله 2 ثانیه بین تلاش‌ها
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def upload_file(file_path, file_name):
    with open(file_path, "rb") as f:
        response = requests.post(f"https://transfer.sh/{file_name or 'file'}", files={"file": f})
    response.raise_for_status()
    return response.text.strip()

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    if chat_member.status in ["left", "kicked"]:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("عضویت در کانال", url=JOIN_LINK)]]
        )
        await update.message.reply_text(
            "لطفا اول در کانال عضو شوید تا بتوانید فایل ارسال کنید.",
            reply_markup=keyboard,
        )
        return

    if not can_upload(user_id):
        await update.message.reply_text(
            f"⚠️ محدودیت روزانه شما ({MAX_DAILY_UPLOADS} فایل) تکمیل شده است. لطفا فردا دوباره تلاش کنید."
        )
        return

    file = (
        update.message.document
        or update.message.video
        or update.message.audio
        or (update.message.photo[-1] if update.message.photo else None)
    )
    if not file:
        await update.message.reply_text("لطفا فقط فایل ارسال کنید.")
        return

    await update.message.reply_text("در حال آپلود فایل، لطفا صبر کنید...")

    file_obj = await file.get_file()
    file_path = f"temp_{user_id}"

    try:
        await file_obj.download_to_drive(file_path)
    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود فایل: {e}")
        return

    try:
        download_link = upload_file(file_path, file.file_name)
        increment_usage(user_id)
        await update.message.reply_text(f"لینک دانلود فایل شما:\n{download_link}")
    except requests.RequestException as e:
        await update.message.reply_text(f"خطا در آپلود فایل به سرور. لطفا دوباره تلاش کنید.\n{e}")
    except Exception as e:
        await update.message.reply_text(f"خطای غیرمنتظره: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.PHOTO, handle_file))

    print("ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
