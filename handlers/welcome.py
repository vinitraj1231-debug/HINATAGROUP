
import re
from telegram import Update, ChatMemberUpdated
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler, MessageHandler, filters
from database import get_conn
from helpers import admin_check, reply

def _parse_buttons(text: str):
    """Parse [Button Text](url) | [Button2](url2) style from text."""
    button_pattern = re.compile(r"\[(.+?)\]\((https?://\S+)\)")
    buttons = []
    clean_text = text
    for line in text.split("\n"):
        row = button_pattern.findall(line)
        if row:
            buttons.append([{"text": t, "url": u} for t, u in row])
            clean_text = clean_text.replace(line, "")
    return clean_text.strip(), buttons

def _format_welcome(template: str, member, chat) -> str:
    username = f"@{member.username}" if member.username else member.first_name
    mention = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
    return (
        template
        .replace("{first_name}", member.first_name or "")
        .replace("{username}", username)
        .replace("{id}", str(member.id))
        .replace("{mention}", mention)
        .replace("{title}", chat.title or "")
    )

async def setwelcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat_id = update.effective_chat.id
    msg = update.effective_message
    text = None
    if msg.reply_to_message:
        if msg.reply_to_message.text:
            text = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text = msg.reply_to_message.caption
    elif context.args:
        text = " ".join(context.args)

    if not text:
        await reply(update, "❌ Please provide a welcome message or reply to one.")
        return

    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO welcome (chat_id, message, enabled) VALUES (?, ?, 1)",
        (chat_id, text)
    )
    conn.commit()
    await reply(update, f"✅ Welcome message set!\n\n<b>Preview:</b>\n{text}", parse_mode="HTML")

async def welcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat_id = update.effective_chat.id
    if not context.args:
        await reply(update, "Usage: /welcome on|off"); return
    state = 1 if context.args[0].lower() == "on" else 0
    conn = get_conn()
    conn.execute(
        "INSERT INTO welcome (chat_id, enabled) VALUES (?,?) ON CONFLICT(chat_id) DO UPDATE SET enabled=?",
        (chat_id, state, state)
    )
    conn.commit()
    await reply(update, f"✅ Welcome messages {'enabled' if state else 'disabled'}.")

async def cleanwelcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    chat_id = update.effective_chat.id
    if not context.args:
        await reply(update, "Usage: /cleanwelcome on|off"); return
    state = 1 if context.args[0].lower() == "on" else 0
    conn = get_conn()
    conn.execute(
        "INSERT INTO welcome (chat_id, clean_welcome) VALUES (?,?) ON CONFLICT(chat_id) DO UPDATE SET clean_welcome=?",
        (chat_id, state, state)
    )
    conn.commit()
    await reply(update, f"✅ Clean welcome {'enabled' if state else 'disabled'}.")

async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not update.message or not update.message.new_chat_members:
        return
    conn = get_conn()
    row = conn.execute("SELECT * FROM welcome WHERE chat_id=?", (chat.id,)).fetchone()
    if not row or not row["enabled"]:
        return
    template = row["message"] or "Welcome {mention} to {title}!"
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        text = _format_welcome(template, member, chat)
        clean_text, parsed_buttons = _parse_buttons(text)
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        kb = None
        if parsed_buttons:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(b["text"], url=b["url"]) for b in row_btns]
                for row_btns in parsed_buttons
            ])
        sent = await context.bot.send_message(
            chat.id, clean_text, reply_markup=kb, parse_mode="HTML"
        )
        if row["clean_welcome"] and row["last_welcome_id"]:
            try:
                await context.bot.delete_message(chat.id, row["last_welcome_id"])
            except Exception:
                pass
        conn.execute(
            "UPDATE welcome SET last_welcome_id=? WHERE chat_id=?",
            (sent.message_id, chat.id)
        )
        conn.commit()

def register(app):
    app.add_handler(CommandHandler("setwelcome", setwelcome_command))
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("cleanwelcome", cleanwelcome_toggle))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
