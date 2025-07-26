from pickledb import PickleDB

class SettingsDatabase :

    def __init__(self) :
        self.db = PickleDB('settings.db')

    def set_settings(self, settings) :
        self.db.set("settings", settings)
        self.db.save()

    def get_settings(self):
        return self.db.get("settings")

