import json
import os
from pathlib import Path
from typing import Optional

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    "ru": "Русский",
    "en": "English",
    "uk": "Українська",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
    "ar": "العربية",
    "tr": "Türkçe",
    "pl": "Polski",
    "nl": "Nederlands",
}

# Обратный маппинг (название -> код)
LANGUAGE_NAME_TO_CODE = {v.lower(): k for k, v in SUPPORTED_LANGUAGES.items()}

class TranslateSettings:
    def __init__(self, storage_path: str = "/tmp/translate_settings.json"):
        self.storage_path = Path(storage_path)
        self.settings = self._load()
    
    def _load(self) -> dict:
        """Загружает настройки из файла"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save(self):
        """Сохраняет настройки в файл"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек перевода: {e}")
    
    def get_language(self, user_id: int) -> Optional[str]:
        """Получает язык перевода для пользователя (2-буквенный код или None)"""
        lang = self.settings.get(str(user_id))
        if lang and lang != "off":
            return lang
        return None
    
    def set_language(self, user_id: int, language: str):
        """Устанавливает язык перевода для пользователя"""
        self.settings[str(user_id)] = language
        self._save()
    
    def disable(self, user_id: int):
        """Отключает перевод для пользователя"""
        self.settings[str(user_id)] = "off"
        self._save()

def parse_language_input(input_text: str) -> Optional[str]:
    """Преобразует ввод пользователя в 2-буквенный код языка"""
    input_lower = input_text.lower().strip()
    
    # Проверка на специальные команды
    if input_lower in ["off", "status", "list"]:
        return input_lower
    
    # Проверка прямого кода
    if input_lower in SUPPORTED_LANGUAGES:
        return input_lower
    
    # Проверка по названию
    if input_lower in LANGUAGE_NAME_TO_CODE:
        return LANGUAGE_NAME_TO_CODE[input_lower]
    
    # Частичное совпадение по названию
    for name, code in LANGUAGE_NAME_TO_CODE.items():
        if input_lower in name or name.startswith(input_lower):
            return code
    
    return None

def get_supported_languages_text() -> str:
    """Возвращает текст со списком поддерживаемых языков"""
    lines = ["<b>Поддерживаемые языки:</b>\n"]
    for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1]):
        lines.append(f"• {name} (<code>{code}</code>)")
    return "\n".join(lines)

# Глобальный экземпляр
translate_settings = TranslateSettings()