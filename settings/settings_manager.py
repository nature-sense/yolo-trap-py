from settings.network_manager import get_wifi_state, get_wifi_ssid
from settings.settings import Settings
from settings.settings_database import SettingsDatabase

class SettingsManager :
    def __init__(self,):
        self.database  = SettingsDatabase()
        self.settings = self.database.get_settings()
        if self.settings is None:
            wifi_state = get_wifi_state()
            if wifi_state :
                wifi_ssid = get_wifi_ssid()


    def get_settings(self) :
        return Settings("","", "",True,5,0.5)