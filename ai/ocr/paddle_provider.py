from typing import List
from .interface import OCRProvider, OCRResult

class PaddleOCRProvider(OCRProvider):
    def __init__(self):
        try:
            from paddleocr import PaddleOCR
            # Lazy load model
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
        except ImportError:
            self.ocr = None
            print("WARNING: PaddleOCR not installed. This provider will fail if invoked.")

    def process(self, file_path: str) -> List[OCRResult]:
        if not self.ocr:
            raise RuntimeError("PaddleOCR is not installed or failed to load.")
            
        result = self.ocr.ocr(file_path, cls=True)
        # PaddleOCR returns a list of pages. If image, length is 1.
        
        results = []
        for page_idx, page_data in enumerate(result):
            if not page_data:
                continue
            
            raw_text = []
            bboxes = []
            total_conf = 0.0
            
            for line in page_data:
                bbox, (text, conf) = line
                raw_text.append(text)
                bboxes.append({"box": bbox, "text": text, "conf": conf})
                total_conf += conf
                
            avg_conf = total_conf / len(page_data) if page_data else 0.0
            
            results.append(
                OCRResult(
                    raw_text="\n".join(raw_text),
                    page_number=page_idx + 1,
                    confidence=avg_conf,
                    bounding_boxes=bboxes
                )
            )
            
        return results
