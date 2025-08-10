from dataclasses import dataclass

@dataclass
class Settings :
    trap_name : str
    wifi_ssid : str
    wifi_password : str
    wifi_enabled : bool
    max_sessions : int
    min_score : float

