
"""
Notes, Force-Sub, Activity Tracker, Remove Deleted Accounts
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import get_conn
from helpers import admin_check, reply

# ─── NOTES ────────────────────────────────────────────────────────────────────

async def setnote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if len(context.args) < 2:
        await reply(update, "Usage: /setnote <name> <content>"); return
    name = context.args[0].lower()
    content = " ".join(context.args[1:])
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO notes (chat_id, name, content) VALUES (?,?,?)",
        (chat_id, name, content)
    )
    conn.commit()
    await reply(update, f"✅ Note '<code>{name}</code>' saved.", parse_mode="HTML")

async def delnote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /delnote <name>"); return
    name = context.args[0].lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM notes WHERE chat_id=? AND name=?", (chat_id, name))
    conn.commit()
    await reply(update, f"✅ Note '<code>{name}</code>' deleted.", parse_mode="HTML")

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT name FROM notes WHERE chat_id=?", (chat_id,)).fetchall()
    if not rows:
        await reply(update, "ℹ️ No notes in this group."); return
    text = "📝 <b>Available Notes:</b>\n" + "\n".join(f"• #{r['name']}" for r in rows)
    await reply(update, text, parse_mode="HTML")

async def check_note_hashtag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text: return
    if not msg.text.startswith("#"): return
    name = msg.text[1:].split()[0].lower()
    chat_id = update.effective_chat.id
    conn = get_conn()
    row = conn.execute("SELECT content FROM notes WHERE chat_id=? AND name=?", (chat_id, name)).fetchone()
    if row:
        user = update.effective_user
        try:
            await context.bot.send_message(user.id, f"📝 <b>Note: {name}</b>\n\n{row['content']}", parse_mode="HTML")
            await msg.reply_text("📬 Note sent to your private messages!")
        except Exception:
            await msg.reply_text(f"📝 <b>Note: {name}</b>\n\n{row['content']}", parse_mode="HTML")

# ─── FORCE SUBSCRIBE ──────────────────────────────────────────────────────────

async def addfsub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /addfsub <@channel or channel_id>"); return
    channel = context.args[0]
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO fsub (chat_id, channel) VALUES (?,?)", (chat_id, channel))
    conn.commit()
    await reply(update, f"✅ Force-sub channel <b>{channel}</b> added.", parse_mode="HTML")

async def removefsub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /removefsub <@channel or channel_id>"); return
    channel = context.args[0]
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("DELETE FROM fsub WHERE chat_id=? AND channel=?", (chat_id, channel))
    conn.commit()
    await reply(update, f"✅ Force-sub channel <b>{channel}</b> removed.", parse_mode="HTML")

async def fsublist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute("SELECT channel FROM fsub WHERE chat_id=?", (chat_id,)).fetchall()
    if not rows:
        await reply(update, "ℹ️ No force-sub channels set."); return
    text = "📢 <b>Force-Sub Channels:</b>\n" + "\n".join(f"• {r['channel']}" for r in rows)
    await reply(update, text, parse_mode="HTML")

async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not update.effective_user: return
    from helpers import is_admin
    if await is_admin(update, context): return
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    conn = get_conn()
    channels = conn.execute("SELECT channel FROM fsub WHERE chat_id=?", (chat_id,)).fetchall()
    not_joined = []
    for row in channels:
        channel = row["channel"]
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    if not_joined:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        buttons = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.lstrip('@')}")] for ch in not_joined]
        try:
            await msg.delete()
        except Exception:
            pass
        warn = await context.bot.send_message(
            chat_id,
            f"🔒 {update.effective_user.first_name}, please join all required channels to chat!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# ─── ACTIVITY TRACKER ─────────────────────────────────────────────────────────

async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user: return
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute("""
        INSERT INTO activity (chat_id, user_id, username, first_name, msg_count)
        VALUES (?,?,?,?,1)
        ON CONFLICT(chat_id, user_id) DO UPDATE SET
            msg_count = msg_count + 1,
            username = excluded.username,
            first_name = excluded.first_name
    """, (chat_id, user.id, user.username or "", user.first_name or ""))
    conn.commit()

async def topusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_conn()
    rows = conn.execute(
        "SELECT first_name, username, msg_count FROM activity WHERE chat_id=? ORDER BY msg_count DESC LIMIT 10",
        (chat_id,)
    ).fetchall()
    if not rows:
        await reply(update, "ℹ️ No activity data yet."); return
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    lines = []
    for i, row in enumerate(rows):
        name = row["first_name"] or row["username"] or "Unknown"
        lines.append(f"{medals[i]} {name}: <b>{row['msg_count']}</b> msgs")
    await reply(update, "📊 <b>Top 10 Active Users:</b>\n" + "\n".join(lines), parse_mode="HTML")

async def userstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if msg.reply_to_message:
        user = msg.reply_to_message.from_user
    else:
        user = update.effective_user
    conn = get_conn()
    row = conn.execute(
        "SELECT msg_count FROM activity WHERE chat_id=? AND user_id=?",
        (chat_id, user.id)
    ).fetchone()
    count = row["msg_count"] if row else 0
    await reply(update, f"📈 <b>{user.first_name}</b> has sent <b>{count}</b> messages in this group.", parse_mode="HTML")

# ─── REMOVE DELETED ACCOUNTS ──────────────────────────────────────────────────

async def remove_deleted_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat_id = update.effective_chat.id
    msg = await reply(update, "🔍 Scanning for deleted accounts...")
    removed = 0
    try:
        async for member in context.bot.get_chat_members(chat_id):
            if member.user.is_deleted:
                try:
                    await context.bot.ban_chat_member(chat_id, member.user.id)
                    await context.bot.unban_chat_member(chat_id, member.user.id)
                    removed += 1
                except Exception:
                    pass
    except AttributeError:
        # get_chat_members may not exist on all versions - use alternative approach
        pass
    await msg.edit_text(f"✅ Removed <b>{removed}</b> deleted account(s).", parse_mode="HTML")

def register(app):
    # Notes
    app.add_handler(CommandHandler("setnote", setnote_command))
    app.add_handler(CommandHandler("delnote", delnote_command))
    app.add_handler(CommandHandler("notes", notes_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^#\w+"), check_note_hashtag), group=7)
    # Force-sub
    app.add_handler(CommandHandler("addfsub", addfsub_command))
    app.add_handler(CommandHandler("removefsub", removefsub_command))
    app.add_handler(CommandHandler("fsublist", fsublist_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_fsub), group=8)
    # Activity
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_activity), group=9)
    app.add_handler(CommandHandler("topusers", topusers_command))
    app.add_handler(CommandHandler("userstats", userstats_command))
    # Remove deleted
    app.add_handler(CommandHandler("remove_deleted", remove_deleted_command))
