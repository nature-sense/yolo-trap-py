apt update
apt full-upgrade -y
apt install -y python3-picamera2 --no-install-recommends
apt install -y python3-multiprocess
apt install -y python3-protobuf
apt install -y python3-numpy
apt install -y python3-opencv
apt install -y autofs
apt install -y git
apt install -y pmount
apt install -y python3-tk

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

cp installation-files/usbstick.rules /etc/udev/rules.d/
cp installation-files/usbstick-handler@.service /lib/systemd/system/
cp installation-files/cpmount /usr/local/bin/
cp installation-files/cpumount /usr/local/bin/
cp installation-files/yolotrap.service /lib/systemd/system/




