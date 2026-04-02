import cv2
from src.anti_spoof import is_real_face

cap = cv2.VideoCapture(0)

frame_count = 0
result = False

while True:

    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    if frame_count % 3 == 0:
        result = is_real_face(frame)

    if result:
        text = "Real Face"
        color = (0,255,0)
    else:
        text = "Spoof Detected"
        color = (0,0,255)

    cv2.putText(frame, text, (30,50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, color, 2)

    cv2.imshow("Anti Spoof Test", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()