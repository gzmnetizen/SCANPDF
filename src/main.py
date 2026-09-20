import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QFileDialog, QTabWidget, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal

# 导入各个功能模块
from downloader import PDFDownloader
from parser import PDFParser
from ocr import OCRProcessor
from cleaner import TextCleaner
from database import DatabaseManager

class ProcessingWorker(QThread):
    """后台异步处理线程，防止 PyQt 界面在处理耗时任务时卡死"""
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, task_type, source_path_or_url, api_key=""):
        super().__init__()
        self.task_type = task_type  # 'local' 或 'url'
        self.source = source_path_or_url
        self.api_key = api_key
        self.db_manager = DatabaseManager()
        self.ocr_processor = OCRProcessor()

    def run(self):
        try:
            file_path = ""
            file_name = ""

            # 1. 资源获取：根据任务类型下载或获取本地文件路径
            if self.task_type == 'url':
                success, path, msg = PDFDownloader.download_pdf(self.source)
                if not success:
                    self.finished_signal.emit(False, "", msg)
                    return
                file_path = path
                file_name = os.path.basename(file_path)
            else:
                file_path = self.source
                if not os.path.exists(file_path):
                    self.finished_signal.emit(False, "", f"本地文件不存在: {file_path}")
                    return
                file_name = os.path.basename(file_path)

            # 2. PDF 解析模块：提取原生文本
            success, raw_text, msg = PDFParser.extract_text(file_path)
            
            # 若原生文本提取失败或内容过少，尝试通过 OCR 引擎进行补充识别
            if not success or len(raw_text.strip()) < 10:
                ocr_success, ocr_text, ocr_msg = self.ocr_processor.extract_text_from_image(file_path)
                if ocr_success and ocr_text.strip():
                    raw_text = ocr_text

            # 3. 文本清洗模块
            cleaned_text = TextCleaner.clean_raw_text(raw_text)

            # 4. AI 整理层：调用大模型进行结构化处理
            ai_success, structured_data, ai_msg = TextCleaner.structured_ai_process(cleaned_text, self.api_key)
            
            # 5. 数据库存储模块：持久化存入 SQLite
            structured_preview_str = str(structured_data.get("structured_preview", ""))
            self.db_manager.insert_record(file_name, file_path, cleaned_text, structured_preview_str)

            result_output = f"【处理完成】\n文件名: {file_name}\n状态: {ai_msg}\n\n--- 结构化结果预览 ---\n{structured_preview_str}"
            self.finished_signal.emit(True, result_output, "处理成功")
        except Exception as e:
            self.finished_signal.emit(False, "", f"处理过程发生异常: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 整理助手")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # API Key 输入配置行
        api_layout = QHBoxLayout()
        self.api_label = QLabel("Gemini API Key (可选):")
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setPlaceholderText("留空则使用本地默认模式或环境变量")
        api_layout.addWidget(self.api_label)
        api_layout.addWidget(self.api_input)
        main_layout.addLayout(api_layout)

        # 选项卡：支持本地文件处理 vs 网络下载处理
        self.tabs = QTabWidget()
        
        # Tab 1: 本地文件处理页
        tab_local = QWidget()
        local_layout = QVBoxLayout()
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("请选择本地 PDF 文件...")
        btn_browse = QPushButton("浏览文件")
        btn_browse.clicked.connect(self.browse_file)
        
        local_layout.addWidget(QLabel("选择本地 PDF："))
        local_layout.addWidget(self.local_path_input)
        local_layout.addWidget(btn_browse)
        
        self.btn_start_local = QPushButton("开始处理本地 PDF")
        self.btn_start_local.clicked.connect(self.start_local_task)
        local_layout.addWidget(self.btn_start_local)
        tab_local.setLayout(local_layout)
        
        # Tab 2: 网络下载处理页
        tab_url = QWidget()
        url_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入 PDF 的网络下载链接 (URL)...")
        
        url_layout.addWidget(QLabel("输入 PDF 网址："))
        url_layout.addWidget(self.url_input)
        
        self.btn_start_url = QPushButton("下载并处理网络 PDF")
        self.btn_start_url.clicked.connect(self.start_url_task)
        url_layout.addWidget(self.btn_start_url)
        tab_url.setLayout(url_layout)

        self.tabs.addTab(tab_local, "本地 PDF 处理")
        self.tabs.addTab(tab_url, "网络 PDF 下载与处理")
        main_layout.addWidget(self.tabs)

        # 日志与结果输出文本框
        main_layout.addWidget(QLabel("处理日志与结果输出："))
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        main_layout.addWidget(self.text_output)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择 PDF 文件", "", "PDF Files (*.pdf)")
        if file_name:
            self.local_path_input.setText(file_name)

    def start_local_task(self):
        path = self.local_path_input.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "警告", "请先选择一个有效的本地 PDF 文件！")
            return
        self.run_worker('local', path)

    def start_url_task(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入有效的下载链接！")
            return
        self.run_worker('url', url)

    def run_worker(self, task_type, source):
        self.set_ui_enabled(False)
        api_key = self.api_input.text().strip()
        self.text_output.append(f"[*] 开始执行任务，数据来源: {source}")
        
        self.worker = ProcessingWorker(task_type, source, api_key)
        self.worker.finished_signal.connect(self.on_task_finished)
        self.worker.start()

    def on_task_finished(self, success, result_msg, status_title):
        if success:
            self.text_output.append(f"\n{result_msg}\n" + "="*40)
        else:
            QMessageBox.critical(self, "错误", result_msg)
            self.text_output.append(f"[!] 错误: {result_msg}\n" + "="*40)
        self.set_ui_enabled(True)

    def set_ui_enabled(self, enabled):
        self.btn_start_local.setEnabled(enabled)
        self.btn_start_url.setEnabled(enabled)
        self.api_input.setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
