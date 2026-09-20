import os
from paddleocr import PaddleOCR

class OCRProcessor:
    def __init__(self):
        """初始化 PaddleOCR 实例（支持中英文识别与方向分类）"""
        try:
            self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            self.initialized = True
        except Exception as e:
            self.initialized = False
            self.init_error = str(e)

    def extract_text_from_image(self, img_path):
        """对单张图片或扫描件页面图像进行 OCR 文本识别"""
        if not self.initialized:
            return False, "", f"PaddleOCR 初始化失败: {self.init_error}"
            
        try:
            if not os.path.exists(img_path):
                return False, "", f"图像路径不存在: {img_path}"
            
            result = self.ocr.ocr(img_path, cls=True)
            extracted_lines = []
            
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]  # 提取识别出的文本内容
                    extracted_lines.append(text)
                    
            return True, "\n".join(extracted_lines), "OCR 识别成功"
        except Exception as e:
            return False, "", f"OCR 识别执行异常: {str(e)}"
