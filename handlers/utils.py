
"""
Combined handler for: Rules, Blacklist, AFK, Filters, Ghost Mode
"""
import time
import re
from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import get_conn
from helpers import admin_check, reply

# ─── RULES ────────────────────────────────────────────────────────────────────

async def setrules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /setrules <text>"); return
    text = " ".join(context.args)
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO rules (chat_id, rules_text) VALUES (?,?)", (chat_id, text))
    conn.commit()
    await reply(update, "✅ Rules have been set.")

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    row = conn.execute("SELECT rules_text FROM rules WHERE chat_id=?", (chat_id,)).fetchone()
    if not row:
        await reply(update, "ℹ️ No rules set for this group."); return
    await reply(update, f"📜 <b>Group Rules:</b>\n\n{row['rules_text']}", parse_mode="HTML")

async def clearrules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM rules WHERE chat_id=?", (chat_id,))
    conn.commit()
    await reply(update, "✅ Rules cleared.")

# ─── BLACKLIST ─────────────────────────────────────────────────────────────────

async def addblack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /addblack <word>"); return
    word = " ".join(context.args).lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO blacklist (chat_id, word) VALUES (?,?)", (chat_id, word))
    conn.commit()
    await reply(update, f"✅ '<code>{word}</code>' added to blacklist.", parse_mode="HTML")

async def rmblack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /rmblack <word>"); return
    word = " ".join(context.args).lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM blacklist WHERE chat_id=? AND word=?", (chat_id, word))
    conn.commit()
    await reply(update, f"✅ '<code>{word}</code>' removed from blacklist.", parse_mode="HTML")

async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT word FROM blacklist WHERE chat_id=?", (chat_id,)).fetchall()
    if not rows:
        await reply(update, "✅ Blacklist is empty."); return
    text = "🚫 <b>Blacklisted words:</b>\n" + "\n".join(f"• <code>{r['word']}</code>" for r in rows)
    await reply(update, text, parse_mode="HTML")

async def check_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text: return
    from helpers import is_admin
    if await is_admin(update, context):
        return
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT word FROM blacklist WHERE chat_id=?", (chat_id,)).fetchall()
    text_lower = msg.text.lower()
    for row in rows:
        if row["word"] in text_lower:
            try:
                await msg.delete()
                warn = await context.bot.send_message(
                    chat_id, f"⚠️ Message deleted: contains blacklisted word."
                )
                import asyncio; await asyncio.sleep(5); await warn.delete()
            except Exception:
                pass
            return

# ─── AFK ──────────────────────────────────────────────────────────────────────

async def afk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    reason = " ".join(context.args) if context.args else "AFK"
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO afk (user_id, chat_id, reason, since) VALUES (?,?,?,?)",
        (user.id, chat_id, reason, time.time())
    )
    conn.commit()
    await reply(update, f"😴 {user.first_name} is now AFK.\n📝 Reason: {reason}")

async def check_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text: return
    user = update.effective_user
    chat_id = update.effective_chat.id
    conn = get_conn()

    # Return from AFK if user sends a message
    was_afk = conn.execute(
        "SELECT * FROM afk WHERE user_id=? AND chat_id=?", (user.id, chat_id)
    ).fetchone()
    if was_afk:
        conn.execute("DELETE FROM afk WHERE user_id=? AND chat_id=?", (user.id, chat_id))
        conn.commit()
        elapsed = int(time.time() - was_afk["since"])
        mins, secs = divmod(elapsed, 60)
        await msg.reply_text(f"👋 Welcome back {user.first_name}! You were AFK for {mins}m {secs}s.")

    # Check if message mentions an AFK user
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_id = msg.reply_to_message.from_user.id
        afk_row = conn.execute(
            "SELECT * FROM afk WHERE user_id=? AND chat_id=?", (target_id, chat_id)
        ).fetchone()
        if afk_row:
            elapsed = int(time.time() - afk_row["since"])
            mins, secs = divmod(elapsed, 60)
            name = msg.reply_to_message.from_user.first_name
            await msg.reply_text(
                f"😴 {name} is currently AFK ({mins}m {secs}s ago).\n📝 Reason: {afk_row['reason']}"
            )

# ─── FILTERS ──────────────────────────────────────────────────────────────────

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if not context.args:
        await reply(update, "Usage: /filter <keyword> (reply to message)"); return
    keyword = context.args[0].lower()
    reply_text = None
    file_id = None
    file_type = None
    if msg.reply_to_message:
        rm = msg.reply_to_message
        if rm.text:
            reply_text = rm.text
        elif rm.sticker:
            file_id = rm.sticker.file_id
            file_type = "sticker"
        elif rm.photo:
            file_id = rm.photo[-1].file_id
            file_type = "photo"
            reply_text = rm.caption
        elif rm.animation:
            file_id = rm.animation.file_id
            file_type = "animation"
    else:
        reply_text = " ".join(context.args[1:]) or keyword

    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO filters (chat_id, keyword, reply, file_id, file_type) VALUES (?,?,?,?,?)",
        (chat_id, keyword, reply_text, file_id, file_type)
    )
    conn.commit()
    await reply(update, f"✅ Filter for '<code>{keyword}</code>' set.", parse_mode="HTML")

async def stop_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /stop <keyword>"); return
    keyword = " ".join(context.args).lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM filters WHERE chat_id=? AND keyword=?", (chat_id, keyword))
    conn.commit()
    await reply(update, f"✅ Filter '<code>{keyword}</code>' removed.", parse_mode="HTML")

async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text: return
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT * FROM filters WHERE chat_id=?", (chat_id,)).fetchall()
    text_lower = msg.text.lower()
    for row in rows:
        if row["keyword"] in text_lower:
            try:
                if row["file_type"] == "sticker":
                    await context.bot.send_sticker(chat_id, row["file_id"])
                elif row["file_type"] == "photo":
                    await context.bot.send_photo(chat_id, row["file_id"], caption=row["reply"])
                elif row["file_type"] == "animation":
                    await context.bot.send_animation(chat_id, row["file_id"])
                elif row["reply"]:
                    await context.bot.send_message(chat_id, row["reply"])
            except Exception:
                pass
            break

# ─── GHOST MODE ───────────────────────────────────────────────────────────────

async def ghostmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /ghostmode on|off"); return
    state = 1 if context.args[0].lower() == "on" else 0
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO ghost_mode (chat_id, enabled) VALUES (?,?)",
        (chat_id, state)
    )
    conn.commit()
    await reply(update, f"👻 Ghost mode {'enabled' if state else 'disabled'}.")

async def check_ghost_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg: return
    if not (msg.new_chat_members or msg.left_chat_member):
        return
    chat_id = update.effective_chat.id
    conn = get_conn()
    row = conn.execute("SELECT enabled FROM ghost_mode WHERE chat_id=?", (chat_id,)).fetchone()
    if row and row["enabled"]:
        try:
            await msg.delete()
        except Exception:
            pass

def register(app):
    # Rules
    app.add_handler(CommandHandler("setrules", setrules_command))
    app.add_handler(CommandHandler("rules", rules_command))
    app.add_handler(CommandHandler("clearrules", clearrules_command))
    # Blacklist
    app.add_handler(CommandHandler("addblack", addblack_command))
    app.add_handler(CommandHandler("rmblack", rmblack_command))
    app.add_handler(CommandHandler("blacklist", blacklist_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_blacklist), group=3)
    # AFK
    app.add_handler(CommandHandler("afk", afk_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_afk), group=4)
    # Filters
    app.add_handler(CommandHandler("filter", filter_command))
    app.add_handler(CommandHandler("stop", stop_filter_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_filters), group=5)
    # Ghost mode
    app.add_handler(CommandHandler("ghostmode", ghostmode_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, check_ghost_mode), group=6)
