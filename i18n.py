"""
i18n.py — Opporta bilingual layer (English + हिंदी).

Two jobs:
  1. t(key, lang)        — translate a UI label. Falls back to English, then to
                           the key itself, so a missing translation never crashes
                           or shows a blank.
  2. tender_explainer()  — turn a raw tender record into a PLAIN-LANGUAGE summary
     tender_money_reqs()   and a money-requirements breakdown (EMD/TDR, bank
                           solvency, tender form fee) that a first-time bidder in
                           a village can actually understand — in English OR Hindi.

The explainers are deliberately RULE-BASED (no AI call): instant, free, offline-
safe, and identical every time. They read only the fields already on the record
(title, organization, value, deadline, class, EMD, …) and degrade gracefully when
a field is missing — pointing the user to the official tender PDF for exact
figures rather than inventing them.
"""

from __future__ import annotations

from datetime import date

import core

LANGS = {"en": "English", "hi": "हिंदी"}
DEFAULT_LANG = "en"


# ──────────────────────────────────────────────────────────────────────────────
# 1. UI string table
# ──────────────────────────────────────────────────────────────────────────────
STRINGS: dict[str, dict[str, str]] = {
    # ── Navigation ──
    "nav_dashboard": {"en": "Dashboard",  "hi": "डैशबोर्ड"},
    "nav_home":      {"en": "Home",       "hi": "होम"},
    "nav_profile":   {"en": "Profile",    "hi": "प्रोफ़ाइल"},
    "nav_tenders":   {"en": "Tenders",    "hi": "टेंडर"},
    "nav_jobs":      {"en": "Jobs",        "hi": "नौकरियाँ"},
    "nav_analytics": {"en": "Analytics",  "hi": "विश्लेषण"},
    "nav_menu":      {"en": "Menu",        "hi": "मेन्यू"},
    "go_to":         {"en": "Go to",       "hi": "यहाँ जाएँ"},
    "logout":        {"en": "Log Out",    "hi": "लॉग आउट"},
    "language":      {"en": "Language",   "hi": "भाषा"},

    # ── Auth ──
    "sign_in":          {"en": "Secure Sign In",   "hi": "सुरक्षित साइन इन"},
    "login":            {"en": "Login",             "hi": "लॉगिन"},
    "register":         {"en": "Register",          "hi": "रजिस्टर"},
    "create_account":   {"en": "Create Account",    "hi": "खाता बनाएँ"},
    "continue_google":  {"en": "Continue with Google", "hi": "Google से जारी रखें"},
    "or":               {"en": "or",                "hi": "या"},
    "email":            {"en": "Email",             "hi": "ईमेल"},
    "password":         {"en": "Password",          "hi": "पासवर्ड"},
    "forgot_password":  {"en": "Forgot password?",  "hi": "पासवर्ड भूल गए?"},
    "reset_email_label": {"en": "Your account email", "hi": "आपका खाता ईमेल"},
    "send_reset_link":  {"en": "Send reset link",   "hi": "रीसेट लिंक भेजें"},
    "set_new_password": {"en": "Set a new password", "hi": "नया पासवर्ड बनाएँ"},
    "new_password":     {"en": "New password",      "hi": "नया पासवर्ड"},
    "confirm_password": {"en": "Confirm new password", "hi": "नया पासवर्ड दोबारा डालें"},
    "update_password":  {"en": "Update password",   "hi": "पासवर्ड अपडेट करें"},
    "passwords_no_match": {"en": "Passwords don't match.", "hi": "पासवर्ड मेल नहीं खा रहे।"},
    "back_to_login":    {"en": "← Back to login",   "hi": "← लॉगिन पर वापस"},
    "pw_min_len":       {"en": "Password must be at least 6 characters.",
                         "hi": "पासवर्ड कम से कम 6 अक्षरों का होना चाहिए।"},

    # ── Tender detail (Feature 3) ──
    "about_this_tender": {"en": "What this tender is about",
                          "hi": "यह टेंडर किस बारे में है"},
    "how_to_take_part":  {"en": "How to take part (simple steps)",
                          "hi": "कैसे भाग लें (आसान चरण)"},
    "money_requirements": {"en": "Money & deposits you will need",
                           "hi": "ज़रूरी राशि और जमा"},
    "key_facts":         {"en": "Key facts", "hi": "मुख्य बातें"},
    "official_doc_note": {"en": "Exact amounts and rules are in the official tender document — always read it before bidding.",
                          "hi": "सटीक राशि और नियम आधिकारिक टेंडर दस्तावेज़ में हैं — बोली लगाने से पहले उसे अवश्य पढ़ें।"},
    "save_pipeline":     {"en": "Save to Pipeline", "hi": "पाइपलाइन में सहेजें"},
    "open_official_doc": {"en": "Open official tender document",
                          "hi": "आधिकारिक टेंडर दस्तावेज़ खोलें"},

    # ── Money requirement terms (label + simple meaning) ──
    "emd_label":     {"en": "EMD / TDR (Earnest Money)", "hi": "EMD / TDR (अग्रिम जमा राशि)"},
    "emd_meaning":   {"en": "A refundable security deposit you submit with your bid (by DD, bank guarantee, FDR or TDR). Returned if you don't win.",
                      "hi": "बोली के साथ जमा की जाने वाली वापसी-योग्य सुरक्षा राशि (DD, बैंक गारंटी, FDR या TDR द्वारा)। न जीतने पर वापस मिल जाती है।"},
    "solvency_label":   {"en": "Bank Solvency Certificate", "hi": "बैंक सॉल्वेंसी प्रमाणपत्र"},
    "solvency_meaning": {"en": "A letter from your bank proving you can fund the work. Larger tenders usually ask for one.",
                         "hi": "आपके बैंक का पत्र जो दर्शाता है कि आप काम के लिए धन जुटा सकते हैं। बड़े टेंडर में आमतौर पर यह माँगा जाता है।"},
    "formfee_label":    {"en": "Tender Form Fee", "hi": "टेंडर फॉर्म शुल्क"},
    "formfee_meaning":  {"en": "A small non-refundable fee to buy/submit the tender form. The amount is stated in the document.",
                         "hi": "टेंडर फॉर्म खरीदने/जमा करने का छोटा गैर-वापसी शुल्क। राशि दस्तावेज़ में दी गई होती है।"},
    "as_per_doc":    {"en": "as stated in the tender document", "hi": "टेंडर दस्तावेज़ के अनुसार"},

    # ── Bid workshop ──
    "bid_language":   {"en": "Bid document language", "hi": "बिड दस्तावेज़ की भाषा"},

    # ── Generic ──
    "days_left":      {"en": "days left", "hi": "दिन शेष"},
    "expired":        {"en": "Expired",    "hi": "समाप्त"},
    "no_deadline":    {"en": "No deadline", "hi": "कोई अंतिम तिथि नहीं"},
    "state_wide":     {"en": "State-wide",  "hi": "राज्य-व्यापी"},
    "not_specified":  {"en": "not specified", "hi": "उल्लेख नहीं"},
}


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    """Translate a UI key. Falls back EN → key, so it is impossible to crash."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("en") or key


# ──────────────────────────────────────────────────────────────────────────────
# Phrase translator — map a whole English UI phrase straight to Hindi. Lets us
# translate headings / buttons / labels in place without inventing a key for each.
# Unknown phrases fall back to the original English, so nothing ever breaks.
# ──────────────────────────────────────────────────────────────────────────────
TR_HI: dict[str, str] = {
    # ── Section headers ──
    "🛠 Bid Workshop":            "🛠 बिड वर्कशॉप",
    "📋 Active Tenders":          "📋 सक्रिय टेंडर",
    "🔔 Smart Pipeline Alerts":   "🔔 स्मार्ट पाइपलाइन अलर्ट",
    "💼 Latest Government Jobs":   "💼 नवीनतम सरकारी नौकरियाँ",
    "📄 Tender Portal":           "📄 टेंडर पोर्टल",
    "Tender Document Evaluator":  "टेंडर दस्तावेज़ मूल्यांकन",
    "Resume Analyzer":            "रिज़्यूमे विश्लेषक",
    "Bid Document Drafter":       "बिड दस्तावेज़ ड्राफ्टर",
    "💼 Government Job Board":     "💼 सरकारी नौकरी बोर्ड",
    "📊 Market Intelligence":     "📊 बाज़ार जानकारी",
    "👤 My Profile":              "👤 मेरी प्रोफ़ाइल",
    "📋 My Saved Tender Pipeline":"📋 मेरी सहेजी टेंडर सूची",
    # ── Common filters / labels ──
    "Search":                     "खोजें",
    "State":                      "राज्य",
    "District":                   "ज़िला",
    "Category":                   "श्रेणी",
    "All":                        "सभी",
    "Status":                     "स्थिति",
    "Deadline":                   "अंतिम तिथि",
    "Value":                      "मूल्य",
    "Organization":               "विभाग",
    # ── Common buttons / actions ──
    "Login":                      "लॉगिन",
    "Register":                   "रजिस्टर",
    "Log Out":                    "लॉग आउट",
    "Save":                       "सहेजें",
    "Search jobs":                "नौकरियाँ खोजें",
    # ── Common messages ──
    "No results found":           "कोई परिणाम नहीं मिला",
    "results found":              "परिणाम मिले",
}


def tr(text: str, lang: str = DEFAULT_LANG) -> str:
    """Translate a full English UI phrase to `lang`. Unknown text returns as-is."""
    if lang == "en" or not text:
        return text
    return TR_HI.get(text.strip(), text)


def nav_label(page_key: str, lang: str = DEFAULT_LANG) -> str:
    """Translate a nav page key like '📄  Tenders' → keeps the emoji, swaps the word.

    The underlying st.session_state.current_page value stays English (so all the
    `"Tenders" in page` routing checks keep working); only the visible word here
    changes for the user."""
    mapping = {
        "Dashboard": "nav_dashboard", "Home": "nav_home", "Profile": "nav_profile",
        "Tenders": "nav_tenders", "Jobs": "nav_jobs", "Analytics": "nav_analytics",
    }
    if lang == "en":
        return page_key
    for word, key in mapping.items():
        if word in page_key:
            return page_key.replace(word, t(key, lang))
    return page_key


# ──────────────────────────────────────────────────────────────────────────────
# 2. Plain-language tender explainer (rule-based, bilingual)
# ──────────────────────────────────────────────────────────────────────────────
def _s(v, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return default if s.lower() in ("", "nan", "none", "nat", "—") else s


def _value_label(rec: dict, lang: str) -> str:
    vt = _s(rec.get("value_text"))
    if vt:
        return vt
    try:
        vl = float(rec.get("value_lakhs") or 0)
    except (TypeError, ValueError):
        vl = 0
    if vl >= 100:
        cr = vl / 100
        return f"₹{cr:.2f} करोड़" if lang == "hi" else f"₹{cr:.2f} Cr"
    if vl > 0:
        return f"₹{vl:.0f} लाख" if lang == "hi" else f"₹{vl:.0f} Lakh"
    return t("not_specified", lang)


def _days_left(rec: dict):
    d = core.parse_date(rec.get("deadline"))
    if not d:
        return None
    return (d - date.today()).days


def tender_explainer(rec: dict, lang: str = DEFAULT_LANG) -> dict:
    """Return a plain-language explanation of one tender. Never raises.

    Keys: about (str), steps (list[str]), facts (list[(label, value)]).
    """
    try:
        org      = _s(rec.get("organization"), t("not_specified", lang))
        category = _s(rec.get("category"), "")
        district = _s(rec.get("district"), t("state_wide", lang))
        state    = _s(rec.get("state"), "")
        cls      = _s(rec.get("contractor_class"))
        emd      = _s(rec.get("emd"))
        value    = _value_label(rec, lang)
        dl       = _days_left(rec)
        deadline = _s(rec.get("deadline"), t("not_specified", lang))

        place = ", ".join(p for p in (district, state) if p) or t("not_specified", lang)

        if lang == "hi":
            work = f"{category} का काम" if category else "एक सरकारी काम"
            about = (f"{org} {place} में {work} करवाना चाहता है। "
                     f"अनुमानित लागत लगभग {value} है।")
            steps = [
                "आधिकारिक टेंडर दस्तावेज़ (NIT/PDF) को ध्यान से पढ़ें।",
                "जाँचें कि आप पात्रता पूरी करते हैं "
                + (f"(आवश्यक श्रेणी: {cls})।" if cls else "(श्रेणी, टर्नओवर, अनुभव)।"),
                "EMD/अग्रिम जमा राशि तैयार करें "
                + (f"({emd})।" if emd else "(राशि दस्तावेज़ में दी गई है)।"),
                "ज़रूरी कागज़ात तैयार करें — GST, PAN, पंजीकरण, अनुभव प्रमाणपत्र।",
                f"अंतिम तिथि {deadline} से पहले बोली जमा करें — ऑनलाइन या कार्यालय में।",
            ]
            facts = [
                ("जारीकर्ता", org),
                ("स्थान", place),
                ("अनुमानित लागत", value),
                ("आवश्यक श्रेणी", cls or t("not_specified", lang)),
                ("EMD", emd or t("as_per_doc", lang)),
                ("अंतिम तिथि", deadline + (f" ({dl} {t('days_left', lang)})" if dl is not None and dl >= 0 else "")),
            ]
        else:
            work = f"{category} work" if category else "a government work"
            about = (f"{org} wants to get {work} done in {place}. "
                     f"The estimated cost is about {value}.")
            steps = [
                "Read the official tender document (NIT/PDF) carefully.",
                "Check that you meet the eligibility "
                + (f"(required class: {cls})." if cls else "(class, turnover, experience)."),
                "Arrange the EMD / earnest money "
                + (f"({emd})." if emd else "(amount is in the document)."),
                "Prepare the needed papers — GST, PAN, registration, experience certificate.",
                f"Submit your bid before {deadline} — online or at the office.",
            ]
            facts = [
                ("Issued by", org),
                ("Location", place),
                ("Estimated cost", value),
                ("Required class", cls or t("not_specified", lang)),
                ("EMD", emd or t("as_per_doc", lang)),
                ("Last date", deadline + (f" ({dl} {t('days_left', lang)})" if dl is not None and dl >= 0 else "")),
            ]
        return {"about": about, "steps": steps, "facts": facts}
    except Exception:
        # Absolute safety net — a malformed record must never break the page.
        return {"about": _s(rec.get("title"), ""), "steps": [], "facts": []}


def tender_money_reqs(rec: dict, lang: str = DEFAULT_LANG) -> list[dict]:
    """Return the money/deposit items a bidder needs, each with a simple meaning.

    EMD shows the real value when the record has one; solvency & form fee are
    explained generically and point to the official document for exact amounts
    (we never fabricate figures).
    """
    emd = _s(rec.get("emd"))
    return [
        {"label": t("emd_label", lang),
         "value": emd or t("as_per_doc", lang),
         "meaning": t("emd_meaning", lang)},
        {"label": t("solvency_label", lang),
         "value": t("as_per_doc", lang),
         "meaning": t("solvency_meaning", lang)},
        {"label": t("formfee_label", lang),
         "value": t("as_per_doc", lang),
         "meaning": t("formfee_meaning", lang)},
    ]
