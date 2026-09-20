import fitz  # PyMuPDF

class PDFParser:
    @staticmethod
    def extract_text(file_path):
        """使用 PyMuPDF 提取本地 PDF 文件的原生文本内容"""
        try:
            doc = fitz.open(file_path)
            full_text = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    full_text.append(f"--- 第 {page_num + 1} 页 ---\n" + text)
            
            doc.close()
            return True, "\n".join(full_text), "原生文本解析成功"
        except Exception as e:
            return False, "", f"PDF 解析失败: {str(e)}"
