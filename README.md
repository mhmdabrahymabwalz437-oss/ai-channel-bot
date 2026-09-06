# ABU ALAZ manager channel

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

## مصادر TikTok وInstagram وLikee

لا يقوم الوكيل بتنزيل فيديوهات عشوائية من صفحات هذه المنصات أو إزالة العلامات المائية؛ هذا يتطلب صلاحية من صاحب المحتوى وقد يخالف شروط الخدمة أو حقوق النشر. حاليًا يقبل البوت مصادر RSS وروابط الوسائط المباشرة المصرّح بها، ويمكن إضافة موصل رسمي لكل حساب تملكه بعد توفير OAuth/API credentials. TikTok Content Posting API مخصص أساسًا للنشر إلى TikTok، وInstagram Graph API يتيح وسائط الحسابات الاحترافية، بينما لم يتم اعتماد واجهة عامة رسمية من Likee لجلب فيديوهات المستخدمين.

لذلك المسار الآمن هو: **حسابات تملكها أو محتوى لديك إذن مكتوب بإعادة نشره → تخزين الملف في مجلد `media/` → فحصه → نشره على Telegram مع ذكر المصدر**. لا تضع كلمات مرور المنصات داخل `.env` ولا تستخدم scraping لتجاوز تسجيل الدخول أو القيود.

### Instaloader لحسابات Instagram المصرح بها

أضيفت مكتبة [Instaloader](https://github.com/instaloader/instaloader) كموصل اختياري. لا يعمل الموصل إلا عند تحديد حسابات مصرح بها وتفعيل التأكيد صراحة:

```env
INSTAGRAM_PROFILES=my_owned_profile,authorized_creator
INSTAGRAM_RIGHTS_CONFIRMED=true
```

سيختار أحدث فيديو من الحسابات المحددة، ويحفظه محليًا، ثم يمرره إلى ناشر Telegram. لا يمرر البوت كلمة مرور Instagram، ولا يقبل حسابات عشوائية من المستخدمين، ولا يزيل العلامة المائية. استخدام Instaloader يبقى على مسؤولية المشغّل، ويجب إيقافه إذا خالف شروط Instagram أو إذن صاحب المحتوى.

## Instagram Reels وYouTube Shorts

لا يمكن نشرهما عبر Telegram Bot API. يحتاج Instagram إلى حساب Professional وتطبيق Meta وAccess Token، ثم إنشاء container عبر `/{IG_ID}/media` باستخدام `media_type=REELS` و`video_url` عام، والانتظار حتى تجهز المعالجة ثم استدعاء `/{IG_ID}/media_publish`. يحتاج YouTube إلى OAuth 2.0 ونطاق `youtube.upload` واستدعاء `videos.insert` مع رفع resumable. تضاف هذه الموصلات كناشرين مستقلين بجانب `TelegramPublisher`، ولا ينبغي استخدام تسجيل دخول آلي أو scraping.
