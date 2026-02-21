
#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
   🤖 NOMADE BOT — Advanced Telegram Group Manager
   All features: Welcome, Locks, Moderation, Rules,
   Blacklist, AFK, Filters, Ghost Mode, Notes, FSub,
   Anti-Cheater, Force-Add, Life Game, Sticker Prot,
   Bio Filter, Remove Deleted, Tag All, Accept All
╚══════════════════════════════════════════════╝
"""
import logging
from telegram.ext import Application
from config import BOT_TOKEN
from database import init_db
from handlers import register_all

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Initialize database
    init_db()

    # Build application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register all handlers
    register_all(app)

    logger.info("✅ Nomade Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
