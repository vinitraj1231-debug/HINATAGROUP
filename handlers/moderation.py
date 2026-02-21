
import time
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler
from database import get_conn
from helpers import admin_check, reply, get_user_id_from_msg, is_admin

MAX_WARNINGS = 3

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    if await is_admin(update, context, user_id):
        await reply(update, "❌ Cannot kick an admin."); return
    try:
        await chat.ban_member(user_id)
        await chat.unban_member(user_id)
        await reply(update, f"✅ {name} has been kicked from the group.")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    if await is_admin(update, context, user_id):
        await reply(update, "❌ Cannot ban an admin."); return
    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "No reason"
    try:
        await chat.ban_member(user_id)
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO bans (chat_id, user_id, reason) VALUES (?,?,?)",
            (chat.id, user_id, reason)
        )
        conn.commit()
        await reply(update, f"🚫 {name} has been <b>banned</b>.\n📝 Reason: {reason}", parse_mode="HTML")
        await _track_admin_action(update, context, "ban")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    try:
        await chat.unban_member(user_id)
        conn = get_conn()
        conn.execute("DELETE FROM bans WHERE chat_id=? AND user_id=?", (chat.id, user_id))
        conn.commit()
        await reply(update, f"✅ {name} has been <b>unbanned</b>.", parse_mode="HTML")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    if await is_admin(update, context, user_id):
        await reply(update, "❌ Cannot mute an admin."); return
    try:
        await context.bot.restrict_chat_member(
            chat.id, user_id,
            ChatPermissions(can_send_messages=False)
        )
        await reply(update, f"🔇 {name} has been <b>muted</b>.", parse_mode="HTML")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    try:
        await context.bot.restrict_chat_member(
            chat.id, user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await reply(update, f"🔊 {name} has been <b>unmuted</b>.", parse_mode="HTML")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    if await is_admin(update, context, user_id):
        await reply(update, "❌ Cannot warn an admin."); return
    conn = get_conn()
    row = conn.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?", (chat.id, user_id)).fetchone()
    count = (row["count"] if row else 0) + 1
    conn.execute(
        "INSERT OR REPLACE INTO warnings (chat_id, user_id, count) VALUES (?,?,?)",
        (chat.id, user_id, count)
    )
    conn.commit()
    if count >= MAX_WARNINGS:
        try:
            await context.bot.restrict_chat_member(chat.id, user_id, ChatPermissions(can_send_messages=False))
            await reply(update, f"⚠️ {name} has been warned {count}/{MAX_WARNINGS} times and is now <b>muted</b>!", parse_mode="HTML")
            conn.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?", (chat.id, user_id))
            conn.commit()
        except Exception as e:
            await reply(update, f"❌ Failed to mute: {e}")
    else:
        await reply(update, f"⚠️ {name} has been warned. [{count}/{MAX_WARNINGS}]")

async def warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        user_id = update.effective_user.id
        name = update.effective_user.first_name
    conn = get_conn()
    row = conn.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?", (chat.id, user_id)).fetchone()
    count = row["count"] if row else 0
    await reply(update, f"⚠️ {name} has <b>{count}/{MAX_WARNINGS}</b> warnings.", parse_mode="HTML")

async def resetwarns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    conn = get_conn()
    conn.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?", (chat.id, user_id))
    conn.commit()
    await reply(update, f"✅ Warnings for {name} have been reset.")

async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    title = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else ""
    try:
        from telegram import ChatAdministratorRights
        await context.bot.promote_chat_member(
            chat.id, user_id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True,
        )
        if title:
            await context.bot.set_chat_administrator_custom_title(chat.id, user_id, title)
        await reply(update, f"✅ {name} has been <b>promoted</b>!", parse_mode="HTML")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    user_id, name = get_user_id_from_msg(update)
    if not user_id:
        await reply(update, "❌ Reply to a user or provide username/ID."); return
    try:
        await context.bot.promote_chat_member(chat.id, user_id)
        await reply(update, f"✅ {name} has been <b>demoted</b>.", parse_mode="HTML")
    except Exception as e:
        await reply(update, f"❌ Failed: {e}")

async def unbanall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat = update.effective_chat
    conn = get_conn()
    banned = conn.execute("SELECT user_id FROM bans WHERE chat_id=?", (chat.id,)).fetchall()
    if not banned:
        await reply(update, "ℹ️ No banned users recorded."); return
    count = 0
    for row in banned:
        try:
            await context.bot.unban_chat_member(chat.id, row["user_id"])
            count += 1
        except Exception:
            pass
    conn.execute("DELETE FROM bans WHERE chat_id=?", (chat.id,))
    conn.commit()
    await reply(update, f"✅ Unbanned <b>{count}</b> users.", parse_mode="HTML")

async def _track_admin_action(update, context, action_type):
    """Track admin actions for anti-cheater."""
    chat = update.effective_chat
    admin_id = update.effective_user.id
    conn = get_conn()
    now = time.time()
    row = conn.execute(
        "SELECT * FROM anticheater WHERE chat_id=? AND admin_id=?",
        (chat.id, admin_id)
    ).fetchone()
    if row:
        reset_time = row["reset_time"]
        if now - reset_time > 86400:
            conn.execute(
                "UPDATE anticheater SET action_count=1, reset_time=? WHERE chat_id=? AND admin_id=?",
                (now, chat.id, admin_id)
            )
        else:
            new_count = row["action_count"] + 1
            conn.execute(
                "UPDATE anticheater SET action_count=? WHERE chat_id=? AND admin_id=?",
                (new_count, chat.id, admin_id)
            )
            if new_count > 10:
                try:
                    await context.bot.promote_chat_member(chat.id, admin_id)
                    await context.bot.send_message(
                        chat.id,
                        f"🚨 Admin <a href='tg://user?id={admin_id}'>{admin_id}</a> was auto-demoted for excessive bans/kicks (>{10} in 24h).",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
    else:
        conn.execute(
            "INSERT INTO anticheater (chat_id, admin_id, action_count, reset_time) VALUES (?,?,1,?)",
            (chat.id, admin_id, now)
        )
    conn.commit()

def register(app):
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(CommandHandler("warns", warns_command))
    app.add_handler(CommandHandler("resetwarns", resetwarns_command))
    app.add_handler(CommandHandler("promote", promote_command))
    app.add_handler(CommandHandler("demote", demote_command))
    app.add_handler(CommandHandler("unbanall", unbanall_command))
