from src.anti_spoof import is_real_face
import cv2

cap = cv2.VideoCapture(0)
print("Press 'Q' to exit Neural Liveness Probe.")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Run the core liveness check
    is_real = is_real_face(frame)
    
    status = "REAL" if is_real else "SPOOF"
    color = (0, 255, 0) if is_real else (0, 0, 255)
    
    cv2.putText(frame, f"Liveness: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Neural Liveness Probe", frame)
    
    if cv2.waitKey(1) == ord('q'): 
        break
        
cap.release()
cv2.destroyAllWindows()