"""
Settings Dialog — Provider & Model selection, API keys
"""

import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTabWidget, QWidget, QFormLayout,
    QGroupBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.agent.llm_client import PROVIDERS

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings — LLM Provider & API Keys")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.config = self._load_config()
        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #1A1A1A; color: #E0E0E0; }
            QTabWidget::pane { border: 1px solid #404040; }
            QTabBar::tab { background: #2D2D2D; color: #E0E0E0; padding: 8px 16px; }
            QTabBar::tab:selected { background: #0078D4; }
            QGroupBox { border: 1px solid #404040; border-radius: 6px; margin-top: 12px; padding: 10px; color: #E0E0E0; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLabel { color: #E0E0E0; }
            QLineEdit {
                background-color: #2D2D2D; color: #E0E0E0;
                border: 1px solid #404040; border-radius: 4px; padding: 6px;
            }
            QLineEdit:focus { border: 1px solid #0078D4; }
            QComboBox {
                background-color: #2D2D2D; color: #E0E0E0;
                border: 1px solid #404040; border-radius: 4px; padding: 6px;
                min-width: 200px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #2D2D2D; color: #E0E0E0; }
            QPushButton {
                background-color: #0078D4; color: white; border: none;
                border-radius: 6px; padding: 8px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton#cancel { background-color: #2D2D2D; border: 1px solid #404040; }
            QPushButton#cancel:hover { background-color: #3D3D3D; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("⚙️  ChE Agent Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #58A6FF; padding: 8px 0;")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()

        # ---- Tab 1: Provider & Model ----
        provider_tab = QWidget()
        p_layout = QVBoxLayout(provider_tab)

        provider_group = QGroupBox("LLM Provider")
        pg_layout = QFormLayout(provider_group)

        self.provider_combo = QComboBox()
        for key, val in PROVIDERS.items():
            self.provider_combo.addItem(f"  {val['name']}", key)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        pg_layout.addRow("Provider:", self.provider_combo)

        self.model_combo = QComboBox()
        pg_layout.addRow("Model:", self.model_combo)

        self.model_info = QLabel("")
        self.model_info.setStyleSheet("color: #888; font-size: 11px;")
        pg_layout.addRow("", self.model_info)

        p_layout.addWidget(provider_group)

        # Active provider display
        self.active_label = QLabel()
        self.active_label.setStyleSheet("color: #00CC00; padding: 6px; font-size: 12px;")
        p_layout.addWidget(self.active_label)
        p_layout.addStretch()
        tabs.addTab(provider_tab, "🤖 Provider & Model")

        # ---- Tab 2: API Keys ----
        keys_tab = QWidget()
        k_layout = QVBoxLayout(keys_tab)

        keys_group = QGroupBox("API Keys (stored locally in config.json)")
        kg_layout = QFormLayout(keys_group)

        self.key_fields = {}
        key_labels = {
            "claude":      ("Anthropic API Key", "sk-ant-..."),
            "openai":      ("OpenAI API Key", "sk-..."),
            "openrouter":  ("OpenRouter API Key", "sk-or-..."),
            "deepseek":    ("DeepSeek API Key", "sk-..."),
        }
        for provider_id, (label, placeholder) in key_labels.items():
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setEchoMode(QLineEdit.EchoMode.Password)

            row_layout = QHBoxLayout()
            row_layout.addWidget(field)
            show_btn = QPushButton("👁")
            show_btn.setFixedWidth(32)
            show_btn.setStyleSheet("background:#2D2D2D; border:1px solid #404040; border-radius:4px;")
            show_btn.setCheckable(True)
            show_btn.toggled.connect(lambda checked, f=field: f.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            ))
            row_layout.addWidget(show_btn)

            container = QWidget()
            container.setLayout(row_layout)
            kg_layout.addRow(f"{label}:", container)
            self.key_fields[provider_id] = field

        ollama_note = QLabel("Ollama (local) — no API key needed. Install from ollama.com")
        ollama_note.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        kg_layout.addRow("", ollama_note)

        k_layout.addWidget(keys_group)
        k_layout.addStretch()
        tabs.addTab(keys_tab, "🔑 API Keys")

        # ---- Tab 3: DWSIM ----
        dwsim_tab = QWidget()
        d_layout = QVBoxLayout(dwsim_tab)

        dwsim_group = QGroupBox("DWSIM Configuration")
        dg_layout = QFormLayout(dwsim_group)

        self.dwsim_path_field = QLineEdit()
        self.dwsim_path_field.setPlaceholderText(r"C:\Users\User\AppData\Local\DWSIM")

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_dwsim)

        path_row = QHBoxLayout()
        path_row.addWidget(self.dwsim_path_field)
        path_row.addWidget(browse_btn)
        path_container = QWidget()
        path_container.setLayout(path_row)
        dg_layout.addRow("DWSIM Path:", path_container)

        self.dwsim_status = QLabel("● Checking...")
        self.dwsim_status.setStyleSheet("color: #FFA500;")
        dg_layout.addRow("Status:", self.dwsim_status)

        d_layout.addWidget(dwsim_group)
        d_layout.addStretch()
        tabs.addTab(dwsim_tab, "🧪 DWSIM")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save & Apply")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _populate_fields(self):
        # Set provider
        saved_provider = self.config.get("provider", "claude")
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == saved_provider:
                self.provider_combo.setCurrentIndex(i)
                break
        self._on_provider_changed()

        # Set model
        saved_model = self.config.get("model", "")
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                break

        # Set API keys
        api_keys = self.config.get("api_keys", {})
        for provider_id, field in self.key_fields.items():
            field.setText(api_keys.get(provider_id, ""))

        # DWSIM path
        self.dwsim_path_field.setText(
            self.config.get("dwsim_path", r"C:\Users\User\AppData\Local\DWSIM")
        )
        self._check_dwsim_status()

        # Active display
        provider_name = PROVIDERS.get(saved_provider, {}).get("name", saved_provider)
        self.active_label.setText(f"● Currently active: {provider_name} / {saved_model}")

    def _on_provider_changed(self):
        provider_id = self.provider_combo.currentData()
        provider = PROVIDERS.get(provider_id, {})
        models = provider.get("models", {})

        self.model_combo.clear()
        for model_id, model_name in models.items():
            self.model_combo.addItem(f"  {model_name}", model_id)

        default = provider.get("default_model", "")
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == default:
                self.model_combo.setCurrentIndex(i)
                break

        if provider_id == "ollama":
            self.model_info.setText("Ollama must be running locally (ollama serve). No API key needed.")
        elif provider_id == "openrouter":
            self.model_info.setText("OpenRouter gives access to 100+ models with one key — openrouter.ai")
        else:
            self.model_info.setText("")

    def _browse_dwsim(self):
        from PyQt6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "Select DWSIM Installation Folder")
        if path:
            self.dwsim_path_field.setText(path)
            self._check_dwsim_status()

    def _check_dwsim_status(self):
        import os
        path = self.dwsim_path_field.text()
        automation_dll = os.path.join(path, "DWSIM.Automation.dll")
        if os.path.exists(automation_dll):
            self.dwsim_status.setText("● Found — DWSIM.Automation.dll detected")
            self.dwsim_status.setStyleSheet("color: #00CC00;")
        else:
            self.dwsim_status.setText("● Not found — check path")
            self.dwsim_status.setStyleSheet("color: #FF4444;")

    def _save(self):
        provider_id = self.provider_combo.currentData()
        model_id = self.model_combo.currentData()

        api_keys = {}
        for pid, field in self.key_fields.items():
            key = field.text().strip()
            if key:
                api_keys[pid] = key

        self.config["provider"] = provider_id
        self.config["model"] = model_id
        self.config["api_keys"] = api_keys
        self.config["dwsim_path"] = self.dwsim_path_field.text()

        # Set env vars for current session
        import os
        key_env_map = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        if provider_id in api_keys:
            os.environ[key_env_map.get(provider_id, "")] = api_keys[provider_id]

        self._write_config()
        QMessageBox.information(self, "Saved", f"Settings saved!\n\nProvider: {PROVIDERS[provider_id]['name']}\nModel: {model_id}\n\nRestart will apply DWSIM path change.")
        self.accept()

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_selected_provider(self) -> str:
        return self.provider_combo.currentData()

    def get_selected_model(self) -> str:
        return self.model_combo.currentData()
