
import sqlite3
import threading
from config import DATABASE_URL

_local = threading.local()

def get_conn():
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn

def init_db():
    conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
    c = conn.cursor()

    # Welcome
    c.execute("""CREATE TABLE IF NOT EXISTS welcome (
        chat_id INTEGER PRIMARY KEY,
        message TEXT,
        enabled INTEGER DEFAULT 1,
        clean_welcome INTEGER DEFAULT 0,
        last_welcome_id INTEGER DEFAULT 0
    )""")

    # Locks
    c.execute("""CREATE TABLE IF NOT EXISTS locks (
        chat_id INTEGER,
        lock_type TEXT,
        PRIMARY KEY (chat_id, lock_type)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS language_locks (
        chat_id INTEGER,
        language TEXT,
        PRIMARY KEY (chat_id, language)
    )""")

    # Rules
    c.execute("""CREATE TABLE IF NOT EXISTS rules (
        chat_id INTEGER PRIMARY KEY,
        rules_text TEXT
    )""")

    # Blacklist
    c.execute("""CREATE TABLE IF NOT EXISTS blacklist (
        chat_id INTEGER,
        word TEXT,
        PRIMARY KEY (chat_id, word)
    )""")

    # AFK
    c.execute("""CREATE TABLE IF NOT EXISTS afk (
        user_id INTEGER,
        chat_id INTEGER,
        reason TEXT,
        since REAL,
        PRIMARY KEY (user_id, chat_id)
    )""")

    # Filters
    c.execute("""CREATE TABLE IF NOT EXISTS filters (
        chat_id INTEGER,
        keyword TEXT,
        reply TEXT,
        file_id TEXT,
        file_type TEXT,
        PRIMARY KEY (chat_id, keyword)
    )""")

    # Ghost mode
    c.execute("""CREATE TABLE IF NOT EXISTS ghost_mode (
        chat_id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 0
    )""")

    # Notes
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        chat_id INTEGER,
        name TEXT,
        content TEXT,
        PRIMARY KEY (chat_id, name)
    )""")

    # Force subscribe
    c.execute("""CREATE TABLE IF NOT EXISTS fsub (
        chat_id INTEGER,
        channel TEXT,
        PRIMARY KEY (chat_id, channel)
    )""")

    # Anti-cheater
    c.execute("""CREATE TABLE IF NOT EXISTS anticheater (
        chat_id INTEGER,
        admin_id INTEGER,
        action_count INTEGER DEFAULT 0,
        reset_time REAL,
        PRIMARY KEY (chat_id, admin_id)
    )""")

    # Force add
    c.execute("""CREATE TABLE IF NOT EXISTS forceadd (
        chat_id INTEGER PRIMARY KEY,
        required INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS forceadd_progress (
        chat_id INTEGER,
        user_id INTEGER,
        count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    )""")

    # Life game
    c.execute("""CREATE TABLE IF NOT EXISTS lifegame (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 100,
        level INTEGER DEFAULT 1,
        bio TEXT DEFAULT '',
        spouse_id INTEGER DEFAULT 0,
        rob_cooldown REAL DEFAULT 0,
        gift_cooldown REAL DEFAULT 0,
        last_robbed REAL DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS betstats (
        user_id INTEGER PRIMARY KEY,
        total_bets INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        total_won INTEGER DEFAULT 0,
        total_lost INTEGER DEFAULT 0
    )""")

    # Sticker protection
    c.execute("""CREATE TABLE IF NOT EXISTS sticker_prot (
        chat_id INTEGER,
        set_name TEXT,
        approved INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, set_name)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sticker_newuser (
        chat_id INTEGER PRIMARY KEY,
        restrict_hours INTEGER DEFAULT 0
    )""")

    # Bio filter
    c.execute("""CREATE TABLE IF NOT EXISTS bio_filter (
        chat_id INTEGER PRIMARY KEY,
        links_enabled INTEGER DEFAULT 0,
        usernames_enabled INTEGER DEFAULT 0
    )""")

    # Activity
    c.execute("""CREATE TABLE IF NOT EXISTS activity (
        chat_id INTEGER,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        msg_count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    )""")

    # Warnings
    c.execute("""CREATE TABLE IF NOT EXISTS warnings (
        chat_id INTEGER,
        user_id INTEGER,
        count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    )""")

    # Bans
    c.execute("""CREATE TABLE IF NOT EXISTS bans (
        chat_id INTEGER,
        user_id INTEGER,
        reason TEXT,
        PRIMARY KEY (chat_id, user_id)
    )""")

    # Join request auto-accept
    c.execute("""CREATE TABLE IF NOT EXISTS acceptall (
        chat_id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 0
    )""")

    conn.commit()
    conn.close()
    print("✅ Database initialized.")
