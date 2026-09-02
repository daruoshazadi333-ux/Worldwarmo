import asyncio, json, random, logging, traceback, time, re
from pathlib import Path
from datetime import datetime, date, timedelta
from os import system as os_system, name as os_name
from rubka.asynco import Robot
from rubka.context import Message
from rubka.keypad import ChatKeypadBuilder

# ---------- storage root (must exist before logging starts) ----------
DB_ROOT = Path("wwx_database")
DB_ROOT.mkdir(parents=True, exist_ok=True)

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wwx_database/engine_errors.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------- config ----------
BOT_TOKEN = "BHJEGG0LZYHJRDVYGAQUHCZXQLNBOMCRDTAWBRSPVRGVDOHEJZIZOOXSYIXOEEOK"
ADMINS = [admin for admin in ["", "b0IHXHW0nOE0346b7cf8cf9382619504"] if admin]
ADMIN_PASSWORD = "admin24354657"
ADMIN_USERNAME = "@Saaid987"
OWNER_ID = "b0IHXHW0nOE0346b7cf8cf9382619504"
INACTIVITY_DAYS = 14
INACTIVITY_CHECK_SECONDS = 3600
# ---------- storage (new isolated database layout) ----------
DATA_FILE = DB_ROOT / "core_users_v2.json"
COUNTRIES_FILE = DB_ROOT / "nations_registry_v2.json"
UN_FILE = DB_ROOT / "global_council_v2.json"
ALLIANCE_FILE = DB_ROOT / "alliances_network_v2.json"
BOT_STATUS_FILE = DB_ROOT / "runtime_state_v2.json"
DB_META_FILE = DB_ROOT / "database_meta.json"
DB_VERSION = 2

def ensure_database():
    meta = {
        "schema": DB_VERSION,
        "engine": "WWX_JSON_STORAGE",
        "created_at": datetime.now().isoformat(),
        "layout": "isolated_v2"
    }
    try:
        if not DB_META_FILE.exists():
            with DB_META_FILE.open("w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

ensure_database()

F = {"b":"**","i":"_","m":"`","l":"▬"*30,"a":"➤","s":"★","f":"🔥","c":"♛","sh":"🛡","sw":"⚔","co":"🪙","d":"◆","ch":"✅","cr":"❌","sk":"💀","t":"🏆","g":"🌐","bo":"💥","h":"🤝","be":"🗡️"}

MAX_WARNINGS = 3
RULES_TEXT = (
    "📜 قوانین جنگ جهانی\n\n"
    "⚠️ اخطارها فقط توسط مدیریت و از پنل ادمین ثبت می‌شوند.\n"
    "🔴 مجموع اخطارها حداکثر ۳ عدد است.\n"
    "🚫 با رسیدن به ۳ اخطار، کشور شما ریست و حساب شما مسدود می‌شود.\n"
    "💰 پول پرداخت‌شده برای پک‌ها و خریدها به هیچ عنوان پس داده نمی‌شود.\n"
    "⚔️ سوءاستفاده از باگ، اسپم و ایجاد مزاحمت نیز می‌تواند اخطار داشته باشد.\n"
    "🛡️ قوانین برای همه کاربران یکسان است."
)
# واژه‌های پایه برای تشخیص توهین؛ فهرست عمداً کوتاه نگه داشته شده تا خطای تشخیص کم شود.
BAD_WORDS = {
    "احمق","بی شعور","بی‌شعور","کسخل","کودن","نفهم","حرومزاده","حرامزاده",
    "گمشو","دهنتو ببند","خفه شو","عوضی","فحش","fuck","shit"
}


COUNTRIES = [
    {"code":"US","flag":"🇺🇸","name":"آمریکا","emoji":"🦅","bonus":500},
    {"code":"GB","flag":"🇬🇧","name":"بریتانیا","emoji":"👑","bonus":400},
    {"code":"FR","flag":"🇫🇷","name":"فرانسه","emoji":"🗼","bonus":350},
    {"code":"DE","flag":"🇩🇪","name":"آلمان","emoji":"🦅","bonus":450},
    {"code":"IT","flag":"🇮🇹","name":"ایتالیا","emoji":"🍕","bonus":300},
    {"code":"CA","flag":"🇨🇦","name":"کانادا","emoji":"🍁","bonus":350},
    {"code":"ES","flag":"🇪🇸","name":"اسپانیا","emoji":"💃","bonus":300},
    {"code":"GR","flag":"🇬🇷","name":"یونان","emoji":"🏛","bonus":200},
    {"code":"NL","flag":"🇳🇱","name":"هلند","emoji":"🌷","bonus":250},
    {"code":"NO","flag":"🇳🇴","name":"نروژ","emoji":"🏔","bonus":200},
    {"code":"JP","flag":"🇯🇵","name":"ژاپن","emoji":"🗾","bonus":400},
    {"code":"RU","flag":"🇷🇺","name":"روسیه","emoji":"🐻","bonus":500},
    {"code":"CN","flag":"🇨🇳","name":"چین","emoji":"🐉","bonus":500},
    {"code":"IR","flag":"🇮🇷","name":"ایران","emoji":"🦁","bonus":350},
    {"code":"IN","flag":"🇮🇳","name":"هند","emoji":"🐘","bonus":450},
    {"code":"KP","flag":"🇰🇵","name":"کره شمالی","emoji":"💣","bonus":300},
    {"code":"IL","flag":"✡️","name":"اسرائیل","emoji":"🕎","bonus":350},
    {"code":"SA","flag":"🇸🇦","name":"عربستان","emoji":"🕋","bonus":400},
    {"code":"TR","flag":"🇹🇷","name":"ترکیه","emoji":"🕌","bonus":300},
    {"code":"BR","flag":"🇧🇷","name":"برزیل","emoji":"⚽","bonus":300},
    {"code":"AE","flag":"🇦🇪","name":"امارات","emoji":"🏙","bonus":400},
    {"code":"PK","flag":"🇵🇰","name":"پاکستان","emoji":"⭐","bonus":250},
    {"code":"EG","flag":"🇪🇬","name":"مصر","emoji":"🏺","bonus":250},
    {"code":"KR","flag":"🇰🇷","name":"کره جنوبی","emoji":"🎵","bonus":300},
    {"code":"SY","flag":"🇸🇾","name":"سوریه","emoji":"🏛","bonus":150},
    {"code":"VN","flag":"🇻🇳","name":"ویتنام","emoji":"🌴","bonus":200},
    {"code":"VE","flag":"🇻🇪","name":"ونزوئلا","emoji":"🛢","bonus":200},
    {"code":"CU","flag":"🇨🇺","name":"کوبا","emoji":"🚬","bonus":150},
    {"code":"ET","flag":"🇪🇹","name":"اتیوپی","emoji":"☕","bonus":150},
    {"code":"LB","flag":"🇱🇧","name":"لبنان","emoji":"🌲","bonus":150},
    {"code":"PS","flag":"🇵🇸","name":"فلسطین","emoji":"🕊","bonus":200},
    {"code":"ZA","flag":"🇿🇦","name":"آفریقای جنوبی","emoji":"🦁","bonus":200},
    {"code":"IQ","flag":"🇮🇶","name":"عراق","emoji":"🏛","bonus":200},
    {"code":"AU","flag":"🇦🇺","name":"استرالیا","emoji":"🦘","bonus":350},
    {"code":"NZ","flag":"🇳🇿","name":"نیوزیلند","emoji":"🥝","bonus":220},
    {"code":"MX","flag":"🇲🇽","name":"مکزیک","emoji":"🌵","bonus":280},
    {"code":"AR","flag":"🇦🇷","name":"آرژانتین","emoji":"⚽","bonus":320},
    {"code":"CL","flag":"🇨🇱","name":"شیلی","emoji":"🏔","bonus":220},
    {"code":"CO","flag":"🇨🇴","name":"کلمبیا","emoji":"☕","bonus":240},
    {"code":"PE","flag":"🇵🇪","name":"پرو","emoji":"🦙","bonus":210},
    {"code":"UY","flag":"🇺🇾","name":"اروگوئه","emoji":"⚽","bonus":190},
    {"code":"PY","flag":"🇵🇾","name":"پاراگوئه","emoji":"🌿","bonus":160},
    {"code":"BO","flag":"🇧🇴","name":"بولیوی","emoji":"⛰️","bonus":150},
    {"code":"EC","flag":"🇪🇨","name":"اکوادور","emoji":"🌋","bonus":170},
    {"code":"GY","flag":"🇬🇾","name":"گویان","emoji":"🌴","bonus":130},
    {"code":"SR","flag":"🇸🇷","name":"سورینام","emoji":"🌳","bonus":120},
    {"code":"FJ","flag":"🇫🇯","name":"فیجی","emoji":"🌴","bonus":100},
    {"code":"PT","flag":"🇵🇹","name":"پرتغال","emoji":"⚓","bonus":280},
    {"code":"IE","flag":"🇮🇪","name":"ایرلند","emoji":"☘️","bonus":210},
    {"code":"IS","flag":"🇮🇸","name":"ایسلند","emoji":"❄️","bonus":180},
    {"code":"SE","flag":"🇸🇪","name":"سوئد","emoji":"🛡️","bonus":260},
    {"code":"FI","flag":"🇫🇮","name":"فنلاند","emoji":"❄️","bonus":240},
    {"code":"DK","flag":"🇩🇰","name":"دانمارک","emoji":"⚔️","bonus":230},
    {"code":"PL","flag":"🇵🇱","name":"لهستان","emoji":"🦅","bonus":260},
    {"code":"CZ","flag":"🇨🇿","name":"چک","emoji":"🏰","bonus":210},
    {"code":"SK","flag":"🇸🇰","name":"اسلواکی","emoji":"🏔","bonus":160},
    {"code":"HU","flag":"🇭🇺","name":"مجارستان","emoji":"🦅","bonus":190},
    {"code":"RO","flag":"🇷🇴","name":"رومانی","emoji":"🏰","bonus":200},
    {"code":"BG","flag":"🇧🇬","name":"بلغارستان","emoji":"🌹","bonus":170},
    {"code":"RS","flag":"🇷🇸","name":"صربستان","emoji":"🦅","bonus":180},
    {"code":"HR","flag":"🇭🇷","name":"کرواسی","emoji":"♟️","bonus":200},
    {"code":"HT","flag":"🇭🇹","name":"هائیتی","emoji":"🌴","bonus":110},
    {"code":"SI","flag":"🇸🇮","name":"اسلوونی","emoji":"🏔","bonus":150},
    {"code":"AL","flag":"🇦🇱","name":"آلبانی","emoji":"🦅","bonus":140},
    {"code":"DO","flag":"🇩🇴","name":"جمهوری دومینیکن","emoji":"🌴","bonus":140},
    {"code":"TT","flag":"🇹🇹","name":"ترینیداد و توباگو","emoji":"🌊","bonus":110},
    {"code":"JM","flag":"🇯🇲","name":"جامائیکا","emoji":"🎵","bonus":130},
    {"code":"UA","flag":"🇺🇦","name":"اوکراین","emoji":"🌾","bonus":280},
    {"code":"BY","flag":"🇧🇾","name":"بلاروس","emoji":"🌲","bonus":190},
    {"code":"MD","flag":"🇲🇩","name":"مولداوی","emoji":"🍇","bonus":130},
    {"code":"LT","flag":"🇱🇹","name":"لیتوانی","emoji":"🌲","bonus":150},
    {"code":"LV","flag":"🇱🇻","name":"لتونی","emoji":"🌲","bonus":145},
    {"code":"EE","flag":"🇪🇪","name":"استونی","emoji":"💻","bonus":150},
    {"code":"GE","flag":"🇬🇪","name":"گرجستان","emoji":"🍇","bonus":170},
    {"code":"AM","flag":"🇦🇲","name":"ارمنستان","emoji":"⛰️","bonus":140},
    {"code":"AZ","flag":"🇦🇿","name":"آذربایجان","emoji":"🔥","bonus":190},
    {"code":"KZ","flag":"🇰🇿","name":"قزاقستان","emoji":"🐎","bonus":240},
    {"code":"UZ","flag":"🇺🇿","name":"ازبکستان","emoji":"🏜️","bonus":190},
    {"code":"TM","flag":"🇹🇲","name":"ترکمنستان","emoji":"🐎","bonus":150},
    {"code":"KG","flag":"🇰🇬","name":"قرقیزستان","emoji":"🏔","bonus":140},
    {"code":"TJ","flag":"🇹🇯","name":"تاجیکستان","emoji":"⛰️","bonus":140},
    {"code":"MN","flag":"🇲🇳","name":"مغولستان","emoji":"🐎","bonus":180},
    {"code":"AF","flag":"🇦🇫","name":"افغانستان","emoji":"🏔","bonus":170},
    {"code":"BD","flag":"🇧🇩","name":"بنگلادش","emoji":"🌊","bonus":180},
    {"code":"LK","flag":"🇱🇰","name":"سریلانکا","emoji":"🌴","bonus":170},
    {"code":"NP","flag":"🇳🇵","name":"نپال","emoji":"🏔","bonus":180},
    {"code":"BT","flag":"🇧🇹","name":"بوتان","emoji":"🐉","bonus":110},
    {"code":"MM","flag":"🇲🇲","name":"میانمار","emoji":"🌴","bonus":150},
    {"code":"TH","flag":"🇹🇭","name":"تایلند","emoji":"🐘","bonus":220},
    {"code":"MY","flag":"🇲🇾","name":"مالزی","emoji":"🌴","bonus":230},
    {"code":"SG","flag":"🇸🇬","name":"سنگاپور","emoji":"🏙️","bonus":300},
    {"code":"ID","flag":"🇮🇩","name":"اندونزی","emoji":"🌋","bonus":240},
    {"code":"PH","flag":"🇵🇭","name":"فیلیپین","emoji":"🌊","bonus":200},
    {"code":"KH","flag":"🇰🇭","name":"کامبوج","emoji":"🏯","bonus":130},
    {"code":"LA","flag":"🇱🇦","name":"لائوس","emoji":"🌿","bonus":120},
    {"code":"BN","flag":"🇧🇳","name":"برونئی","emoji":"🛢️","bonus":150},
    {"code":"TL","flag":"🇹🇱","name":"تیمور شرقی","emoji":"🌊","bonus":100},
    {"code":"WS","flag":"🇼🇸","name":"ساموآ","emoji":"🌴","bonus":100},
    {"code":"QA","flag":"🇶🇦","name":"قطر","emoji":"🏙️","bonus":280},
    {"code":"KW","flag":"🇰🇼","name":"کویت","emoji":"🛢️","bonus":260},
    {"code":"BH","flag":"🇧🇭","name":"بحرین","emoji":"🌊","bonus":200},
    {"code":"OM","flag":"🇴🇲","name":"عمان","emoji":"🏜️","bonus":220},
    {"code":"YE","flag":"🇾🇪","name":"یمن","emoji":"🏔","bonus":130},
    {"code":"JO","flag":"🇯🇴","name":"اردن","emoji":"🏜️","bonus":180},
    {"code":"TO","flag":"🇹🇴","name":"تونگا","emoji":"🌊","bonus":95},
    {"code":"MA","flag":"🇲🇦","name":"مراکش","emoji":"🕌","bonus":230},
    {"code":"DZ","flag":"🇩🇿","name":"الجزایر","emoji":"🏜️","bonus":230},
    {"code":"TN","flag":"🇹🇳","name":"تونس","emoji":"🏺","bonus":180},
    {"code":"LY","flag":"🇱🇾","name":"لیبی","emoji":"🛢️","bonus":160},
    {"code":"SD","flag":"🇸🇩","name":"سودان","emoji":"🌾","bonus":140},
    {"code":"SS","flag":"🇸🇸","name":"سودان جنوبی","emoji":"🌿","bonus":120},
    {"code":"SO","flag":"🇸🇴","name":"سومالی","emoji":"🏜️","bonus":120},
    {"code":"DJ","flag":"🇩🇯","name":"جیبوتی","emoji":"⚓","bonus":100},
    {"code":"ER","flag":"🇪🇷","name":"اریتره","emoji":"🏜️","bonus":110},
    {"code":"KE","flag":"🇰🇪","name":"کنیا","emoji":"🦁","bonus":180},
    {"code":"TZ","flag":"🇹🇿","name":"تانزانیا","emoji":"🦒","bonus":170},
    {"code":"UG","flag":"🇺🇬","name":"اوگاندا","emoji":"🦍","bonus":140},
    {"code":"RW","flag":"🇷🇼","name":"رواندا","emoji":"🌋","bonus":120},
    {"code":"GH","flag":"🇬🇭","name":"غنا","emoji":"⭐","bonus":160},
    {"code":"NG","flag":"🇳🇬","name":"نیجریه","emoji":"🦅","bonus":240},
    {"code":"CM","flag":"🇨🇲","name":"کامرون","emoji":"🦁","bonus":130},
    {"code":"SN","flag":"🇸🇳","name":"سنگال","emoji":"🦁","bonus":140},
    {"code":"CI","flag":"🇨🇮","name":"ساحل عاج","emoji":"🐘","bonus":150},
    {"code":"ML","flag":"🇲🇱","name":"مالی","emoji":"🏜️","bonus":120},
    {"code":"NE","flag":"🇳🇪","name":"نیجر","emoji":"🏜️","bonus":110},
    {"code":"MR","flag":"🇲🇷","name":"موریتانی","emoji":"🐪","bonus":110},
    {"code":"ZW","flag":"🇿🇼","name":"زیمبابوه","emoji":"🦁","bonus":130},
    {"code":"ZM","flag":"🇿🇲","name":"زامبیا","emoji":"🦅","bonus":120},
    {"code":"MZ","flag":"🇲🇿","name":"موزامبیک","emoji":"🌊","bonus":130},
    {"code":"AO","flag":"🇦🇴","name":"آنگولا","emoji":"🛢️","bonus":170},
    {"code":"NA","flag":"🇳🇦","name":"نامیبیا","emoji":"🏜️","bonus":120},
    {"code":"BW","flag":"🇧🇼","name":"بوتسوانا","emoji":"🐘","bonus":110},
    {"code":"MG","flag":"🇲🇬","name":"ماداگاسکار","emoji":"🌴","bonus":120},
    {"code":"MU","flag":"🇲🇺","name":"موریس","emoji":"🌊","bonus":100},
    {"code":"SC","flag":"🇸🇨","name":"سیشل","emoji":"🌊","bonus":100},
    {"code":"CD","flag":"🇨🇩","name":"کنگو","emoji":"🌳","bonus":150},
    {"code":"CG","flag":"🇨🇬","name":"کنگو برازاویل","emoji":"🌳","bonus":130},
    {"code":"GA","flag":"🇬🇦","name":"گابن","emoji":"🌳","bonus":120},
    {"code":"GQ","flag":"🇬🇶","name":"گینه استوایی","emoji":"🛢️","bonus":120},
    {"code":"VU","flag":"🇻🇺","name":"وانواتو","emoji":"🌋","bonus":95},
    {"code":"BJ","flag":"🇧🇯","name":"بنین","emoji":"🌴","bonus":110},
    {"code":"TG","flag":"🇹🇬","name":"توگو","emoji":"🌴","bonus":105},
    {"code":"BF","flag":"🇧🇫","name":"بورکینافاسو","emoji":"🏜️","bonus":110},
    {"code":"GN","flag":"🇬🇳","name":"گینه","emoji":"🌿","bonus":110},
    {"code":"SL","flag":"🇸🇱","name":"سیرالئون","emoji":"🌊","bonus":100},
    {"code":"LR","flag":"🇱🇷","name":"لیبریا","emoji":"🌴","bonus":100},
    {"code":"CV","flag":"🇨🇻","name":"کیپ ورد","emoji":"🌊","bonus":95},
    {"code":"GM","flag":"🇬🇲","name":"گامبیا","emoji":"🌊","bonus":95},
    {"code":"BI","flag":"🇧🇮","name":"بوروندی","emoji":"🌿","bonus":100},
    {"code":"MW","flag":"🇲🇼","name":"مالاوی","emoji":"🌿","bonus":100},
]

FACTIONS = {
    "sepah":{"name":"سپاه پاسداران","icon":"🛡⚔️","emoji":"🇮🇷","atk":1.5,"def":2.0,"w":["خیبرشکن","موشک","پهپاد"],"min":5000,"max":10},
    "darkweb":{"name":"دارک وب","icon":"💀🌐","emoji":"🖤","atk":2.0,"def":0.5,"w":["بمب اتم","پهپاد","B2"],"min":8000,"max":7},
    "hezbollah":{"name":"حزب‌الله","icon":"⚔️🕊","emoji":"🇱🇧","atk":1.8,"def":1.5,"w":["موشک","خیبرشکن","تانک"],"min":4000,"max":12}
}

EQUIP = {
    "اف۲۲":(1600,"🛩","جنگنده",50),"اف۳۵":(1700,"🛩","جنگنده",60),"اف۱۶":(1500,"🛩","جنگنده",40),
    "اف۱۵":(1450,"🛩","جنگنده",35),"تایفون":(1550,"🛩","جنگنده",45),"سوخو۳۵":(1650,"🛩","جنگنده",55),
    "سوخو۵۷":(1800,"🛩","جنگنده",70),"جی۲۰":(1750,"🛩","جنگنده",65),
    "B2":(3100,"💣","بمب‌افکن",200),"B1":(2900,"💣","بمب‌افکن",180),"B52":(2600,"💣","بمب‌افکن",150),
    "موشک":(1400,"🚀","موشکی",30),"خیبرشکن":(1900,"🚀","موشکی",80),"پهپاد":(1350,"🛸","پهپادی",25),
    "تانک":(1500,"🪖","زمینی",40),"بالگرد":(1450,"🚁","هوایی",35),"زیردریایی":(1700,"🌊","دریایی",60),
    "ناو":(2100,"🚢","دریایی",100),"بمب اتم":(10000,"☢️","ویژه",1000),"بمب تزار":(9100,"💥","ویژه",800),
    "پدافند":(1300,"🛡","دفاعی",20),"اس۴۰۰":(1400,"🛡","دفاعی",30),"پاتریوت":(1380,"🛡","دفاعی",28),
    "تاد":(1420,"🛡","دفاعی",32),"گنبد":(1450,"🛡","دفاعی",35),"اس۵۰۰":(1500,"🛡","دفاعی",40),
}

# تجهیزات نظامی گسترده‌تر برای تنوع بیشتر بازی
EQUIP.update({
    "رافال":(1580,"🛩️","جنگنده",48), "گریپن":(1500,"🛩️","جنگنده",42),
    "میگ۳۵":(1480,"🛩️","جنگنده",44), "سوخو۳۰":(1550,"🛩️","جنگنده",50),
    "جی۱۰":(1450,"🛩️","جنگنده",38), "اف۲۲ رپتور":(1850,"🛩️","جنگنده",75),
    "اف۳۵ لایتنینگ":(1900,"🛩️","جنگنده",78), "توپولف":(2800,"💣","بمب‌افکن",170),
    "کالیبر":(1750,"🚀","موشکی",55), "اسکندر":(1850,"🚀","موشکی",65),
    "فاتح":(1700,"🚀","موشکی",58), "ذوالفقار":(1800,"🚀","موشکی",62),
    "هایپرسونیک":(2300,"🚀","موشکی",95), "کروز":(1650,"🚀","موشکی",48),
    "سامانه لیزری":(2200,"🔆","دفاعی",55), "آیرون دوم":(1550,"🛡️","دفاعی",36),
    "تروفلاین":(1480,"🛡️","دفاعی",34), "دفاع هوایی":(1350,"🛡️","دفاعی",24),
    "مرکاوا":(1650,"🪖","زمینی",48), "لئوپارد۲":(1700,"🪖","زمینی",52),
    "آبرامز":(1750,"🪖","زمینی",55), "چلنگر":(1600,"🪖","زمینی",45),
    "زره‌پوش":(1200,"🚙","زمینی",22), "توپخانه":(1250,"🎯","زمینی",28),
    "راکت‌انداز":(1450,"🚀","زمینی",35), "کماندو":(900,"🪖","زمینی",15),
    "ناو هواپیمابر":(4200,"🚢","دریایی",180), "ناوشکن":(2400,"🚢","دریایی",115),
    "ناوچه":(1900,"🚢","دریایی",75), "قایق رزمی":(1000,"🚤","دریایی",25),
    "زیردریایی اتمی":(3600,"🌊","دریایی",150), "مین دریایی":(800,"🌊","دریایی",18),
    "هلیکوپتر آپاچی":(1800,"🚁","هوایی",55), "بلک هاوک":(1500,"🚁","هوایی",38),
    "ترابری نظامی":(1300,"✈️","هوایی",25), "پهپاد رزمی":(1550,"🛸","پهپادی",38),
    "پهپاد شناسایی":(1100,"🛸","پهپادی",16), "پهپاد سنگین":(1750,"🛸","پهپادی",45),
    "جنگ الکترونیک":(2000,"📡","ویژه",50), "ماهواره نظامی":(3000,"🛰️","ویژه",70),
    "رادار دوربرد":(1600,"📡","دفاعی",42), "مرکز فرماندهی":(2500,"🏢","ویژه",65),
    "سپر موشکی":(2100,"🛡️","دفاعی",50), "پایگاه هوایی":(2800,"🛬","ویژه",60),
})

PACKS = {
    "پک جنگنده":(15000,"🛩","ناوگان هوایی",{"اف۲۲":300,"اف۳۵":300,"اف۱۶":300,"اف۱۵":300,"تایفون":300,"سوخو۳۵":300,"سوخو۵۷":300,"جی۲۰":300}),
    "پک نابود":(35000,"💀","قدرت تخریب بالا",{"B2":200,"B1":200,"B52":200,"موشک":200,"پهپاد":200,"تانک":100,"بالگرد":50,"زیردریایی":25,"ناو":10,"بمب اتم":5}),
    "پک اقتصادی":(35000,"💰","مقرون به صرفه",{"B2":100,"B1":100,"B52":100,"موشک":100,"پدافند":100,"تانک":50,"بالگرد":30,"زیردریایی":20,"ناو":10}),
    "پک افسانه":(35000,"👑","افسانه‌ای و بی‌نظیر",{"موشک":350,"خیبرشکن":200,"زیردریایی":150,"ناو":100,"بمب تزار":100,"پدافند":200,"B2":200,"اف۳۵":200}),
    "پدافند جهان":(30000,"🛡","سپر دفاعی قدرتمند",{"اس۴۰۰":1000,"پاتریوت":1000,"تاد":1000,"گنبد":1000,"اس۵۰۰":1000})
}

# ---------- helpers ----------
def sty(t,s="b"): return f"{F[s]}{t}{F[s]}"
def fn(n): return f"{n:,}"
def ml(c="▬",n=30): return c*n
def mh(t,i="🔹"): return f"{i}{ml('═',15)}{i}\n{sty('  '+t+'  ','b')}\n{i}{ml('═',15)}{i}"
def mf(txt,title="",icon="📨"):
    lines=txt.split('\n')
    max_len=max((len(l) for l in lines),default=20)
    border="╔"+"═"*(max_len+2)+"╗"
    bottom="╚"+"═"*(max_len+2)+"╝"
    header=f"║ {icon} {title}".ljust(max_len+3)+"║" if title else ""
    content="\n".join("║ "+l.ljust(max_len)+" ║" for l in lines)
    return f"{border}\n{header}\n{content}\n{bottom}" if header else f"{border}\n{content}\n{bottom}"

def gid(msg,uid):
    try:
        if hasattr(msg,'author') and msg.author:
            un=getattr(msg.author,'username',None)
            if un: return f"@{un} | `{uid}`"
            fn=getattr(msg.author,'first_name',None)
            if fn: return f"{fn} | `{uid}`"
    except: pass
    try:
        sn=getattr(msg,'sender_name',None)
        if sn: return f"{sn} | `{uid}`"
    except: pass
    return f"`{uid}`"

def guser(msg):
    try:
        if hasattr(msg,'author') and msg.author:
            return getattr(msg.author,'username',None) or getattr(msg.author,'first_name',None)
    except: pass
    try: return getattr(msg,'sender_name',None)
    except: pass
    return None

def power(data,uid):
    countries=load_countries()
    eq=data.get("user_eq",{}).get(uid,{})
    pk=data.get("user_packs",{}).get(uid,[])
    p=sum(EQUIP.get(k,(0,)*4)[3]*v for k,v in eq.items())
    st=get_country_stats(data,uid)
    p+=int(st.get("soldiers",0)*0.5 + st.get("factories",0)*250 + st.get("cities",0)*150 + st.get("universities",0)*200)
    p+=len(set(pk))*500
    fac=data.get("users",{}).get(uid,{}).get("faction")
    if fac and fac in FACTIONS: p=int(p*FACTIONS[fac]["atk"])
    un=load_un()
    if uid==get_un_leader_uid(un,countries): p=int(p*1.5)
    elif uid in un.get("members",[]): p=int(p*1.2)
    return p

def defense_power(data,uid):
    eq=data.get("user_eq",{}).get(uid,{})
    dp=sum(EQUIP.get(it,(0,)*4)[3]*eq.get(it,0) for it in ["پدافند","اس۴۰۰","پاتریوت","تاد","گنبد","اس۵۰۰"])
    dp += get_country_stats(data,uid).get("bases",0)*250 + get_country_stats(data,uid).get("powerplants",0)*50
    fac=data.get("users",{}).get(uid,{}).get("faction")
    if fac and fac in FACTIONS: dp=int(dp*FACTIONS[fac]["def"])
    return dp

def get_coins(data,uid): return data.get("users",{}).get(uid,{}).get("coins",0)

def addc(data,uid,amt):
    if uid not in data.get("users",{}): return
    data["users"][uid]["coins"]=data["users"][uid].get("coins",0)+amt
    save_data(data)

def remc(data,uid,amt):
    if uid not in data.get("users",{}): return False,"کاربر یافت نشد"
    cur=data["users"][uid].get("coins",0)
    if amt<=0: return False,"مقدار باید مثبت باشد"
    if cur<amt: return False,f"موجودی کافی نیست. موجودی: {fn(cur)}"
    data["users"][uid]["coins"]=cur-amt
    save_data(data)
    return True,"موفق"

def addeq(data,uid,eq,amt):
    if amt<=0: return
    if "user_eq" not in data: data["user_eq"]={}
    if uid not in data["user_eq"]: data["user_eq"][uid]={}
    data["user_eq"][uid][eq]=data["user_eq"][uid].get(eq,0)+amt
    save_data(data)

def remeq(data,uid,eq,amt):
    if amt<=0: return False,"مقدار باید مثبت باشد"
    if "user_eq" not in data: data["user_eq"]={}
    if uid not in data["user_eq"]: data["user_eq"][uid]={}
    cur=data["user_eq"][uid].get(eq,0)
    if cur<amt: return False,f"تجهیزات کافی نیست. موجودی: {fn(cur)}"
    data["user_eq"][uid][eq]=cur-amt
    if data["user_eq"][uid][eq]<=0: del data["user_eq"][uid][eq]
    save_data(data)
    return True,"موفق"

def totaleq(data,uid):
    eq=data.get("user_eq",{}).get(uid,{}).copy()
    return eq

def consume(data,uid,eq,amt):
    if amt<=0: return 0,False
    total=data.get("user_eq",{}).get(uid,{}).get(eq,0)
    if total<amt: return 0,False
    data["user_eq"][uid][eq]-=amt
    if data["user_eq"][uid][eq]<=0: del data["user_eq"][uid][eq]
    save_data(data)
    return amt,True


def warning_count(data, uid):
    return int(data.get("users", {}).get(uid, {}).get("warnings", 0))

def set_warnings(data, uid, count):
    if uid in data.get("users", {}):
        data["users"][uid]["warnings"] = max(0, min(MAX_WARNINGS, int(count)))
        save_data(data)

async def issue_warning(bot, data, countries, uid, reason="تخلف از قوانین", notify=True):
    """یک اخطار ثبت می‌کند؛ اخطار سوم = ریست کشور + مسدودی."""
    if uid not in data.get("users", {}) or uid in ADMINS:
        return False
    user = data["users"][uid]
    count = warning_count(data, uid) + 1
    user["warnings"] = count
    user.setdefault("warning_log", []).append({
        "reason": reason, "time": datetime.now().isoformat()
    })
    if len(user["warning_log"]) > 20:
        user["warning_log"] = user["warning_log"][-20:]
    save_data(data)
    if count >= MAX_WARNINGS:
        my = next((code for code, info in countries.items() if info.get("owner") == uid), None)
        if my:
            info = countries[my]
            info["owner"] = None
            info["defense"] = False
            info["damage_taken"] = 0
        user["has_country"] = False
        user["coins"] = 0
        user["faction"] = None
        data.setdefault("user_eq", {})[uid] = {}
        data.setdefault("user_packs", {})[uid] = []
        data.setdefault("banned_users", [])
        if uid not in data["banned_users"]:
            data["banned_users"].append(uid)
        save_data(data)
        save_countries(countries)
        if notify:
            try:
                await bot.send_message(uid,
                    "🚫 اخطار سوم ثبت شد.\n"
                    "💥 کشور شما ریست شد.\n"
                    "🔒 حساب شما مسدود شد.\n\n"
                    "💰 مبالغ پرداخت‌شده برای پک‌ها و خریدها قابل استرداد نیستند.")
            except Exception:
                pass
        return True
    if notify:
        try:
            await bot.send_message(uid,
                f"⚠️ اخطار شماره {count}/{MAX_WARNINGS}\n"
                f"📌 دلیل: {reason}\n"
                f"🔴 اخطار سوم باعث ریست کشور و مسدودی می‌شود.")
        except Exception:
            pass
    return True

def contains_bad_word(text):
    t = (text or "").strip().lower()
    return any(w in t for w in BAD_WORDS)

def get_rules_menu():
    b = ChatKeypadBuilder()
    b.row(b.button(id="rules", text="📜 قوانین"))
    b.row(b.button(id="back_to_menu", text="🏠 بازگشت"))
    return b.build(resize_keyboard=True, on_time_keyboard=True)

# ---------- admin equipment + support + inactivity ----------
def parse_admin_equipment(text):
    """فرمت ترجیحی سه خطی و فرمت یک خطی را پشتیبانی می‌کند."""
    raw=(text or "").strip()
    if not raw:
        raise ValueError("empty")
    lines=[x.strip() for x in raw.replace("\r","").split("\n") if x.strip()]
    # )شناسه(
    # اسم وسیله
    # تعداد
    if len(lines)==3 and lines[0].startswith(")") and lines[0].endswith("("):
        target=lines[0][1:-1].strip()
        eq_name=lines[1]
        count=int(lines[2])
        return target,eq_name,count
    # )شناسه( اسم وسیله تعداد
    m=re.match(r'^\)\s*(.+?)\s*\(\s+(.+?)\s+(\d+)\s*$',raw,re.S)
    if m:
        return m.group(1).strip(),m.group(2).strip(),int(m.group(3))
    # legacy: id equipment amount (اسم چندکلمه‌ای هم پشتیبانی می‌شود)
    parts=raw.split()
    if len(parts)>=3:
        return parts[0]," ".join(parts[1:-1]),int(parts[-1])
    raise ValueError("bad format")

async def check_inactive_users(bot, data, countries):
    """بعد از ۱۴ روز عدم فعالیت، کشور و دارایی‌های کاربر را ریست می‌کند."""
    now=datetime.now(); changed_data=False; changed_countries=False
    for uid,user in list(data.get("users",{}).items()):
        if uid in ADMINS:
            continue
        raw=user.get("last_activity")
        if not raw:
            # کاربران قدیمی از زمان اجرای اولین بررسی شمارش می‌شوند.
            user["last_activity"]=now.isoformat(); changed_data=True; continue
        try:
            last=datetime.fromisoformat(raw)
        except (TypeError,ValueError):
            user["last_activity"]=now.isoformat(); changed_data=True; continue
        if now-last < timedelta(days=INACTIVITY_DAYS):
            continue
        owned=[code for code,info in countries.items() if info.get("owner")==uid]
        if not owned:
            continue
        for code in owned:
            info=countries[code]
            info["owner"]=None; info["defense"]=False; info["damage_taken"]=0
            changed_countries=True
        user["has_country"]=False
        user["coins"]=0
        user["faction"]=None
        data.setdefault("user_eq",{})[uid]={}
        data.setdefault("user_packs",{})[uid]=[]
        user["last_activity"]=now.isoformat()
        changed_data=True
        try:
            await bot.send_message(uid,"⏰ به دلیل ۱۴ روز عدم فعالیت، کشور شما آزاد شد و کوین‌ها، پک‌ها و تجهیزات شما پاک شدند.")
        except Exception:
            pass
    if changed_data: save_data(data)
    if changed_countries: save_countries(countries)

async def inactivity_worker(bot):
    while True:
        try:
            data=load_data(); countries=load_countries()
            await check_inactive_users(bot,data,countries)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Inactivity worker error: {e}\n{traceback.format_exc()}")
        await asyncio.sleep(INACTIVITY_CHECK_SECONDS)

# ---------- alliances ----------
def load_alliance():
    try:
        if ALLIANCE_FILE.exists():
            with ALLIANCE_FILE.open('r',encoding='utf-8') as f: return json.load(f)
    except: pass
    d={"alliances":{},"user_alliance":{},"traitor_until":{}}
    save_alliance(d)
    return d
def save_alliance(d):
    try:
        with ALLIANCE_FILE.open('w',encoding='utf-8') as f: json.dump(d,f,indent=4,ensure_ascii=False)
    except: pass
def get_al(ad,uid):
    name=ad["user_alliance"].get(uid)
    if name and name in ad["alliances"]: return name,ad["alliances"][name]
    return None,None
def is_leader(ad,uid):
    name=ad["user_alliance"].get(uid)
    return name in ad.get("alliances",{}) and ad["alliances"][name]["leader"]==uid

# ---------- file loaders ----------
def safe_json_load(file,default):
    if file.exists():
        try:
            with file.open('r',encoding='utf-8') as f: return json.load(f)
        except: pass
    return default

def get_un_leader_uid(un, countries):
    """رئیس سازمان ملل همیشه آمریکا است؛ اگر آمریکا مالک داشته باشد همان کاربر رئیس است."""
    leader=un.get("leader", "US")
    if leader=="US":
        return countries.get("US",{}).get("owner") or "US"
    return leader

def load_un():
    d=safe_json_load(UN_FILE,{"leader":"US","members":[],"requests":[],"resolutions":[],"created_at":datetime.now().isoformat()})
    d["leader"]="US"
    d.setdefault("members",[]); d.setdefault("requests",[]); d.setdefault("resolutions",[])
    save_un(d)
    return d
def save_un(d):
    try:
        with UN_FILE.open('w',encoding='utf-8') as f: json.dump(d,f,indent=4,ensure_ascii=False)
    except: pass

def load_countries():
    d=safe_json_load(COUNTRIES_FILE,None)
    if d is None:
        d={}
    # Migration: add any newly introduced countries without touching existing ownership.
    for c in COUNTRIES:
        d.setdefault(c["code"],{"flag":c["flag"],"name":c["name"],"emoji":c["emoji"],"owner":None,"defense":False,"damage_taken":0,"power_bonus":c["bonus"]})
    return d
def save_countries(cd):
    try:
        with COUNTRIES_FILE.open('w',encoding='utf-8') as f: json.dump(cd,f,indent=4,ensure_ascii=False)
    except: pass

def default_country_stats():
    return {"money":10000,"gold":100,"diamond":10,"food":1000,"oil":500,"gas":300,"iron":500,"population":100000,"workers":50000,"soldiers":1000,"cities":1,"factories":0,"roads":0,"schools":0,"hospitals":0,"powerplants":0,"bases":0,"universities":0,"ports":0,"airports":0}

def get_country_stats(data, uid):
    data.setdefault("country_stats", {})
    st=data["country_stats"].setdefault(str(uid), default_country_stats())
    for k,v in default_country_stats().items(): st.setdefault(k,v)
    return st

def save_activity(data, actor, action, detail=""):
    data.setdefault("admin_logs", []).append({"actor":str(actor),"action":str(action),"detail":str(detail),"time":datetime.now().isoformat()})
    data["admin_logs"]=data["admin_logs"][-300:]

def get_admin_roles(data):
    roles=data.setdefault("admin_roles", {})
    roles.setdefault(OWNER_ID,"owner")
    return roles

def admin_level(data, uid):
    return get_admin_roles(data).get(str(uid))

def can_admin(data, uid, minimum="admin"):
    order={"admin":1,"manager":2,"owner":3}
    role=admin_level(data,uid)
    return role in order and order[role]>=order[minimum]

def load_data():
    d=safe_json_load(DATA_FILE,None)
    if d is None:
        d={"users":{},"banned_users":[],"user_eq":{},"user_packs":{},"attack_logs":[],"bot_country":None,"bot_last_action":None,"country_stats":{},"trade_offers":[],"sanctions":{},"diplomacy":{},"wars":[],"events":[],"admin_logs":[],"admin_roles":{OWNER_ID:"owner"},"settings":{"season":1,"maintenance":False}}
    for k,v in {"users":{},"banned_users":[],"user_eq":{},"user_packs":{},"attack_logs":[],"bot_country":None,"bot_last_action":None,"daily_rewards":{},"coin_transfers":[],"country_stats":{},"trade_offers":[],"sanctions":{},"diplomacy":{},"wars":[],"events":[],"admin_logs":[],"admin_roles":{OWNER_ID:"owner"},"settings":{"season":1,"maintenance":False}}.items():
        if k not in d: d[k]=v
    for uid,u in d.get("users",{}).items():
        u.setdefault("warnings",0); u.setdefault("warning_log",[]); u.setdefault("daily_statements",{}); u.setdefault("faction",None); get_country_stats(d,uid)
    return d
def save_data(data):
    try:
        with DATA_FILE.open('w',encoding='utf-8') as f: json.dump(data,f,indent=4,ensure_ascii=False)
    except: pass

def load_bot_status():
    d=safe_json_load(BOT_STATUS_FILE,{"online":True})
    save_bot_status(d)
    return d
def save_bot_status(s):
    try:
        with BOT_STATUS_FILE.open('w',encoding='utf-8') as f: json.dump(s,f,indent=4,ensure_ascii=False)
    except: pass

# ---------- bot AI ----------
async def bot_ai(bot,data,countries):
    now=datetime.now()
    last=data.get("bot_last_action")
    if last:
        try:
            last_time=datetime.fromisoformat(last)
            if (now-last_time).total_seconds()<3600: return
        except: pass
    data["bot_last_action"]=now.isoformat()
    un=load_un()
    if not un.get("leader"): un["leader"]="US"; save_un(un)
    # Recover an existing AI country before creating a new one.
    existing_ai = next((c for c, info in countries.items() if info.get("owner")=="BOT_AI"), None)
    if existing_ai:
        data["bot_country"] = existing_ai
        countries[existing_ai].setdefault("defense", True)
    elif not data.get("bot_country") or data.get("bot_country") not in countries:
        free=[(c,i) for c,i in countries.items() if not i.get("owner")]
        if free:
            bot_code,info=random.choice(free)
            countries[bot_code]["owner"]="BOT_AI"
            countries[bot_code]["defense"]=True
            data["bot_country"]=bot_code
    # Always ensure the AI has a usable arsenal, without overwriting existing stock.
    if "user_eq" not in data: data["user_eq"]={}
    bot_eq=data["user_eq"].setdefault("BOT_AI",{})
    defaults={"اف۲۲":200,"موشک":500,"پدافند":600,"تانک":150,"پهپاد":200,"بمب اتم":20,"خیبرشکن":100,"ناو":50}
    for eq_name, amount in defaults.items():
        if eq_name in EQUIP:
            bot_eq.setdefault(eq_name, amount)
    save_data(data); save_countries(countries)

# ---------- BOT counterattack ----------
async def bot_counterattack(bot, data, countries, attacked_uid, reason=""):
    """Immediately retaliate against a player who attacked BOT_AI.
    This function is intentionally isolated from do_attack so it cannot recursively trigger itself.
    """
    try:
        if attacked_uid == "BOT_AI":
            return
        bot_country = data.get("bot_country")
        if not bot_country or bot_country not in countries:
            bot_country = next((c for c, info in countries.items() if info.get("owner")=="BOT_AI"), None)
        if not bot_country:
            return

        # Find the player's current country.
        target_code = next((c for c, info in countries.items() if info.get("owner")==attacked_uid), None)
        if not target_code or target_code == bot_country:
            return

        bot_eq = data.setdefault("user_eq", {}).setdefault("BOT_AI", {})
        available = [(name, int(amount)) for name, amount in bot_eq.items()
                     if name in EQUIP and int(amount) > 0]
        if not available:
            # Self-heal an empty AI arsenal.
            defaults = {"اف۲۲":200,"موشک":500,"پدافند":600,"تانک":150,
                        "پهپاد":200,"بمب اتم":20,"خیبرشکن":100,"ناو":50}
            for name, amount in defaults.items():
                if name in EQUIP:
                    bot_eq[name] = amount
            available = [(name, int(amount)) for name, amount in bot_eq.items()
                         if name in EQUIP and int(amount) > 0]
        if not available:
            return

        # Prefer a strong but controlled weapon.
        available.sort(key=lambda x: EQUIP[x[0]][3], reverse=True)
        eq_name, stock = available[0]
        use = max(1, min(stock, max(1, stock // 10)))
        eq_power = max(1, int(EQUIP[eq_name][3]))
        attack_power = int(use * eq_power * 0.75)

        target_info = countries[target_code]
        defense = defense_power(data, attacked_uid)
        win_ch = max(0.45, min(0.90, attack_power/(attack_power+defense))) if defense > 0 else 0.85
        # AI retaliates deterministically enough to feel responsive, but not every hit is overwhelming.
        won = random.random() < win_ch
        damage = int(attack_power * (0.55 if won else 0.12))
        if target_info.get("defense"):
            damage = max(0, damage - 150)
        if damage <= 0:
            damage = 1

        bot_eq[eq_name] = max(0, stock-use)
        target_info["damage_taken"] = target_info.get("damage_taken", 0) + damage

        destroyed = False
        if target_code != "US" and target_info["damage_taken"] >= 200000:
            await destroy(bot, data, countries, target_code, attacked_uid)
            destroyed = True

        save_countries(countries)
        save_data(data)

        flag = target_info.get("flag","🌍")
        name = target_info.get("name","کشور")
        result = (
            "🤖⚔️ ضدحمله ربات\n\n"
            f"🎯 هدف: {flag} {name}\n"
            f"💣 سلاح: {eq_name} × {use}\n"
            f"💥 خسارت: {fn(damage)}\n"
            f"📊 خسارت کل: {fn(target_info.get('damage_taken',0))}/۲۰۰,۰۰۰\n"
        )
        if destroyed:
            result += "☠️ کشور شما در ضدحمله نابود شد!"
        elif won:
            result += "🔴 ربات در ضدحمله موفق شد."
        else:
            result += "🟡 ضدحمله ربات انجام شد، اما قدرت آن محدود بود."

        try:
            await bot.send_message(attacked_uid, result, chat_keypad=get_main_menu())
        except Exception:
            pass

        # Notify others without allowing a notification failure to break the attack flow.
        try:
            await broadcast_war(
                bot, data, countries, "BOT_AI", target_code,
                eq_name, use, damage, won,
                "🤖 این حمله، پاسخ مستقیم ربات به حمله قبلی بود."
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"BOT counterattack error: {e}\n{traceback.format_exc()}")

# ---------- destroy country ----------
async def destroy(bot,data,countries,code,owner):
    info=countries[code]
    if owner and owner!="BOT_AI" and owner in data.get("users",{}):
        data["users"][owner]["has_country"]=False
        data["users"][owner]["coins"]=0
        data["users"][owner]["faction"]=None
        data["user_eq"][owner]={}
        data["user_packs"][owner]=[]
    countries[code]["owner"]=None; countries[code]["defense"]=False; countries[code]["damage_taken"]=0
    save_data(data); save_countries(countries)
    if owner and owner!="BOT_AI":
        try: await bot.send_message(owner,f"💥 کشور {info['flag']} {info['name']} نابود شد!\nتمامی دارایی‌ها پاک شد.",chat_keypad=get_main_menu())
        except: pass
    for u in data["users"]:
        try: await bot.send_message(u,f"☠️ کشور {info['flag']} {info['name']} نابود شد!")
        except: pass

# ---------- broadcast ----------
async def broadcast_war(bot,data,countries,attacker_uid,target,eq_name,amt,damage,won,extra=""):
    tinfo=countries.get(target,{})
    ac=None
    for c,i in countries.items():
        if i.get("owner")==attacker_uid: ac=i; break
    if not ac or not tinfo: return
    aname=data["users"].get(attacker_uid,{}).get("username","نامشخص")
    towner=tinfo.get("owner")
    tname="🤖 ربات" if towner=="BOT_AI" else data["users"].get(towner,{}).get("username","نامشخص")
    emoji="🏆" if won else "💀"
    txt=f"{sty('پیروز شد!','b')}" if won else f"{sty('شکست خورد!','b')}"
    col="🟢" if won else "🔴"
    msg=f"🌐 {mh('خبر فوری','📡')}\n\n{col} {ac['flag']} {ac['name']} به {tinfo['flag']} {tinfo['name']} حمله کرد!\n⚔️ مهاجم: {aname}\n🛡 مدافع: {tname}\n💣 سلاح: {eq_name} × {fn(amt)}\n💥 خسارت: {fn(damage)}\n{extra}\nنتیجه: {emoji} {txt}"
    for u in data["users"]:
        try: await bot.send_message(u,msg); await asyncio.sleep(0.05)
        except: pass

# ---------- attack ----------
def record_battle(data, uid, target, won, damage, eq, amount, opponent_owner):
    """Store a small bounded battle history; never raises into the battle flow."""
    try:
        logs=data.setdefault("attack_logs",[])
        logs.append({
            "uid":str(uid), "target":str(target), "won":bool(won),
            "damage":int(damage), "equipment":str(eq), "amount":int(amount),
            "opponent":str(opponent_owner), "time":datetime.now().isoformat()
        })
        if len(logs)>100:
            del logs[:-100]
    except Exception as e:
        logger.error(f"battle history error: {e}")

async def do_attack(bot,cid,data,countries,uid,target,eq,amt):
    if amt<=0: return await bot.send_message(cid,"❌ تعداد باید مثبت باشد.")
    last_attack = data["users"][uid].get("last_attack")
    if last_attack:
        try:
            last_time = datetime.fromisoformat(last_attack)
            if (datetime.now() - last_time).total_seconds() < 300:
                remaining = int(300 - (datetime.now() - last_time).total_seconds())
                return await bot.send_message(cid, f"⏳ {remaining} ثانیه تا حمله بعدی صبر کنید.")
        except: pass

    attacker_code = None
    for c,i in countries.items():
        if i.get("owner")==uid: attacker_code=c; break
    if not attacker_code: return await bot.send_message(cid,"❌ کشور ندارید!",chat_keypad=get_main_menu())
    tinfo=countries.get(target)
    if not tinfo or not tinfo.get("owner"): return await bot.send_message(cid,"❌ هدف نامعتبر!")
    if attacker_code==target: return await bot.send_message(cid,"❌ به خودتان نمی‌توانید حمله کنید!")
    arms_block=any(x.get("active") and x.get("by")==towner and x.get("type")=="تسلیحاتی" for x in data.get("sanctions",{}).get(uid,[]))
    if arms_block: return await bot.send_message(cid,"🚫 به دلیل تحریم تسلیحاتی، حمله مجاز نیست.")

    if eq not in EQUIP: return await bot.send_message(cid,"❌ تجهیزات نامعتبر!")
    total = totaleq(data,uid).get(eq,0)
    if total<amt: return await bot.send_message(cid,f"❌ موجودی کافی نیست! (داری: {fn(total)})")

    data["users"][uid]["last_attack"] = datetime.now().isoformat()
    save_data(data)

    user = data["users"][uid]
    fac = user.get("faction")
    atk_bonus = FACTIONS[fac]["atk"] if fac and fac in FACTIONS else 1.0
    towner = tinfo["owner"]
    tdef = defense_power(data,towner)
    eq_power = EQUIP[eq][3]
    attack_power = int(amt*eq_power*atk_bonus)
    win_ch = max(0.2, min(0.85, attack_power/(attack_power+tdef))) if tdef>0 else 0.9
    won = random.random()<win_ch

    used,ok = consume(data,uid,eq,amt)
    if not ok: return await bot.send_message(cid,"❌ مصرف تجهیزات با خطا مواجه شد.")
    remaining = totaleq(data,uid).get(eq,0)

    attacker_flag = countries[attacker_code]["flag"]
    attacker_name = countries[attacker_code]["name"]
    target_flag = tinfo["flag"]
    target_name = tinfo["name"]

    if won:
        dmg = int(attack_power*0.7)
        if countries[target].get("defense"): dmg = max(0,dmg-300)
        countries[target]["damage_taken"] = countries[target].get("damage_taken",0)+dmg
        destroyed = False
        if target!="US" and countries[target]["damage_taken"]>=200000:
            if towner in data.get("users",{}):
                await destroy(bot,data,countries,target,towner)
                destroyed=True
        loot_text = ""
        if not destroyed and towner!="BOT_AI" and random.random()<0.4:
            loot_item = random.choice(list(EQUIP.keys()))
            loot_amt = random.randint(1,5)
            addeq(data,uid,loot_item,loot_amt)
            loot_text = f"\n🎁 غنیمت: {loot_item} × {loot_amt}"
        if destroyed: loot_text += "\n☠️ کشور هدف نابود شد!"
        addc(data,uid,100)
        record_battle(data, uid, target, True, dmg, eq, used, towner)
        save_countries(countries); save_data(data)
        user_coins = get_coins(data,uid)
        result = f"{mh('گزارش نبرد','⚔️')}\n\n🏆 پیروز شدید!\n\n🗡 {attacker_flag} {attacker_name}\n🎯 {target_flag} {target_name}\n💣 {eq} × {fn(used)}\n📦 موجودی: {fn(remaining)}\n⚔️ قدرت حمله: {fn(attack_power)}\n🛡 پدافند دشمن: {fn(tdef)}\n📊 شانس برد: {int(win_ch*100)}٪\n💥 خسارت: {fn(dmg)} (کل: {fn(countries[target].get('damage_taken',0))}/۲۰۰,۰۰۰)\n{loot_text}\n🪙 +۱۰۰ کوین\n🪙 موجودی: {fn(user_coins)}"
        await bot.send_message(cid, result, chat_keypad=get_main_menu())
        await broadcast_war(bot,data,countries,uid,target,eq,used,dmg,True,loot_text)
        if towner=="BOT_AI":
            await bot_counterattack(bot,data,countries,uid,"player_won")
    else:
        dmg = int(attack_power*0.15)
        if countries[target].get("defense"): dmg = max(0,dmg-200)
        countries[target]["damage_taken"] = countries[target].get("damage_taken",0)+dmg
        destroyed = False
        if target!="US" and countries[target]["damage_taken"]>=200000:
            if towner in data.get("users",{}):
                await destroy(bot,data,countries,target,towner)
                destroyed=True
        casualty = ""
        if destroyed: casualty = "\n☠️ کشور هدف نابود شد!"
        addc(data,uid,-20)
        record_battle(data, uid, target, False, dmg, eq, used, towner)
        save_countries(countries); save_data(data)
        user_coins = get_coins(data,uid)
        result = f"{mh('گزارش نبرد','⚔️')}\n\n💀 شکست خوردید!\n\n🗡 {attacker_flag} {attacker_name}\n🎯 {target_flag} {target_name}\n💣 {eq} × {fn(used)}\n📦 موجودی: {fn(remaining)}\n⚔️ قدرت حمله: {fn(attack_power)}\n🛡 پدافند دشمن: {fn(tdef)}\n📊 شانس برد: {int(win_ch*100)}٪\n💥 خسارت: {fn(dmg)} (کل: {fn(countries[target].get('damage_taken',0))}/۲۰۰,۰۰۰)\n{casualty}\n🪙 -۲۰ کوین\n🪙 موجودی: {fn(user_coins)}"
        await bot.send_message(cid, result, chat_keypad=get_main_menu())
        await broadcast_war(bot,data,countries,uid,target,eq,used,dmg,False,casualty)
        if towner=="BOT_AI":
            await bot_counterattack(bot,data,countries,uid,"player_lost")

async def send_battle_report(bot, cid, data, countries, uid):
    logs=[x for x in data.get("attack_logs",[]) if str(x.get("uid"))==str(uid)]
    logs=logs[-10:][::-1]
    if not logs:
        return await bot.send_message(cid,"📜 هنوز هیچ نبردی در تاریخچه شما ثبت نشده است.",chat_keypad=get_main_menu())
    wins=sum(1 for x in logs if x.get("won"))
    total_damage=sum(int(x.get("damage",0)) for x in logs)
    lines=["📜 گزارش ۱۰ نبرد اخیر","","🏆 پیروزی: %d"%wins,"⚔️ نبردها: %d"%len(logs),f"💥 مجموع خسارت: {fn(total_damage)}",""]
    for x in logs:
        target=x.get("target","?")
        name=countries.get(target,{}).get("name",target)
        icon="🏆" if x.get("won") else "💀"
        lines.append(f"{icon} {name} | {x.get('equipment','-')} × {x.get('amount',0)} | 💥{fn(int(x.get('damage',0)))}")
    await bot.send_message(cid,"\n".join(lines),chat_keypad=get_main_menu())

# ---------- daily reward / leave ----------
async def daily(bot,cid,data,uid):
    today=date.today().isoformat()
    if "daily_rewards" not in data: data["daily_rewards"]={}
    if data["daily_rewards"].get(uid)==today: return await bot.send_message(cid,"❌ امروز دریافت کرده‌اید!")
    data["daily_rewards"][uid]=today
    addc(data,uid,500)
    await bot.send_message(cid,f"🎁 ۵۰۰ کوین دریافت کردید!\n🪙 موجودی: {fn(get_coins(data,uid))}",chat_keypad=get_main_menu())

async def leave_country(bot,cid,data,countries,uid):
    my=None
    for c,i in countries.items():
        if i.get("owner")==uid: my=c; break
    if not my: return await bot.send_message(cid,"❌ کشوری ندارید!")
    info=countries[my]
    data["users"][uid]["has_country"]=False
    data["users"][uid]["coins"]=0
    data["users"][uid]["faction"]=None
    data["user_eq"][uid]={}
    data["user_packs"][uid]=[]
    countries[my]["owner"]=None; countries[my]["defense"]=False; countries[my]["damage_taken"]=0
    save_data(data); save_countries(countries)
    await bot.send_message(cid,f"🚪 کشور {info['flag']} {info['name']} را ترک کردید!\n💀 تمام دارایی‌ها پاک شد.",chat_keypad=get_main_menu())


async def admin_reset_user(bot, data, countries, uid):
    if uid not in data.get("users",{}): return False
    for code,info in countries.items():
        if info.get("owner")==uid:
            info["owner"]=None; info["defense"]=False; info["damage_taken"]=0
    u=data["users"][uid]
    u.update({"coins":0,"has_country":False,"faction":None,"warnings":0,"warning_log":[]})
    data.setdefault("user_eq",{})[uid]={}
    data.setdefault("user_packs",{})[uid]=[]
    save_data(data); save_countries(countries)
    try: await bot.send_message(uid,"👑 ادمین حساب شما را ریست کرد.")
    except Exception: pass
    return True

# ---------- admin functions ----------
async def admin_change_owner(bot,cid,data,countries,country_code,new_owner_uid):
    if country_code not in countries:
        await bot.send_message(cid,"❌ کشور نامعتبر!")
        return
    info=countries[country_code]
    old_owner=info.get("owner")
    if old_owner and old_owner!="BOT_AI" and old_owner in data.get("users",{}):
        data["users"][old_owner]["has_country"]=False
    if new_owner_uid not in data.get("users",{}):
        await bot.send_message(cid,"❌ کاربر مقصد وجود ندارد!")
        return
    for c,i in countries.items():
        if i.get("owner")==new_owner_uid and c!=country_code:
            await bot.send_message(cid,"❌ کاربر مقصد قبلاً یک کشور دارد!")
            return
    info["owner"]=new_owner_uid
    if "has_country" not in data["users"][new_owner_uid]: data["users"][new_owner_uid]["has_country"]=True
    data["users"][new_owner_uid]["has_country"]=True
    save_data(data); save_countries(countries)
    new_name=data["users"][new_owner_uid].get("username",new_owner_uid[:10])
    await bot.send_message(cid,f"✅ مالک {info['flag']} {info['name']} به {new_name} (`{new_owner_uid}`) تغییر یافت.")

async def admin_reset_country(bot,cid,data,countries,country_code):
    if country_code not in countries:
        await bot.send_message(cid,"❌ کشور نامعتبر!")
        return
    info=countries[country_code]
    old_owner=info.get("owner")
    if old_owner and old_owner!="BOT_AI" and old_owner in data.get("users",{}):
        data["users"][old_owner]["has_country"]=False
        data["users"][old_owner]["coins"]=0
        data["users"][old_owner]["faction"]=None
        data["user_eq"][old_owner]={}
        data["user_packs"][old_owner]=[]
    info["owner"]=None; info["defense"]=False; info["damage_taken"]=0
    save_data(data); save_countries(countries)
    await bot.send_message(cid,f"✅ کشور {info['flag']} {info['name']} کاملاً ریست شد.")

GAME_INFO_TEXT = """جنگ جهانی

🌍 ربات جنگ جهانی | @GJFaBot

🆓 امکانات رایگان:
🌍 ساخت کشور • انتخاب نام • پرچم • تصویر • نشان • شعار • پایتخت
👑 حاکم • رئیس‌جمهور • وزرا • آموزش‌وپرورش • خارجه • دفاع • اقتصاد • صنعت • کشاورزی • بهداشت • اطلاعات • قوه قضائیه
🏙️ ساخت شهر • استان • جاده • مدرسه • بیمارستان • کارخانه • نیروگاه • پایگاه
💰 پول • دلار • خزانه • مالیات • بودجه • تجارت
🌾 گندم • غلات • غذا • نفت • گاز • آهن • طلا • جمعیت • نیروی کار • سرباز
⚔️ سرباز • تانک • هواپیما • ناو • تجهیزات نظامی • حمله • دفاع • جنگ
🤝 اتحاد • صلح • تجارت • سفارت • اعلام جنگ
🎯 مأموریت روزانه • جایزه • رتبه‌بندی • آمار کشور

💎 امکانات اشتراکی:
👑 ساخت سلسله • خاندان سلطنتی • ولیعهد • جانشینی • ازدواج سیاسی • کاخ سلطنتی
🎨 نام‌گذاری اختصاصی شهرها • استان‌ها • سلاح‌ها • تجهیزات • کارخانه‌ها • پایگاه‌ها • مناطق • واحد پول
🏗️ شهرها و سازه‌های ویژه • کارخانه و دانشگاه پیشرفته • فرودگاه و بندر پیشرفته
⚔️ موشک • پدافند پیشرفته • تجهیزات ویژه • فرماندهان ویژه • پایگاه‌های پیشرفته
💰 بانک • سرمایه‌گذاری • بازار و تجارت پیشرفته • اقتصاد پیشرفته
🕵️ جاسوسی • ضدجاسوسی • عملیات مخفی • دیپلماسی پیشرفته

🏪 فروشگاه:
🌾 غلات • ⚔️ سلاح • 💪 قدرت • ⛏️ منابع • 💰 ثروت • 💵 دلار • 💎 الماس • 💠 جم • 🪙 سکه

👑 پنل مدیریت مالک:
📊 داشبورد و آمار • 👥 مدیریت کاربران • 🌍 مدیریت کشورها • 👑 مدیریت حکومت و سلسله‌ها
⚔️ مدیریت جنگ و ارتش • 🤝 مدیریت اتحاد و دیپلماسی • 🚫 مدیریت تحریم‌ها
🌾 مدیریت منابع • 💰 مدیریت اقتصاد و ارزها • 🏗️ مدیریت ساخت‌وساز
🏪 مدیریت فروشگاه • 💎 مدیریت اشتراک‌ها • 🎯 مدیریت مأموریت و رویداد
🎁 مدیریت جوایز • 🏆 مدیریت رتبه‌بندی • 📢 پیام همگانی • 📰 اخبار
👨‍💼 مدیریت مدیران و سطح دسترسی • 🛡️ ضدتقلب • 📜 لاگ فعالیت‌ها
⚙️ تنظیمات بازی • 🔧 فعال/غیرفعال کردن قابلیت‌ها • 🔄 مدیریت فصل‌ها • 💾 بکاپ و بازیابی

💸 مدیریت مالی:
📤 انتقال پول به یک کشور • چند کشور • همه کشورها
💵 انتخاب نوع ارز • تعیین مبلغ • تاریخچه انتقال • برگشت تراکنش

🚫 سیستم تحریم:
💰 تحریم اقتصادی • 📦 تحریم تجاری • 🏦 تحریم بانکی • ⚔️ تحریم تسلیحاتی
🚢 محدودیت واردات و صادرات • ⛏️ محدودیت منابع • ⏳ تعیین مدت • 🔓 لغو تحریم

💳 خرید پک‌ها و اشتراک‌ها:
📩 شناسه خرید: @Saaid987

🔥 از یک کشور کوچک شروع کن و به قدرت اول جهان تبدیل شو!"""

# ---------- keyboards ----------
def get_main_menu():
    b=ChatKeypadBuilder()
    # چیدمان جدید: بخش‌های اصلی در ردیف‌های دوتایی، با ظاهر متفاوت و خواناتر
    b.row(b.button(id="my_info",text="【👤 پروفایل】"),b.button(id="buy_country",text="【🌍 کشور من】"))
    b.row(b.button(id="attack",text="【⚔️ نبرد】"),b.button(id="equipment_shop",text="【🛒 فروشگاه】"))
    b.row(b.button(id="arsenal",text="【🧰 زرادخانه】"),b.button(id="buy_single",text="【🎯 تجهیزات】"))
    b.row(b.button(id="alliance_menu",text="【🤝 اتحادها】"),b.button(id="faction_menu",text="【⚔️ جناح‌ها】"))
    b.row(b.button(id="un_menu",text="【🏛 سازمان ملل】"),b.button(id="world_status",text="【🌎 وضعیت جهان】"))
    b.row(b.button(id="top_owners",text="【🏆 رتبه‌بندی】"),b.button(id="battle_report",text="【📜 گزارش نبرد】"))
    b.row(b.button(id="daily_reward",text="【🎁 پاداش روزانه】"),b.button(id="send_message",text="【📨 بیانیه】"))
    b.row(b.button(id="economy_menu",text="【💰 اقتصاد】"),b.button(id="army_menu",text="【🪖 ارتش】"))
    b.row(b.button(id="build_menu",text="【🏗 توسعه کشور】"),b.button(id="diplomacy_menu",text="【🤝 دیپلماسی】"))
    b.row(b.button(id="trade_menu",text="【🚫 تحریم و تجارت】"),b.button(id="game_info",text="【📘 امکانات بازی】"))
    b.row(b.button(id="rules",text="【📖 قوانین】"),b.button(id="my_warnings",text="【⚠️ اخطارهای من】"))
    b.row(b.button(id="leave_country",text="【🚪 ترک کشور】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_alliance_menu(is_member,is_leader):
    b=ChatKeypadBuilder()
    b.row(b.button(id="alliance_list",text="【📋 فهرست اتحادها】"))
    if not is_member:
        b.row(b.button(id="alliance_create",text="【📝 ساخت اتحاد】"))
    else:
        b.row(b.button(id="alliance_info",text="【🔍 اتحاد من】"),b.button(id="alliance_chat",text="【💬 گفت‌وگو】"))
        b.row(b.button(id="alliance_leave",text="【🚪 خروج】"),b.button(id="alliance_betray",text="【💀 خیانت】"))
        if is_leader:
            b.row(b.button(id="alliance_manage",text="【👥 مدیریت اعضا】"),b.button(id="alliance_disband",text="【❌ انحلال】"))
    b.row(b.button(id="back_to_menu",text="【↩️ بازگشت】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_un_menu():
    b=ChatKeypadBuilder()
    b.row(b.button(id="un_info",text="【🏛 اطلاعات】"),b.button(id="un_members",text="【👥 اعضا】"))
    b.row(b.button(id="un_join",text="【📝 عضویت】"),b.button(id="un_resolutions",text="【📜 قطعنامه‌ها】"))
    b.row(b.button(id="un_stats",text="【📊 آمار】"),b.button(id="un_power",text="【⚔️ قدرت سازمان】"))
    b.row(b.button(id="un_request_list",text="【📋 درخواست‌ها】"),b.button(id="back_to_menu",text="【↩️ بازگشت】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_faction_menu():
    b=ChatKeypadBuilder()
    b.row(b.button(id="faction_sepah",text="【🛡️ سپاه】"),b.button(id="faction_darkweb",text="【💀 دارک‌وب】"))
    b.row(b.button(id="faction_hezbollah",text="【⚔️ حزب‌الله】"),b.button(id="faction_info",text="【📊 اطلاعات جناح‌ها】"))
    b.row(b.button(id="back_to_menu",text="【↩️ بازگشت】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_countries_kb(countries,page=0):
    b=ChatKeypadBuilder()
    lst=list(countries.items())
    start=page*12; end=start+12; cur=lst[start:end]
    row=[]
    for code,info in cur:
        st="🟢" if info.get("owner") else "⚪"
        bt="🤖" if info.get("owner")=="BOT_AI" else ""
        row.append(b.button(id=f"country_{code}",text=f"{info['flag']} {st}{bt}"))
        if len(row)==3: b.row(*row); row=[]
    if row: b.row(*row)
    nav=[]
    if page>0: nav.append(b.button(id=f"countries_page_{page-1}",text="◀️ قبل"))
    nav.append(b.button(id="back_to_menu",text="🏠 خانه"))
    if end<len(lst): nav.append(b.button(id=f"countries_page_{page+1}",text="بعد ▶️"))
    if nav: b.row(*nav)
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_attack_countries_kb(countries,page=0):
    b=ChatKeypadBuilder()
    active=[(c,i) for c,i in countries.items() if i.get("owner")]
    start=page*9; end=start+9; cur=active[start:end]
    row=[]
    for code,info in cur:
        bt=" 🤖" if info.get("owner")=="BOT_AI" else ""
        row.append(b.button(id=f"attack_{code}",text=f"{info['flag']} {info['name']}{bt}"))
        if len(row)==3: b.row(*row); row=[]
    if row: b.row(*row)
    nav=[]
    if page>0: nav.append(b.button(id=f"attack_page_{page-1}",text="◀️"))
    nav.append(b.button(id="back_to_menu",text="🏠"))
    if end<len(active): nav.append(b.button(id=f"attack_page_{page+1}",text="▶️"))
    if nav: b.row(*nav)
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_admin_country_kb(countries,action_prefix,page=0):
    b=ChatKeypadBuilder()
    lst=list(countries.items())
    per_page=15
    start=max(0,page)*per_page; cur=lst[start:start+per_page]
    row=[]
    for code,info in cur:
        row.append(b.button(id=f"{action_prefix}{code}",text=f"{info['flag']} {info['name']}"))
        if len(row)==3: b.row(*row); row=[]
    if row: b.row(*row)
    nav=[]
    if page>0: nav.append(b.button(id=f"ad_country_page_{action_prefix}p{page-1}",text="◀️ قبلی"))
    if start+per_page<len(lst): nav.append(b.button(id=f"ad_country_page_{action_prefix}p{page+1}",text="بعدی ▶️"))
    if nav: b.row(*nav)
    b.row(b.button(id="cancel",text="❌ لغو"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_attack_eq_kb(ueq,upacks,target):
    b=ChatKeypadBuilder()
    items={}
    for eq,cnt in ueq.items():
        if cnt>0: items[eq]=items.get(eq,0)+cnt
    row=[]
    for eq,cnt in list(items.items())[:24]:
        short=eq[:10]+".." if len(eq)>10 else eq
        row.append(b.button(id=f"eq_{target}_{eq}",text=f"🔸 {short} ({cnt})"))
        if len(row)==2: b.row(*row); row=[]
    if row: b.row(*row)
    b.row(b.button(id="back_to_menu",text="🏠 بازگشت"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_attack_amt_kb(target,eq,max_cnt):
    b=ChatKeypadBuilder()
    amounts=[1,5,10,25,50,100,200,500]
    row=[]
    for amt in amounts:
        if amt<=max_cnt: row.append(b.button(id=f"amt_{target}_{eq}_{amt}",text=f"🎯 {amt}"))
        if len(row)==4: b.row(*row); row=[]
    if row: b.row(*row)
    b.row(b.button(id=f"custom_{target}_{eq}",text="✏️ تعداد دلخواه"),b.button(id="back_to_menu",text="🏠"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_single_eq_kb():
    b=ChatKeypadBuilder()
    cats={}
    for eq,info in EQUIP.items():
        cats.setdefault(info[2],[]).append((eq,info))
    for cat,items in cats.items():
        row=[]
        for eq,info in items[:4]:
            row.append(b.button(id=f"buyeq_{eq}",text=f"{info[1]} {eq} | 🪙{info[0]}"))
            if len(row)==3: b.row(*row); row=[]
        if row: b.row(*row)
    b.row(b.button(id="back_to_menu",text="🏠 بازگشت"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_shop_menu():
    b=ChatKeypadBuilder()
    for pn,pi in PACKS.items():
        b.row(b.button(id=f"shop_{pn}",text=f"【{pi[1]} {pn}】  🪙{fn(pi[0])}"))
    b.row(b.button(id="back_to_menu",text="【↩️ بازگشت به فرماندهی】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)


def get_economy_menu():
    b=ChatKeypadBuilder(); b.row(b.button(id="eco_collect",text="【💰 تولید منابع】"),b.button(id="eco_transfer",text="【📤 انتقال پول】")); b.row(b.button(id="eco_info",text="【📊 خزانه و منابع】"),b.button(id="back_to_menu",text="【↩️ بازگشت】")); return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_army_menu():
    b=ChatKeypadBuilder(); b.row(b.button(id="army_train",text="【🪖 آموزش سرباز】"),b.button(id="arsenal",text="【🧰 زرادخانه】")); b.row(b.button(id="army_defense",text="【🛡 تقویت دفاع】"),b.button(id="back_to_menu",text="【↩️ بازگشت】")); return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_build_menu():
    b=ChatKeypadBuilder();
    for ident,text in [("build_city","🏙 شهر"),("build_factory","🏭 کارخانه"),("build_road","🛣 جاده"),("build_school","🏫 مدرسه"),("build_hospital","🏥 بیمارستان"),("build_power","⚡ نیروگاه"),("build_base","🛡 پایگاه"),("build_port","⚓ بندر"),("build_airport","🛬 فرودگاه"),("build_university","🎓 دانشگاه")]: b.row(b.button(id=ident,text=f"【{text}】"))
    b.row(b.button(id="back_to_menu",text="【↩️ بازگشت】")); return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_diplomacy_menu():
    b=ChatKeypadBuilder(); b.row(b.button(id="dip_list",text="【📜 پیمان‌ها】"),b.button(id="dip_peace",text="【🕊 پیشنهاد صلح】")); b.row(b.button(id="alliance_menu",text="【🤝 اتحادها】"),b.button(id="dip_pact",text="【🛡 پیمان دفاعی】")); b.row(b.button(id="back_to_menu",text="【↩️ بازگشت】")); return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_trade_offers_menu(data, uid):
    b=ChatKeypadBuilder()
    offers=[(i,x) for i,x in enumerate(data.get("trade_offers",[])) if x.get("to")==str(uid) and x.get("status")=="sent"][-10:]
    for i,x in offers:
        b.row(b.button(id=f"trade_accept_{i}",text=f"【✅ قبول {x.get('from','?')} | 💵{fn(x.get('money',0))}】"))
    b.row(b.button(id="trade_menu",text="【↩️ تجارت】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_trade_menu():
    b=ChatKeypadBuilder(); b.row(b.button(id="trade_list",text="【📦 تجارت】"),b.button(id="trade_offer",text="【📤 پیشنهاد تجارت】")); b.row(b.button(id="sanction_menu",text="【🚫 تحریم‌ها】"),b.button(id="back_to_menu",text="【↩️ بازگشت】")); return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_admin_sections():
    b=ChatKeypadBuilder();
    b.row(b.button(id="ad_users",text="【👥 کاربران】"),b.button(id="ad_countries",text="【🌍 کشورها】"))
    b.row(b.button(id="ad_economy",text="【💰 اقتصاد】"),b.button(id="ad_army",text="【🪖 ارتش】"))
    b.row(b.button(id="ad_country_create",text="【➕ ساخت کشور】"),b.button(id="ad_country_edit",text="【✏️ ویرایش کشور】"))
    b.row(b.button(id="ad_country_delete",text="【🗑 حذف کشور】"),b.button(id="ad_reward",text="【🎁 جایزه سریع】"))
    b.row(b.button(id="ad_wars",text="【⚔️ جنگ‌ها】"),b.button(id="ad_events",text="【🎁 جوایز/رویداد】"))
    b.row(b.button(id="ad_stats",text="【📊 آمار】"),b.button(id="ad_settings",text="【⚙️ تنظیمات】"))
    b.row(b.button(id="ad_admins",text="【👑 مدیریت ادمین‌ها】"),b.button(id="ad_logs",text="【📝 لاگ فعالیت】"))
    b.row(b.button(id="ad_broadcast",text="【📢 پیام همگانی】"),b.button(id="ad_backup",text="【💾 پشتیبان】"))
    b.row(b.button(id="ad_to_main_menu",text="【🏠 منوی اصلی】"),b.button(id="ad_close",text="【🔒 خروج】"))
    return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_admin_admins_menu():
    b=ChatKeypadBuilder(); b.row(b.button(id="ad_admin_add",text="【➕ افزودن ادمین】"),b.button(id="ad_admin_remove",text="【❌ حذف ادمین】")); b.row(b.button(id="ad_admin_level",text="【🔐 سطح دسترسی】"),b.button(id="ad_admin_list",text="【📋 فهرست ادمین‌ها】")); b.row(b.button(id="ad_back_to_admin",text="【↩️ بازگشت】")); return b.build(resize_keyboard=True,on_time_keyboard=True)

def get_admin_panel(bs):
    return get_admin_sections()

def get_admin_back():
    b=ChatKeypadBuilder(); b.row(b.button(id="ad_back_to_admin",text="🔙 پنل ادمین"),b.button(id="ad_to_main_menu",text="🏠 منوی اصلی")); return b.build(resize_keyboard=True,on_time_keyboard=True)
def get_admin_back_cancel():
    b=ChatKeypadBuilder(); b.row(b.button(id="ad_back_to_admin",text="🔙 پنل ادمین"),b.button(id="cancel",text="❌ لغو")); return b.build(resize_keyboard=True,on_time_keyboard=True)
def get_back():
    b=ChatKeypadBuilder(); b.row(b.button(id="back_to_menu",text="🏠 بازگشت")); return b.build(resize_keyboard=True,on_time_keyboard=True)
def get_cancel():
    b=ChatKeypadBuilder(); b.row(b.button(id="cancel",text="❌ لغو")); return b.build(resize_keyboard=True,on_time_keyboard=True)

async def safe_send(bot, cid, text, **kwargs):
    """ارسال امن روبیکا: محدودیت ۵۰۰۰ کاراکتر/۱۲۸ خط را رعایت می‌کند."""
    text="" if text is None else str(text)
    if not text: text=" "
    max_chars=4500
    max_lines=100
    lines=text.splitlines() or [text]
    chunks=[]; cur=[]; size=0
    for line in lines:
        # خطوط خیلی بلند هم جدا می‌شوند
        while len(line)>max_chars:
            part=line[:max_chars]; line=line[max_chars:]
            if cur:
                chunks.append("\n".join(cur)); cur=[]; size=0
            chunks.append(part)
        add=len(line)+(1 if cur else 0)
        if cur and (len(cur)>=max_lines or size+add>max_chars):
            chunks.append("\n".join(cur)); cur=[line]; size=len(line)
        else:
            cur.append(line); size+=add
    if cur: chunks.append("\n".join(cur))
    for idx,chunk in enumerate(chunks):
        kw=kwargs if idx==len(chunks)-1 else {}
        try:
            await bot.send_message(cid,chunk,**kw)
        except Exception:
            # اگر کی‌پد باعث INVALID_INPUT شد، یک‌بار بدون کی‌پد ارسال می‌کنیم.
            if kw:
                await bot.send_message(cid,chunk)
            else:
                raise

# ---------- bot instance ----------
bot = Robot(token=BOT_TOKEN)
user_states={}
admin_session={}

@bot.on_message()
async def handler(bot_instance:Robot,msg:Message):
    global user_states,admin_session
    try:
        cid=msg.chat_id
        text=msg.text.strip() if msg.text else ""
        cb=None
        if hasattr(msg,'aux_data') and msg.aux_data:
            cb=getattr(msg.aux_data,'button_id',None) or ''
    except Exception as e:
        logger.error(f"Error in handler initial block: {e}")
        return

    try:
        bs=load_bot_status()
        uid=str(cid)
        data=load_data()
        is_admin=can_admin(data, uid, "admin")
        if (not bs.get("online",True) or data.get("settings",{}).get("maintenance",False)) and not is_admin:
            if text=="/start" or cb: await safe_send(bot_instance,cid,"😴 ربات در حال استراحت است.")
            return
        countries=load_countries()
        adata=load_alliance()
        if uid in data.get("banned_users",[]):
            await msg.reply("🚫 مسدود هستید."); return
        username=guser(msg)
        if uid not in data.get("users",{}):
            data["users"][uid]={"join_date":datetime.now().isoformat(),"coins":1000,"username":username or f"فرمانده{uid[:6]}","has_country":False,"daily_statements":{},"faction":None,"warnings":0,"warning_log":[],"last_activity":datetime.now().isoformat()}
            save_data(data)
        data["users"][uid].setdefault("warnings",0); data["users"][uid].setdefault("warning_log",[])
        data["users"][uid].setdefault("last_activity",datetime.now().isoformat())
        if not is_admin:
            data["users"][uid]["last_activity"]=datetime.now().isoformat()
            save_data(data)
        data["users"][uid].setdefault("last_activity",datetime.now().isoformat())
        if not is_admin:
            data["users"][uid]["last_activity"]=datetime.now().isoformat()
            save_data(data)
        if username and data["users"][uid].get("username")!=username:
            data["users"][uid]["username"]=username; save_data(data)
        # اخطار خودکار غیرفعال است؛ اخطار فقط از پنل ادمین ثبت می‌شود.
        await bot_ai(bot_instance,data,countries)

        # admin states
        if user_states.get(cid,{}).get("wait_change_owner_uid"):
            new_owner_uid=text.strip()
            country_code=user_states[cid]["country_code"]
            await admin_change_owner(bot_instance,cid,data,countries,country_code,new_owner_uid)
            user_states[cid]={}; return
        if user_states.get(cid,{}).get("confirm_reset"):
            if text.strip().lower()=="بله":
                country_code=user_states[cid]["country_code"]
                await admin_reset_country(bot_instance,cid,data,countries,country_code)
            else:
                await safe_send(bot_instance,cid,"❌ عملیات لغو شد.")
            user_states[cid]={}; return

        # alliance creation / chat states
        if user_states.get(cid,{}).get("creating_alliance"):
            new_name=text.strip()
            if not new_name: await safe_send(bot_instance,cid,"❌ نام نامعتبر!"); user_states[cid]={}; return
            if new_name in adata["alliances"]: await safe_send(bot_instance,cid,"❌ این نام قبلاً استفاده شده!"); user_states[cid]={}; return
            success,msg=remc(data,uid,5000)
            if not success: await safe_send(bot_instance,cid,f"❌ {msg}"); user_states[cid]={}; return
            adata["alliances"][new_name]={"leader":uid,"members":[uid],"created":datetime.now().isoformat()}
            adata["user_alliance"][uid]=new_name
            save_alliance(adata); save_data(data)
            await safe_send(bot_instance,cid,f"✅ اتحاد {new_name} ایجاد شد!",chat_keypad=get_main_menu())
            user_states[cid]={}; return
        if user_states.get(cid,{}).get("alliance_chat"):
            name,_=get_al(adata,uid)
            if not name: await safe_send(bot_instance,cid,"❌ خطا!"); user_states[cid]={}; return
            sender=data["users"][uid].get("username",uid[:10])
            msg_text=f"💬 [{name}] {sender}:\n{text}"
            for m in adata["alliances"][name]["members"]:
                try: await safe_send(bot_instance,m,msg_text)
                except: pass
            await safe_send(bot_instance,cid,"✅ پیام ارسال شد.")
            user_states[cid]={}; return

        in_admin=admin_session.get(cid,False)

        if text=="/start":
            user_states[cid]={}
            await safe_send(bot_instance,cid,f"{mh('🌍 جنگ جهانی')}\n\n🆔 {gid(msg,uid)}\n🔑 شناسه: {sty(uid,'m')}\n🪙 کوین: {fn(get_coins(data,uid))}",chat_keypad=get_main_menu())
            return
        if text=="/admin":
            user_states[cid]={"wait_pass":True}
            await safe_send(bot_instance,cid,"╭─ 🔐 ورود به مرکز فرماندهی ─╮\n│ رمز مدیریت را وارد کنید.\n╰──────────────────────╯"); return
        if user_states.get(cid,{}).get("wait_pass"):
            if text==ADMIN_PASSWORD:
                admin_session[cid]=True; user_states[cid]={}
                await safe_send(bot_instance,cid,"╭─ 🟢 دسترسی تأیید شد ─╮\n│ مرکز فرماندهی آماده است.\n╰────────────────────╯",chat_keypad=get_admin_panel(bs))
            else: user_states[cid]={}; await safe_send(bot_instance,cid,"╭─ 🔴 دسترسی رد شد ─╮\n│ رمز واردشده صحیح نیست.\n╰──────────────────╯")
            return

        if cb=="back_to_menu":
            user_states[cid]={}
            await safe_send(bot_instance,cid,"🏠 منوی اصلی:",chat_keypad=get_main_menu()); return
        if cb=="game_info":
            await safe_send(bot_instance,cid,GAME_INFO_TEXT,chat_keypad=get_main_menu()); return
        if cb=="cancel":
            user_states[cid]={}
            await safe_send(bot_instance,cid,"❌ لغو شد.",chat_keypad=get_admin_panel(bs) if in_admin else get_main_menu()); return

        if in_admin:
            if cb=="ad_to_main_menu": admin_session[cid]=False; await safe_send(bot_instance,cid,"🏠 منوی اصلی:",chat_keypad=get_main_menu()); return
            if cb=="ad_back_to_admin": await safe_send(bot_instance,cid,"🔙 پنل مدیریت:",chat_keypad=get_admin_panel(bs)); return
            if cb=="ad_close": admin_session[cid]=False; await safe_send(bot_instance,cid,"🔒 پنل بسته شد.",chat_keypad=get_main_menu()); return
            if cb=="ad_bot_off": bs["online"]=False; save_bot_status(bs); await safe_send(bot_instance,cid,"🔴 ربات خاموش شد.",chat_keypad=get_admin_panel(bs)); return
            if cb=="ad_bot_on": bs["online"]=True; save_bot_status(bs); await safe_send(bot_instance,cid,"🟢 ربات روشن شد.",chat_keypad=get_admin_panel(bs)); return
            if cb=="ad_stats":
                users=len(data["users"]); banned=len(data.get("banned_users",[]))
                total_coins=sum(u.get("coins",0) for u in data["users"].values())
                taken=sum(1 for c in countries.values() if c.get("owner"))
                un=load_un()
                stats=f"📊 آمار\n👥 کاربران: {users}\n🚫 مسدود: {banned}\n🪙 مجموع کوین: {fn(total_coins)}\n🌍 کشورها: {len(countries)} (تصرف‌شده: {taken})\n🌐 اعضای UN: {len(un.get('members',[]))}"
                await safe_send(bot_instance,cid,stats,chat_keypad=get_admin_back()); return
            if cb=="ad_countries":
                txt="🌍 کشورها:\n"
                for c,i in countries.items():
                    if i.get("owner"): own=i["owner"]; name="🤖 ربات" if own=="BOT_AI" else data["users"].get(own,{}).get("username",own[:15]); txt+=f"\n{i['flag']} {i['name']} | 👤 {name} | 🆔 `{own}`"
                    else: txt+=f"\n{i['flag']} {i['name']} | ⚪ آزاد"
                await safe_send(bot_instance,cid,txt,chat_keypad=get_admin_back()); return
            if cb=="ad_users":
                txt="👥 کاربران:\n"
                for u,info in list(data["users"].items())[:20]:
                    sts="🚫" if u in data.get("banned_users",[]) else "✅"
                    txt+=f"\n{sts} `{u}` | {info.get('username','؟')} | 🪙 {fn(get_coins(data,u))}"
                await safe_send(bot_instance,cid,txt,chat_keypad=get_admin_back()); return
            if cb=="ad_broadcast":
                user_states[cid]={"broadcast":True}
                await safe_send(bot_instance,cid,"📣 پیام همگانی:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("broadcast"):
                cnt=0
                for u2 in data["users"]:
                    if u2 not in ADMINS:
                        try: await safe_send(bot_instance,u2,f"📣 {mh('پیام فرماندهی')}\n\n{text}"); cnt+=1
                        except: pass
                await safe_send(bot_instance,cid,f"✅ به {cnt} نفر ارسال شد.",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_add_coins":
                user_states[cid]={"add_coins":True}
                await safe_send(bot_instance,cid,"🪙 شناسه و مقدار:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("add_coins"):
                try:
                    parts=text.split(); target=parts[0]; amt=int(parts[1])
                    if amt<=0: await safe_send(bot_instance,cid,"❌ مقدار باید مثبت باشد")
                    elif target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                    else: addc(data,target,amt); await safe_send(bot_instance,cid,f"✅ {amt} کوین اضافه شد.")
                except: await safe_send(bot_instance,cid,"❌ فرمت اشتباه")
                user_states[cid]={}; return
            if cb=="ad_remove_coins":
                user_states[cid]={"remove_coins":True}
                await safe_send(bot_instance,cid,"🪙 شناسه و مقدار:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("remove_coins"):
                try:
                    parts=text.split(); target=parts[0]; amt=int(parts[1])
                    ok,msg=remc(data,target,amt)
                    await safe_send(bot_instance,cid,f"✅ {amt} کوین کم شد." if ok else f"❌ {msg}")
                except: await safe_send(bot_instance,cid,"❌ فرمت اشتباه")
                user_states[cid]={}; return
            if cb=="ad_add_pack":
                user_states[cid]={"add_pack":True}
                await safe_send(bot_instance,cid,f"🎁 شناسه و نام پک:\n{', '.join(PACKS.keys())}",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("add_pack"):
                try:
                    parts=text.split(" ",1); target=parts[0]; pack_name=parts[1]
                    if target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                    elif pack_name not in PACKS: await safe_send(bot_instance,cid,"❌ پک نامعتبر!")
                    else:
                        if "user_packs" not in data: data["user_packs"]={}
                        if target not in data["user_packs"]: data["user_packs"][target]=[]
                        if pack_name in data["user_packs"][target]: await safe_send(bot_instance,cid,"⚠️ کاربر این پک را دارد!")
                        else:
                            data.setdefault("user_packs", {}).setdefault(target, [])
                            data.setdefault("user_eq", {}).setdefault(target, {})
                            data["user_packs"][target].append(pack_name)
                            # Grant every equipment item contained in the pack.
                            pack_items = PACKS[pack_name][3] if len(PACKS[pack_name]) > 3 else {}
                            for eq_name, amount in pack_items.items():
                                if eq_name in EQUIP:
                                    data["user_eq"][target][eq_name] = data["user_eq"][target].get(eq_name, 0) + int(amount)
                            save_data(data)
                            await safe_send(bot_instance,cid,f"✅ پک {pack_name} اضافه شد.\n🧰 تجهیزات داخل پک هم به موجودی کاربر اضافه شدند.")
                except: await safe_send(bot_instance,cid,"❌ فرمت اشتباه")
                user_states[cid]={}; return
            if cb=="ad_add_eq":
                user_states[cid]={"add_eq":True}
                await safe_send(bot_instance,cid,"➕ شناسه، تجهیزات و تعداد:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("add_eq"):
                try:
                    target,eq_name,count=parse_admin_equipment(text)
                    if count<=0: await safe_send(bot_instance,cid,"❌ تعداد باید مثبت باشد")
                    elif target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                    elif eq_name not in EQUIP: await safe_send(bot_instance,cid,f"❌ تجهیزات نامعتبر!\n📋 نام‌های موجود: {', '.join(EQUIP.keys())}")
                    else:
                        addeq(data,target,eq_name,count)
                        await safe_send(bot_instance,cid,f"✅ {count:,} عدد {eq_name} به {target} اضافه شد.")
                except Exception:
                    await safe_send(bot_instance,cid,"❌ فرمت اشتباه.\n\n)شناسه(\nاسم وسیله\nتعداد\n\nیا یک خط:\n)شناسه( اسم وسیله تعداد")
                user_states[cid]={}; return
            if cb=="ad_remove_eq":
                user_states[cid]={"remove_eq":True}
                await safe_send(bot_instance,cid,"➖ شناسه، تجهیزات و تعداد:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("remove_eq"):
                try:
                    target,eq_name,count=parse_admin_equipment(text)
                    ok,msg=remeq(data,target,eq_name,count)
                    await safe_send(bot_instance,cid,f"✅ {count:,} عدد {eq_name} کم شد." if ok else f"❌ {msg}")
                except Exception:
                    await safe_send(bot_instance,cid,"❌ فرمت اشتباه.\n\n)شناسه(\nاسم وسیله\nتعداد")
                user_states[cid]={}; return
            if cb=="ad_warn":
                user_states[cid]={"admin_warn":True}
                await safe_send(bot_instance,cid,"⚠️ شناسه و دلیل اختیاری:\nمثال: 12345 اسپم",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_warn"):
                parts=text.split(" ",1); target=parts[0]; reason=parts[1] if len(parts)>1 else "تخلف از قوانین"
                if target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                elif target in ADMINS: await safe_send(bot_instance,cid,"🛡️ برای ادمین اخطار ثبت نمی‌شود.")
                else:
                    await issue_warning(bot_instance,data,countries,target,reason)
                    await safe_send(bot_instance,cid,f"✅ اخطار ثبت شد: {warning_count(data,target)}/{MAX_WARNINGS}")
                user_states[cid]={}; return
            if cb=="ad_unwarn":
                user_states[cid]={"admin_unwarn":True}
                await safe_send(bot_instance,cid,"🧹 شناسه کاربر:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_unwarn"):
                target=text.strip()
                if target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                else:
                    data["users"][target]["warnings"]=max(0,warning_count(data,target)-1)
                    save_data(data)
                    await safe_send(bot_instance,cid,f"✅ اخطار حذف شد: {warning_count(data,target)}/{MAX_WARNINGS}")
                user_states[cid]={}; return
            if cb=="ad_reset_user":
                user_states[cid]={"admin_reset_user":True}
                await safe_send(bot_instance,cid,"👑 شناسه کاربر برای ریست کامل:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_reset_user"):
                target=text.strip()
                if target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                else:
                    await admin_reset_user(bot_instance,data,countries,target)
                    await safe_send(bot_instance,cid,"✅ کاربر ریست شد.")
                user_states[cid]={}; return
            if cb=="ad_give_country":
                await safe_send(bot_instance,cid,"🌍 کشور مورد نظر:",chat_keypad=get_admin_country_kb(countries,"ad_give_c_")); return
            if cb and cb.startswith("ad_give_c_"):
                code=cb.replace("ad_give_c_","")
                user_states[cid]={"admin_give_country":True,"country_code":code}
                await safe_send(bot_instance,cid,"🆔 شناسه کاربر جدید:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_give_country"):
                target=text.strip(); code=user_states[cid]["country_code"]
                if target not in data["users"]: await safe_send(bot_instance,cid,"❌ کاربر یافت نشد!")
                elif any(i.get("owner")==target for i in countries.values()): await safe_send(bot_instance,cid,"❌ کاربر قبلاً کشور دارد!")
                else:
                    countries[code]["owner"]=target; countries[code]["defense"]=False
                    data["users"][target]["has_country"]=True
                    save_countries(countries); save_data(data)
                    await safe_send(bot_instance,cid,f"✅ {countries[code]['flag']} {countries[code]['name']} به کاربر داده شد.")
                user_states[cid]={}; return
            if cb=="ad_user_search":
                user_states[cid]={"admin_search":True}
                await safe_send(bot_instance,cid,"🔎 شناسه یا نام کاربر:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_search"):
                q=text.lower(); found=[]
                for u,info in data["users"].items():
                    if q in str(u).lower() or q in str(info.get("username","")).lower():
                        found.append((u,info))
                if not found: out="❌ نتیجه‌ای پیدا نشد."
                else:
                    out="🔎 نتایج:\n" + "\n".join(
                        f"• {info.get('username','؟')} | `{u}` | 🪙 {fn(get_coins(data,u))} | ⚠️ {warning_count(data,u)}"
                        for u,info in found[:15])
                await safe_send(bot_instance,cid,out,chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_economy":
                total=sum(get_coins(data,u) for u in data["users"]); packs=sum(len(v) for v in data.get("user_packs",{}).values()); eq=sum(sum(int(x) for x in v.values()) for v in data.get("user_eq",{}).values())
                user_states[cid]={"admin_economy":True}
                await safe_send(bot_instance,cid,f"💰 اقتصاد سرور\n🪙 مجموع کوین: {fn(total)}\n📦 پک‌ها: {fn(packs)}\n🧰 تجهیزات: {fn(eq)}\n\nفرمت تنظیم منابع: شناسه | نوع | مقدار\nانواع: money, gold, diamond, food, oil, gas, iron",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_economy"):
                try:
                    target,kind,amt=[x.strip() for x in text.split('|')]; amt=int(amt)
                    if target not in data['users'] or kind not in ('money','gold','diamond','food','oil','gas','iron'): raise ValueError
                    st=get_country_stats(data,target); st[kind]=max(0,st.get(kind,0)+amt); save_activity(data,uid,'economy',f'{target}:{kind}:{amt}'); save_data(data); await safe_send(bot_instance,cid,"✅ اقتصاد کشور به‌روزرسانی شد.",chat_keypad=get_admin_back())
                except: await safe_send(bot_instance,cid,"❌ فرمت: شناسه | نوع | مقدار",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_system":
                await safe_send(bot_instance,cid,
                    f"🛡 وضعیت سیستم\n👥 کاربران: {len(data['users'])}\n🌍 کشورها: {len(countries)}\n🚫 مسدودها: {len(data.get('banned_users',[]))}\n⚠️ مجموع اخطار: {sum(warning_count(data,u) for u in data['users'])}\n🤖 AI: {'فعال' if bs.get('online',True) else 'خاموش'}",
                    chat_keypad=get_admin_back()); return
            if cb=="ad_backup":
                backup_name=f"worldwar_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup={"data":data,"countries":countries,"alliance":adata,"un":load_un(),"status":bs}
                Path(backup_name).write_text(json.dumps(backup,ensure_ascii=False,indent=2),encoding="utf-8")
                await safe_send(bot_instance,cid,f"💾 پشتیبان ساخته شد: `{backup_name}`",chat_keypad=get_admin_back()); return

            if cb=="ad_eq_catalog":
                txt="🧰 کاتالوگ تجهیزات نظامی\n\n"
                cats={}
                for name,info in EQUIP.items(): cats.setdefault(info[2],[]).append((name,info))
                for cat,items in cats.items():
                    txt+=f"【{cat}】\n"+"\n".join(f"• {n} | 🪙 {fn(i[0])} | 💥 {i[3]}" for n,i in items)+"\n\n"
                await safe_send(bot_instance,cid,txt,chat_keypad=get_admin_back()); return
            if cb=="ad_un_resolve":
                user_states[cid]={"admin_resolution":True}
                await safe_send(bot_instance,cid,"📜 متن قطعنامه جدید را وارد کنید:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_resolution"):
                resolution=text.strip()
                if not resolution:
                    await safe_send(bot_instance,cid,"❌ متن خالی است.",chat_keypad=get_admin_back()); user_states[cid]={}; return
                un=load_un(); un.setdefault("resolutions",[]).append({"text":resolution,"author":uid,"time":datetime.now().isoformat()})
                un["resolutions"]=un["resolutions"][-100:]; save_un(un)
                await safe_send(bot_instance,cid,"✅ قطعنامه با موفقیت ثبت شد.",chat_keypad=get_admin_back()); user_states[cid]={}; return
            if cb=="ad_un_manage":
                un=load_un()
                await safe_send(bot_instance,cid,f"🌐 مدیریت سازمان ملل\n👑 رئیس: 🇺🇸 آمریکا | 🆔 {get_un_leader_uid(un,countries)}\n👥 اعضا: {len(un.get('members',[]))}\n📋 درخواست‌ها: {len(un.get('requests',[]))}",chat_keypad=get_admin_back()); return
            if cb=="ad_ban":
                user_states[cid]={"ban":True}
                await safe_send(bot_instance,cid,"🚫 شناسه:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("ban"):
                target=text.strip()
                if target in data.get("banned_users",[]): await safe_send(bot_instance,cid,"⚠️ قبلاً مسدود شده!")
                else: data.setdefault("banned_users",[]).append(target); save_data(data); await safe_send(bot_instance,cid,"✅ مسدود شد.")
                user_states[cid]={}; return
            if cb=="ad_unban":
                user_states[cid]={"unban":True}
                await safe_send(bot_instance,cid,"✅ شناسه:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("unban"):
                target=text.strip()
                if target in data.get("banned_users",[]): data["banned_users"].remove(target); save_data(data); await safe_send(bot_instance,cid,"✅ رفع مسدود شد.")
                else: await safe_send(bot_instance,cid,"⚠️ مسدود نیست!")
                user_states[cid]={}; return

            if cb=="ad_change_owner":
                await safe_send(bot_instance,cid,"🔄 کشور مورد نظر برای تغییر مالک:",chat_keypad=get_admin_country_kb(countries,"ad_chg_c_"))
                return
            if cb and cb.startswith("ad_chg_c_"):
                code=cb.replace("ad_chg_c_","")
                user_states[cid]={"wait_change_owner_uid":True,"country_code":code}
                await safe_send(bot_instance,cid,f"🔑 شناسه کاربر جدید برای مالکیت {countries[code]['flag']} {countries[code]['name']}:",chat_keypad=get_cancel())
                return
            if cb=="ad_reset_country":
                await safe_send(bot_instance,cid,"♻️ کشور مورد نظر برای ریست:",chat_keypad=get_admin_country_kb(countries,"ad_rst_c_"))
                return
            if cb and cb.startswith("ad_rst_c_"):
                code=cb.replace("ad_rst_c_","")
                user_states[cid]={"confirm_reset":True,"country_code":code}
                await safe_send(bot_instance,cid,f"⚠️ مطمئنی می‌خوای {countries[code]['flag']} {countries[code]['name']} رو کامل ریست کنی؟ (بله / خیر)",chat_keypad=get_cancel())
                return

            if cb and cb.startswith("ad_country_page_"):
                payload=cb.replace("ad_country_page_","")
                # payload format: <action_prefix>p<page>
                if "p" not in payload:
                    await safe_send(bot_instance,cid,"❌ صفحه نامعتبر.",chat_keypad=get_admin_panel(bs)); return
                action_prefix,page_text=payload.rsplit("p",1)
                try:
                    page=int(page_text)
                except ValueError:
                    await safe_send(bot_instance,cid,"❌ صفحه نامعتبر.",chat_keypad=get_admin_panel(bs)); return
                if action_prefix not in ("ad_chg_c_","ad_rst_c_"):
                    await safe_send(bot_instance,cid,"❌ عملیات نامعتبر.",chat_keypad=get_admin_panel(bs)); return
                await safe_send(bot_instance,cid,"🌍 کشور مورد نظر را انتخاب کنید:",chat_keypad=get_admin_country_kb(countries,action_prefix,page))
                return

            if cb=="ad_country_create":
                user_states[cid]={"admin_country_create":True}; await safe_send(bot_instance,cid,"🌍 فرمت: CODE | نام | پرچم | پاداش قدرت",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_country_create"):
                try:
                    code,name,flag,bonus=[x.strip() for x in text.split('|')]; bonus=int(bonus)
                    if not code or code in countries: raise ValueError
                    countries[code]={"flag":flag or "🌍","name":name,"emoji":"🌍","owner":None,"defense":False,"damage_taken":0,"power_bonus":bonus}
                    save_countries(countries); save_activity(data,uid,"create_country",code); save_data(data); await safe_send(bot_instance,cid,"✅ کشور جدید ساخته شد.",chat_keypad=get_admin_back())
                except: await safe_send(bot_instance,cid,"❌ فرمت نامعتبر یا کد تکراری.",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_country_edit":
                user_states[cid]={"admin_country_edit":True}; await safe_send(bot_instance,cid,"✏️ فرمت: CODE | نام جدید | پرچم جدید | پاداش",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_country_edit"):
                try:
                    code,name,flag,bonus=[x.strip() for x in text.split('|')]; bonus=int(bonus)
                    if code not in countries: raise ValueError
                    countries[code].update({"name":name,"flag":flag,"power_bonus":bonus}); save_countries(countries); save_activity(data,uid,"edit_country",code); save_data(data); await safe_send(bot_instance,cid,"✅ کشور ویرایش شد.",chat_keypad=get_admin_back())
                except: await safe_send(bot_instance,cid,"❌ اطلاعات کشور نامعتبر.",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_country_delete":
                user_states[cid]={"admin_country_delete":True}; await safe_send(bot_instance,cid,"🗑 کد کشور برای حذف:",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_country_delete"):
                code=text.strip(); info=countries.get(code)
                if not info: await safe_send(bot_instance,cid,"❌ کشور یافت نشد.",chat_keypad=get_admin_back())
                elif info.get('owner'): await safe_send(bot_instance,cid,"❌ کشور دارای مالک است؛ ابتدا مالکیت را بردارید.",chat_keypad=get_admin_back())
                else: del countries[code]; save_countries(countries); save_activity(data,uid,"delete_country",code); save_data(data); await safe_send(bot_instance,cid,"✅ کشور حذف شد.",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_reward":
                user_states[cid]={"admin_reward":True}; await safe_send(bot_instance,cid,"🎁 فرمت: شناسه کاربر مبلغ کوین",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_reward"):
                try:
                    target,amt=text.split()[0],int(text.split()[1]);
                    if target not in data['users'] or amt<=0: raise ValueError
                    addc(data,target,amt); save_activity(data,uid,"reward",f"{target}:{amt}"); save_data(data); await safe_send(bot_instance,cid,"✅ جایزه پرداخت شد.",chat_keypad=get_admin_back())
                except: await safe_send(bot_instance,cid,"❌ فرمت نامعتبر.",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_admins":
                await safe_send(bot_instance,cid,"👑 مدیریت ادمین‌ها",chat_keypad=get_admin_admins_menu()); return
            if cb=="ad_admin_list":
                roles=get_admin_roles(data); txt="📋 ادمین‌ها\n\n"+"\n".join(f"• {u} | {r}" for u,r in roles.items()); await safe_send(bot_instance,cid,txt,chat_keypad=get_admin_admins_menu()); return
            if cb in ("ad_admin_add","ad_admin_remove","ad_admin_level"):
                if not can_admin(data,uid,"owner"): return await safe_send(bot_instance,cid,"⛔ فقط مالک ربات دسترسی دارد.",chat_keypad=get_admin_admins_menu())
                user_states[cid]={"admin_manage":cb}; await safe_send(bot_instance,cid,"🆔 فرمت: شناسه [سطح]\nسطح‌ها: admin / manager / owner",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_manage"):
                mode=user_states[cid]['admin_manage']; parts=text.split(); target=parts[0] if parts else ''
                roles=get_admin_roles(data)
                if mode=="ad_admin_add":
                    roles[target]=parts[1] if len(parts)>1 and parts[1] in ("admin","manager") else "admin"; save_activity(data,uid,"add_admin",target); save_data(data); out="✅ ادمین اضافه شد."
                elif mode=="ad_admin_remove":
                    if target==OWNER_ID: out="❌ مالک حذف نمی‌شود."
                    else: roles.pop(target,None); save_activity(data,uid,"remove_admin",target); save_data(data); out="✅ ادمین حذف شد."
                else:
                    if target==OWNER_ID: out="❌ سطح مالک قابل تغییر نیست."
                    elif target not in roles: out="❌ ادمین یافت نشد."
                    elif len(parts)<2 or parts[1] not in ("admin","manager"): out="❌ سطح نامعتبر."
                    else: roles[target]=parts[1]; save_activity(data,uid,"change_admin_level",f"{target}:{parts[1]}"); save_data(data); out="✅ سطح دسترسی تغییر کرد."
                await safe_send(bot_instance,cid,out,chat_keypad=get_admin_admins_menu()); user_states[cid]={}; return
            if cb=="ad_army":
                txt="🪖 وضعیت ارتش کاربران\n\n"+"\n".join(f"{u}: سرباز {fn(get_country_stats(data,u)['soldiers'])} | قدرت {fn(power(data,u))}" for u in list(data['users'])[:30])
                user_states[cid]={"admin_army":True}; await safe_send(bot_instance,cid,txt+"\n\nفرمت تنظیم سرباز: شناسه | مقدار",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_army"):
                try:
                    target,amt=[x.strip() for x in text.split('|')]; amt=int(amt)
                    if target not in data['users'] or amt<0: raise ValueError
                    get_country_stats(data,target)['soldiers']=amt; save_activity(data,uid,'army',f'{target}:{amt}'); save_data(data); await safe_send(bot_instance,cid,"✅ تعداد سرباز تنظیم شد.",chat_keypad=get_admin_back())
                except: await safe_send(bot_instance,cid,"❌ فرمت: شناسه | مقدار",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_wars":
                logs=data.get('attack_logs',[])[-20:]; await safe_send(bot_instance,cid,"⚔️ آخرین جنگ‌ها\n\n"+("\n".join(f"{x.get('uid')} → {x.get('target')} | {'برد' if x.get('won') else 'باخت'} | {fn(x.get('damage',0))}" for x in logs) if logs else "جنگی ثبت نشده."),chat_keypad=get_admin_back()); return
            if cb=="ad_events":
                user_states[cid]={"admin_event":True}; await safe_send(bot_instance,cid,"🎁 فرمت رویداد: متن | پاداش کوین",chat_keypad=get_admin_back_cancel()); return
            if user_states.get(cid,{}).get("admin_event"):
                try:
                    msg_event,reward=text.split('|',1); reward=int(reward); data.setdefault('events',[]).append({'text':msg_event.strip(),'reward':reward,'time':datetime.now().isoformat(),'active':True}); save_activity(data,uid,'create_event',msg_event.strip()); save_data(data); await safe_send(bot_instance,cid,"✅ رویداد ساخته شد.",chat_keypad=get_admin_back())
                except: await safe_send(bot_instance,cid,"❌ فرمت: متن | پاداش",chat_keypad=get_admin_back())
                user_states[cid]={}; return
            if cb=="ad_settings":
                settings=data.setdefault('settings',{'season':1,'maintenance':False}); settings.setdefault('season',1); settings.setdefault('maintenance',False); await safe_send(bot_instance,cid,f"⚙️ تنظیمات\n🎬 فصل: {settings['season']}\n🔧 تعمیرات: {'فعال' if settings['maintenance'] else 'خاموش'}\n\nبرای تغییر فصل: season 2\nبرای تعمیرات: maintenance on/off",chat_keypad=get_admin_back()); user_states[cid]={"admin_settings":True}; return
            if user_states.get(cid,{}).get("admin_settings"):
                parts=text.split(); settings=data.setdefault('settings',{'season':1,'maintenance':False})
                if len(parts)==2 and parts[0].lower()=='season' and parts[1].isdigit(): settings['season']=int(parts[1]); out='✅ فصل تغییر کرد.'
                elif len(parts)==2 and parts[0].lower()=='maintenance' and parts[1].lower() in ('on','off'): settings['maintenance']=parts[1].lower()=='on'; out='✅ وضعیت تعمیرات تغییر کرد.'
                else: out='❌ دستور نامعتبر.'
                save_activity(data,uid,'settings',text); save_data(data); await safe_send(bot_instance,cid,out,chat_keypad=get_admin_back()); user_states[cid]={}; return
            if cb=="ad_logs":
                logs=data.get('admin_logs',[])[-50:]; await safe_send(bot_instance,cid,"📝 لاگ فعالیت ادمین‌ها\n\n"+("\n".join(f"{x['time'][:19]} | {x['actor']} | {x['action']} | {x['detail']}" for x in logs) if logs else "لاگی نیست."),chat_keypad=get_admin_back()); return

            return

        # ---------- new game systems ----------
        if cb=="economy_menu": await safe_send(bot_instance,cid,"💰 اقتصاد کشور",chat_keypad=get_economy_menu()); return
        if cb=="eco_info":
            st=get_country_stats(data,uid); await safe_send(bot_instance,cid,"💰 خزانه و منابع\n\n"+"\n".join([f"💵 پول: {fn(st['money'])}",f"🪙 کوین: {fn(get_coins(data,uid))}",f"🥇 طلا: {fn(st['gold'])}",f"💎 الماس: {fn(st['diamond'])}",f"🌾 غذا: {fn(st['food'])}",f"🛢 نفت: {fn(st['oil'])}",f"🔥 گاز: {fn(st['gas'])}",f"⛏ آهن: {fn(st['iron'])}",f"👥 جمعیت: {fn(st['population'])}",f"👷 نیروی کار: {fn(st['workers'])}"]),chat_keypad=get_economy_menu()); return
        if cb=="eco_collect":
            st=get_country_stats(data,uid); st['money']+=1000+st['factories']*300; st['food']+=100+st['farms']*50 if 'farms' in st else 100; st['oil']+=50; st['iron']+=50; save_data(data); await safe_send(bot_instance,cid,"✅ تولید منابع انجام شد.\n💵 +پول و منابع به خزانه اضافه شد.",chat_keypad=get_economy_menu()); return
        if cb=="eco_transfer":
            user_states[cid]={"eco_transfer":True}; await safe_send(bot_instance,cid,"📤 فرمت: شناسه مقصد مقدار",chat_keypad=get_cancel()); return
        if user_states.get(cid,{}).get("eco_transfer"):
            try:
                parts=text.split(); target,amt=parts[0],int(parts[1]); st=get_country_stats(data,uid)
                if target not in data['users'] or amt<=0 or st['money']<amt: raise ValueError
                st['money']-=amt; get_country_stats(data,target)['money']+=amt; data.setdefault('coin_transfers',[]).append({'from':uid,'to':target,'amount':amt,'type':'money','time':datetime.now().isoformat()}); save_data(data); await safe_send(bot_instance,cid,"✅ انتقال با موفقیت انجام شد.",chat_keypad=get_economy_menu())
            except: await safe_send(bot_instance,cid,"❌ فرمت یا موجودی نامعتبر.",chat_keypad=get_economy_menu())
            user_states[cid]={}; return
        if cb=="army_menu": await safe_send(bot_instance,cid,"🪖 مدیریت ارتش",chat_keypad=get_army_menu()); return
        if cb=="army_train":
            st=get_country_stats(data,uid); count=100; cost=500
            if st['money']<cost: return await safe_send(bot_instance,cid,"❌ پول کافی نیست.",chat_keypad=get_army_menu())
            st['money']-=cost; st['soldiers']+=count; save_data(data); await safe_send(bot_instance,cid,"🪖 ۱۰۰ سرباز آموزش دیدند.",chat_keypad=get_army_menu()); return
        if cb=="army_defense":
            st=get_country_stats(data,uid); st['bases']+=1; st['money']=max(0,st['money']-1500); save_data(data); await safe_send(bot_instance,cid,"🛡 یک پایگاه دفاعی به کشور اضافه شد.",chat_keypad=get_army_menu()); return
        if cb=="build_menu": await safe_send(bot_instance,cid,"🏗 توسعه کشور",chat_keypad=get_build_menu()); return
        build_map={"build_city":("cities","🏙 شهر",50000),"build_factory":("factories","🏭 کارخانه",90000),"build_road":("roads","🛣 جاده",25000),"build_school":("schools","🏫 مدرسه",40000),"build_hospital":("hospitals","🏥 بیمارستان",55000),"build_power":("powerplants","⚡ نیروگاه",80000),"build_base":("bases","🛡 پایگاه",75000),"build_port":("ports","⚓ بندر",150000),"build_airport":("airports","🛬 فرودگاه",180000),"build_university":("universities","🎓 دانشگاه",220000)}
        if cb in build_map:
            key,label,cost=build_map[cb]; st=get_country_stats(data,uid)
            if st['money']<cost: return await safe_send(bot_instance,cid,f"❌ برای ساخت {label} باید {fn(cost)} پول در خزانه داشته باشید.\n💰 موجودی فعلی: {fn(st.get("money",0))}",chat_keypad=get_build_menu())
            st['money']-=cost; st[key]=st.get(key,0)+1; save_data(data); await safe_send(bot_instance,cid,f"✅ {label} ساخته شد.",chat_keypad=get_build_menu()); return
        if cb=="diplomacy_menu": await safe_send(bot_instance,cid,"🤝 دیپلماسی",chat_keypad=get_diplomacy_menu()); return
        if cb in ("dip_peace","dip_pact"):
            user_states[cid]={"diplomacy":cb}; await safe_send(bot_instance,cid,"🆔 شناسه کشور مقابل را وارد کنید:",chat_keypad=get_cancel()); return
        if user_states.get(cid,{}).get("diplomacy"):
            target=text.strip(); mode=user_states[cid]['diplomacy']
            if target not in data['users'] or target==uid: await safe_send(bot_instance,cid,"❌ شناسه نامعتبر.",chat_keypad=get_diplomacy_menu())
            else:
                key='peace' if mode=='dip_peace' else 'defense_pact'; data.setdefault('diplomacy',{}).setdefault(key,[]).append({'from':uid,'to':target,'status':'pending','time':datetime.now().isoformat()}); save_data(data); await safe_send(bot_instance,cid,"✅ پیشنهاد دیپلماتیک ثبت شد.",chat_keypad=get_diplomacy_menu())
            user_states[cid]={}; return
        if cb=="dip_list":
            d=data.get('diplomacy',{}); lines=[]
            for k,arr in d.items():
                for x in arr[-20:]:
                    if x.get('from')==uid or x.get('to')==uid: lines.append(f"• {k}: {x.get('from')} → {x.get('to')} | {x.get('status')}")
            await safe_send(bot_instance,cid,"📜 پیمان‌ها\n\n"+("\n".join(lines) if lines else "موردی نیست."),chat_keypad=get_diplomacy_menu()); return
        if cb=="trade_menu": await safe_send(bot_instance,cid,"📦 تجارت و تحریم",chat_keypad=get_trade_menu()); return
        if cb=="trade_offer": user_states[cid]={"trade_offer":True}; await safe_send(bot_instance,cid,"📦 فرمت: شناسه مقصد مقدار پول مقدار غذا",chat_keypad=get_cancel()); return
        if user_states.get(cid,{}).get("trade_offer"):
            try:
                parts=text.split(); target,money,food=parts[0],int(parts[1]),int(parts[2]); st=get_country_stats(data,uid)
                blocked=any(x.get("active") and x.get("by")==target and x.get("type") in ("اقتصادی","تجاری","بانکی") for x in data.get("sanctions",{}).get(uid,[]))
                if blocked: raise ValueError
                if target not in data['users'] or money<0 or food<0 or st['money']<money or st['food']<food: raise ValueError
                data.setdefault('trade_offers',[]).append({'from':uid,'to':target,'money':money,'food':food,'status':'sent','time':datetime.now().isoformat()}); save_data(data); await safe_send(bot_instance,cid,"✅ پیشنهاد تجارت ارسال شد.",chat_keypad=get_trade_menu())
            except: await safe_send(bot_instance,cid,"❌ اطلاعات تجارت نامعتبر است.",chat_keypad=get_trade_menu())
            user_states[cid]={}; return
        if cb and cb.startswith("trade_accept_"):
            try:
                idx=int(cb.replace("trade_accept_","")); offer=data.get("trade_offers",[])[idx]
                if offer.get("to")!=uid or offer.get("status")!="sent": raise ValueError
                sender=offer.get("from"); recv=get_country_stats(data,uid); src=get_country_stats(data,sender)
                money=int(offer.get("money",0)); food=int(offer.get("food",0))
                if src.get("money",0)<money or recv.get("food",0)<food: raise ValueError
                src["money"]-=money; recv["money"]+=money; recv["food"]-=food; src["food"]+=food
                offer["status"]="accepted"; offer["accepted_at"]=datetime.now().isoformat(); save_data(data)
                await safe_send(bot_instance,cid,"✅ پیشنهاد تجارت پذیرفته شد.",chat_keypad=get_trade_menu())
                try: await safe_send(bot_instance,sender,f"📦 تجارت شما با {uid} پذیرفته شد.")
                except: pass
            except: await safe_send(bot_instance,cid,"❌ پیشنهاد نامعتبر یا منابع کافی نیست.",chat_keypad=get_trade_menu())
            return
        if cb=="trade_list":
            arr=[x for x in data.get('trade_offers',[]) if x.get('from')==uid or x.get('to')==uid][-15:]; await safe_send(bot_instance,cid,"📦 پیشنهادهای تجارت\n\n"+("\n".join(f"• {x['from']} → {x['to']} | 💵{fn(x['money'])} | 🌾{fn(x['food'])} | {x['status']}" for x in arr) if arr else "موردی نیست."),chat_keypad=get_trade_offers_menu(data,uid) if any(x.get("to")==uid and x.get("status")=="sent" for x in data.get("trade_offers",[])) else get_trade_menu()); return
        if cb=="sanction_menu":
            user_states[cid]={"sanction":True}; await safe_send(bot_instance,cid,"🚫 فرمت: شناسه کشور نوع تحریم\nانواع: اقتصادی تجاری بانکی تسلیحاتی",chat_keypad=get_cancel()); return
        if user_states.get(cid,{}).get("sanction"):
            parts=text.split();
            if len(parts)<2: await safe_send(bot_instance,cid,"❌ فرمت نامعتبر.",chat_keypad=get_trade_menu())
            else:
                target,kind=parts[0],parts[1]
                if target not in data['users'] or target==uid: await safe_send(bot_instance,cid,"❌ کشور نامعتبر.",chat_keypad=get_trade_menu())
                else:
                    valid_kinds={"اقتصادی":20000,"تجاری":30000,"بانکی":50000,"تسلیحاتی":75000}
                    if kind not in valid_kinds:
                        await safe_send(bot_instance,cid,"❌ نوع تحریم نامعتبر است. یکی از اقتصادی، تجاری، بانکی یا تسلیحاتی را وارد کنید.",chat_keypad=get_trade_menu())
                    else:
                        sanction_cost=valid_kinds[kind]
                        st= get_country_stats(data,uid)
                        if st.get("money",0) < sanction_cost:
                            await safe_send(bot_instance,cid,f"❌ برای اعمال تحریم {kind} حداقل {fn(sanction_cost)} پول لازم است. موجودی: {fn(st.get('money',0))}",chat_keypad=get_trade_menu())
                        else:
                            st["money"]-=sanction_cost
                            data.setdefault('sanctions',{}).setdefault(target,[]).append({'by':uid,'type':kind,'time':datetime.now().isoformat(),'active':True,'cost':sanction_cost})
                            save_data(data)
                            save_activity(data,uid,"sanction",f"{target}:{kind}:{sanction_cost}")
                            await safe_send(bot_instance,cid,f"🚫 تحریم {kind} ثبت شد.\n💰 هزینه: {fn(sanction_cost)} پول",chat_keypad=get_trade_menu())
            user_states[cid]={}; return
            return

        # user menu        # user menu
        if cb=="rules":
            await safe_send(bot_instance,cid,RULES_TEXT,chat_keypad=get_rules_menu()); return
        if cb=="my_warnings":
            logs=data["users"][uid].get("warning_log",[])
            recent="\n".join(f"• {x.get('reason','تخلف')} | {x.get('time','')[:19]}" for x in logs[-5:])
            await safe_send(bot_instance,cid,
                f"⚠️ اخطارهای شما: {warning_count(data,uid)}/{MAX_WARNINGS}\n\n"
                f"{recent or '✅ اخطاری ثبت نشده است.'}\n\n"
                "🔴 اخطار سوم = ریست کشور + مسدودی",
                chat_keypad=get_rules_menu()); return
        if cb=="arsenal":
            eq=totaleq(data,uid)
            if not eq:
                return await safe_send(bot_instance,cid,"🧰 زرادخانه شما خالی است.",chat_keypad=get_main_menu())
            rows=[]
            for name,cnt in sorted(eq.items(),key=lambda x:(EQUIP.get(x[0],(0,"","",0))[2],x[0])):
                info=EQUIP.get(name)
                if info: rows.append(f"{info[1]} {name} × {fn(cnt)} | 💥 {info[3]}")
            await safe_send(bot_instance,cid,"🧰 زرادخانه من\n\n"+"\n".join(rows),chat_keypad=get_main_menu()); return
        if cb=="world_status":
            taken=sum(1 for i in countries.values() if i.get("owner"))
            free=len(countries)-taken
            strongest=sorted(((power(data,i.get("owner")),c,i) for c,i in countries.items() if i.get("owner") and i.get("owner") in data.get("users",{})),reverse=True)[:10]
            txt=f"🌎 وضعیت جهان\n\n🌍 کل کشورها: {len(countries)}\n🟢 آزاد: {free}\n🔴 تصرف‌شده: {taken}\n\n🏆 ۱۰ قدرت برتر:\n"
            for n,(pwr,c,i) in enumerate(strongest,1): txt+=f"{n}. {i['flag']} {i['name']} | ⚔️ {fn(pwr)}\n"
            await safe_send(bot_instance,cid,txt,chat_keypad=get_main_menu()); return
        if cb=="daily_reward": await daily(bot_instance,cid,data,uid); return
        if cb=="leave_country":
            if not user_states.get(cid,{}).get("confirm_leave"):
                user_states[cid]={"confirm_leave":True}
                await safe_send(bot_instance,cid,"🚪 هشدار: تمام دارایی‌ها پاک میشود!\nبرای تأیید دوباره بزنید.",chat_keypad=get_main_menu())
            else: user_states[cid]={}; await leave_country(bot_instance,cid,data,countries,uid)
            return
        if cb=="my_info":
            user=data["users"][uid]; user_coins=get_coins(data,uid); pwr=power(data,uid)
            my=next((i for i in countries.values() if i.get("owner")==uid),None)
            un=load_un()
            un_status="👑 رئیس" if get_un_leader_uid(un,countries)==uid else ("✅ عضو" if uid in un.get("members",[]) else "❌ غیرعضو")
            fac=user.get("faction")
            fac_name=f"{FACTIONS[fac]['icon']} {FACTIONS[fac]['name']}" if fac and fac in FACTIONS else "❌ ندارد"
            aname,_=get_al(adata,uid); al_str=aname if aname else "❌ ندارد"
            txt=f"👤 پروفایل\n🆔 {gid(msg,uid)}\n🔑 شناسه: {sty(uid,'m')}\n🪙 کوین: {fn(user_coins)}\n⚔️ قدرت: {fn(pwr)}\n⚠️ اخطار: {warning_count(data,uid)}/{MAX_WARNINGS}\n🌐 سازمان ملل: {un_status}\n⚔️ گروهک: {fac_name}\n🤝 اتحاد: {al_str}"
            if my:
                cst=get_country_stats(data,uid)
                txt+=f"\n🌍 کشور: {my['flag']} {my['name']}\n💥 خسارت: {fn(my.get('damage_taken',0))}/۲۰۰,۰۰۰\n🏙 شهر: {cst.get('cities',0)} | 🏭 کارخانه: {cst.get('factories',0)} | 🪖 سرباز: {fn(cst.get('soldiers',0))}\n💵 خزانه: {fn(cst.get('money',0))}"
            await safe_send(bot_instance,cid,txt); return
        if cb=="alliance_menu":
            await safe_send(bot_instance,
                cid,
                "🤝 برای دریافت اتحاد، به پشتیبانی زیر پیام دهید:\n\n📩 @Saaid987",
                chat_keypad=get_main_menu()
            )
            return
        if cb=="battle_report":
            await send_battle_report(bot_instance,cid,data,countries,uid)
            return
        if cb=="alliance_create":
            if get_al(adata,uid)[0]: return await safe_send(bot_instance,cid,"❌ شما قبلاً عضو یک اتحاد هستید!")
            if not any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ برای ایجاد اتحاد باید کشور داشته باشید!")
            if get_coins(data,uid)<5000: return await safe_send(bot_instance,cid,f"❌ هزینه ایجاد اتحاد ۵,۰۰۰ کوین است. موجودی: {fn(get_coins(data,uid))}")
            user_states[cid]={"creating_alliance":True}
            await safe_send(bot_instance,cid,"📝 نام اتحاد جدید را وارد کنید:",chat_keypad=get_cancel()); return
        if cb=="alliance_list":
            alliances=adata["alliances"]
            if not alliances: return await safe_send(bot_instance,cid,"📋 هیچ اتحادی وجود ندارد.")
            txt="📋 اتحادهای موجود:\n"
            for i,(a_name,a_info) in enumerate(alliances.items(),1):
                leader_name=data["users"].get(a_info["leader"],{}).get("username","نامشخص")
                txt+=f"\n{i}. {a_name} (رهبر: {leader_name}, اعضا: {len(a_info['members'])})"
            await safe_send(bot_instance,cid,txt); return
        if cb and cb.startswith("join_alliance_"):
            a_name=cb.replace("join_alliance_","")
            if a_name not in adata["alliances"]: return await safe_send(bot_instance,cid,"❌ اتحاد یافت نشد.")
            if adata["user_alliance"].get(uid): return await safe_send(bot_instance,cid,"❌ شما قبلاً عضو یک اتحاد هستید!")
            if adata["traitor_until"].get(uid):
                try:
                    until=datetime.fromisoformat(adata["traitor_until"][uid])
                    if datetime.now()<until: return await safe_send(bot_instance,cid,"⛔ به دلیل خیانت نمی‌توانید عضو شوید.")
                    else: del adata["traitor_until"][uid]
                except: pass
            if not any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ برای پیوستن باید کشور داشته باشید!")
            if uid in adata["alliances"][a_name]["members"]: return await safe_send(bot_instance,cid,"⚠️ شما قبلاً عضو این اتحاد هستید!")
            adata["alliances"][a_name]["members"].append(uid)
            adata["user_alliance"][uid]=a_name; save_alliance(adata)
            await safe_send(bot_instance,cid,f"✅ شما به اتحاد {a_name} پیوستید!",chat_keypad=get_main_menu())
            try: await safe_send(bot_instance,adata["alliances"][a_name]["leader"],f"👤 {username or uid} به اتحاد شما پیوست!")
            except: pass
            return
        if cb=="alliance_info":
            name,info=get_al(adata,uid)
            if not name: return await safe_send(bot_instance,cid,"❌ شما عضو هیچ اتحادی نیستید!")
            leader_name=data["users"].get(info["leader"],{}).get("username","نامشخص")
            members="\n".join(f"{'👑' if m==info['leader'] else '👤'} {data['users'].get(m,{}).get('username',m[:10])} (`{m}`)" for m in info["members"])
            await safe_send(bot_instance,cid,f"🔍 اتحاد {name}\nرهبر: {leader_name}\nاعضا ({len(info['members'])}):\n{members}"); return
        if cb=="alliance_chat":
            if not get_al(adata,uid)[0]: return await safe_send(bot_instance,cid,"❌ عضو اتحاد نیستید!")
            user_states[cid]={"alliance_chat":True}
            await safe_send(bot_instance,cid,"💬 پیام خود را برای اتحاد بفرستید:",chat_keypad=get_cancel()); return
        if cb=="alliance_leave":
            name,info=get_al(adata,uid)
            if not name: return await safe_send(bot_instance,cid,"❌ عضو اتحاد نیستید!")
            if info["leader"]==uid: return await safe_send(bot_instance,cid,"❌ رهبر نمی‌تواند خارج شود.")
            if uid in info["members"]: info["members"].remove(uid)
            if uid in adata["user_alliance"]: del adata["user_alliance"][uid]
            save_alliance(adata)
            await safe_send(bot_instance,cid,f"🚪 شما از اتحاد {name} خارج شدید.",chat_keypad=get_main_menu()); return
        if cb=="alliance_betray":
            name,info=get_al(adata,uid)
            if not name: return await safe_send(bot_instance,cid,"❌ عضو اتحاد نیستید!")
            if info["leader"]==uid: return await safe_send(bot_instance,cid,"❌ رهبر نمی‌تواند خیانت کند!")
            user_coins=get_coins(data,uid); penalty=int(user_coins*0.5)
            remc(data,uid,penalty)
            ueq=totaleq(data,uid); removed=[]
            for _ in range(2):
                if not ueq: break
                eq=random.choice(list(ueq.keys())); amt=min(random.randint(1,3),ueq[eq])
                if amt>0:
                    ok,_=consume(data,uid,eq,amt)
                    if ok: removed.append(f"{eq} x{amt}")
                    ueq=totaleq(data,uid)
            save_data(data)
            if uid in info["members"]: info["members"].remove(uid)
            if uid in adata["user_alliance"]: del adata["user_alliance"][uid]
            adata["traitor_until"][uid]=(datetime.now()+timedelta(hours=24)).isoformat(); save_alliance(adata)
            traitor_name=data["users"][uid].get("username",uid[:10])
            for m in info["members"]:
                try: await safe_send(bot_instance,m,f"💀 {traitor_name} به اتحاد خیانت کرد و جریمه شد!")
                except: pass
            await safe_send(bot_instance,cid,f"💀 شما به اتحاد {name} خیانت کردید!\n🪙 جریمه: {fn(penalty)} کوین\n📦 تجهیزات از دست رفته: {', '.join(removed) if removed else 'هیچ'}\n⛔ تا ۲۴ ساعت نمی‌توانید عضو اتحاد شوید.",chat_keypad=get_main_menu()); return
        if cb=="alliance_manage":
            name,info=get_al(adata,uid)
            if not name or info["leader"]!=uid: return await safe_send(bot_instance,cid,"❌ فقط رهبر می‌تواند مدیریت کند!")
            if len(info["members"])<=1: return await safe_send(bot_instance,cid,"❌ هیچ عضوی برای مدیریت وجود ندارد.")
            builder=ChatKeypadBuilder()
            for m in info["members"]:
                if m!=uid: builder.row(builder.button(id=f"kick_{m}",text=f"❌ {data['users'].get(m,{}).get('username',m[:10])}"))
            builder.row(builder.button(id="back_to_menu",text="🏠 بازگشت"))
            await safe_send(bot_instance,cid,"👥 اعضای اتحاد:",chat_keypad=builder.build(resize_keyboard=True,on_time_keyboard=True)); return
        if cb and cb.startswith("kick_"):
            target=cb.replace("kick_","")
            name,info=get_al(adata,uid)
            if not name or info["leader"]!=uid: return await safe_send(bot_instance,cid,"❌ دسترسی غیرمجاز!")
            if target not in info["members"]: return await safe_send(bot_instance,cid,"❌ کاربر در اتحاد نیست!")
            info["members"].remove(target)
            if target in adata["user_alliance"]: del adata["user_alliance"][target]
            save_alliance(adata)
            tname=data["users"].get(target,{}).get("username",target[:10])
            await safe_send(bot_instance,cid,f"✅ {tname} از اتحاد اخراج شد.")
            try: await safe_send(bot_instance,target,f"❌ شما از اتحاد {name} اخراج شدید.")
            except: pass
            return
        if cb=="alliance_disband":
            name,info=get_al(adata,uid)
            if not name or info["leader"]!=uid: return await safe_send(bot_instance,cid,"❌ فقط رهبر می‌تواند منحل کند!")
            for m in info["members"]:
                if m in adata["user_alliance"]: del adata["user_alliance"][m]
            if name in adata["alliances"]: del adata["alliances"][name]
            save_alliance(adata)
            await safe_send(bot_instance,cid,f"❌ اتحاد {name} منحل شد.",chat_keypad=get_main_menu())
            for m in info["members"]:
                try: await safe_send(bot_instance,m,f"❌ اتحاد {name} توسط رهبر منحل شد.")
                except: pass
            return
        if cb=="attack":
            if not any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ کشور ندارید!",chat_keypad=get_main_menu())
            await safe_send(bot_instance,cid,"🎯 هدف:",chat_keypad=get_attack_countries_kb(countries,0)); return
        if cb and cb.startswith("attack_page_"):
            page=max(0,int(cb.replace("attack_page_","")))
            await safe_send(bot_instance,cid,"🎯 هدف:",chat_keypad=get_attack_countries_kb(countries,page)); return
        if cb and cb.startswith("attack_"):
            target=cb.replace("attack_","")
            eq=data.get("user_eq",{}).get(uid,{}); packs=data.get("user_packs",{}).get(uid,[])
            await safe_send(bot_instance,cid,"🔸 تجهیزات:",chat_keypad=get_attack_eq_kb(eq,packs,target)); return
        if cb and cb.startswith("eq_"):
            parts=cb.replace("eq_","").split("_",1)
            if len(parts)<2: return
            target,eq_name=parts[0],parts[1]
            if eq_name not in EQUIP: return await safe_send(bot_instance,cid,"❌ تجهیزات نامعتبر!")
            max_cnt=totaleq(data,uid).get(eq_name,0)
            if max_cnt==0: return await safe_send(bot_instance,cid,"❌ موجود نیست!")
            await safe_send(bot_instance,cid,f"🎯 تعداد {eq_name}: {fn(max_cnt)}",chat_keypad=get_attack_amt_kb(target,eq_name,max_cnt)); return
        if cb and cb.startswith("amt_"):
            parts=cb.replace("amt_","").split("_")
            if len(parts)<3: return
            await do_attack(bot_instance,cid,data,countries,uid,parts[0],parts[1],int(parts[2])); return
        if cb and cb.startswith("custom_"):
            parts=cb.replace("custom_","").split("_",1)
            if len(parts)<2: return
            user_states[cid]={"wait_custom":True,"target":parts[0],"eq":parts[1]}
            await safe_send(bot_instance,cid,f"✏️ تعداد {parts[1]}:",chat_keypad=get_cancel()); return
        if user_states.get(cid,{}).get("wait_custom"):
            try:
                amt=int(text)
                if amt<=0: return await safe_send(bot_instance,cid,"❌ تعداد باید مثبت باشد.")
                target=user_states[cid]["target"]; eq_name=user_states[cid]["eq"]
                if eq_name not in EQUIP: return await safe_send(bot_instance,cid,"❌ تجهیزات نامعتبر!")
                max_cnt=totaleq(data,uid).get(eq_name,0)
                if amt>max_cnt: return await safe_send(bot_instance,cid,f"❌ حداکثر: {fn(max_cnt)}")
                await do_attack(bot_instance,cid,data,countries,uid,target,eq_name,amt)
                user_states[cid]={}
            except: await safe_send(bot_instance,cid,"❌ عدد معتبر!")
            return
        if cb=="buy_country":
            await safe_send(bot_instance,cid,"🌍 انتخاب کشور:",chat_keypad=get_countries_kb(countries,0)); return
        if cb and cb.startswith("countries_page_"):
            page=max(0,int(cb.replace("countries_page_","")))
            await safe_send(bot_instance,cid,"🌍 انتخاب کشور:",chat_keypad=get_countries_kb(countries,page)); return
        if cb and cb.startswith("country_"):
            code=cb.replace("country_","")
            info=countries.get(code)
            if not info or info.get("owner"): return await safe_send(bot_instance,cid,"❌ نامعتبر!")
            if any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ قبلاً کشور دارید!")
            addc(data,uid,1000)
            countries[code]["owner"]=uid; data["users"][uid]["has_country"]=True
            save_data(data); save_countries(countries)
            await safe_send(bot_instance,cid,f"🎉 کشور {info['flag']} {info['name']} تصرف شد!\n🪙 ۱,۰۰۰ کوین",chat_keypad=get_main_menu()); return
        if cb=="buy_single":
            await safe_send(bot_instance,cid,"🎯 تجهیزات:",chat_keypad=get_single_eq_kb()); return
        if cb and cb.startswith("buyeq_"):
            eq_name=cb.replace("buyeq_","")
            if eq_name not in EQUIP: return await safe_send(bot_instance,cid,"❌ نامعتبر!")
            price=EQUIP[eq_name][0]; user_coins=get_coins(data,uid)
            if user_coins<price: return await safe_send(bot_instance,cid,f"❌ کوین کافی نیست! ({fn(price)})")
            data["users"][uid]["coins"]=user_coins-price; addeq(data,uid,eq_name,1); save_data(data)
            await safe_send(bot_instance,cid,f"✅ {eq_name} خریداری شد!",chat_keypad=get_single_eq_kb()); return
        if cb=="equipment_shop":
            await safe_send(bot_instance,cid,"🛒 فروشگاه پک‌ها",chat_keypad=get_shop_menu()); return
        for pn in PACKS:
            if cb==f"shop_{pn}":
                await safe_send(bot_instance,cid,f"📦 {pn}\n💰 {fn(PACKS[pn][0])} تومان\n🔴 مبالغ پرداخت‌شده برای پک و خریدها پس داده نمی‌شود.\nبرای خرید به {ADMIN_USERNAME} پیام دهید."); return
        if cb=="send_message":
            if not any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ کشور ندارید!")
            user_states[cid]={"wait_msg":True}
            await safe_send(bot_instance,cid,"📨 بیانیه:",chat_keypad=get_cancel()); return
        if user_states.get(cid,{}).get("wait_msg"):
            my_country=next((i for i in countries.values() if i.get("owner")==uid),None)
            if my_country:
                today=date.today().isoformat()
                data["users"][uid].setdefault("daily_statements",{})
                cnt=data["users"][uid]["daily_statements"].get(today,0)
                if cnt>=30: return await safe_send(bot_instance,cid,"❌ محدودیت ۳۰ بیانیه!")
                data["users"][uid]["daily_statements"][today]=cnt+1
                addc(data,uid,50); save_data(data)
                full_id=gid(msg,uid)
                framed=mf(text,title=f"{my_country['flag']} {my_country['name']}",icon="📨")
                final=f"{framed}\n\n👤 {full_id}\n🪙 +۵۰ کوین"
                count=0
                for u2 in data["users"]:
                    if u2!=uid:
                        try: await safe_send(bot_instance,u2,final); count+=1
                        except: pass
                await safe_send(bot_instance,cid,f"✅ بیانیه به {count} نفر ارسال شد!",chat_keypad=get_main_menu())
            user_states[cid]={}; return
        if cb=="top_owners":
            un=load_un(); tops=[]
            for c,i in countries.items():
                if i.get("owner"):
                    own=i["owner"]; pwr=power(data,own)
                    is_leader=(own==get_un_leader_uid(un,countries)); own_name="🤖 ربات" if own=="BOT_AI" else data["users"].get(own,{}).get("username",own[:15])
                    tops.append({"flag":i["flag"],"name":i["name"],"power":pwr+(10000 if is_leader else 0),"damage":i.get("damage_taken",0),"owner":own_name,"uid":own,"is_leader":is_leader})
            tops.sort(key=lambda x:x["power"],reverse=True)
            txt="🏆 رتبه‌بندی:\n\n"; medals=["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
            for idx,t in enumerate(tops[:10]):
                dmg=f" | 💥 {fn(t['damage'])}" if t["damage"]>0 else ""
                txt+=f"{medals[idx]} {t['flag']} {t['name']} | 👤 {t['owner']} | 🆔 `{t['uid']}` | ⚔️ {fn(t['power'])}{dmg}\n"
            await safe_send(bot_instance,cid,txt); return
        if cb=="un_menu": await safe_send(bot_instance,cid,"🌐 سازمان ملل:",chat_keypad=get_un_menu()); return
        if cb=="un_info":
            un=load_un()
            await safe_send(bot_instance,cid,f"🏛 سازمان ملل متحد\n🇺🇸 رئیس سازمان: آمریکا\n👤 رئیس فعلی: {get_un_leader_uid(un,countries)}\n👥 اعضا: {len(un.get('members',[]))}\n📜 قطعنامه‌ها: {len(un.get('resolutions',[]))}",chat_keypad=get_un_menu()); return
        if cb=="un_join":
            un=load_un()
            if uid in un.get("members",[]): return await safe_send(bot_instance,cid,"✅ عضو هستید!")
            if any(req["uid"]==uid and req.get("status")=="pending" for req in un.get("requests",[])):
                return await safe_send(bot_instance,cid,"⏳ درخواست قبلی در حال بررسی است!")
            if not any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ کشور ندارید!")
            un["requests"].append({"uid":uid,"status":"pending","time":datetime.now().isoformat()}); save_un(un)
            await safe_send(bot_instance,cid,"✅ درخواست ثبت شد!"); return
        if cb=="un_members":
            un=load_un(); members=un.get("members",[])
            if not members:
                return await safe_send(bot_instance,cid,"👥 هنوز عضوی در سازمان ملل نیست.",chat_keypad=get_un_menu())
            rows=[f"• {data.get('users',{}).get(m,{}).get('username',m[:12])} — `{m}`" for m in members]
            await safe_send(bot_instance,cid,"👥 اعضای سازمان ملل:\n\n"+"\n".join(rows[:100]),chat_keypad=get_un_menu()); return
        if cb=="un_resolutions":
            un=load_un(); resolutions=un.get("resolutions",[])
            if not resolutions:
                return await safe_send(bot_instance,cid,"📜 هنوز قطعنامه‌ای ثبت نشده است.",chat_keypad=get_un_menu())
            txt="📜 قطعنامه‌های سازمان ملل:\n\n"+"\n".join(f"{i+1}. {r if isinstance(r,str) else r.get('text',str(r))}" for i,r in enumerate(resolutions[-30:]))
            await safe_send(bot_instance,cid,txt,chat_keypad=get_un_menu()); return
        if cb=="un_stats":
            un=load_un()
            members=set(un.get("members",[]))
            active_members=sum(1 for m in members if any(i.get("owner")==m for i in countries.values()))
            total_power=sum(power(data,m) for m in members if m in data.get("users",{}))
            await safe_send(bot_instance,cid,
                f"📊 آمار سازمان ملل\n\n🇺🇸 ریاست: آمریکا\n👥 اعضا: {len(members)}\n🌍 اعضای دارای کشور: {active_members}\n⚔️ قدرت مجموع اعضا: {fn(total_power)}\n📜 تعداد قطعنامه‌ها: {len(un.get('resolutions',[]))}",
                chat_keypad=get_un_menu()); return
        if cb=="un_power":
            un=load_un(); rows=[]
            for m in un.get("members",[]):
                if m in data.get("users",{}): rows.append((power(data,m),m))
            rows.sort(reverse=True)
            txt="⚔️ قدرت اعضای سازمان ملل\n\n"
            for n,(pwr,m) in enumerate(rows[:20],1):
                txt+=f"{n}. {data['users'][m].get('username',m[:10])} | ⚔️ {fn(pwr)}\n"
            await safe_send(bot_instance,cid,txt,chat_keypad=get_un_menu()); return
        if cb=="un_request_list":
            un=load_un()
            if uid!=get_un_leader_uid(un,countries) and uid not in ADMINS:
                return await safe_send(bot_instance,cid,"⛔ فقط رئیس سازمان ملل یا ادمین می‌تواند درخواست‌ها را ببیند.",chat_keypad=get_un_menu())
            pending=[r for r in un.get("requests",[]) if r.get("status")=="pending"]
            if not pending:
                return await safe_send(bot_instance,cid,"📋 درخواست در حال بررسی وجود ندارد.",chat_keypad=get_un_menu())
            txt="📋 درخواست‌های عضویت:\n\n"+"\n".join(f"• {r.get('uid')} | {r.get('time','')[:19]}" for r in pending[:50])
            await safe_send(bot_instance,cid,txt,chat_keypad=get_un_menu()); return
        if cb=="faction_menu":
            await safe_send(bot_instance,cid,"⚔️ گروهک‌ها:",chat_keypad=get_faction_menu()); return
        if cb=="faction_info":
            txt="📊 اطلاعات گروهک‌ها\n\n"
            for key,f in FACTIONS.items():
                weapons="، ".join(f.get("w",[])) or "بدون تجهیزات ویژه"
                txt+=f"{f.get('icon','⚔️')} {f.get('name',key)}\n🎁 پاداش ورود: ۳,۰۰۰ کوین + تجهیزات ویژه\n⚔️ تجهیزات: {weapons}\n\n"
            await safe_send(bot_instance,cid,txt,chat_keypad=get_faction_menu()); return
        if cb and cb.startswith("faction_"):
            faction_key=cb.replace("faction_","")
            if faction_key in FACTIONS:
                f=FACTIONS[faction_key]
                if data["users"][uid].get("faction"): return await safe_send(bot_instance,cid,"❌ قبلاً عضو یک گروهک هستید!")
                if not any(i.get("owner")==uid for i in countries.values()): return await safe_send(bot_instance,cid,"❌ برای عضویت باید کشور داشته باشید!")
                data["users"][uid]["faction"]=faction_key
                for w in f.get("w",[]): addeq(data,uid,w,50)
                addc(data,uid,3000); save_data(data)
                await safe_send(bot_instance,cid,f"✅ به {f['name']} پیوستید!\n🪙 +۳,۰۰۰ کوین",chat_keypad=get_main_menu()); return
    except Exception as e:
        logger.error(f"Unhandled error in handler: {e}\n{traceback.format_exc()}")
        try:
            await safe_send(bot_instance,cid, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

async def main():
    inactivity_task=asyncio.create_task(inactivity_worker(bot))
    try:
        while True:
            try:
                logger.info("ربات در حال اجرا...")
                await bot.run()
            except asyncio.CancelledError:
                logger.info("ربات به صورت دستی متوقف شد.")
                break
            except Exception as e:
                logger.error(f"ربات با خطا متوقف شد: {e}\n{traceback.format_exc()}")
                logger.info("تلاش برای راه‌اندازی مجدد در ۵ ثانیه...")
                await asyncio.sleep(5)
    finally:
        inactivity_task.cancel()
        try:
            await inactivity_task
        except asyncio.CancelledError:
            pass

if __name__=="__main__":
    os_system('cls' if os_name=='nt' else 'clear')
    load_data(); load_countries(); load_un(); load_alliance(); load_bot_status()
    print("🚀 ربات جنگ جهانی با ۱۵۰ کشور در حال اجراست...\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد")
