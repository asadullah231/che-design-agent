"""
Main Desktop UI - PyQt6 based chat interface for ChE Design Agent
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QFileDialog,
    QSplitter, QFrame, QScrollArea, QSizePolicy, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor

from src.agent.che_agent import ChEDesignAgent


class AgentWorker(QThread):
    """Run agent in background thread so UI doesn't freeze"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, agent: ChEDesignAgent, message: str):
        super().__init__()
        self.agent = agent
        self.message = message

    def run(self):
        try:
            response = self.agent.chat(self.message)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        label = QTextEdit()
        label.setReadOnly(True)
        label.setMarkdown(text)
        label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        label.document().setDocumentMargin(10)

        if is_user:
            label.setStyleSheet("""
                QTextEdit {
                    background-color: #0078D4;
                    color: white;
                    border-radius: 12px;
                    padding: 8px;
                    font-size: 13px;
                }
            """)
            layout.addStretch()
            layout.addWidget(label)
        else:
            label.setStyleSheet("""
                QTextEdit {
                    background-color: #2D2D2D;
                    color: #E0E0E0;
                    border-radius: 12px;
                    padding: 8px;
                    font-size: 13px;
                    border: 1px solid #404040;
                }
            """)
            layout.addWidget(label)
            layout.addStretch()

        # Auto-resize height
        label.document().contentsChanged.connect(
            lambda: label.setFixedHeight(int(label.document().size().height()) + 20)
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.worker = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._setup_ui()
        self._init_agent()

    def _setup_ui(self):
        self.setWindowTitle("ChE Design Agent — Powered by Claude AI + DWSIM")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; color: #E0E0E0; }
            QScrollArea { border: none; background-color: #1A1A1A; }
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #0078D4; }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton:disabled { background-color: #404040; color: #808080; }
            QPushButton#secondary {
                background-color: #2D2D2D;
                border: 1px solid #404040;
            }
            QPushButton#secondary:hover { background-color: #3D3D3D; }
            QStatusBar { background-color: #0078D4; color: white; font-size: 11px; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #0D1117; border-bottom: 1px solid #30363D;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("⚗️ ChE Design Agent")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #58A6FF;")

        self.status_label = QLabel("● Initializing...")
        self.status_label.setStyleSheet("color: #FFA500;")

        import_btn = QPushButton("Import DWSIM")
        import_btn.setObjectName("secondary")
        import_btn.setFixedWidth(130)
        import_btn.clicked.connect(self._import_dwsim_file)

        export_excel_btn = QPushButton("Export Excel")
        export_excel_btn.setObjectName("secondary")
        export_excel_btn.setFixedWidth(110)
        export_excel_btn.clicked.connect(self._export_excel)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setObjectName("secondary")
        export_pdf_btn.setFixedWidth(100)
        export_pdf_btn.clicked.connect(self._export_pdf)

        new_btn = QPushButton("New Design")
        new_btn.setObjectName("secondary")
        new_btn.setFixedWidth(100)
        new_btn.clicked.connect(self._new_conversation)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(import_btn)
        header_layout.addWidget(export_excel_btn)
        header_layout.addWidget(export_pdf_btn)
        header_layout.addWidget(new_btn)

        # Chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)

        # Welcome message
        self._add_agent_message(
            "**Welcome to ChE Design Agent!** ⚗️\n\n"
            "I'm your AI-powered chemical engineering design assistant. "
            "I can help you design:\n\n"
            "- **Distillation Columns** — McCabe-Thiele, FUG shortcut, rigorous simulation\n"
            "- **Heat Exchangers** — LMTD method, sizing, selection\n"
            "- **Reactors** — CSTR, PFR, batch reactor design\n\n"
            "Just describe your problem in **English or Urdu** and I'll handle the calculations!\n\n"
            "*Example: 'Mujhe ethanol-water distillation column design chahiye, "
            "feed 1000 kg/hr, 95% ethanol purity'*"
        )

        # Input area
        input_frame = QFrame()
        input_frame.setFixedHeight(80)
        input_frame.setStyleSheet("background-color: #0D1117; border-top: 1px solid #30363D;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 15, 20, 15)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Describe your chemical engineering problem... (English or Urdu)"
        )
        self.input_box.setFixedHeight(46)
        self.input_box.returnPressed.connect(self._send_message)

        self.send_btn = QPushButton("Send ➤")
        self.send_btn.setFixedSize(100, 46)
        self.send_btn.clicked.connect(self._send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready — DWSIM status will appear here")

        main_layout.addWidget(header)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(input_frame)
        self.setStatusBar(self.status_bar)

    def _init_agent(self):
        if not self.api_key:
            self._prompt_api_key()
            return
        try:
            self.agent = ChEDesignAgent(api_key=self.api_key)
            dwsim_status = "Connected" if self.agent.dwsim.is_available() else "Not Connected (using built-in calculations)"
            self.status_label.setText(f"● DWSIM: {dwsim_status}")
            color = "#00CC00" if self.agent.dwsim.is_available() else "#FFA500"
            self.status_label.setStyleSheet(f"color: {color};")
            self.status_bar.showMessage(f"Agent ready | DWSIM: {dwsim_status}")
        except Exception as e:
            self._add_agent_message(f"**Error initializing agent:** {e}\n\nPlease check your API key in config.json")

    def _prompt_api_key(self):
        from PyQt6.QtWidgets import QInputDialog
        key, ok = QInputDialog.getText(
            self, "API Key Required",
            "Enter your Anthropic API Key:",
            QLineEdit.EchoMode.Password
        )
        if ok and key:
            self.api_key = key
            os.environ["ANTHROPIC_API_KEY"] = key
            self._save_api_key(key)
            self._init_agent()
        else:
            self._add_agent_message("**API Key not provided.** Please set ANTHROPIC_API_KEY in config.json and restart.")

    def _save_api_key(self, key: str):
        import json
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception:
            config = {}
        config["anthropic_api_key"] = key
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _send_message(self):
        text = self.input_box.text().strip()
        if not text or not self.agent:
            return

        self.input_box.clear()
        self._add_user_message(text)
        self._set_loading(True)

        self.worker = AgentWorker(self.agent, text)
        self.worker.response_ready.connect(self._on_response)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_response(self, response: str):
        self._set_loading(False)
        self._add_agent_message(response)
        self.status_bar.showMessage("Response received — ready for next input")

    def _on_error(self, error: str):
        self._set_loading(False)
        self._add_agent_message(f"**Error:** {error}")

    def _add_user_message(self, text: str):
        bubble = ChatBubble(text, is_user=True)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _add_agent_message(self, text: str):
        bubble = ChatBubble(text, is_user=False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def _set_loading(self, loading: bool):
        self.send_btn.setEnabled(not loading)
        self.input_box.setEnabled(not loading)
        if loading:
            self.send_btn.setText("...")
            self.status_bar.showMessage("Agent is calculating...")
        else:
            self.send_btn.setText("Send ➤")

    def _import_dwsim_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import DWSIM File", "", "DWSIM Files (*.dwxmz);;All Files (*)"
        )
        if filepath and self.agent:
            result = self.agent.chat(f"Import this DWSIM file: {filepath}")
            self._add_agent_message(result)

    def _export_excel(self):
        if self.agent:
            self.agent.chat("Export results to Excel file named 'design_results'")
            self._add_agent_message("Excel export requested. Check the **exports/** folder.")

    def _export_pdf(self):
        if self.agent:
            self.agent.chat("Export results to PDF report named 'design_report'")
            self._add_agent_message("PDF export requested. Check the **exports/** folder.")

    def _new_conversation(self):
        reply = QMessageBox.question(
            self, "New Design",
            "Start a new design? Current conversation will be cleared.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.agent:
                self.agent.reset_conversation()
            # Clear chat
            while self.chat_layout.count() > 1:
                item = self.chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._add_agent_message("New design session started! Describe your process requirements.")


def run_app():
    app = QApplication(sys.argv)
    app.setApplicationName("ChE Design Agent")

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
    try:
        import json
        with open(config_path) as f:
            config = json.load(f)
        if config.get("anthropic_api_key"):
            os.environ.setdefault("ANTHROPIC_API_KEY", config["anthropic_api_key"])
    except Exception:
        pass

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
