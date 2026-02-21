
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

HELP_TEXT = {
    "welcome": (
        "╔══════════════════╗\n"
        "   👋 WELCOME SYSTEM\n"
        "╚══════════════════╝\n\n"
        "⚙️ Commands:\n"
        "• /setwelcome — Set welcome message\n"
        "• /welcome on/off — Enable or disable welcomes\n"
        "• /cleanwelcome on/off — Delete old welcomes\n\n"
        "🧩 Supported placeholders:\n"
        "• {first_name} → User first name\n"
        "• {username}   → @username (fallback to name)\n"
        "• {id}         → User ID\n"
        "• {mention}    → Clickable mention\n"
        "• {title}      → Group name\n\n"
        "📝 How to set:\n"
        "• Reply to a message (text/photo/video) with /setwelcome\n"
        "• Or send text directly\n\n"
        "🔗 Buttons example:\n"
        " [Rules](https://t.me/yourrules) | [Support](https://t.me/support)"
    ),
    "locks": (
        "╔══════════════════╗\n"
        "   🔒 LOCKS SYSTEM\n"
        "╚══════════════════╝\n\n"
        "📚 Commands:\n"
        "• /lock <type>       — Enable a lock\n"
        "• /unlock <type>     — Disable a lock\n"
        "• /locks             — Show active locks\n"
        "• /locklanguage <language>   — Lock a language\n"
        "• /unlocklanguage <language> — Unlock a language\n"
        "• /language_locks    — Show locked languages\n"
        "• /available_languages — Show all lockable languages\n\n"
        "🧹 Available lock types:\n"
        "• url       — Block links\n"
        "• forward   — Block forwarded messages\n"
        "• sticker   — Block stickers\n"
        "• media     — Block photos / videos / gifs\n"
        "• username  — Block @username mentions\n"
        "• language  — Block messages in specific languages\n\n"
        "😉 Usage Tip:\n"
        "🌟 Admins can combine multiple locks to fully protect groups from spam, raids, and unwanted content."
    ),
    "moderation": (
        "╔══════════════════╗\n"
        "   👮 MODERATION SYSTEM\n"
        "╚══════════════════╝\n\n"
        "🛠️ Commands & Tools:\n"
        "• /kick       — Remove a user\n"
        "• /ban        — Ban permanently\n"
        "• /unban      — Lift ban\n"
        "• /mute       — Disable messages\n"
        "• /unmute     — Allow messages again\n"
        "• /warn       — Add warning (3 = mute)\n"
        "• /warns      — View warnings\n"
        "• /resetwarns — Clear all warnings\n"
        "• /promote    — Make admin\n"
        "• /demote     — Remove from admin\n"
        "• /unbanall   — Unban all banned members\n\n"
        "📝 Example:\nReply to a user or type:\n/ban @username"
    ),
    "activity": (
        "╔══════════════════╗\n"
        "   📈 ACTIVITY TRACKER\n"
        "╚══════════════════╝\n\n"
        "🛠️ Commands:\n"
        "- /topusers — Show top 10 active users\n"
        "- /userstats <reply/user> — Show message count of a user\n\n"
        "🌟 Keep track of your community's most active members."
    ),
    "rules": (
        "╔══════════════════╗\n"
        "   📜 RULES\n"
        "╚══════════════════╝\n\n"
        "🛠️ Commands:\n"
        "- /setrules <text> — Set group rules\n"
        "- /rules           — Show current rules\n"
        "- /clearrules      — Remove all rules\n\n"
        "🌟 Keep your group organized and respectful."
    ),
    "blacklist": (
        "╔══════════════════╗\n"
        "   🚫 BLACKLIST\n"
        "╚══════════════════╝\n\n"
        "⚠️ Commands:\n"
        "- /addblack <word> — Add a word to the blacklist\n"
        "- /rmblack <word> — Remove a word from the blacklist\n"
        "- /blacklist — List all blacklisted words\n\n"
        "🌟 Keep your group clean and safe for everyone."
    ),
    "afk": (
        "╔══════════════════╗\n"
        "   💤 AFK SYSTEM\n"
        "╚══════════════════╝\n\n"
        "🛠️ Commands:\n"
        "/afk <reason> — Set yourself as AFK\n"
        "- Auto-reply will notify others when someone mentions an AFK user\n\n"
        "- Let others know you're away without missing any important messages."
    ),
    "filters": (
        "╔══════════════════╗\n"
        "   📝 FILTERS\n"
        "╚══════════════════╝\n\n"
        "🛠️ Commands:\n"
        "- /filter <keyword> (reply to message/sticker) — Add a filter\n"
        "- /stop <keyword> — Remove a filter\n\n"
        "- Automate replies and make your group more interactive."
    ),
    "ghost": (
        "╔══════════════════╗\n"
        "   👻 GHOST MODE\n"
        "╚══════════════════╝\n\n"
        "🛠️ Commands:\n"
        "- /ghostmode on — Enable ghost mode\n"
        "- /ghostmode off — Disable ghost mode\n\n"
        "- When enabled, service messages like join/leave are automatically deleted."
    ),
    "notes": (
        "╔════════════════════════╗\n"
        "   📝 NOTES\n"
        "╚════════════════════════╝\n\n"
        "👮 Admin Commands:\n"
        "• /setnote <name> <content>\n"
        "• /delnote <name>\n\n"
        "👥 User Commands:\n"
        "• /notes  → list all notes\n"
        "• #note_name → view note (sent in private)"
    ),
    "fsub": (
        "╔══════════════════╗\n"
        "   🔗 FORCE-SUBSCRIBE\n"
        "╚══════════════════╝\n\n"
        "📢 Commands:\n"
        "- /addfsub <channel> — Add a channel\n"
        "- /removefsub <channel> — Remove a channel\n"
        "- /fsublist — List all force-sub channels\n\n"
        "- Users who haven't joined all required channels are blocked from sending messages."
    ),
    "anticheater": (
        "╔══════════════════╗\n"
        "   👮 ANTI-CHEATER SYSTEM\n"
        "╚══════════════════╝\n\n"
        "🚨 Works automatically — no commands needed\n\n"
        "- The bot tracks admin actions.\n"
        "- If an admin kicks or bans more than 10 users in 24 hours, they are auto‑demoted.\n"
        "- Limits reset automatically every 24 hours.\n"
        "- Only admins promoted by this bot can be auto‑demoted using /promote (bot must have Add Admin permission).\n\n"
        "⚠️ Protects your group from fake or abusive admins."
    ),
    "forceadd": (
        "╔══════════════════╗\n"
        "   🔗 FORCE-ADD MEMBERS\n"
        "╚══════════════════╝\n\n"
        "👥 Commands:\n"
        "- /setforceadd <number> — Set how many members each user must add\n"
        "- /getforceadd — Show the current value\n\n"
        "- Users who haven't added enough members will have their messages deleted and receive a notification.\n"
        "🌟 Ensure everyone contributes for a healthy, active group!"
    ),
    "lifegame": (
        "╔══════════════════╗\n"
        "   🌱 LIFE GAME\n"
        "╚══════════════════╝\n\n"
        "🎮 Commands & Actions:\n"
        "- /startlife        :  Join the life game\n"
        "- /profile          :  View your profile\n"
        "- /setbio           :  Set your bio\n"
        "- /rob              :  Rob another user\n"
        "- /gift             :  Gift 10 coins to another user\n"
        "- /marry            :  Marry another user\n\n"
        "🎲 Betting System (group only):\n"
        "- /bet <amount>     :  Bet your coins on luck 🎯\n"
        "- /betstats         :  View your betting stats\n\n"
        "🏆 Level & Coins:\n"
        "- Earn coins by robbing, gifts, and other actions\n"
        "- Level up automatically based on total coins\n\n"
        "📜 Rules:\n"
        "- You cannot rob the same user more than once a day\n"
        "- You cannot gift/marry yourself\n\n"
        "🌟 Have fun and level up your life game journey!"
    ),
    "stickers": (
        "╔════════════════════════╗\n"
        "   🧷 STICKER PROTECTION\n"
        "╚════════════════════════╝\n\n"
        "🛠️ Commands:\n"
        "• /stickers approve  \n  ➜ Reply to a sticker to approve its pack\n"
        "• /stickers disapprove  \n  ➜ Reply to a sticker to block its pack\n"
        "• /stickers reset  \n  ➜ Reset ALL sticker settings\n\n"
        "⏱️ New User Restriction:\n"
        "• /restrict stickers newusers <hours>  \n  ➜ New members cannot send stickers for given hours\n\n"
        "📌 Examples:\n/stickers approve (reply)\n/stickers disapprove (reply)\n/stickers reset\n/restrict stickers newusers 24"
    ),
    "biofilter": (
        "╔════════════════════════╗\n"
        "   🔐 BIO FILTER – ANTI-LINK SYSTEM\n"
        "╚════════════════════════╝\n\n"
        "🛠️ Admin Commands:\n"
        "• /bio_links on|off → Toggle link filter\n"
        "• /bio_usernames on|off → Toggle username filter\n\n"
        "⚠️ Users must remove any links or @usernames before sending messages."
    ),
    "removedeleted": (
        "╔════════════════════╗\n"
        "   ⚠️ REMOVE DELETED ACCOUNTS\n"
        "╚════════════════════╝\n\n"
        "🛠️ Commands:\n"
        "- /remove_deleted — Scan and remove all deleted accounts\n\n"
        "- Bot must be an admin with permission to ban users.\n"
        "- Only the group owner or an admin with sufficient privileges can use this command."
    ),
    "tagall": (
        "╔════════════════════════╗\n"
        "   📢 TAG ALL – MENTION MEMBERS\n"
        "╚════════════════════════╝\n\n"
        "🛠️ How to use:\n"
        "• Send /tagall\n"
        "• Or /tagall your message\n\n"
        "👮 Permissions:\n"
        "• Only admins can use this command\n"
        "• Bot must be admin in the group\n\n"
        "⚠️ Note:\n"
        "• Works in groups only\n"
        "• Mentions members in parts to avoid issues"
    ),
    "acceptall": (
        "╔════════════════════════╗\n"
        "   🤖 AUTO ACCEPT – JOIN REQUESTS\n"
        "╚════════════════════════╝\n\n"
        "🛠️ How to use:\n"
        "• /acceptall on  – Enable\n"
        "• /acceptall off – Disable\n\n"
        "👮 Permissions:\n"
        "• Only group admins can use this\n"
        "• Bot must be admin with approval rights\n\n"
        "🌟 Works only in groups with join requests enabled."
    ),
}

HELP_BUTTONS = [
    [
        InlineKeyboardButton("🌸 GREETINGS", callback_data="help_welcome"),
        InlineKeyboardButton("🔒 LOCKS", callback_data="help_locks"),
        InlineKeyboardButton("🛡 MODERATION", callback_data="help_moderation"),
        InlineKeyboardButton("📊 ACTIVITY", callback_data="help_activity"),
    ],
    [
        InlineKeyboardButton("📜 RULES", callback_data="help_rules"),
        InlineKeyboardButton("🚫 BLACKLIST", callback_data="help_blacklist"),
        InlineKeyboardButton("💤 AFK", callback_data="help_afk"),
        InlineKeyboardButton("⚙ FILTERS", callback_data="help_filters"),
    ],
    [
        InlineKeyboardButton("👻 GHOST MODE", callback_data="help_ghost"),
        InlineKeyboardButton("📝 NOTES", callback_data="help_notes"),
        InlineKeyboardButton("📣 FORCE-SUB", callback_data="help_fsub"),
        InlineKeyboardButton("🚨 ANTI-CHEATER", callback_data="help_anticheater"),
    ],
    [
        InlineKeyboardButton("➕ FORCE-ADD", callback_data="help_forceadd"),
        InlineKeyboardButton("🎮 LIFE GAME", callback_data="help_lifegame"),
        InlineKeyboardButton("🎴 STICKER PROT", callback_data="help_stickers"),
        InlineKeyboardButton("🔗 BIO FILTER", callback_data="help_biofilter"),
    ],
    [
        InlineKeyboardButton("🗑 REMOVE DEL", callback_data="help_removedeleted"),
        InlineKeyboardButton("🔔 TAG ALL", callback_data="help_tagall"),
        InlineKeyboardButton("✅ AUTO ACCEPT", callback_data="help_acceptall"),
        InlineKeyboardButton("⭐ SUPPORT", callback_data="help_support"),
    ],
]

BACK_BUTTON = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="help_main")]]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        text = (
            f"✦ HELP MENU ✦\n\n"
            f"Hello {user.first_name}! 👋\n"
            f"I'm <b>Nomade Bot</b> — a powerful group management bot.\n\n"
            f"Select a category below to explore:"
        )
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(HELP_BUTTONS),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "✅ I'm online! Use /help to see all commands.",
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✦ HELP MENU ✦\n\n"
        "Select a category below to explore:"
    )
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(HELP_BUTTONS),
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help_main":
        await query.edit_message_text(
            "✦ HELP MENU ✦\n\nSelect a category below to explore:",
            reply_markup=InlineKeyboardMarkup(HELP_BUTTONS),
        )
        return

    if data == "help_support":
        from config import SUPPORT_CHAT
        await query.edit_message_text(
            f"⭐ SUPPORT\n\nJoin our support chat: {SUPPORT_CHAT}",
            reply_markup=InlineKeyboardMarkup(BACK_BUTTON),
        )
        return

    key = data.replace("help_", "")
    text = HELP_TEXT.get(key, "❌ Section not found.")
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(BACK_BUTTON),
    )

def register(app):
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_callback, pattern=r"^help_"))
