
"""
Force-Add Members System
"""
import time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler, MessageHandler, filters
from database import get_conn
from helpers import admin_check, reply

async def setforceadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /setforceadd <number>"); return
    try:
        num = int(context.args[0])
    except ValueError:
        await reply(update, "❌ Please enter a valid number."); return
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO forceadd (chat_id, required) VALUES (?,?)",
        (chat_id, num)
    )
    conn.commit()
    await reply(update, f"✅ Each user must add <b>{num}</b> member(s) to chat.", parse_mode="HTML")

async def getforceadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    row = conn.execute("SELECT required FROM forceadd WHERE chat_id=?", (chat_id,)).fetchone()
    if not row:
        await reply(update, "ℹ️ Force-add is not configured."); return
    await reply(update, f"📊 Required members to add: <b>{row['required']}</b>", parse_mode="HTML")

async def track_new_member_for_forceadd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track who invited new members."""
    msg = update.effective_message
    if not msg or not msg.new_chat_members: return
    chat_id = update.effective_chat.id
    conn = get_conn()
    row = conn.execute("SELECT required FROM forceadd WHERE chat_id=?", (chat_id,)).fetchone()
    if not row: return
    inviter = msg.from_user
    if inviter and not inviter.is_bot:
        conn.execute("""
            INSERT INTO forceadd_progress (chat_id, user_id, count) VALUES (?,?,?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET count = count + ?
        """, (chat_id, inviter.id, len(msg.new_chat_members), len(msg.new_chat_members)))
        conn.commit()

async def check_forceadd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete messages from users who haven't added enough members."""
    msg = update.effective_message
    if not msg: return
    from helpers import is_admin
    if await is_admin(update, context): return
    user = update.effective_user
    if not user: return
    chat_id = update.effective_chat.id
    conn = get_conn()
    required_row = conn.execute("SELECT required FROM forceadd WHERE chat_id=?", (chat_id,)).fetchone()
    if not required_row: return
    required = required_row["required"]
    progress_row = conn.execute(
        "SELECT count FROM forceadd_progress WHERE chat_id=? AND user_id=?",
        (chat_id, user.id)
    ).fetchone()
    current = progress_row["count"] if progress_row else 0
    if current < required:
        try:
            await msg.delete()
            warn = await context.bot.send_message(
                chat_id,
                f"⚠️ {user.first_name}, you need to add <b>{required - current}</b> more member(s) to chat!",
                parse_mode="HTML"
            )
            import asyncio; await asyncio.sleep(6); await warn.delete()
        except Exception:
            pass

def register(app):
    app.add_handler(CommandHandler("setforceadd", setforceadd_command))
    app.add_handler(CommandHandler("getforceadd", getforceadd_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_member_for_forceadd), group=12)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_forceadd), group=13)
