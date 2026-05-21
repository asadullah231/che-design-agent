# ChE Design Agent

AI-powered Chemical Engineering Design Assistant — chat se process design karo!

## Features
- Natural language chat (English + Urdu)
- Distillation column design (FUG shortcut method + DWSIM simulation)
- Heat exchanger design (LMTD method)
- Export results to Excel & PDF
- Import/export DWSIM `.dwxmz` files

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API key
```bash
cp config.example.json config.json
# Edit config.json and add your Anthropic API key
```

### 3. Install DWSIM (optional but recommended)
Download from: https://github.com/DanWBR/dwsim/releases
Install to `C:\DWSIM`

### 4. Run
```bash
python main.py
```

## Usage
Just type your engineering problem in the chat box!

**Examples:**
- `"Ethanol-water distillation, feed 1000 kg/hr, 95% purity chahiye"`
- `"Design a heat exchanger to cool steam from 150°C to 80°C"`
- Import an existing DWSIM file and modify it through chat

## Project Structure
```
che-design-agent/
├── main.py                  # Entry point
├── src/
│   ├── agent/
│   │   └── che_agent.py     # AI brain (Claude API)
│   ├── dwsim_bridge/
│   │   └── dwsim_connector.py  # DWSIM automation
│   ├── calculations/
│   │   ├── distillation.py  # FUG shortcut method
│   │   ├── heat_exchanger.py
│   │   └── exporter.py      # Excel/PDF export
│   └── ui/
│       └── main_window.py   # PyQt6 desktop UI
├── exports/                 # Generated reports
├── designs/                 # Saved DWSIM files
├── requirements.txt
└── config.json
```
