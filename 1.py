import cv2
cap = cv2.VideoCapture('/dev/video10')
ret, frame = cap.read()
print("Кадр получен:", ret)
