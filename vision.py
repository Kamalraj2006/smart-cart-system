import cv2
import numpy as np
from typing import Tuple, Optional

detector = cv2.QRCodeDetector()

def process_frame_for_actions(frame_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    Decodes the image and looks for a QR code.
    If it finds a QR code with text 'ADD:product_id' or 'REMOVE:product_id', it returns the action and product_id.
    """
    try:
        nparr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, None
            
        data, bbox, _ = detector.detectAndDecode(img)
        
        if data:
            print(f"Detected QR raw data: {data}")
            parts = data.split(":")
            if len(parts) == 2:
                action, product_id = parts[0], parts[1]
                if action in ["ADD", "REMOVE"]:
                    return action, product_id
                    
        return None, None
    except Exception as e:
        print(f"Error processing frame: {e}")
        return None, None
