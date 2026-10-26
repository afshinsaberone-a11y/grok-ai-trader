# آرشیو پیوستهٔ ForexAI — قفل وابستگی‌های Provider
تاریخ: ۲۵ اکتبر ۲۰۲۶

این فایل یک افزودهٔ مستقل به تاریخچهٔ پروژه است؛ هیچ آرشیو قبلی حذف یا بازنویسی نشده است.

## مسئله
اسکریپت bootstrap میزبان Provider در مسیر Administrator، نسخهٔ pip را به‌صورت نامقید ارتقا می‌داد و وابستگی‌های requirements.txt را که نسخه‌های بازه‌ای دارند نصب می‌کرد. موفقیت آزمون‌های کد به‌تنهایی اصالت و تغییرناپذیری کل وابستگی‌های مستقیم و غیرمستقیم را اثبات نمی‌کند.

## تغییر واقعی در شاخه
در شاخهٔ ops/bootstrap-provider-host-v1-20261025:
- ارتقای نامقید pip حذف شد.
- نصب مستقیم از requirements.txt حذف شد.
- bootstrap اکنون وجود requirements-provider.lock.txt با pinهای دقیق و hashهای SHA-256 را شرط می‌کند و در نبود/نامعتبر بودن آن fail-closed متوقف می‌شود.
- نصب وابستگی‌ها فقط با --require-hashes --only-binary=:all: انجام می‌شود.
- SHA-256 فایل lock در گزارش bootstrap ثبت خواهد شد.
- آزمون قراردادی برای تضمین این کنترل‌ها اضافه شد.
- گردش‌کار دستی فقط‌خواندنی برای ساخت نامزد lock و مستندات بازبینی/ترتیب اتصال به SHA ثابت اضافه شد.

## محدودیت فعلی
هیچ lockfile تأییدشده‌ای هنوز ثبت نشده است؛ hashها جعل نشده‌اند. SHA ثابت فعلی 41883f30d32747d07d7b7772f8ee7c656a95e4a1 lockfile جدید را در خود ندارد. بنابراین bootstrap باید متوقف بماند تا فایل lock تولید، بازبینی و در یک commit معتبر ادغام شود و سپس $expectedCommit در تغییر جداگانه به همان commit شامل lockfile متصل شود.

## وضعیت کنترل‌های معامله
این تغییرات مرز مجوز معامله را باز نکرده‌اند. کلید Promotion و مرجع رسمی آن همچنان باید مستقلاً تأیید شوند؛ منابع Signal، Risk/Reservation، Operator و Grant نیز اثبات عملیاتی نشده‌اند. Grant صادر نشده، Demo مجاز نیست، Live غیرفعال است و سفارشی ارسال نشده است.

## آزمون و بازبینی
تست‌های قراردادی جدید در مخزن ثبت شده‌اند؛ اجرای واقعی GitHub Actions پس از این تغییرات هنوز باید تأیید شود. این افزوده ادعای موفقیت CI یا استقرار روی میزبان واقعی نمی‌کند.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: ایمن‌سازی و راه‌اندازی نامزد lock

برای جلوگیری از شکست گردش‌کار روی Runnerهای جدید و حذف وابستگی به tagهای قابل‌تغییر، اکشن‌های خارجی به SHA کامل commitهای تأییدشده pin شدند: checkout v7.0.1، setup-python v7.1.0 و upload-artifact v7.0.2. اعتبارنامه‌های checkout در پیکربندی Git نگه داشته نمی‌شوند؛ مجوز workflow همچنان فقط `contents: read` است.

گردش‌کار علاوه بر اجرای دستی، اکنون فقط هنگام push به شاخهٔ `ops/bootstrap-provider-host-v1-20261025` و در صورت تغییر workflow یا فایل‌های `requirements-provider-lock.in` / `requirements.txt` اجرا می‌شود. هدف صرفاً ساخت artifact نامعتبر تا قبل از بازبینی است؛ هیچ فایل lock خودکار commit/تأیید نمی‌شود و هیچ Secret یا مجوز معاملاتی به workflow داده نشده است.

آزمون قراردادی جدید، pin کامل SHA اکشن‌ها، محدودیت مجوز، عدم ذخیرهٔ credential و محدودبودن trigger را بررسی می‌کند. تغییرها در PR #331 ثبت شده‌اند؛ نتیجهٔ CI جدید باید تا پایان اجرا بررسی شود. این کار قفل وابستگی را تکمیل نمی‌کند: فایل نهایی هنوز باید تولید، بازبینی، در commit معتبر ثبت و سپس به SHA ثابت Bootstrap متصل شود. Demo غیرمجاز، Live غیرفعال و سفارش‌ها خاموش می‌مانند.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: آزمون نصب واقعی lock روی Windows

اجرای اولیهٔ نامزد lock موفق شد و artifact به‌صورت ZIP با شناسهٔ `12619211868` تولید شد. هش SHA-256 آرشیو ZIP برابر `f7b8d78a27597cdb281b81b5333dde6b219bedc9b05a13053b23ccd30b2e5a17` بود. فایل استخراج‌شده ۶۰ pin دقیق و ۱۴۰۷ مقدار hash دارد. این بررسی ساختاری فقط نشان می‌دهد خروجی تولید شده؛ خودش تأیید امنیت تک‌تک بسته‌ها یا قابلیت نصب روی میزبان هدف نیست.

برای بستن فاصلهٔ مهم بین «تولید موفق» و «نصب‌پذیری»، گردش‌کار به‌روزرسانی شد تا قبل از upload:
- در Windows و Python 3.13.17 یک venv تازه بسازد؛
- قفل را با `--require-hashes --only-binary=:all:`، همان فلگ‌های Bootstrap، نصب کند؛
- importهای اصلی را بررسی کند؛
- چهار ماژول آزمون قراردادی Provider را اجرا کند.

برای این نسخهٔ جدید باید منتظر نتیجهٔ CI تازه ماند. حتی در صورت موفقیت آن، آزمون مستقل روی Windows Server 2022، بازبینی provenance/نسخه‌های بسته‌ها، ثبت فایل قفل در commit بازبینی‌شده و به‌روزرسانی جداگانهٔ SHA ثابت Bootstrap همچنان لازم هستند. هیچ lock تأییدشده‌ای هنوز به main اضافه نشده است. سرویس یا رجیستری تولیدی نصب/ایجاد نشده؛ مجوز Demo غیرفعال و Live بسته باقی می‌ماند.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: اصلاح وابستگی Provider به‌جای تغییر استراتژی

بازبینی artifact نامزد نخست نشان داد که `backtesting==0.3.3` در PyPI فقط sdist دارد و wheel ندارد. چون Bootstrap الزام `--only-binary=:all:` دارد، lock مبتنی بر همهٔ `requirements.txt` قابل‌نصب نبود. این مانع واقعی بود؛ قفل اولیه هرچند از نظر ساختاری ۶۰ pin و ۱۴۰۷ hash داشت، نباید به نصب تولیدی راه می‌یافت.

برای رفع مانع، نسخهٔ کتابخانهٔ بک‌تست پروژه تغییر داده نشد. به‌جای آن `requirements-provider-lock.in` به وابستگی‌های کوچک Provider محدود شد: `cryptography>=42,<52` و `pytest>=8,<9`. کنترل‌های import در Bootstrap و گردش‌کار نامزد lock نیز از بررسی numpy/pandas/backtesting/openai-agents به cryptography/pytest تغییر کرد. آزمون‌های قراردادی Provider برای تضمین این مرز اضافه شدند. این کار پشتهٔ تحقیق را از محیط سرویس مرجع اعتماد جدا می‌کند و از تغییر ناخواستهٔ رفتار استراتژی جلوگیری می‌کند.

این اصلاح هنوز به نتیجهٔ CI جدید نیاز دارد: تولید lock، نصب binary-only با hash، importها و چهار مجموعه آزمون Provider باید همگی موفق شوند. سپس lock باید مستقلاً بازبینی شود و در محیط آزمایشی جداگانهٔ Windows Server 2022 نصب شود. تا آن زمان هیچ lock تولیدی تأییدشده‌ای وجود ندارد؛ سرویس/رجیستری تولیدی فعال نشده، Demo غیرمجاز، Live غیرفعال و سفارش‌ها خاموش می‌مانند.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: جداسازی نهایی محیط runtime و آزمون

طراحی قبلی که `pytest` را در محیط پایدار Provider نصب می‌کرد، اصلاح شد. اکنون دو ورودی مستقل داریم:
- `requirements-provider-lock.in`: فقط وابستگی runtime تولیدی یعنی `cryptography>=42,<52`.
- `requirements-provider-test-lock.in`: ورودی runtime به‌علاوهٔ `pytest>=8,<9` برای اجرای آزمون‌ها.

گردش‌کار نامزد lock باید هر دو lock را با SHA-256 تولید کند و هرکدام را با `--require-hashes --only-binary=:all:` در virtualenv جداگانهٔ Windows/Python 3.13 نصب و بررسی کند. runtime فقط `cryptography` را import می‌کند؛ محیط آزمون `cryptography` و `pytest` را import کرده و چهار فایل آزمون قراردادی Provider را اجرا می‌کند. سپس فقط پس از موفقیت، هر دو artifact را برای بازبینی بارگذاری می‌کند.

Bootstrap هم همین مرز را حفظ می‌کند: محیط پایدار Provider فقط lock تولیدی را نصب می‌کند؛ آزمون‌ها در محیط موقت واقع در work root حفاظت‌شده اجرا می‌شوند و پس از موفقیت، آن محیط آزمون حذف می‌شود. هش هر دو lock در گزارش ثبت می‌شود. این طراحی مانع ماندن pytest در محیط سرویس مرجع اعتماد می‌شود.

Artifact قبلی که فقط یک lock داشت، برای ورودی‌های جدید معتبر نیست و تأیید نهایی محسوب نمی‌شود. هر دو lock تازه باید از ورودی‌های جدید تولید، بررسی و با آزمون binary-only پاس شوند؛ سپس نصب مستقل روی Windows Server 2022 و بازبینی انسانی لازم است. تا آن زمان، SHA ثابت Bootstrap تغییر نمی‌کند و Demo/Live مجوز نمی‌گیرند؛ سفارشی ارسال نمی‌شود.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: نتیجهٔ نامزد دو lock و بازبینی منشأ بسته‌ها

اجرای گردش‌کار دو lock در Windows/Python 3.13.17 با موفقیت تمام شد: [Run 40248842829](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40248842829). سه blob ورودی و workflow استفاده‌شده در آن اجرا با blobهای فعلی شاخه یکسان‌اند.

Artifact شناسهٔ `12620266328`، حجم ۱۲٬۷۱۵ بایت و هش ZIP برابر `13effc0bf5d8c6b39182c6d941247e59d69097fe3f90a13f0bf6562fc624f4ce` است:
- runtime lock: سه pin و ۱۶۱ hash، SHA-256 برابر `f772c00c23acc36d2b52c09cf2ac53a1653f4c8fff31f7d1b5104b727162b017`.
- test lock: نه pin و ۱۷۳ hash، SHA-256 برابر `9102f41c1e071cf0469326233c106f6d55764495cfbb1c89451d106353f81cdb`.

هر دو فایل با `--require-hashes --only-binary=:all:` نصب شدند، importها موفق بودند و چهار مجموعه آزمون Provider با **۷۷ تست موفق در ۱٫۲۵ ثانیه** تمام شدند. یک guard جدید نیز اضافه شده تا قفل runtime نتواند pytest یا بسته‌های تحقیق/backtesting را وارد کند؛ اجرای CI مربوط به این guard هنوز باید کامل شود.

بازبینی metadata منشأ بسته‌ها یک مانع باقی‌مانده نشان داد:
- `cryptography==50.0.2`: صفحه PyPI می‌گوید هر ۵۹ فایل release provenance دارند و با Trusted Publishing بارگذاری شده‌اند: https://pypi.org/project/cryptography/50.0.2/.
- `cffi==2.1.1`: PyPI می‌گوید provenance ندارد؛ tag رسمی upstream به commit `fd33e7700f0ebafe6f30bd5053f13327221b77a2` می‌رسد که امضای GitHub آن معتبر است: https://github.com/python-cffi/cffi/commit/fd33e7700f0ebafe6f30bd5053f13327221b77a2.
- `pycparser==3.12`: PyPI می‌گوید provenance ندارد؛ tag `release_v3.12` به commit `3ec766b7cd94724cba714296509604597ea4ce4e` می‌رسد که GitHub آن را بدون امضا گزارش می‌کند: https://github.com/eliben/pycparser/commit/3ec766b7cd94724cba714296509604597ea4ce4e.

پس هش‌ها، نصب wheel-only و آزمون‌های قرارداد تأیید شده‌اند، اما منشأ artifactهای cffi/pycparser و بازبینی مستقل هنوز باز هستند. صرف موفقیت نصب و تست به معنی اعتماد تولیدی نیست. دو فایل lock تا تکمیل بررسی منشأ، بازبینی مستقل و تمرین نصب جداگانه روی Windows Server 2022 نباید وارد SHA ثابت Bootstrap شوند.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: آزمون موفق روی Windows Server 2022

برای نزدیک‌ترشدن آزمون به سیستم مقصد، Runner گردش‌کار از `windows-latest` به `windows-2022` تغییر کرد. [اجرای 40249481942](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249481942) موفق شد. این Runner میزبانی‌شدهٔ GitHub با Windows Server 2022 است؛ این نتیجه هنوز آزمون نصب روی VPS واقعی مقصد نیست.

شواهد:
- Python `3.13.17` روی Runner راه‌اندازی شد.
- هر دو lock با `--require-hashes --only-binary=:all:` نصب شدند.
- محدودهٔ runtime دقیقاً `cffi, cryptography, pycparser` و محیط آزمون دقیقاً `cffi, colorama, cryptography, iniconfig, packaging, pluggy, pycparser, pygments, pytest` بود.
- چهار مجموعه آزمون قراردادی Provider همگی موفق شدند: **۷۷ تست در ۲٫۰۷ ثانیه**.
- بررسی نسخه‌های دقیق، هش‌ها و محدودهٔ بسته‌ها موفق شد و artifact بارگذاری شد.

شناسهٔ artifact برابر `12620098076` و SHA-256 آرشیو ZIP برابر `07686102d48180728e2a45bc75484a056a0ea85e2f4b665a290359cb87aa6cd0` است. هش lock runtime برابر `f772c00c23acc36d2b52c09cf2ac53a1653f4c8fff31f7d1b5104b727162b017` و هش lock آزمون برابر `9102f41c1e071cf0469326233c106f6d55764495cfbb1c89451d106353f81cdb` است. بررسی محلی آرشیو ZIP و فایل‌های استخراج‌شده این هش‌ها را تأیید کرد.

در SHA شاخه PR یعنی `2208965804f9e80c8c1ddefd837c75a80d946d26`، آزمون‌های مخزن، اعتبارسنجی ایستای G13 و Agent Runtime Check نیز موفق شدند:
- [Tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249492344)
- [G13 Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249492340)
- [Agent Runtime](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249492388)

این نتیجه گیت نصب/آزمون روی Runner میزبانی‌شدهٔ Windows Server 2022 را می‌بندد، اما lock را برای تولید تأیید نمی‌کند. بازبینی مستقل منشأ بسته‌ها و تمرین نصب در مقصد آزمایشی جداگانه هنوز لازم است. به‌خصوص PyPI برای `cffi==2.1.1` و `pycparser==3.12` provenance منتشرشده ندارد؛ commit رسمی cffi امضای معتبر دارد اما commit نسخهٔ pycparser امضا نشده است. تا حل این ریسک و تأیید بازبین مستقل، فایل‌ها فقط artifact نامزد باقی می‌مانند و نباید وارد SHA ثابت Bootstrap شوند.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: تفکیک CI فعلی از اعتبارسنجی artifact وابستگی

بازخوانی مستقیم GitHub در سرشاخهٔ فعلی PR #331 نشان داد:
- HEAD شاخه: `534f9b8d023dab8c024894e4672b7846ca495643`
- مبنای `main`: `41883f30d32747d07d7b7772f8ee7c656a95e4a1` (بدون تغییر)
- PR هنوز باز و ادغام‌نشده است و API بازبینی، هیچ review ارسالی برنمی‌گرداند.
- تست‌های مخزن و parser پاورشل: [run 40249683335](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249683335) — موفق.
- Agent Runtime Check: [run 40249683214](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249683214) — موفق.
- G13 Workflow Static Validation: [run 40249683212](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249683212) — موفق.

**تمایز ضروری در شواهد:** artifact نصب/آزمون lock در [run 40249481942](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249481942) تولید شده، اما آن run به SHA قدیمی‌تر `0bff777c6fc8f4cddc545dfc0de0bbc1f5a83589` تعلق دارد. ورودی‌های runtime/test و فایل workflow در HEAD فعلی همان blobهای قبلی‌اند، ولی این موضوع artifact قدیمی را به lock تأییدشده یا آزمون روی VPS واقعی تبدیل نمی‌کند. artifact ID `12620098076` و SHA-256 آرشیو ZIP `07686102d48180728e2a45bc75484a056a0ea85e2f4b665a290359cb87aa6cd0` هستند.

در HEAD فعلی، هر دو فایل `requirements-provider.lock.txt` و `requirements-provider-test.lock.txt` هنوز در مخزن وجود ندارند؛ بررسی Contents API برای هر دو مسیر نتیجهٔ 404 داد. بنابراین bootstrap با SHA ثابت فعلی باید در guard مربوط به lock متوقف شود؛ این توقف رفتار fail-closed مورد انتظار است. هیچ فایل قفل یا hash دستی ساخته نشده و bootstrap روی VPS واقعی اجرا نشده است.

مانع منشأ بسته‌ها همچنان حل نشده است: PyPI برای فایل‌های `cffi==2.1.1` و `pycparser==3.12` provenance منتشرشده نشان نمی‌دهد. هش‌ها و نصب wheel-only صرفاً یکپارچگی بایت‌های دریافت‌شده نسبت به hash ثبت‌شده و سازگاری آزمون را نشان می‌دهند؛ به‌تنهایی منشأ معتبر بسته‌ها را ثابت نمی‌کنند. بازبینی مستقل و آزمون نصب در محیط مقصدِ تحت کنترل جداگانه هنوز لازم‌اند.

این تغییر فقط تاریخچهٔ پیشرفت را تکمیل می‌کند؛ هیچ‌یک از موانع امنیتی معامله تغییر نکرده‌اند: Grant signer مستقل provision نشده، Promotion trust anchor نیازمند تطبیق است، Signal و Risk/Reservation و Operator approval عملیاتی مستقل اثبات نشده‌اند، Demo غیرمجاز است، Live غیرفعال است و هیچ سفارشی ارسال نشده است.


## افزودهٔ پیوسته — ۲۶ اکتبر ۲۰۲۶: کنترل خودکار provenance و نتیجهٔ اجرای واقعی

برای اینکه «نصب موفق» با «منشأ قابل‌اعتماد» اشتباه نشود، گردش‌کار نامزد lock به‌روزرسانی شد تا wheelهای واقعاً انتخاب‌شده برای Windows Server 2022 / Python 3.13.17 را دوباره با `--require-hashes --only-binary=:all:` دریافت کند و برای هر filename دقیق، API رسمی Integrity در PyPI را بررسی کند. گزارش این بررسی پیش از مرحلهٔ نهایی policy در artifact بارگذاری می‌شود؛ سپس اگر provenance مفقود باشد، گردش‌کار با شکست صریح متوقف می‌شود. این audit فقط وجود metadata را می‌سنجد و امضا، هویت ناشر، یا رابطهٔ source-to-wheel را رمزنگاری‌وار تأیید نمی‌کند.

### شواهد اجرا
- Commit workflow حاوی gate: `4249db5661d246e599ff817f7c3bad6e196de731`
- اجرای نامزد lock: [40257890420](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40257890420)
- نتیجهٔ اجرا: `failure` به‌علت سیاست provenance؛ این شکست عمدی و fail-closed است، نه شکست نصب یا آزمون قراردادی.
- Runtime و test lock هر دو با hash enforcement و wheel-only نصب شدند؛ چهار مجموعه آزمون Provider موفق شدند: ۷۷ تست.
- گزارش provenance برای ۹ wheel هدف ساخته شد و artifact پیش از اجرای gate نهایی بارگذاری شد: ID `12623427296`, اندازه 13,621 بایت، SHA-256 آرشیو `3034919cdf5736855c13d3d703b13fd23c7fdec88ba6328b0b0c21fb524eb59f`.

### نتیجهٔ دقیق برای wheelهای هدف
**Provenance مفقود (BLOCKED):**
- `cffi-2.1.1-cp313-cp313-win_amd64.whl`
- `colorama-0.4.6-py2.py3-none-any.whl`
- `pycparser-3.12-py3-none-any.whl`
- `pygments-2.21.0-py3-none-any.whl`

**Metadata موجود ولی از این audit به‌تنهایی تأیید رمزنگاری نشده:**
- `cryptography-50.0.2-cp311-abi3-win_amd64.whl`
- `iniconfig-2.3.1-py3-none-any.whl`
- `packaging-26.3-py3-none-any.whl`
- `pluggy-1.7.0-py3-none-any.whl`
- `pytest-8.4.2-py3-none-any.whl`

این گزارش مستند می‌کند که ارتقای CI از «تولید نامزد و تست نصب» به «رد خودکار بسته‌های فاقد provenance» انجام شده است. برای حل نهایی باید برای چهار فایل مسدودشده provenance معتبر از ناشر/منبع رسمی فراهم شود، یا یک مسیر build داخلی از source بازبینی‌شده با زنجیرهٔ منشأ قابل‌تأیید طراحی و به‌طور مستقل بررسی شود. فقط تغییر شمارهٔ نسخه یا خاموش‌کردن gate مجاز نیست.

پس از این تغییرها، HEAD شاخه `38d355660ca2cc848ff5d4c2b25f853448ef6db3` این CIها را با موفقیت گذراند:
- [Repository tests + PowerShell parser](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40257973886)
- [Project Repair Loop](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40257973866)
- [G13 static validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40257971298)
- [Agent Runtime](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40257971239)

PR #331 همچنان باز و ادغام‌نشده است؛ هیچ بازبینی مستقل ثبت نشده و `main` روی `41883f30d32747d07d7b7772f8ee7c656a95e4a1` باقی مانده است. فایل‌های lock تأییدنشده در مخزن اضافه نشده‌اند و bootstrap به‌صورت fail-closed متوقف می‌ماند. این تغییرات هیچ منبع امضاکنندهٔ مستقل Grant یا مجوز معاملاتی ایجاد نکرده‌اند؛ Demo غیرمجاز، Live غیرفعال و سفارش‌ها ارسال‌نشده باقی می‌مانند.
