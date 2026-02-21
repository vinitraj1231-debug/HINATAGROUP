"""
Sticker Protection, Bio Filter, Tag All, Accept All (Join Requests)
"""
import re
import time
from telegram import Update, ChatJoinRequest
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, ChatJoinRequestHandler, filters
from database import get_conn
from helpers import admin_check, reply

# ─── STICKER PROTECTION ────────────────────────────────────────────────────────

async def stickers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /stickers approve|disapprove|reset"); return
    action = context.args[0].lower()
    chat_id = update.effective_chat.id
    msg = update.effective_message

    if action == "reset":
        conn = get_conn()
        conn.execute("DELETE FROM sticker_prot WHERE chat_id=?", (chat_id,))
        conn.execute("DELETE FROM sticker_newuser WHERE chat_id=?", (chat_id,))
        conn.commit()
        await reply(update, "✅ All sticker settings reset.")
        return

    if action in ("approve", "disapprove"):
        if not msg.reply_to_message or not msg.reply_to_message.sticker:
            await reply(update, "❌ Reply to a sticker to approve/disapprove its pack."); return
        sticker = msg.reply_to_message.sticker
        set_name = sticker.set_name
        if not set_name:
            await reply(update, "❌ This sticker has no set."); return
        approved = 1 if action == "approve" else 0
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO sticker_prot (chat_id, set_name, approved) VALUES (?,?,?)",
            (chat_id, set_name, approved)
        )
        conn.commit()
        status = "approved ✅" if approved else "disapproved 🚫"
        await reply(update, f"Sticker pack '<code>{set_name}</code>' has been {status}.", parse_mode="HTML")

async def restrict_stickers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    # /restrict stickers newusers <hours>
    if len(context.args) < 3 or context.args[0] != "stickers" or context.args[1] != "newusers":
        await reply(update, "Usage: /restrict stickers newusers <hours>"); return
    try:
        hours = int(context.args[2])
    except ValueError:
        await reply(update, "❌ Hours must be a number."); return
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO sticker_newuser (chat_id, restrict_hours) VALUES (?,?)",
        (chat_id, hours)
    )
    conn.commit()
    await reply(update, f"✅ New users cannot send stickers for <b>{hours}</b> hours.", parse_mode="HTML")

async def check_sticker_prot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.sticker: return
    from helpers import is_admin
    if await is_admin(update, context): return
    chat_id = update.effective_chat.id
    user = update.effective_user
    sticker = msg.sticker
    set_name = sticker.set_name
    conn = get_conn()

    # Check new user restriction
    restriction = conn.execute(
        "SELECT restrict_hours FROM sticker_newuser WHERE chat_id=?", (chat_id,)
    ).fetchone()
    if restriction and restriction["restrict_hours"] > 0:
        try:
            member = await context.bot.get_chat_member(chat_id, user.id)
            join_date = getattr(member, "joined_date", None)
            if join_date:
                hours_since = (time.time() - join_date.timestamp()) / 3600
                if hours_since < restriction["restrict_hours"]:
                    try:
                        await msg.delete()
                        warn = await context.bot.send_message(
                            chat_id,
                            f"🚫 New users cannot send stickers for {restriction['restrict_hours']}h after joining."
                        )
                        import asyncio; await asyncio.sleep(5); await warn.delete()
                    except Exception:
                        pass
                    return
        except Exception:
            pass

    if not set_name:
        return
    # Check disapproved packs
    row = conn.execute(
        "SELECT approved FROM sticker_prot WHERE chat_id=? AND set_name=?",
        (chat_id, set_name)
    ).fetchone()
    if row and row["approved"] == 0:
        try:
            await msg.delete()
            warn = await context.bot.send_message(chat_id, "🚫 This sticker pack is not allowed.")
            import asyncio; await asyncio.sleep(5); await warn.delete()
        except Exception:
            pass

# ─── BIO FILTER ───────────────────────────────────────────────────────────────

async def bio_links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /bio_links on|off"); return
    state = 1 if context.args[0].lower() == "on" else 0
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT INTO bio_filter (chat_id, links_enabled) VALUES (?,?) ON CONFLICT(chat_id) DO UPDATE SET links_enabled=?",
        (chat_id, state, state)
    )
    conn.commit()
    await reply(update, f"✅ Bio link filter {'enabled' if state else 'disabled'}.")

async def bio_usernames_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /bio_usernames on|off"); return
    state = 1 if context.args[0].lower() == "on" else 0
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT INTO bio_filter (chat_id, usernames_enabled) VALUES (?,?) ON CONFLICT(chat_id) DO UPDATE SET usernames_enabled=?",
        (chat_id, state, state)
    )
    conn.commit()
    await reply(update, f"✅ Bio username filter {'enabled' if state else 'disabled'}.")

async def check_bio_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not update.effective_user: return
    from helpers import is_admin
    if await is_admin(update, context): return
    chat_id = update.effective_chat.id
    user = update.effective_user
    conn = get_conn()
    row = conn.execute("SELECT * FROM bio_filter WHERE chat_id=?", (chat_id,)).fetchone()
    if not row: return
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        bio = getattr(chat_member.user, "bio", "") or ""
    except Exception:
        return
    blocked = False
    if row["links_enabled"] and re.search(r"https?://\S+|t\.me/\S+|www\.\S+", bio):
        blocked = True
    if row["usernames_enabled"] and re.search(r"@\w+", bio):
        blocked = True
    if blocked:
        try:
            await msg.delete()
            warn = await context.bot.send_message(
                chat_id,
                f"🔐 {user.first_name}, please remove links/usernames from your bio to send messages."
            )
            import asyncio; await asyncio.sleep(8); await warn.delete()
        except Exception:
            pass

# ─── TAG ALL ──────────────────────────────────────────────────────────────────

async def tagall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat_id = update.effective_chat.id
    extra_msg = " ".join(context.args) if context.args else ""
    if extra_msg:
        await reply(update, f"📢 {extra_msg}")
    members_text = ""
    count = 0
    CHUNK_SIZE = 5
    chunk = []
    try:
        administrators = await context.bot.get_chat_administrators(chat_id)
        all_members = []
        async for member in context.bot.get_chat_members(chat_id):
            if not member.user.is_bot:
                all_members.append(member.user)
        for user in all_members:
            if user.username:
                chunk.append(f"@{user.username}")
            else:
                chunk.append(f'<a href="tg://user?id={user.id}">{user.first_name}</a>')
            count += 1
            if len(chunk) >= CHUNK_SIZE:
                await context.bot.send_message(chat_id, " ".join(chunk), parse_mode="HTML")
                chunk = []
                import asyncio; await asyncio.sleep(1)
        if chunk:
            await context.bot.send_message(chat_id, " ".join(chunk), parse_mode="HTML")
        await context.bot.send_message(chat_id, f"✅ Tagged <b>{count}</b> members.", parse_mode="HTML")
    except Exception as e:
        # Fallback if get_chat_members not supported
        await reply(update, f"❌ Could not tag all members: {e}")

# ─── ACCEPT ALL JOIN REQUESTS ─────────────────────────────────────────────────

async def acceptall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args:
        await reply(update, "Usage: /acceptall on|off"); return
    state = 1 if context.args[0].lower() == "on" else 0
    chat_id = update.effective_chat.id
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO acceptall (chat_id, enabled) VALUES (?,?)",
        (chat_id, state)
    )
    conn.commit()
    await reply(update, f"✅ Auto-accept join requests {'enabled' if state else 'disabled'}.")

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request: ChatJoinRequest = update.chat_join_request
    chat_id = request.chat.id
    conn = get_conn()
    row = conn.execute("SELECT enabled FROM acceptall WHERE chat_id=?", (chat_id,)).fetchone()
    if row and row["enabled"]:
        try:
            await request.approve()
        except Exception:
            pass

def register(app):
    # Sticker protection
    app.add_handler(CommandHandler("stickers", stickers_command))
    app.add_handler(CommandHandler("restrict", restrict_stickers_command))
    app.add_handler(MessageHandler(filters.Sticker.ALL, check_sticker_prot), group=10)
    # Bio filter
    app.add_handler(CommandHandler("bio_links", bio_links_command))
    app.add_handler(CommandHandler("bio_usernames", bio_usernames_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_bio_filter), group=11)
    # Tag all
    app.add_handler(CommandHandler("tagall", tagall_command))
    # Accept all
    app.add_handler(CommandHandler("acceptall", acceptall_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))

