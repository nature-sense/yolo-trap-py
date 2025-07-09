sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-picamera2 --no-install-recommends
sudo apt install -y python3-multiprocess
sudo apt install -y python3-protobuf
sudo apt install -y python3-numpy
sudo apt install -y python3-opencv
sudo apt install -y autofs
sudo apt install -y git
sudo apt install -y pmount
sudo apt install -y python3-tk

python -m venv  --system-site-packages .venv
source .venv/bin/activate
echo 'source .venv/bin/activate' >> .profile
echo 'dtoverlay=imx708,cam1' | sudo tee -a /boot/firmware/config.txt 

pip install asyncio
pip install bless
pip install bleak==0.22.3
pip install json_strong_typing
pip install ultralytics
pip install ncnn
pip install picologging
pip install thonny
pip install numpy==1.26.4

sudo cp installation-files/usbstick.rules /etc/udev/rules.d/
sudo cp installation-files/usbstick-handler@.service /lib/systemd/system/
sudo cp installation-files/cpmount /usr/local/bin/
sudo cp installation-files/cpumount /usr/local/bin/
sudo cp installation-files/yolotrap.service /lib/systemd/system/




