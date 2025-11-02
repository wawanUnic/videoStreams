# videoStreams

MJPEG-мультипоток с OpenCV и uStreamer
Проект для создания масштабируемой архитектуры видеопотока с использованием:

1. физической камеры (/dev/video0)
2. двух виртуальных устройств (v4l2loopback)
3. OpenCV-обработки
4. трансляции через ustreamer с низкой частотой кадров (например, 1 FPS)

Установка зависимостей
```
sudo apt-get install v4l2loopback-dkms v4l2loopback-utils ffmpeg python3-venv git
```

Установка uStreamer
```
sudo apt-get update
sudo apt-get install build-essential libevent-dev libjpeg-dev pkg-config libbsd-dev
git clone https://github.com/pikvm/ustreamer.git
cd ustreamer
make
sudo make install
```
Если включён Secure Boot — отключите его или зарегистрируйте модуль через MOK.

Настройка виртуальных устройств
Создаём два v4l2loopback-устройства:
```
sudo modprobe v4l2loopback devices=2 video_nr=10,11 card_label="InputCam,ProcessedCam" exclusive_caps=1
```

Проверка:
```
v4l2-ctl --list-devices
```

Поток с камеры в виртуальные устройства
Копируем MJPEG с физической камеры в /dev/video10:
```
ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 \
       -f v4l2 -vcodec copy /dev/video10
```

Копируем с понижением FPS в /dev/video11:

```
ffmpeg -f v4l2 -input_format mjpeg -framerate 1 -i /dev/video10 \
       -f v4l2 -vcodec copy /dev/video11
```

Проверка мультичтения через OpenCV
```
mkdir opencv && cd opencv
python3 -m venv venv
source venv/bin/activate
pip install opencv-python opencv-contrib-python
```

Простой тест (1.py):
```
import cv2
cap = cv2.VideoCapture('/dev/video10')
ret, frame = cap.read()
print("Кадр получен:", ret)
```

Трансляция через uStreamer
```
# Поток 1: необработанный
ustreamer --device=/dev/video10 --format=mjpeg --host=0.0.0.0 --port=2000 --desired-fps=1

# Поток 2: обработанный
ustreamer --device=/dev/video11 --format=mjpeg --host=0.0.0.0 --port=2001 --desired-fps=1
```

Архитектура

[ /dev/video0 ] ← физическая камера (MJPEG)
      │
      ▼
[ ffmpeg ] ← копирует MJPEG → /dev/video10
      │
      ▼
[ /dev/video10 ] ← виртуальное устройство
     ├── OpenCV читает, обрабатывает кадры ──▶ /dev/video11
     └── ustreamer1 транслирует в браузер1 (1 FPS)
      │
      ▼
[ /dev/video11 ] ← виртуальное устройство
     └── ustreamer2 транслирует в браузер2 (1 FPS)

Примечания:
1. exclusive_caps=1 позволяет каждому клиенту получать собственный формат
2. MJPEG позволяет работать без перекодирования и с минимальной задержкой
3. Частота кадров ограничивается на этапе ffmpeg и/или в ustreamer через --desired-fps
4. OpenCV может использоваться для коррекции искажений, наложения overlay, распознавания и т.д.
