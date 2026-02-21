
from telegram import Update, ChatMember
from telegram.ext import ContextTypes

ADMIN_STATUSES = (ChatMember.ADMINISTRATOR, ChatMember.OWNER)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> bool:
    if user_id is None:
        user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status in ADMIN_STATUSES
    except Exception:
        return False

async def is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> bool:
    if user_id is None:
        user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status == ChatMember.OWNER
    except Exception:
        return False

async def reply(update: Update, text: str, **kwargs):
    return await update.effective_message.reply_text(text, **kwargs)

async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not await is_admin(update, context):
        await reply(update, "❌ Only admins can use this command.")
        return False
    return True

def get_user_id_from_msg(update: Update):
    msg = update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user.id, msg.reply_to_message.from_user.first_name
    args = msg.text.split()[1:] if msg.text else []
    if args:
        arg = args[0]
        if arg.startswith("@"):
            return arg, arg
        try:
            return int(arg), arg
        except ValueError:
            pass
    return None, None
