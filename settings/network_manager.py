import subprocess

# nmcli d wifi connect my_wifi password <password>
#sudo nmcli r wifi on
#nmcli -t radio wifi -< enabled/disabled

def get_wifi_ssid():
    try:
        process = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'],
                                 capture_output=True, text=True, check=True)
        output_lines = process.stdout.strip().split('\n')
        for line in output_lines:
            if line.startswith('yes:'):
                return line.split(':', 1)[1]  # Return the SSID
        return None  # No active Wi-Fi found
    except subprocess.CalledProcessError as e:
        print(f"Error executing nmcli: {e}")
        return None

def set_wifi_state(state) :
    try:
        if state :
            subprocess.run(['sudo', 'nmcli', 'r', 'wifi', 'on'],
                                 capture_output=True, text=True, check=True)
        else :
            subprocess.run(['sudo', 'nmcli', 'r', 'wifi', 'off'],
                                     capture_output=True, text=True, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error executing nmcli: {e}")
        return None

def get_wifi_state() :
    try:
        process = subprocess.run(['nmcli', '-t', 'radio', 'wifi'],
                                 capture_output=True, text=True, check=True)
        output_lines = process.stdout.strip().split('\n')
        for line in output_lines:
            if line.startswith('enabled'):
                return True
            else :
                return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing nmcli: {e}")
        return None

