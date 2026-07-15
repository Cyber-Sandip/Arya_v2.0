# Arya V2.0

> AI-powered desktop assistant for Windows with voice, GUI, and automation support.

---

## 🚀 Project Overview

**Arya V2.0** is a college project that demonstrates desktop automation, natural language command handling, and packaging a Python application into a Windows executable.

Key features:
- Voice and text command input
- Browser control, search, and website navigation
- System actions like screenshot, lock, shutdown, and restart
- WhatsApp messaging and email support
- Desktop GUI built with `pywebview`

---

## 📁 Project Structure

```
Arya v2.0/
├── main.py
├── router.py
├── config.py
├── ai/
│   ├── gemini.py
│   └── memory.py
├── commands/
│   ├── apps.py
│   ├── browser.py
│   ├── communication.py
│   ├── developer.py
│   ├── file.py
│   ├── media.py
│   ├── productivity.py
│   ├── automation.py
│   ├── smart.py
│   └── utilities.py
├── voice/
│   ├── speech_to_text.py
│   └── text_to_speech.py
├── Gui/
│   ├── index.html
│   ├── main.js
│   └── style.css
├── components/
├── data/
├── models/
└── plugins/
```

---

## ⚙️ Requirements

Install dependencies with:

```powershell
pip install -r requirements.txt
```

---

## 🛠 Build EXE

Run the packaging command from the project root:

```powershell
Set-Location "c:\Users\sandi\OneDrive\Desktop\Arya V2.0"
& "c:\Users\sandi\OneDrive\Desktop\Arya V2.0\.env311\Scripts\python.exe" -m PyInstaller Arya.spec --noconfirm
```

The generated executable will appear in the `dist` folder.

---

## ▶️ Run the App

### Development mode

```powershell
& "c:\Users\sandi\OneDrive\Desktop\Arya V2.0\.env311\Scripts\python.exe" main.py
```

### Packaged mode

```powershell
dist\Arya V2.0.exe
```

---

## 💡 Notes

- Gemini AI support requires a valid `GEMINI_API_KEY` in a `.env` file.
- Voice features require microphone access and working speech libraries.
- If Windows blocks the EXE, run it as administrator or allow it in your security software.

---

## 🧠 College Project Highlights

This project shows:
- Python desktop automation
- voice and text command handling
- GUI integration with webview
- packaging into a Windows executable

---

## 📌 Author

Sandip Hazra
Sayan Betal


