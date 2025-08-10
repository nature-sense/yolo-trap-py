from settings.settings import Settings
from settings.settings_database import SettingsDatabase



class SettingsManager :
    def __init__(self,):
        self.database  = SettingsDatabase("configuration/settings.db")
        self.settings = self.database.read_settings()
        if self.settings is None:
            self.settings = Settings(
                "", #trap_name
                "", #eifi_ssid,
                "", #wifi_password,
                True, #wifi_enabled,
                5, #max_sessions,
                0.75 #min_score
            )
            self.set_settings(self.settings)


    def get_settings(self) :
        return self.settings

    def set_settings(self, settings):
        self.settings = settings
        self.database.write_settings(self.settings)

