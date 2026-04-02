import cv2
import numpy as np
from src.anti_spoof import is_real_face
import time

def run_diagnostic():
    print("--- 🧬 Biometric Neural Diagnostic Tool ---")
    print("Instructions:")
    print("1. Look at the camera. Check terminal for 'Probs'.")
    print("2. P0 is usually SPOOF, P1 is usually REAL.")
    print("3. Try showing a photo of yourself on a PHONE to the camera.")
    print("4. See if the numbers swap. Press 'Q' to exit.")
    print("-------------------------------------------")
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to access camera.")
            break
            
        frame = cv2.flip(frame, 1)
        
        # We call the function which now prints diagnostic logs to terminal
        result = is_real_face(frame)
        
        status_color = (0, 255, 0) if result else (0, 0, 255)
        status_text = "MATCHED (REAL)" if result else "BLOCKED (SPOOF/WEAK)"
        
        cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        cv2.imshow("Neural Diagnostic Feed", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_diagnostic()
