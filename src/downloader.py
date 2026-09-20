import os
import requests

class PDFDownloader:
    @staticmethod
    def download_pdf(url, save_dir="downloads"):
        """从指定 URL 下载 PDF 文件到本地目录"""
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 从 URL 提取文件名，若无法识别则使用默认名称
            file_name = url.split("/")[-1].split("?")[0]
            if not file_name or not file_name.endswith(".pdf"):
                file_name = "downloaded_document.pdf"
            
            file_path = os.path.join(save_dir, file_name)
            
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            return True, file_path, "下载成功"
        except Exception as e:
            return False, "", f"下载失败: {str(e)}"
