# الحاقیهٔ دوم — تشخیص دسترسی رجیستری Provider — ۲۳ اکتبر ۲۰۲۶

این فایل به‌صورت append-only به تاریخچه اضافه شده است؛ آرشیو قبلی تغییر یا حذف نشده. گزارش میزبان در اینجا به شکل حداقلی و بدون مسیرهای واقعی، SID حساب محلی یا اطلاعات محرمانه ثبت می‌شود. SID برای تصمیم عملیاتی در خروجی محلی موجود است، اما در مخزن عمومی کپی نشده است.

## خروجی گزارش تازه

- Schema: `forexai.provider_registry_access_recovery_diagnostic.v1`
- نتیجه: `BLOCKED`؛ کد خروج `2`؛ بررسی فقط‌خواندنی.
- سرویس `ForexAIProviderSvc` ثبت نشده است؛ `StartName` واقعی وجود ندارد.
- حساب محلی هم‌نام `ForexAIProviderSvc` پیدا شده و فعال است (`disabled=false`).
- هویت پیشنهادی در runbook برابر `NT SERVICE\ForexAIProviderSvc` است؛ برای این principal در ACL پوشهٔ والد هیچ ACE صریح Allow یا Deny پیدا نشد.
- برای principal مجزای `<COMPUTER>\ForexAIProviderSvc` یک ACE صریح `Modify, Synchronize` در ACL پوشهٔ والد وجود دارد. این دو principal یکسان نیستند.
- محاسبهٔ دسترسی مؤثر انجام نشده است. هدف رجیستری `NOT_FOUND_OR_INACCESSIBLE` است و ACL فایل هدف قابل بررسی نیست.
- متغیر `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_BACKUP_DIR` تنظیم نشده؛ دایرکتوری یا نامزد پشتیبان تأییدشده‌ای موجود نیست؛ تمرین restore و تطبیق replay انجام نشده است.
- فایل رجیستری یا پشتیبان باز یا تغییر داده نشد. کلید خصوصی، مقدار passphrase، کلید عمومی خام، درخواست امضاشده، ledger یا authenticated envelope خوانده/ساخته/تغییر داده نشد.
- `orders_submitted=false`, `demo_trading_authorized=false`, `live_trading_allowed=false`.

## موانع گزارش‌شده

1. `PROVIDER_SERVICE_NOT_REGISTERED`
2. `PROVIDER_REGISTRY_FILE_NOT_FOUND_OR_INACCESSIBLE`
3. `PROVIDER_REGISTRY_BACKUP_DIRECTORY_NOT_CONFIGURED`
4. `PROVIDER_REGISTRY_BACKUP_DIRECTORY_NOT_AVAILABLE`
5. `PROVIDER_SERVICE_IDENTITY_ACL_PRINCIPAL_MISMATCH_REVIEW`
6. `EFFECTIVE_ACCESS_TEST_UNDER_PROVIDER_IDENTITY_REQUIRED`
7. `REGISTRY_BACKUP_RESTORE_REHEARSAL_AND_REPLAY_RECONCILIATION_REQUIRED`

## تصمیم و اقدام ایمن بعدی

هیچ شواهدی در این خروجی وجود ندارد که مشخص کند حساب محلی موجود، هویت مصوب سرویس است. وجود حساب و ACE آن مجوز انتخاب خودکارش نیست؛ پیشنهاد runbook برای حساب مجازی نیز تا زمانی که سرویس ساخته نشده و مالک Windows/Provider آن را تصویب نکرده، فقط یک سیاست هدف است.

تا وقتی مالک مسئول یک هویت دقیق را تأیید و روش سرویس دائمی را تصویب نکرده است:
- سرویس را نصب یا ثبت نکنید؛ CLI یک‌بارمصرف Admission را مستقیماً به سرویس Windows تبدیل نکنید.
- ACL حساب محلی یا حساب مجازی را تغییر ندهید و هیچ ACEای را حذف نکنید.
- فایل رجیستری ضدتکرار را نسازید یا مقداردهی اولیه نکنید.
- مسیر پشتیبان را حدس نزنید و متغیر آن را به پوشهٔ دلخواه تنظیم نکنید.
- اثر انگشت کلید Promotion را فقط بر پایهٔ فایل محلی یا متغیر فعلی میزبان انتخاب نکنید.

پس از تصویب هویت و مالکیت مسیرها، باید مجوز مؤثر زیر همان هویت واقعی آزمایش، پشتیبان‌گیری و restore تمرین، و سوابق صدور قبلی برای جلوگیری از replay آشتی داده شود. این اقدامات همچنان قبل از provision منابع مستقل Signal، Risk/reservation، Operator و Capital Firewall Grant کافی نیستند.

**وضعیت مجاز باقی می‌ماند: fail-closed؛ Kill Switch = DENY؛ Demo و Live غیرفعال؛ هیچ سفارشی ارسال نشود.**
