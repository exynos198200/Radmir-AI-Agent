import mss
import cv2
import numpy as np
import easyocr

class VisionManager:
    def __init__(self):
        self.sct = mss.mss()
        try:
            self.reader = easyocr.Reader(['ru', 'en'], gpu=True)
            self.ocr_enabled = True
        except Exception as e:
            print(f"Failed to initialize EasyOCR: {e}")
            self.ocr_enabled = False

    def capture_screen(self, monitor_index=1):
        """Captures the selected monitor and returns a valid CV2 image representation."""
        monitor = self.sct.monitors[monitor_index]
        sct_img = self.sct.grab(monitor)
        # Convert to numpy array (BGRA)
        img = np.array(sct_img)
        # Convert to RGB for standard processing
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        return img_rgb

    def extract_text(self, image):
        """Extracts text from an image utilizing EasyOCR."""
        if not self.ocr_enabled:
            return "OCR module offline."
        
        results = self.reader.readtext(image)
        extracted_text = " ".join([result[1] for result in results])
        return extracted_text

    def find_object(self, image, template_path):
        """Simple template matching to find UI elements"""
        # OpenCV template matching stub
        pass
