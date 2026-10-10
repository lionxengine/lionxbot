<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=220&section=header&text=LionX%20Bot&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=38" alt="LionX Bot"/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=F7B731&center=true&vCenter=true&width=600&lines=Telegram+Bot+for+LionX+Engine;Keys+%E2%80%A2+Rewards+%E2%80%A2+Community;Built+with+Python+%2B+aiogram" alt="Typing SVG"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

[📢 Channel](https://t.me/LionX_Engine) • [💬 Support](https://t.me/LionXsupport_bot) • [📖 Docs](#-table-of-contents)

</div>

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration](#️-configuration)
- [🤖 Bot Commands](#-bot-commands)
- [👤 User Guide](#-user-guide)
- [🛡️ Admin Guide](#️-admin-guide)
- [💰 Points Economy](#-points-economy)
- [🔑 Key System](#-key-system)
- [🧠 How It Works](#-how-it-works)
- [☁️ Deployment](#️-deployment)
- [🤝 Contributing](#-contributing)
- [📞 Support](#-support)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔒 **Channel Gate** | Users must join the official channel before using the bot |
| 🗝️ **Daily Free Key** | Every user can claim a free 12-hour key once every 24 hours |
| ⭐ **Points System** | Earn points via invites and daily streaks |
| 🎫 **Key Shop** | Spend points on 1 / 3 / 7 / 15 / 30-day keys |
| 👥 **Referral Program** | Invite friends with your personal link, earn +1 point each |
| 🔥 **Daily Streaks** | Check in daily for points + milestone bonuses |
| 📊 **Profile Stats** | Points, invites, streak and key history at a glance |
| 📝 **Report System** | Users can send reports; admins reply directly |
| 📁 **File Distribution** | Admins upload files (APK, etc.), users download in-bot |
| 📢 **Broadcast** | Admins can message all users at once |
| 🔧 **Maintenance Mode** | One-tap toggle to pause the bot for everyone |
| 🎬 **Rich Media Menus** | Video-powered welcome and menu screens |

---

## 🛠️ Tech Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=python,firebase&theme=dark" alt="Python Firebase" height="60"/>
<img src="https://cdn.simpleicons.org/telegram/2CA5E0" alt="Telegram" height="55"/>

</div>

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Core language |
| **[aiogram 3.x](https://docs.aiogram.dev/)** | Async Telegram Bot API framework |
| **[Firebase Firestore](https://firebase.google.com/)** | Cloud NoSQL database (via REST API) |
| **aiohttp** | Async HTTP client for Firebase calls |
| **aiogram FSM** | Conversation state management (in-memory) |

---

## 📁 Project Structure

```
lionxbot/
├── bot.py              # 🤖 The entire bot — handlers, keyboards, Firebase client
├── requirements.txt    # 📦 Python dependencies
├── .gitignore          # 🙈 Git ignore rules
└── README.md           # 📖 You are here
```

> `bot.py` is a single-file application (~1,600 lines) containing the Firebase
> client, all conversation handlers, inline keyboards, the admin panel and the
> entry point. Simple to deploy, easy to reason about.

---

## 🚀 Quick Start

### Prerequisites

- Python **3.10** or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Firebase project with **Firestore** enabled

### 1️⃣ Clone the repository

```bash
git clone https://github.com/lionxengine/lionxbot.git
cd lionxbot
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure the bot

Open `bot.py` and set your credentials in the config section:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"          # from @BotFather
FIREBASE_PROJECT_ID = "your-project-id"   # Firebase project ID
FIREBASE_API_KEY = "YOUR_FIREBASE_API_KEY" # Firebase Web API key
ADMIN_ID = 123456789                      # your Telegram user ID
CHANNEL_USERNAME = "YourChannelUsername"  # channel users must join
```

> ⚠️ **Security tip:** never commit real tokens to a public repository.
> Use environment variables or a `.env` file (already git-ignored) instead.

### 4️⃣ Run the bot

```bash
python bot.py
```

You should see log output and the bot will start polling Telegram for updates:

```
INFO:aiogram.dispatcher:Start polling
```

🎉 **Done!** Open Telegram, find your bot and press **/start**.

---

## ⚙️ Configuration

All runtime settings live at the top of `bot.py`:

| Setting | Description | Default |
|---|---|---|
| `TOKEN` | Telegram bot token | — |
| `ADMIN_ID` | Telegram ID of the bot admin | — |
| `CHANNEL_USERNAME` | Required channel (without @) | `LionX_Engine` |
| `FIREBASE_PROJECT_ID` | Firestore project ID | `lionengine` |
| `FIREBASE_API_KEY` | Firebase Web API key | — |
| `DAILY_KEY_VALID_HOURS` | Free daily key validity | `12` hours |
| `RESELLER_NAME` | Display name of the reseller | `Khalid Khan` |

### Key pricing (`KEY_COSTS`)

| Duration | Cost |
|---|---|
| 1 Day | 5 points |
| 3 Days | 8 points |
| 7 Days | 15 points |
| 15 Days | 25 points |
| 30 Days | 40 points |

---

## 🤖 Bot Commands

| Command | Who | Description |
|---|---|---|
| `/start` | Everyone | Start the bot / open the main menu (supports invite links: `/start <user_id>`) |
| `/admin` | Admin only | Open the admin control panel |
| `/resetdaily` | Admin only | Reset daily-key claims for all users |

---

## 👤 User Guide

### Getting started
1. Press **/start**
2. Join the official channel 📢 and tap **"I've Joined"**
3. Accept the terms ✅ — the main menu opens 🎬

### 🗝️ Claiming your free daily key
1. Tap **🗝️ Claim Daily Key**
2. Press **✅ Confirm** — the 12-hour timer starts *immediately*
3. Copy your key with **📋 Copy Key**
4. Come back after 24 hours for the next one ⏰

### ⭐ Earning points
| Action | Reward |
|---|---|
| Invite a friend (they join via your link) | **+1 point** per invite |
| Daily streak check-in | **+points** every day |
| 🔥 6-day streak | **+3 bonus** points |
| 🔥 15-day streak | **+5 bonus** points |
| 🔥 30-day streak | **+10 bonus** points |

### 🎫 Generating a key
1. Open **⚙️ Generate Key**
2. Pick a duration — **1 / 3 / 7 / 15 / 30 Days**
3. Points are deducted and your key is created instantly
4. Keys look like `LIONX-XXXXX-XXXXX-XXXXX` and bind to **one device (HWID)**

### 👥 Inviting friends
Tap **Invite** to get your personal referral link and share it anywhere with **📤 Share**.

### 📝 Reporting an issue
Use **Report** in the menu, describe your problem, and the admin can reply to you directly inside the bot.

---

## 🛡️ Admin Guide

Open the panel with **/admin**:

| Action | What it does |
|---|---|
| 📢 **Broadcast** | Send a message to every bot user |
| 📁 **Add File** | Upload a file (e.g. APK) for users to download |
| 📋 **List Files** | View / manage distributed files |
| 👥 **User Stats** | Total users, points and activity overview |
| 🔧 **Maintenance Mode** | Toggle — pauses the bot for everyone except admin |
| 🔄 **Reset All Daily Keys** | Let everyone claim the daily key again |
| 💬 **Reply** | Answer user reports one-to-one |

---

## 💰 Points Economy

```
Invite friend  ──→  +1 point ──→  Key Shop  ──→  LIONX-XXXXX-XXXXX-XXXXX
Daily streak   ──→  +points ─┘         (1/3/7/15/30-day durations)
Milestones     ──→  bonus points
```

Points, invites, streaks and key history are stored per-user in Firestore,
so balances survive restarts.

---

## 🔑 Key System

- **Format:** `LIONX-XXXXX-XXXXX-XXXXX` (random, uppercase alphanumeric)
- **Daily key:** free, valid `12` hours from the moment you confirm, one claim per 24h
- **Paid keys:** bought with points; expiry starts on **device activation (HWID bind)**
- **Binding:** each key locks to a single device — it can't be shared
- **Storage:** every key is saved to the Firestore `keys` collection for the panel/app to verify

---

## 🧠 How It Works

```
                    ┌──────────────┐
                    │   Telegram   │
                    │     User     │
                    └──────┬───────┘
                           │ /start, buttons
                           ▼
┌──────────────────────────────────────────────┐
│                 LionX Bot (aiogram)           │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Channel │  │  Points  │  │  Key Engine  │  │
│  │  Gate   │  │ & Streak │  │ LIONX-XXXXX  │  │
│  └─────────┘  └──────────┘  └──────────────┘  │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Invite  │  │ Reports  │  │ Admin Panel  │  │
│  │ System  │  │ & Reply  │  │  / Broadcast │  │
│  └─────────┘  └──────────┘  └──────────────┘  │
└──────────────────────┬───────────────────────┘
                       │ Firestore REST API
                       ▼
              ┌──────────────────┐
              │  Firebase        │
              │  Firestore       │
              │  users / keys    │
              └──────────────────┘
```

1. **Gate** — every interaction first checks channel membership.
2. **Identity** — users are stored in Firestore (`users` collection) with points, invites, streaks and claim timestamps.
3. **Keys** — generated keys go to the `keys` collection with duration, owner and HWID binding info.
4. **Polling** — the bot uses long polling (`dp.start_polling`), so no webhook server or open ports are needed.

---

## ☁️ Deployment

### Run in the background (Linux)

```bash
nohup python bot.py > bot.log 2>&1 &
```

### Run with systemd

```ini
[Unit]
Description=LionX Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/lionxbot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Run with Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py .
CMD ["python", "bot.py"]
```

```bash
docker build -t lionxbot .
docker run -d --restart unless-stopped --name lionxbot lionxbot
```

---

## 🤝 Contributing

This is a private project, but suggestions are welcome:

1. Fork the repo 🍴
2. Create a feature branch (`git checkout -b feature/my-idea`)
3. Commit your changes (`git commit -m "Add my idea"`)
4. Open a Pull Request 🎉

---

## 📞 Support

- 📢 **Channel:** [@LionX_Engine](https://t.me/LionX_Engine)
- 💬 **Support bot:** [@LionXsupport_bot](https://t.me/LionXsupport_bot)
- 🐛 **Issues:** use the [Issues tab](https://github.com/lionxengine/lionxbot/issues)

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer" alt="footer"/>

**🦁 Built with ❤️ for the LionX community**

</div>
