# 🤖 elitegrouphelp Bot — Advanced Telegram Group Manager

A fully-featured, production-ready Telegram group management bot with **20 feature modules**.

---

## ⚡ Quick Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set environment variables
```bash
export BOT_TOKEN="your_bot_token_from_BotFather"
export OWNER_ID="your_telegram_user_id"
export SUPPORT_CHAT="@YourSupportChannel"
export LOG_CHANNEL="-100xxxxxxxxx"   # Optional
```
Or edit `config.py` directly.

### 3. Run the bot
```bash
python main.py
```

---

## 📦 Features

| Module | Commands |
|--------|----------|
| 👋 **Welcome** | `/setwelcome`, `/welcome on\|off`, `/cleanwelcome on\|off` |
| 🔒 **Locks** | `/lock`, `/unlock`, `/locks`, `/locklanguage`, `/unlocklanguage`, `/language_locks`, `/available_languages` |
| 👮 **Moderation** | `/kick`, `/ban`, `/unban`, `/mute`, `/unmute`, `/warn`, `/warns`, `/resetwarns`, `/promote`, `/demote`, `/unbanall` |
| 📊 **Activity** | `/topusers`, `/userstats` |
| 📜 **Rules** | `/setrules`, `/rules`, `/clearrules` |
| 🚫 **Blacklist** | `/addblack`, `/rmblack`, `/blacklist` |
| 💤 **AFK** | `/afk` |
| ⚙️ **Filters** | `/filter`, `/stop` |
| 👻 **Ghost Mode** | `/ghostmode on\|off` |
| 📝 **Notes** | `/setnote`, `/delnote`, `/notes`, `#note_name` |
| 📣 **Force-Sub** | `/addfsub`, `/removefsub`, `/fsublist` |
| 🚨 **Anti-Cheater** | Automatic (no commands) |
| ➕ **Force-Add** | `/setforceadd`, `/getforceadd` |
| 🎮 **Life Game** | `/startlife`, `/profile`, `/setbio`, `/rob`, `/gift`, `/marry`, `/bet`, `/betstats` |
| 🎴 **Sticker Prot** | `/stickers approve\|disapprove\|reset`, `/restrict stickers newusers <hours>` |
| 🔗 **Bio Filter** | `/bio_links on\|off`, `/bio_usernames on\|off` |
| 🗑️ **Remove Deleted** | `/remove_deleted` |
| 🔔 **Tag All** | `/tagall [message]` |
| ✅ **Auto Accept** | `/acceptall on\|off` |
| ⭐ **Support** | Configurable via `SUPPORT_CHAT` |

---

## 🔧 Configuration (`config.py`)

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789        # Your Telegram user ID
SUPPORT_CHAT = "@YourChat"  # Support group/channel username
LOG_CHANNEL = 0             # Optional: channel ID to log events
DATABASE_URL = "nomade.db"  # SQLite database path
```

---

## 🌟 Welcome Message Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{first_name}` | User's first name |
| `{username}` | @username or first name |
| `{id}` | User ID |
| `{mention}` | Clickable HTML mention |
| `{title}` | Group name |

---

## 🔒 Lock Types

| Type | Blocks |
|------|--------|
| `url` | Links and URLs |
| `forward` | Forwarded messages |
| `sticker` | All stickers |
| `media` | Photos, videos, GIFs |
| `username` | @mentions |
| `language` | Specific languages |

---

## 🎮 Life Game

- Start with **100 coins**
- **Rob** others (60% success, 40% get caught and fined)
- **Gift** 10 coins to friends
- **Marry** other users
- **Bet** coins for luck 🎰
- Level up automatically as you earn coins

---

## 🗄️ Database

SQLite database (`nomade.db`) — auto-created on first run. For production, consider migrating to PostgreSQL.

---

## 🚀 Deployment

### Systemd service (Linux)
```ini
[Unit]
Description=Nomade Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nomade_bot
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## 📝 Notes

- Bot must be **admin** in the group for most features to work
- For **promote/demote**, bot needs the "Add Admins" permission
- For **join requests**, enable "Approve Members" in group settings
- **Anti-cheater** auto-demotes admins who kick/ban >10 users in 24h
- Tag All may be slow in large groups due to Telegram rate limits
