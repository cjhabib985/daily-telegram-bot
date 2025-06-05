import asyncio
import datetime
import random
from telegram import Bot

TOKEN = "توکن_ربات_تو"
CHANNEL_ID = "@آیدی_کانال_تو"  # یا عددی: -1001234567890

bot = Bot(token=TOKEN)

fals = [
    "♈ فروردین: امروز روز خوبی برای تصمیم‌گیریه.",
    "♉ اردیبهشت: بهتره با احتیاط رفتار کنی.",
    "♊ خرداد: زمان خوبیه برای شروع کار جدید.",
    "♋ تیر: به احساساتت توجه کن.",
    "♌ مرداد: امروز با دوستانت وقت بگذرون.",
    "♍ شهریور: تمرکزت رو روی کارهات بذار.",
    "♎ مهر: روز خوبی برای گفت‌وگوست.",
    "♏ آبان: به تغییرات توجه کن.",
    "♐ آذر: زمان برنامه‌ریزیه.",
    "♑ دی: نذار دیگران حواست رو پرت کنن.",
    "♒ بهمن: به خودت ایمان داشته باش.",
    "♓ اسفند: با آرامش پیش برو."
]

async def send_daily_message():
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0:
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text="☀️ صبح بخیر دوستای عزیزم!")
                await asyncio.sleep(2)
                await bot.send_message(chat_id=CHANNEL_ID, text="📜 فال روزانه:\n" + random.choice(fals))
            except Exception as e:
                print("❌ خطا:", e)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

async def main():
    await send_daily_message()

if __name__ == '__main__':
    asyncio.run(main())
