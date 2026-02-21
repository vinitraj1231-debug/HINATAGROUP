"""
Life Game — Full RPG System with coins, levels, rob, gift, marry, bet
"""
import time
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import get_conn
from helpers import reply, get_user_id_from_msg

LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500, 7500]

def get_level(coins: int) -> int:
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if coins >= threshold:
            level = i + 1
        else:
            break
    return min(level, len(LEVEL_THRESHOLDS))

def get_or_create_player(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM lifegame WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO lifegame (user_id, coins, level, bio, spouse_id) VALUES (?,100,1,'',0)",
            (user_id,)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM lifegame WHERE user_id=?", (user_id,)).fetchone()
    return row

async def startlife_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_conn()
    existing = conn.execute("SELECT user_id FROM lifegame WHERE user_id=?", (user.id,)).fetchone()
    if existing:
        await reply(update, "✅ You're already in the Life Game! Use /profile to view your stats.")
        return
    conn.execute(
        "INSERT INTO lifegame (user_id, coins, level, bio, spouse_id) VALUES (?,100,1,'',0)",
        (user.id,)
    )
    conn.commit()
    await reply(update, (
        f"🌱 Welcome to the Life Game, {user.first_name}!\n\n"
        f"💰 Starting coins: 100\n"
        f"⭐ Level: 1\n\n"
        f"Use /profile to view your stats, /rob to steal coins, /gift to share, /marry to find love!"
    ))

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_or_create_player(user.id)
    conn = get_conn()
    level = get_level(player["coins"])
    spouse_name = "None"
    if player["spouse_id"]:
        try:
            spouse_chat = await context.bot.get_chat(player["spouse_id"])
            spouse_name = spouse_chat.first_name or "Unknown"
        except Exception:
            spouse_name = f"ID:{player['spouse_id']}"
    next_threshold = LEVEL_THRESHOLDS[min(level, len(LEVEL_THRESHOLDS) - 1)]
    text = (
        f"👤 <b>{user.first_name}'s Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Level: <b>{level}</b>\n"
        f"💰 Coins: <b>{player['coins']}</b>\n"
        f"📝 Bio: {player['bio'] or 'Not set'}\n"
        f"💑 Spouse: {spouse_name}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Next level at: {next_threshold} coins"
    )
    await reply(update, text, parse_mode="HTML")

async def setbio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await reply(update, "Usage: /setbio <your bio>"); return
    bio = " ".join(context.args)[:100]
    get_or_create_player(user.id)
    conn = get_conn()
    conn.execute("UPDATE lifegame SET bio=? WHERE user_id=?", (bio, user.id))
    conn.commit()
    await reply(update, f"✅ Bio updated: <i>{bio}</i>", parse_mode="HTML")

async def rob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_id, target_name = get_user_id_from_msg(update)
    if not target_id:
        await reply(update, "❌ Reply to a user or provide their username/ID."); return
    if target_id == user.id:
        await reply(update, "❌ You cannot rob yourself!"); return

    robber = get_or_create_player(user.id)
    target = get_or_create_player(target_id)
    now = time.time()

    if now - robber["rob_cooldown"] < 86400:
        remaining = int(86400 - (now - robber["rob_cooldown"]))
        h, m = divmod(remaining // 60, 60)
        await reply(update, f"⏳ You can rob again in {h}h {m}m."); return

    if now - target["last_robbed"] < 86400:
        await reply(update, f"❌ {target_name} was already robbed today!"); return

    if target["coins"] < 10:
        await reply(update, f"❌ {target_name} is too poor to rob!"); return

    success_chance = random.random()
    conn = get_conn()
    if success_chance > 0.4:  # 60% success
        stolen = random.randint(10, min(100, target["coins"]))
        conn.execute("UPDATE lifegame SET coins=coins+?, rob_cooldown=? WHERE user_id=?", (stolen, now, user.id))
        conn.execute("UPDATE lifegame SET coins=coins-?, last_robbed=? WHERE user_id=?", (stolen, now, target_id))
        conn.commit()
        await reply(update, f"🦹 You successfully robbed <b>{target_name}</b> and stole <b>{stolen}</b> coins! 💰", parse_mode="HTML")
    else:
        fine = random.randint(5, 30)
        fine = min(fine, robber["coins"])
        conn.execute("UPDATE lifegame SET coins=coins-?, rob_cooldown=? WHERE user_id=?", (fine, now, user.id))
        conn.execute("UPDATE lifegame SET coins=coins+? WHERE user_id=?", (fine, target_id))
        conn.commit()
        await reply(update, f"👮 You got caught robbing <b>{target_name}</b> and paid a fine of <b>{fine}</b> coins!", parse_mode="HTML")

async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_id, target_name = get_user_id_from_msg(update)
    if not target_id:
        await reply(update, "❌ Reply to a user to gift them."); return
    if target_id == user.id:
        await reply(update, "❌ You cannot gift yourself!"); return

    giver = get_or_create_player(user.id)
    get_or_create_player(target_id)

    if giver["coins"] < 10:
        await reply(update, "❌ You need at least 10 coins to gift!"); return

    conn = get_conn()
    conn.execute("UPDATE lifegame SET coins=coins-10 WHERE user_id=?", (user.id,))
    conn.execute("UPDATE lifegame SET coins=coins+10 WHERE user_id=?", (target_id,))
    conn.commit()
    await reply(update, f"🎁 You gifted <b>10</b> coins to <b>{target_name}</b>! 💖", parse_mode="HTML")

async def marry_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_id, target_name = get_user_id_from_msg(update)
    if not target_id:
        await reply(update, "❌ Reply to a user to propose."); return
    if target_id == user.id:
        await reply(update, "❌ You cannot marry yourself!"); return

    proposer = get_or_create_player(user.id)
    target = get_or_create_player(target_id)

    if proposer["spouse_id"]:
        await reply(update, "❌ You are already married! Use /profile to see your spouse."); return
    if target["spouse_id"]:
        await reply(update, f"❌ {target_name} is already married!"); return

    conn = get_conn()
    conn.execute("UPDATE lifegame SET spouse_id=? WHERE user_id=?", (target_id, user.id))
    conn.execute("UPDATE lifegame SET spouse_id=? WHERE user_id=?", (user.id, target_id))
    conn.commit()
    await reply(update, f"💍 Congratulations! <b>{user.first_name}</b> and <b>{target_name}</b> are now married! 🎉", parse_mode="HTML")

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await reply(update, "Usage: /bet <amount>"); return
    try:
        amount = int(context.args[0])
    except ValueError:
        await reply(update, "❌ Please enter a valid amount."); return
    if amount <= 0:
        await reply(update, "❌ Bet amount must be positive."); return

    player = get_or_create_player(user.id)
    if player["coins"] < amount:
        await reply(update, f"❌ You only have {player['coins']} coins!"); return

    conn = get_conn()
    outcome = random.random()
    if outcome > 0.5:
        conn.execute("UPDATE lifegame SET coins=coins+? WHERE user_id=?", (amount, user.id))
        conn.execute("""
            INSERT INTO betstats (user_id, total_bets, wins, total_won) VALUES (?,1,1,?)
            ON CONFLICT(user_id) DO UPDATE SET total_bets=total_bets+1, wins=wins+1, total_won=total_won+?
        """, (user.id, amount, amount))
        conn.commit()
        await reply(update, f"🎰 You bet <b>{amount}</b> coins and <b>WON</b>! 💰 +{amount} coins!", parse_mode="HTML")
    else:
        conn.execute("UPDATE lifegame SET coins=coins-? WHERE user_id=?", (amount, user.id))
        conn.execute("""
            INSERT INTO betstats (user_id, total_bets, losses, total_lost) VALUES (?,1,1,?)
            ON CONFLICT(user_id) DO UPDATE SET total_bets=total_bets+1, losses=losses+1, total_lost=total_lost+?
        """, (user.id, amount, amount))
        conn.commit()
        await reply(update, f"🎰 You bet <b>{amount}</b> coins and <b>LOST</b>! 😢 -{amount} coins.", parse_mode="HTML")

async def betstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_conn()
    row = conn.execute("SELECT * FROM betstats WHERE user_id=?", (user.id,)).fetchone()
    if not row:
        await reply(update, "ℹ️ You haven't bet yet!"); return
    win_rate = (row["wins"] / row["total_bets"] * 100) if row["total_bets"] else 0
    text = (
        f"🎲 <b>{user.first_name}'s Bet Stats</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Total Bets: <b>{row['total_bets']}</b>\n"
        f"✅ Wins: <b>{row['wins']}</b>\n"
        f"❌ Losses: <b>{row['losses']}</b>\n"
        f"📊 Win Rate: <b>{win_rate:.1f}%</b>\n"
        f"💰 Total Won: <b>{row['total_won']}</b> coins\n"
        f"💸 Total Lost: <b>{row['total_lost']}</b> coins\n"
        f"📈 Net: <b>{row['total_won'] - row['total_lost']}</b> coins"
    )
    await reply(update, text, parse_mode="HTML")

def register(app):
    app.add_handler(CommandHandler("startlife", startlife_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("setbio", setbio_command))
    app.add_handler(CommandHandler("rob", rob_command))
    app.add_handler(CommandHandler("gift", gift_command))
    app.add_handler(CommandHandler("marry", marry_command))
    app.add_handler(CommandHandler("bet", bet_command))
    app.add_handler(CommandHandler("betstats", betstats_command))

