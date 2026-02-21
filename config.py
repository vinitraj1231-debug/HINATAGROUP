import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8564523423:AAE8FMTtmRfae7R-hHLYC06F5eeVJIJACYs")
OWNER_ID = int(os.getenv("OWNER_ID", "8373641692"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "@narzofamily")
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1003730763488"))  # Optional log channel ID
DATABASE_URL = os.getenv("DATABASE_URL", "nomade.db")

