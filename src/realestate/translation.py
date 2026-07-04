"""Arabic -> English translation layer.

The Dubai Pulse transactions workbook ships bilingual columns; the DLD projects
workbook ships paired ``*_ar`` / ``*_en`` columns plus free-text Arabic names.
This module centralises:

* canonical English column names for both datasets;
* value-level Arabic -> English dictionaries derived from the authoritative
  bilingual pairs in the source files;
* a curated developer-name dictionary covering every developer in the DLD
  projects workbook (transliteration alone mangles Arabic names because the
  script omits vowels);
* a ``translate_value`` helper that falls back gracefully (returns the original
  string) when a term is not in the dictionary, so ingestion never crashes on an
  unseen value.
"""
from __future__ import annotations

# --- Transactions workbook: raw header -> canonical English snake_case --------
TRANSACTIONS_COLUMN_MAP = {
    "Year": "year",
    "Quarter": "quarter",
    "Quarter_Number": "quarter_number",
    "Type": "property_type",
    "Title": "transaction_group",   # Sales / Mortgages / Other
    "Description": "measure",        # Value / Number
    "Value": "amount",
    "sort_id": "sort_id",
    # Arabic mirror columns (dropped after validation, kept for provenance)
    "الربع السنوي": "quarter_ar",
    "النوع": "property_type_ar",
    "العنوان": "transaction_group_ar",
    "الوصف": "measure_ar",
}

# --- Value-level Arabic -> English (authoritative, from bilingual source) -----
PROPERTY_TYPE_AR_EN = {
    "وحده": "Units",
    "مبنى": "Building",
    "أرض": "Land",
    "فيلا": "Villa",
}
TRANSACTION_GROUP_AR_EN = {
    "المبايعات": "Sales",
    "الرهون": "Mortgages",
    "أخرى": "Other",
}
MEASURE_AR_EN = {
    "قيمة": "Value",
    "عدد": "Number",
}
QUARTER_AR_EN = {
    "الربع الأول": "First Quarter",
    "الربع الثاني": "Second Quarter",
    "الربع الثالث": "Third Quarter",
    "الربع الرابع": "Fourth Quarter",
}

# Project status codes (DLD) -> human-readable English.
PROJECT_STATUS_MAP = {
    "FINISHED": "Finished",
    "ACTIVE": "Active",
    "NOT_STARTED": "Not Started",
    "PENDING": "Pending",
    "CONDITIONAL_ACTIVATING": "Conditional Activating",
    "FRIEZED": "Frozen",  # source spelling normalised
}

# Quarter label -> integer (used when Quarter_Number is missing).
QUARTER_TO_INT = {
    "First Quarter": 1,
    "Second Quarter": 2,
    "Third Quarter": 3,
    "Fourth Quarter": 4,
}


def translate_value(value, mapping: dict) -> str:
    """Translate a single value using ``mapping``; pass through unknowns."""
    if value is None:
        return value
    key = str(value).strip()
    return mapping.get(key, key)


def normalise_status(value) -> str:
    if value is None:
        return value
    return PROJECT_STATUS_MAP.get(str(value).strip().upper(), str(value).strip().title())


# ---------------------------------------------------------------------------
# English display layer for the dashboard (project types + developers)
# ---------------------------------------------------------------------------
import re as _re

PROJECT_TYPE_AR_EN_DISPLAY = {
    "عادي": "Standard",
    "متعدد": "Mixed-use",
    "بنية تحتية": "Infrastructure",
}

# Curated English names for Dubai developers (covers every developer present
# in the DLD projects workbook). Keys are whitespace-normalised before lookup,
# so single spaces here match multi-space source strings too.
DEVELOPER_AR_EN = {
    "قرية جميرا (ش.ذ.م.م)": "Jumeirah Village",
    "شركة نخيل (ش.م.خ)": "Nakheel",
    "مجموعة ميدان (ش.ذ.م.م)": "Meydan Group",
    "اعمار العقارية (ش . م. ع)": "Emaar Properties",
    "ليوان(ش.ذ.م.م.)": "Liwan",
    "دبي للعقارات (ش.ذ.م.م)": "Dubai Properties",
    "الخليج التجاري (ش.ذ.م.م)": "Business Bay",
    "مؤسسه مدينه دبى للطيران": "Dubai Aviation City Corporation",
    "دبي لاند ريزيدنسز (ش.ذ.م.م)": "Dubailand Residences",
    "مراس العقارية (ش.ذ.م.م)": "Meraas",
    "مدينة دبي الرياضية (ش. ذ. م. م)": "Dubai Sports City",
    "الفرجان ( ش.ذ.م.م )": "Al Furjan",
    "إعمار للتطوير (مساهمة عامة)": "Emaar Development",
    "سلطة دبي للمناطق الإقتصادية المتكاملة": "Dubai Integrated Economic Zones",
    "دبي هيلز استيت ش.ذ.م.م": "Dubai Hills Estate",
    "رمرام ش.ذ.م.م": "Remraam",
    "تيكوم للإستثمارات منطقة حرة- ذ.م.م": "TECOM Investments",
    "مركز دبي للسلع المتعددة": "DMCC (Dubai Multi Commodities Centre)",
    "داماك كريسنت للعقارات (ش.ذ.م.م)": "DAMAC Crescent Properties",
    "شركة الخط الامامي لادارة الاستثمار ش.ذ.م.م": "Front Line Investment Management",
    "انترناشونال سيتي ( ش.ذ.م.م )": "International City",
    "شوبا ش.ذ.م.م": "Sobha",
    "نشاما للعقارات لمالكها نشمي ديفلوبمنت شركة الشخص الواحد ش.ذ.م.م": "Nshama",
    "دبي لاند (ش.ذ.م.م)": "Dubailand",
    "مركز دبي التجاري العالمي ش.ذ.م.م": "Dubai World Trade Centre",
    "نشمي ديفلوبمنت ش.ذ.م.م": "Nashmi Development",
    "مرسى دبي المرحلة الاولى (ش.ذ.م.م)": "Dubai Marina (Phase 1)",
    "دبي للاستثمار العقاري (ش ذ م م)": "Dubai Investment Real Estate",
    # --- Long tail: verified English identities (previously mangled by
    # vowel-less transliteration, e.g. "Tsh R Y Llttwyr L Qry") -------------
    "دى اتش ايه ام منطقه حره - ذ.م.م": "DHAM (Dubai Holding Asset Management)",
    "واحة الجزيرة العقارية (ش.ذ.م.م)": "Wahat Al Jazeera Real Estate",
    "إعمار دبي الجنوب دي دبليو سي ش.ذ.م.م": "Emaar Dubai South DWC",
    "شركة النخلة - جميرا (ش.ذ.م.م)": "Palm Jumeirah",
    "عقارات جميرا جولف ش.ذ.م.م": "Jumeirah Golf Estates",
    "مدينة دبي الملاحية م م ح": "Dubai Maritime City",
    "النخلة - ديره (ش.ذ.م.م)": "Palm Deira",
    "دبي كريك هاربور ش.ذ.م.م": "Dubai Creek Harbour",
    "ذي لاجونز المرحلة الاولى ش.ذ.م.م": "The Lagoons (Phase 1)",
    "ميناء راشد العقارية ش.ذ.م.م": "Mina Rashid Real Estate",
    "شمال العقارية ش.ذ.م.م": "Shamal Real Estate",
    "الاتحاد العقارية (شركة مساهمة عامة)": "Union Properties PJSC",
    "مدينه دبى الطبيه منطقه حرة - ذ.م.م.": "Dubai Healthcare City",
    "شركة داماك ايليت للاستثمار ذ.م.م": "DAMAC Elite Investment",
    "شركة تطوير مجمع دبي للاستثمار (ذ. م. م)": "Dubai Investments Park Development",
    "جيه ايه جي للتطوير ش.ذ.م.م": "JAG Development",
    "الحي الاول - منطقة حرة": "District One",
    "ماجد الفطيم لتشغيل مشاريع المدن المتكاملة الاماراتية ش.ذ.م.م": "Majid Al Futtaim Communities",
    "داماك ميري للاستثمار ش.ذ.م.م": "DAMAC Meree Investment",
    "الياس و مصطفى كلداري لإدارة الاستثمار و التطوير (ش.ذ.م.م)": "Ilyas & Mustafa Galadari Investment & Development",
    "جميرا هيلز ديفيلوبمنت ش.ذ.م.م": "Jumeirah Hills Development",
    "إكسبو سيتي للتطوير العقاري ش م ح": "Expo City Real Estate Development",
    "مؤسسة مدينة ميدان": "Meydan City Corporation",
    "قريه الثقافه ( ش.ذ.م.م)": "Culture Village",
    "دبي بينينسولا ش.ذ.م.م": "Dubai Peninsula",
    "سيتي ووك ريزيدينشال 1 ش.ذ.م.م": "City Walk Residential 1",
    "دي اتش ار اي 2 بي تي اس ش.ذ.م.م": "DHRE 2 BTS (Dubai Holding)",
    "الاريام المرحلة الاولى ش.ذ.م.م": "Al Aryam (Phase 1)",
    "الاريام المرحلة الثانية ش.ذ.م.م": "Al Aryam (Phase 2)",
    "بارك 1 ش.ذ.م.م": "Park 1",
    "دبي هاربور كوميونيتي ذ.م.م": "Dubai Harbour Community",
    "العالم ( ش. ذ. م. م )": "The World",
    "دبي الجنوب للعقارات دي دبليو سي ش.ذ.م.م": "Dubai South Properties DWC",
    "مدينه دبى الصناعيه ش ذ م م": "Dubai Industrial City",
    "تنميات جلوبل للتطوير العقاري ش ذ م م": "Tanmiyat Global Real Estate Development",
    "ليمتلس ش .ذ.م.م": "Limitless",
    "شركة أبواب العقارية المحدودة (ش.ذ.م.م)": "Abwab Real Estate",
    "جميرا بارك (ش.ذ.م.م)": "Jumeirah Park",
    "نشاما للتطوير ش.ذ.م.م": "Nshama Development",
    "شركة الياس ومصطفى كلداري للعقارات (ذ.م.م)": "Ilyas & Mustafa Galadari Real Estate",
    "ام دي ان للعقارات ش.ذ.م.م": "MDN Real Estate",
    "الشركة الخليجية للاستثمارات العامة (ش.م.ع)": "Gulf General Investments (GGICO)",
    "جميرا باي ش.ذ.م.م": "Jumeirah Bay",
    "جيه جي اي للعقارات ش.ذ.م.م": "JGE Real Estate",
    "اعمار بوادي (ذ م م)": "Emaar Bawadi",
    "هاربور العقارية ذ.م.م": "Harbour Real Estate",
    "مراس باي أند ريزيدنس ش.ذ.م.م": "Meraas Bay & Residence",
    "شركة داماك العقارية (ش.ذ.م.م)": "DAMAC Properties",
    "ديفكو لتطوير العقارات ش.ذ.م.م": "DEVCO Real Estate Development",
    "إلينجتون كارما للتطوير ذ.م.م": "Ellington Karma Development",
    "إستثمار العقارية منطقة حرة ذ.م.م": "Istithmar Real Estate",
    "أتش أر أي للتطوير العقاري ش.ذ.م.م": "HRE Real Estate Development",
    "داماك ورلد ريل استيت ش.ذ.م.م": "DAMAC World Real Estate",
    "داماك سي اس ال للاستثمار ش.ذ.م.م": "DAMAC CSL Investment",
    "دار جلوبال لكشري للتطوير العقاري ذ.م.م ش.ش.و": "Dar Global Luxury Real Estate Development",
    "جيرسي للتطوير العقاري ش.ذ.م.م": "Jersey Real Estate Development",
    "جميرا باي ريزيدينشال ذ.م.م": "Jumeirah Bay Residential",
    "بي دي أل أم ريزيدينشال ذ.م.م": "BDLM Residential",
    "ايدن هيلز ش.ذ.م.م": "Eden Hills",
    "بي جي هوتيل ريزيدينشال ش.ذ.م.م": "BG Hotel Residential",
    "ام ايه اس للتطوير العقاري ش.ذ.م.م": "MAS Real Estate Development",
    "الفتان العقارية (ش.ذ.م.م)": "Al Fattan Properties",
    "الخيل هايتس ش.ذ.م.م": "Al Khail Heights",
    "اوريون للتطوير العقاري ش.ذ.م.م": "Orion Real Estate Development",
    "اولد تاون فيوز ش.ذ.م.م": "Old Town Views",
    "اي تي ايه ستار للتطوير العقاري ش.ذ.م.م": "ETA Star Real Estate Development",
    "الحبتور سيتي للتطوير العقاري (فرع من دبي الوطنية للإستثمار(ش.ذ.م.م))": "Al Habtoor City Development",
    "الاصيل للاستثمارات ش.ذ.م.م": "Al Aseel Investments",
    "اراد للتطوير ذ م م للشخص الواحد": "Arada Developments",
    "عزيزي ديفليوبمنتس ش.ذ.م.م": "Azizi Developments",
    "سيفين مايفير للتطوير العقاري ش.ذ.م.م": "Seven Mayfair Real Estate Development",
    "شركة جزر جميرا (ش.ذ.م.م)": "Jumeirah Islands",
    "ديزرت فالكون للتطوير العقاري ش.ذ.م.م": "Desert Falcon Real Estate Development",
    "دي دابليو تي سي إعمار ذ.م.م": "DWTC Emaar",
    "روف للضيافة ش.ذ.م.م": "Rove Hospitality",
    "زعبيل سكوير ش.ذ.م.م": "Za'abeel Square",
    "مدينة دبي للغولف (ش.ذ.م.م)": "Dubai Golf City",
    "مجمع اعمال مركز دبى للسلع المتعدده م.د.م.س": "DMCC Business Park",
    "كرستال ثري ش.ذ.م.م-منطقة حرة": "Crystal Three",
    "كريك هايتس للعقارات ش.ذ.م.م": "Creek Heights Real Estate",
    "مرسى العرب ش.ذ.م.م": "Marsa Al Arab",
    "مرسى العرب ريزدنسز ش.ذ.م.م": "Marsa Al Arab Residences",
    "مشاريع وسط دبي ش.ذ.م.م": "Downtown Dubai Projects",
    "ون زعبيل ذ.م.م": "One Za'abeel",
}


def _norm_ws(s) -> str:
    """Collapse runs of whitespace (source strings often carry double spaces)."""
    return _re.sub(r"\s+", " ", str(s)).strip()


_DEVELOPER_AR_EN_NORM = {_norm_ws(k): v for k, v in DEVELOPER_AR_EN.items()}

# Legal-form suffixes stripped before transliterating long-tail developer names.
_LEGAL_SUFFIX = _re.compile(
    r"\(?\s*(ش\s*\.?\s*ذ\s*\.?\s*م\s*\.?\s*م\.?|ش\s*\.?\s*م\s*\.?\s*ع|ش\s*\.?\s*م\s*\.?\s*خ"
    r"|ذ\s*\.?\s*م\s*\.?\s*م|مساهمة عامة|منطقة حرة|منطقه حره)\s*\)?\.?"
)


def project_type_display(value) -> str:
    if value is None:
        return value
    s = str(value).strip()
    return PROJECT_TYPE_AR_EN_DISPLAY.get(s, _transliterate(s))


def developer_display(name) -> str:
    if name is None:
        return name
    s = _norm_ws(name)
    if s in _DEVELOPER_AR_EN_NORM:
        return _DEVELOPER_AR_EN_NORM[s]
    base = _LEGAL_SUFFIX.sub("", s).strip(" -.،")
    out = _transliterate(base) or _transliterate(s)
    return out


def is_known_developer(name) -> bool:
    """True when we have a verified English identity for this developer.
    Unverified names (which would only render as a raw transliteration)
    can be filtered out of user-facing choice lists."""
    if name is None:
        return False
    s = _norm_ws(name)
    return s in _DEVELOPER_AR_EN_NORM or not _has_arabic(s)


def _has_arabic(s: str) -> bool:
    return any("؀" <= ch <= "ۿ" for ch in str(s))


def _transliterate(s: str) -> str:
    s = str(s)
    if not _has_arabic(s):
        return s.strip()
    try:
        from unidecode import unidecode
        t = unidecode(s)
    except Exception:
        return s.strip()
    t = _re.sub(r"[^A-Za-z0-9 &()\-.]", " ", t)
    t = _re.sub(r"\s+", " ", t).strip(" -.")
    return t.title()
