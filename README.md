<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=150&section=header&text=LionX%20Bot&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=38" alt="LionX Bot"/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=17&pause=1000&color=F7B731&center=true&vCenter=true&width=440&lines=Telegram+Bot+for+LionX+Engine;Keys+%E2%80%A2+Rewards+%E2%80%A2+Community;Built+with+Python+%2B+aiogram" alt="Typing SVG"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=flat-square&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)](LICENSE)

[<img src="assets/icons/megaphone.svg" width="16" height="16" alt=""/> Channel](https://t.me/LionX_Engine) • [<img src="assets/icons/comment-discussion.svg" width="16" height="16" alt=""/> Support](https://t.me/LionXsupport_bot) • [<img src="assets/icons/book.svg" width="16" height="16" alt=""/> Docs](#-table-of-contents)

</div>

---

## <img src="assets/icons/book.svg" width="20" height="20" alt=""/> Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Bot Commands](#bot-commands)
- [User Guide](#user-guide)
- [Admin Guide](#admin-guide)
- [Points Economy](#points-economy)
- [Key System](#key-system)
- [How It Works](#how-it-works)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Support](#support)

---

## <img src="assets/icons/star.svg" width="20" height="20" alt=""/> Features

| Feature | Description |
|---|---|
| <img src="assets/icons/lock.svg" width="18" height="18" alt=""/> **Channel Gate** | Users must join the official channel before using the bot |
| <img src="assets/icons/key.svg" width="18" height="18" alt=""/> **Daily Free Key** | Every user can claim a free 12-hour key once every 24 hours |
| <img src="assets/icons/star.svg" width="18" height="18" alt=""/> **Points System** | Earn points via invites and daily streaks |
| <img src="assets/icons/tag.svg" width="18" height="18" alt=""/> **Key Shop** | Spend points on 1 / 3 / 7 / 15 / 30-day keys |
| <img src="assets/icons/people.svg" width="18" height="18" alt=""/> **Referral Program** | Invite friends with your personal link, earn +1 point each |
| <img src="assets/icons/flame.svg" width="18" height="18" alt=""/> **Daily Streaks** | Check in daily for points + milestone bonuses |
| <img src="assets/icons/graph.svg" width="18" height="18" alt=""/> **Profile Stats** | Points, invites, streak and key history at a glance |
| <img src="assets/icons/pencil.svg" width="18" height="18" alt=""/> **Report System** | Users can send reports; admins reply directly |
| <img src="assets/icons/upload.svg" width="18" height="18" alt=""/> **File Distribution** | Admins upload files (APK, etc.), users download in-bot |
| <img src="assets/icons/megaphone.svg" width="18" height="18" alt=""/> **Broadcast** | Admins can message all users at once |
| <img src="assets/icons/tools.svg" width="18" height="18" alt=""/> **Maintenance Mode** | One-tap toggle to pause the bot for everyone |
| <img src="assets/icons/video.svg" width="18" height="18" alt=""/> **Rich Media Menus** | Video-powered welcome and menu screens |

---

## <img src="assets/icons/tools.svg" width="20" height="20" alt=""/> Tech Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=python,firebase&theme=dark" alt="Python Firebase" height="42"/>
<img src="https://cdn.simpleicons.org/telegram/2CA5E0" alt="Telegram" height="38"/>

</div>

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Core language |
| **[aiogram 3.x](https://docs.aiogram.dev/)** | Async Telegram Bot API framework |
| **[Firebase Firestore](https://firebase.google.com/)** | Cloud NoSQL database (via REST API) |
| **aiohttp** | Async HTTP client for Firebase calls |
| **aiogram FSM** | Conversation state management (in-memory) |

---

## <img src="assets/icons/file-directory.svg" width="20" height="20" alt=""/> Project Structure

`
lionxbot/
├── bot.py  #  The entire bot — handlers, keyboards, Firebase client
├── requirements.txt  #  Python dependencies
├── .gitignore  #  Git ignore rules
└── README.md  #  You are here
`

> `bot.py` is a single-file application (~1,600 lines) containing the Firebase
> client, all conversation handlers, inline keyboards, the admin panel and the
> entry point. Simple to deploy, easy to reason about.

---

## <img src="assets/icons/rocket.svg" width="20" height="20" alt=""/> Quick Start

### Prerequisites

- Python **3.10** or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Firebase project with **Firestore** enabled

### 1. Clone the repository

`bash
git clone https://github.com/lionxengine/lionxbot.git
cd lionxbot
`

### 2. Install dependencies

`bash
pip install -r requirements.txt
`

### 3. Configure the bot

Open `bot.py` and set your credentials in the config section:

`python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # from @BotFather
FIREBASE_PROJECT_ID = "your-project-id"  # Firebase project ID
FIREBASE_API_KEY = "YOUR_FIREBASE_API_KEY" # Firebase Web API key
ADMIN_ID = 123456789  # your Telegram user ID
CHANNEL_USERNAME = "YourChannelUsername"  # channel users must join
`

>  **Security tip:** never commit real tokens to a public repository.
> Use environment variables or a `.env` file (already git-ignored) instead.

### 4. Run the bot

`bash
python bot.py
`

You should see log output and the bot will start polling Telegram for updates:

`
INFO:aiogram.dispatcher:Start polling
`

 **Done!** Open Telegram, find your bot and press **/start**.

---

## <img src="assets/icons/gear.svg" width="20" height="20" alt=""/> Configuration

All runtime settings live at the top of `bot.py`:

| Setting | Description | Default |
|---|---|---|
| `TOKEN` | Telegram bot token | — |
| `ADMIN_ID` | Telegram ID of the bot admin | — |
| `CHANNEL_USERNAME` | Required channel (without @) | LionX_Engine |
| `FIREBASE_PROJECT_ID` | Firestore project ID | lionengine |
| `FIREBASE_API_KEY` | Firebase Web API key | — |
| `DAILY_KEY_VALID_HOURS` | Free daily key validity (Default: `12` hours`) | — |
| `RESELLER_NAME` | Display name of the reseller | Khalid Khan |

### Key pricing (`KEY_COSTS`)

| Duration | Cost |
|---|---|
| 1 Day | 5 points |
| 3 Days | 8 points |
| 7 Days | 15 points |
| 15 Days | 25 points |
| 30 Days | 40 points |

---

## <img src="assets/icons/terminal.svg" width="20" height="20" alt=""/> Bot Commands

| Command | Who | Description |
|---|---|---|
| `/start` | Everyone | Start the bot / open the main menu (supports invite links: `/start <user_id>`) |
| `/admin` | Admin only | Open the admin control panel |
| `/resetdaily` | Admin only | Reset daily-key claims for all users |

---

## <img src="assets/icons/person.svg" width="20" height="20" alt=""/> User Guide

### Getting started
1. Press **/start**
2. Join the official channel  and tap **"I've Joined"**
3. Accept the terms  — the main menu opens 

###  Claiming your free daily key
1. Tap ** Claim Daily Key**
2. Press ** Confirm** — the 12-hour timer starts *immediately*
3. Copy your key with ** Copy Key**
4. Come back after 24 hours for the next one ⏰

###  Earning points
| Action | Reward |
|---|---|
| Invite a friend (they join via your link) | **+1 point** per invite |
| Daily streak check-in | **+points** every day |
| 6-day streak | **+3 bonus** points |
| 15-day streak | **+5 bonus** points |
| 30-day streak | **+10 bonus** points |

###  Generating a key
1. Open ** Generate Key**
2. Pick a duration — **1 / 3 / 7 / 15 / 30 Days**
3. Points are deducted and your key is created instantly
4. Keys look like `LIONX-XXXXX-XXXXX-XXXXX` and bind to **one device (HWID)**

###  Inviting friends
Tap **Invite** to get your personal referral link and share it anywhere with ** Share**.

###  Reporting an issue
Use **Report** in the menu, describe your problem, and the admin can reply to you directly inside the bot.

---

## <img src="assets/icons/shield-check.svg" width="20" height="20" alt=""/> Admin Guide

Open the panel with **/admin**:

| Action | What it does |
|---|---|
| <img src="assets/icons/megaphone.svg" width="18" height="18" alt=""/> **Broadcast** | Send a message to every bot user |
| <img src="assets/icons/upload.svg" width="18" height="18" alt=""/> **Add File** | Upload a file (e.g. APK) for users to download |
| **List Files** | View / manage distributed files |
| <img src="assets/icons/people.svg" width="18" height="18" alt=""/> **User Stats** | Total users, points and activity overview |
| <img src="assets/icons/tools.svg" width="18" height="18" alt=""/> **Maintenance Mode** | Toggle — pauses the bot for everyone except admin |
| **Reset All Daily Keys** | Let everyone claim the daily key again |
| **Reply** | Answer user reports one-to-one |

---

## <img src="assets/icons/graph.svg" width="20" height="20" alt=""/> Points Economy

`
Invite friend  ──→  +1 point ──→  Key Shop  ──→  LIONX-XXXXX-XXXXX-XXXXX
Daily streak  ──→  +points ─┘  (1/3/7/15/30-day durations)
Milestones  ──→  bonus points
`

Points, invites, streaks and key history are stored per-user in Firestore,
so balances survive restarts.

---

## <img src="assets/icons/key.svg" width="20" height="20" alt=""/> Key System

- **Format:** `LIONX-XXXXX-XXXXX-XXXXX` (random, uppercase alphanumeric)
- **Daily key:** free, valid `12` hours from the moment you confirm, one claim per 24h
- **Paid keys:** bought with points; expiry starts on **device activation (HWID bind)**
- **Binding:** each key locks to a single device — it can't be shared
- **Storage:** every key is saved to the Firestore `keys` collection for the panel/app to verify

---

## <img src="assets/icons/cpu.svg" width="20" height="20" alt=""/> How It Works

`
         ┌──────────┐
         │ Telegram │
         │   User   │
         └────┬─────┘
              │ /start
              ▼
 ┌──────────────────────┐
 │  LionX Bot (aiogram) │
 │ Channel │ Points │   │
 │  Gate   │Streak  │   │
 │ Invite  │ Report │   │
 │ System  │ &Reply │   │
 │ Key Engine │ Admin   │
 │ LIONX-XXXX │ Panel   │
 └──────┬───────────────┘
        │ Firestore API
        ▼
   ┌──────────────┐
   │   Firebase   │
   │  users/keys  │
   └──────────────┘
`


1. **Gate** — every interaction first checks channel membership.
2. **Identity** — users are stored in Firestore (`users` collection) with points, invites, streaks and claim timestamps.
3. **Keys** — generated keys go to the `keys` collection with duration, owner and HWID binding info.
4. **Polling** — the bot uses long polling (`dp.start_polling`), so no webhook server or open ports are needed.

---

## <img src="assets/icons/cloud.svg" width="20" height="20" alt=""/> Deployment

### Run in the background (Linux)

`bash
nohup python bot.py > bot.log 2>&1 &
`

### Run with systemd

`ini
[Unit]
Description=LionX Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/lionxbot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
`

### Run with Docker

`dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py .
CMD ["python", "bot.py"]
`

`bash
docker build -t lionxbot .
docker run -d --restart unless-stopped --name lionxbot lionxbot
`

---

## <img src="assets/icons/git-pull-request.svg" width="20" height="20" alt=""/> Contributing

This is a private project, but suggestions are welcome:

1. Fork the repo 
2. Create a feature branch (`git checkout -b feature/my-idea`)
3. Commit your changes (`git commit -m "Add my idea"`)
4. Open a Pull Request 

---

## <img src="assets/icons/comment-discussion.svg" width="20" height="20" alt=""/> Support

-  **Channel:** [@LionX_Engine](https://t.me/LionX_Engine)
-  **Support bot:** [@LionXsupport_bot](https://t.me/LionXsupport_bot)
-  **Issues:** use the [Issues tab](https://github.com/lionxengine/lionxbot/issues)

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=90&section=footer" alt="footer"/>

**Built with <img src="assets/icons/heart.svg" width="16" height="16" alt=""/> for the LionX community**

</div>
