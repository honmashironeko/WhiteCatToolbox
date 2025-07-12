import json
import os
class I18n:
    def __init__(self):
        self.translations = {}
        self.current_language = "zh_CN"
        self.load_translations()
    
    def load_translations(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "app_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_language = config.get("ui_settings", {}).get("language", "zh_CN")
        except:
            self.current_language = "zh_CN"
        
        languages_dir = os.path.join(os.path.dirname(__file__), "languages")
        
        for lang_code in ["zh_CN", "en_US"]:
            lang_file = os.path.join(languages_dir, f"{lang_code}.json")
            if os.path.exists(lang_file):
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except:
                    self.translations[lang_code] = {}
            else:
                self.translations[lang_code] = {}
    
    def t(self, key):
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, key)
        return key
    
    def set_language(self, language):
        self.current_language = language
_i18n_instance = I18n()
def t(key):
    return _i18n_instance.t(key)
def set_language(language):
    _i18n_instance.set_language(language)
def get_current_language():
    return _i18n_instance.current_language