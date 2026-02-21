import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "@YourSupportChat")
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))  # Optional log channel ID
DATABASE_URL = os.getenv("DATABASE_URL", "nomade.db")

