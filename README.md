# بوت إدارة قناة بالذكاء الاصطناعي

بوت بايثون لقنوات Telegram: يقرأ برومبت المحتوى، يجمع عناوين من RSS، يولّد نصًا وكابشنًا، ويستخدم فيديو قصيرًا محليًا عند ضبط `VIDEO_PATH` أو صورة من المصادر، ثم ينشر تلقائيًا في الموعد المحدد.

## تشغيل سريع

```bash
cd ai_channel_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# عدّل .env، ثم اختبر بدون نشر:
python bot.py --once
# تشغيل الجدولة اليومية:
python bot.py
```

ابدأ مع `DRY_RUN=true`. بعد معاينة الملف الناتج والتأكد من الصلاحيات، غيّرها إلى `false`.

## إعداد Telegram

1. أنشئ بوتًا من `@BotFather` وخذ التوكن.
2. أضف البوت إلى القناة كمشرف مع صلاحية نشر الرسائل.
3. ضع `@channel_username` أو رقم chat id في `TELEGRAM_CHAT_ID`.

## ملاحظات مهمة

- استخدم فقط مصادر وصورًا مرخّصة أو مسموحًا بإعادة نشرها، واحفظ المصدر في الكابشن.
- لإرسال فيديو إلى Telegram، ضع مساره في `VIDEO_PATH=media/reel.mp4`. استخدم MP4/H.264 ويفضل أبعاد 9:16، مع إبقاء الملف تحت 50 MB حسب حد `sendVideo` في Telegram Bot API. إذا كان فارغًا، يستخدم البوت صورة المصدر.
- `DRY_RUN=true` هو الوضع الآمن الافتراضي.

## Instagram Reels وYouTube Shorts

لا يمكن نشرهما عبر Telegram Bot API. يحتاج Instagram إلى حساب Professional وتطبيق Meta وAccess Token، ثم إنشاء container عبر `/{IG_ID}/media` باستخدام `media_type=REELS` و`video_url` عام، والانتظار حتى تجهز المعالجة ثم استدعاء `/{IG_ID}/media_publish`. يحتاج YouTube إلى OAuth 2.0 ونطاق `youtube.upload` واستدعاء `videos.insert` مع رفع resumable. تضاف هذه الموصلات كناشرين مستقلين بجانب `TelegramPublisher`، ولا ينبغي استخدام تسجيل دخول آلي أو scraping.

