import re

LANGUAGES = {
    "русский": "ru",
    "russian": "ru",
    "english": "en",
    "английский": "en",
    "українська": "uk",
    "украинский": "uk",
    "deutsch": "de",
    "немецкий": "de",
    "français": "fr",
    "французский": "fr",
    "espanol": "es",
    "español": "es",
    "испанский": "es",
    "italiano": "it",
    "итальянский": "it",
    "português": "pt",
    "португальский": "pt",
    "polski": "pl",
    "польский": "pl",
    "türkçe": "tr",
    "турецкий": "tr",
}

CODE_RE = re.compile(r"^[a-z]{2}$", re.IGNORECASE)


def normalize_lang(input_value: str) -> str | None:
    raw = input_value.strip()
    if not raw:
        return None
    if raw.lower() == "off":
        return "off"
    if raw.lower() in {"status", "list"}:
        return raw.lower()
    if CODE_RE.match(raw):
        return raw.lower()
    key = raw.lower()
    return LANGUAGES.get(key)


def language_list() -> str:
    items = sorted({f"{name} — {code}" for name, code in LANGUAGES.items()})
    return "\n".join(items)


def code_to_name(code: str | None) -> str | None:
    if not code:
        return None
    normalized = code.lower()[:2]
    for name, value in LANGUAGES.items():
        if value == normalized:
            return name
    return normalized
