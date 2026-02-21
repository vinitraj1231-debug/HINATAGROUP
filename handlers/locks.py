
import re
from telegram import Update, ChatPermissions, Message
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import get_conn
from helpers import admin_check, reply

LOCK_TYPES = ["url", "forward", "sticker", "media", "username", "language"]

AVAILABLE_LANGUAGES = [
    "arabic", "chinese", "cyrillic", "hindi", "japanese",
    "korean", "persian", "thai", "turkish", "urdu",
]

LANG_PATTERNS = {
    "arabic":   re.compile(r"[\u0600-\u06FF]"),
    "chinese":  re.compile(r"[\u4E00-\u9FFF]"),
    "cyrillic": re.compile(r"[\u0400-\u04FF]"),
    "hindi":    re.compile(r"[\u0900-\u097F]"),
    "japanese": re.compile(r"[\u3040-\u30FF\u31F0-\u31FF]"),
    "korean":   re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]"),
    "persian":  re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]"),
    "thai":     re.compile(r"[\u0E00-\u0E7F]"),
    "turkish":  re.compile(r"[İıĞğŞşÇçÖöÜü]"),
    "urdu":     re.compile(r"[\u0600-\u06FF\u0750-\u077F]"),
}

async def lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, f"Usage: /lock <type>\nTypes: {', '.join(LOCK_TYPES)}"); return
    lock_type = context.args[0].lower()
    if lock_type not in LOCK_TYPES:
        await reply(update, f"❌ Unknown lock type. Available: {', '.join(LOCK_TYPES)}"); return
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO locks (chat_id, lock_type) VALUES (?,?)",
        (chat_id, lock_type)
    )
    conn.commit()
    await reply(update, f"🔒 Lock <b>{lock_type}</b> enabled.", parse_mode="HTML")

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, f"Usage: /unlock <type>"); return
    lock_type = context.args[0].lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM locks WHERE chat_id=? AND lock_type=?", (chat_id, lock_type))
    conn.commit()
    await reply(update, f"🔓 Lock <b>{lock_type}</b> disabled.", parse_mode="HTML")

async def locks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,)).fetchall()
    active = [r["lock_type"] for r in rows]
    if not active:
        await reply(update, "🔓 No active locks in this group."); return
    text = "🔒 <b>Active Locks:</b>\n" + "\n".join(f"• {l}" for l in active)
    await reply(update, text, parse_mode="HTML")

async def locklanguage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /locklanguage <language>"); return
    lang = context.args[0].lower()
    if lang not in LANG_PATTERNS:
        await reply(update, f"❌ Unknown language. Available: {', '.join(LANG_PATTERNS.keys())}"); return
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO language_locks (chat_id, language) VALUES (?,?)", (chat_id, lang))
    conn.commit()
    await reply(update, f"🔒 Language <b>{lang}</b> locked.", parse_mode="HTML")

async def unlocklanguage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /unlocklanguage <language>"); return
    lang = context.args[0].lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM language_locks WHERE chat_id=? AND language=?", (chat_id, lang))
    conn.commit()
    await reply(update, f"🔓 Language <b>{lang}</b> unlocked.", parse_mode="HTML")

async def language_locks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT language FROM language_locks WHERE chat_id=?", (chat_id,)).fetchall()
    langs = [r["language"] for r in rows]
    if not langs:
        await reply(update, "🔓 No languages locked."); return
    await reply(update, "🔒 Locked languages:\n" + "\n".join(f"• {l}" for l in langs))

async def available_languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, "🌐 Available languages to lock:\n" + "\n".join(f"• {l}" for l in LANG_PATTERNS.keys()))

async def check_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = update.effective_message
    if not msg or not update.effective_chat:
        return
    from helpers import is_admin
    user = update.effective_user
    if not user:
        return
    if await is_admin(update, context, user.id):
        return
    chat_id = update.effective_chat.id
    conn = get_conn()
    lock_rows = conn.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,)).fetchall()
    active_locks = {r["lock_type"] for r in lock_rows}
    text = msg.text or msg.caption or ""

    async def delete_and_warn(reason):
        try:
            await msg.delete()
            warn_msg = await context.bot.send_message(chat_id, f"🔒 {reason}")
            import asyncio
            await asyncio.sleep(5)
            await warn_msg.delete()
        except Exception:
            pass

    if "url" in active_locks:
        url_pattern = re.compile(r"https?://\S+|t\.me/\S+|www\.\S+")
        if url_pattern.search(text):
            await delete_and_warn("Links are locked in this group.")
            return

    if "forward" in active_locks and msg.forward_date:
        await delete_and_warn("Forwarded messages are locked in this group.")
        return

    if "sticker" in active_locks and msg.sticker:
        await delete_and_warn("Stickers are locked in this group.")
        return

    if "media" in active_locks and (msg.photo or msg.video or msg.animation or msg.document):
        await delete_and_warn("Media is locked in this group.")
        return

    if "username" in active_locks:
        if re.search(r"@\w+", text):
            await delete_and_warn("Username mentions are locked in this group.")
            return

    if "language" in active_locks:
        lang_rows = conn.execute("SELECT language FROM language_locks WHERE chat_id=?", (chat_id,)).fetchall()
        for row in lang_rows:
            pattern = LANG_PATTERNS.get(row["language"])
            if pattern and pattern.search(text):
                await delete_and_warn(f"Messages in {row['language']} are locked in this group.")
                return

def register(app):
    app.add_handler(CommandHandler("lock", lock_command))
    app.add_handler(CommandHandler("unlock", unlock_command))
    app.add_handler(CommandHandler("locks", locks_command))
    app.add_handler(CommandHandler("locklanguage", locklanguage_command))
    app.add_handler(CommandHandler("unlocklanguage", unlocklanguage_command))
    app.add_handler(CommandHandler("language_locks", language_locks_command))
    app.add_handler(CommandHandler("available_languages", available_languages_command))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_locks), group=2)
