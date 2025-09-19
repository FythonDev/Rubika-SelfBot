# rubika-group-manager 🛡️

Full-featured group management bot for Rubika, including ban, mute, welcome messages, content filtering, user stats, and behavioral control.  
Built with the powerful `rubpy` library for direct access to Rubika’s API—no middle layers, fast, and fully extensible.

## 📦 Features

- Ban and mute users via commands  
- Auto-welcome with customizable messages  
- Filter links, voice messages, stories, long texts, and banned words  
- Track user stats, message counts, warnings  
- JSON-based data storage  
- Modular architecture ready for dashboard integration

## 🚀 Installation

```bash
pip install -r requirements.txt  
python main.py
```

## 🧪 Usage Example (rubpy)

```python
from rubpy import Client, filters  
from rubpy.types import Update  

bot = Client(name='rubpy')  

@bot.on_message_updates(filters.text)  
async def updates(update: Update):  
  await update.reply("Test message from PeTeR 😎")  

bot.run()
```

## 📜 User and Admin Command List
[`Source Commands
`](./docs/help.md) 


## 📄 License


This project is released under the MIT License. See [`LICENSE`](./LICENSE) for details.

