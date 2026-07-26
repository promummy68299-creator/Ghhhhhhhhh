# bot.py - Complete Fixed Code
import os
import sys
import time
import json
import shutil
import zipfile
import subprocess
import threading
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import telebot
from telebot import types
import psutil

# =========================
# CONFIGURATION - UPDATE THESE
# =========================
BOT_TOKEN = "8840844556:AAHLzE_kl3JClb-nriteYmI_pwZES5-BoRk"  # NEW TOKEN FROM BOTFATHER
ADMIN_ID = 7924753922  # YOUR ADMIN ID

# IMPORTANT: Use full URLs, NOT @username
UPDATES_CHANNEL = "https://t.me/channellelu_pro"
OWNER_USERNAME = "https://t.me/pro_tg01"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
# BOT INIT
# =========================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# =========================
# DATABASE
# =========================
DB_PATH = 'hosting.db'

def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_date TEXT,
        is_banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        storage_limit INTEGER DEFAULT 1073741824
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_name TEXT,
        bot_type TEXT,
        file_path TEXT,
        folder_path TEXT,
        process_id INTEGER,
        status TEXT,
        created_at TEXT,
        last_started TEXT,
        memory_usage INTEGER,
        cpu_usage REAL,
        is_approved INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_id INTEGER,
        log_type TEXT,
        message TEXT,
        timestamp TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS pending_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_id INTEGER,
        file_name TEXT,
        file_size INTEGER,
        uploaded_at TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # Default settings - USE FULL URLS
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('hosting_status', 'online'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('auto_approve', 'true'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_photo', ''))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_caption', ''))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('updates_button', UPDATES_CHANNEL))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('contact_button', OWNER_USERNAME))
    
    conn.commit()
    conn.close()
    
    os.makedirs('users', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Database initialized")

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    result = None
    if fetchone:
        result = c.fetchone()
    elif fetchall:
        result = c.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return result

def get_user(user_id):
    user = db_query("SELECT * FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if not user:
        try:
            user_info = bot.get_chat(user_id)
            username = user_info.username or ""
            first_name = user_info.first_name or ""
        except:
            username = ""
            first_name = ""
        
        db_query(
            "INSERT INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, datetime.now().isoformat()),
            commit=True
        )
        user = db_query("SELECT * FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    return user

def get_setting(key):
    result = db_query("SELECT value FROM settings WHERE key = ?", (key,), fetchone=True)
    return result[0] if result else None

def update_setting(key, value):
    db_query("UPDATE settings SET value = ? WHERE key = ?", (value, key), commit=True)

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_banned(user_id):
    user = get_user(user_id)
    return user[4] == 1 if user else False

def get_hosting_status():
    return get_setting('hosting_status') or 'online'

def get_auto_approve():
    return get_setting('auto_approve') or 'true'

# =========================
# BOT MANAGER
# =========================
class BotManager:
    def __init__(self):
        self.processes = {}
        self.monitor_thread = None
        self.running = True
        self.start_monitor()

    def start_monitor(self):
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self.monitor_bots, daemon=True)
            self.monitor_thread.start()
            logger.info("Bot monitor started")

    def monitor_bots(self):
        while self.running:
            try:
                bots = db_query("SELECT * FROM bots WHERE status = 'running' AND is_approved = 1", fetchall=True)
                for bot_data in bots:
                    process_id = bot_data[6]
                    if process_id:
                        try:
                            os.kill(process_id, 0)
                        except OSError:
                            logger.info(f"Bot {bot_data[2]} crashed, restarting...")
                            self.restart_bot(bot_data[0])
                time.sleep(10)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(30)

    def start_bot(self, bot_id):
        try:
            bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
            if not bot_data:
                return False, "Bot not found"
            
            if bot_data[12] != 1:
                return False, "Bot not approved"
            
            user_id = bot_data[1]
            bot_name = bot_data[2]
            bot_type = bot_data[3]
            file_path = bot_data[4]
            folder_path = bot_data[5]
            
            if not os.path.exists(file_path):
                return False, "Bot file not found"
            
            if bot_type == 'python':
                req_file = os.path.join(folder_path, 'requirements.txt')
                if os.path.exists(req_file):
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_file], 
                                 capture_output=True, text=True)
            elif bot_type == 'node':
                pkg_file = os.path.join(folder_path, 'package.json')
                if os.path.exists(pkg_file):
                    subprocess.run(['npm', 'install'], cwd=folder_path, capture_output=True, text=True)
            
            if bot_type == 'python':
                process = subprocess.Popen(
                    [sys.executable, file_path],
                    cwd=folder_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif bot_type == 'node':
                process = subprocess.Popen(
                    ['node', file_path],
                    cwd=folder_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                return False, "Unsupported bot type"
            
            db_query(
                "UPDATE bots SET process_id = ?, status = 'running', last_started = ? WHERE id = ?",
                (process.pid, datetime.now().isoformat(), bot_id),
                commit=True
            )
            
            self.processes[bot_id] = process
            threading.Thread(target=self.capture_logs, args=(bot_id, process), daemon=True).start()
            
            return True, f"Bot started (PID: {process.pid})"
        
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return False, str(e)

    def capture_logs(self, bot_id, process):
        try:
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    db_query(
                        "INSERT INTO logs (user_id, bot_id, log_type, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                        (0, bot_id, 'stdout', line.strip(), datetime.now().isoformat()),
                        commit=True
                    )
                line = process.stderr.readline()
                if line:
                    db_query(
                        "INSERT INTO logs (user_id, bot_id, log_type, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                        (0, bot_id, 'stderr', line.strip(), datetime.now().isoformat()),
                        commit=True
                    )
        except Exception as e:
            logger.error(f"Log capture error: {e}")

    def stop_bot(self, bot_id):
        try:
            bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
            if not bot_data:
                return False, "Bot not found"
            
            process_id = bot_data[6]
            if process_id:
                try:
                    os.kill(process_id, 9)
                except:
                    pass
            
            db_query(
                "UPDATE bots SET process_id = ?, status = 'stopped' WHERE id = ?",
                (None, bot_id),
                commit=True
            )
            
            if bot_id in self.processes:
                del self.processes[bot_id]
            
            return True, "Bot stopped"
        
        except Exception as e:
            return False, str(e)

    def restart_bot(self, bot_id):
        self.stop_bot(bot_id)
        time.sleep(2)
        return self.start_bot(bot_id)

bot_manager = BotManager()

# =========================
# START COMMAND
# =========================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    get_user(user_id)
    
    if is_banned(user_id):
        db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,), commit=True)
    
    updates_button = get_setting('updates_button') or UPDATES_CHANNEL
    contact_button = get_setting('contact_button') or OWNER_USERNAME
    hosting_status = get_hosting_status()
    auto_approve = get_auto_approve()
    
    first_name = message.from_user.first_name or "User"
    total_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ?", (user_id,), fetchone=True)[0]
    running_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND status = 'running'", (user_id,), fetchone=True)[0]
    
    caption = f"""🔥 <b>24x7 Hosting Bot</b>

👋 Welcome {first_name}

🟢 <b>Status:</b> {hosting_status.upper()}
✅ <b>Auto Approve:</b> {'ON' if auto_approve == 'true' else 'OFF'}

🆔 <b>User ID:</b>
<code>{user_id}</code>

📦 <b>Your Bots:</b>
Total: {total_bots} | Running: {running_bots}

⚡ <b>Features</b>
• Python & NodeJS Hosting
• Auto Install Dependencies
• 24x7 Uptime
• Live Logs
• Auto Restart

👇 Use buttons below"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📢 Updates", url=updates_button),
        types.InlineKeyboardButton("📤 Upload Bot", callback_data="upload")
    )
    keyboard.add(
        types.InlineKeyboardButton("📂 My Bots", callback_data="my_bots"),
        types.InlineKeyboardButton("⚡ Speed", callback_data="speed")
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 Statistics", callback_data="stats"),
        types.InlineKeyboardButton("☎ Contact", url=contact_button)
    )
    
    bot.send_message(user_id, caption, reply_markup=keyboard)

# =========================
# ADMIN COMMAND
# =========================
@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(user_id, "❌ Admin access required!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats")
    )
    keyboard.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ Add User", callback_data="admin_add_user")
    )
    keyboard.add(
        types.InlineKeyboardButton("➖ Ban User", callback_data="admin_ban_user"),
        types.InlineKeyboardButton("📁 User Files", callback_data="admin_user_files")
    )
    keyboard.add(
        types.InlineKeyboardButton("🟢 Hosting ON", callback_data="admin_hosting_on"),
        types.InlineKeyboardButton("🔴 Hosting OFF", callback_data="admin_hosting_off")
    )
    keyboard.add(
        types.InlineKeyboardButton("✅ Auto Approve ON", callback_data="admin_auto_on"),
        types.InlineKeyboardButton("❌ Auto Approve OFF", callback_data="admin_auto_off")
    )
    keyboard.add(
        types.InlineKeyboardButton("📋 Pending", callback_data="admin_pending"),
        types.InlineKeyboardButton("🖼 Change Photo", callback_data="admin_photo")
    )
    keyboard.add(
        types.InlineKeyboardButton("✏ Change Caption", callback_data="admin_caption"),
        types.InlineKeyboardButton("💾 Backup DB", callback_data="admin_backup")
    )
    keyboard.add(
        types.InlineKeyboardButton("♻ Restart", callback_data="admin_restart")
    )
    
    bot.send_message(user_id, "🔧 <b>Admin Panel</b>", reply_markup=keyboard)

# =========================
# FILE HANDLER
# =========================
@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    get_user(user_id)
    
    if is_banned(user_id):
        bot.send_message(user_id, "❌ You are banned!")
        return
    
    if get_hosting_status() == 'offline':
        bot.send_message(user_id, "🔴 Hosting is offline!")
        return
    
    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name
    file_size = message.document.file_size
    
    if file_name.endswith('.zip'):
        bot_type = 'zip'
    elif file_name.endswith('.py'):
        bot_type = 'python'
    elif file_name.endswith('.js'):
        bot_type = 'node'
    else:
        bot.send_message(user_id, "❌ Only .zip, .py, .js files supported!")
        return
    
    msg = bot.reply_to(message, "📝 Enter bot name (letters, numbers, underscores only):")
    bot.register_next_step_handler(msg, process_bot_name, file_info, file_name, file_size, bot_type)

def process_bot_name(message, file_info, file_name, file_size, bot_type):
    user_id = message.from_user.id
    bot_name = message.text.strip()
    
    if not bot_name or not all(c.isalnum() or c == '_' for c in bot_name):
        bot.send_message(user_id, "❌ Invalid name!")
        return
    
    existing = db_query("SELECT * FROM bots WHERE user_id = ? AND bot_name = ?", (user_id, bot_name), fetchone=True)
    if existing:
        bot.send_message(user_id, f"❌ Bot '{bot_name}' already exists!")
        return
    
    try:
        downloaded_file = bot.download_file(file_info.file_path)
        bot_folder = f"users/{user_id}/{bot_name}"
        os.makedirs(bot_folder, exist_ok=True)
        file_path = os.path.join(bot_folder, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        if bot_type == 'zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(bot_folder)
            main_file = None
            for root, dirs, files in os.walk(bot_folder):
                for f in files:
                    if f.endswith('.py'):
                        main_file = os.path.join(root, f)
                        bot_type = 'python'
                        break
                    elif f.endswith('.js'):
                        main_file = os.path.join(root, f)
                        bot_type = 'node'
                        break
                if main_file:
                    break
            if not main_file:
                shutil.rmtree(bot_folder)
                bot.send_message(user_id, "❌ No .py or .js found in zip!")
                return
            main_name = os.path.basename(main_file)
            new_path = os.path.join(bot_folder, main_name)
            shutil.move(main_file, new_path)
            file_path = new_path
        
        auto_approve = get_auto_approve()
        is_approved = 1 if auto_approve == 'true' else 0
        
        db_query(
            """INSERT INTO bots 
            (user_id, bot_name, bot_type, file_path, folder_path, status, created_at, is_approved) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, bot_name, bot_type, file_path, bot_folder, 'stopped', datetime.now().isoformat(), is_approved),
            commit=True
        )
        
        bot_id = db_query("SELECT last_insert_rowid()", fetchone=True)[0]
        
        if auto_approve == 'true':
            success, msg = bot_manager.start_bot(bot_id)
            if success:
                bot.send_message(user_id, f"✅ Bot '{bot_name}' started!\n\n{msg}")
            else:
                bot.send_message(user_id, f"⚠️ Uploaded but failed to start!\n\n{msg}")
        else:
            db_query(
                "INSERT INTO pending_approvals (user_id, bot_id, file_name, file_size, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, bot_id, file_name, file_size, datetime.now().isoformat()),
                commit=True
            )
            bot.send_message(user_id, f"⏳ Bot '{bot_name}' uploaded! Pending approval.")
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{bot_id}"),
                types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{bot_id}")
            )
            bot.send_message(ADMIN_ID, f"📥 New bot pending: {bot_name}", reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.send_message(user_id, f"❌ Error: {str(e)}")

# =========================
# CALLBACK HANDLER
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    if data == "upload":
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "📤 Send your bot file!\n\nSupported: .py, .js, .zip")
    
    elif data == "my_bots":
        bot.answer_callback_query(call.id)
        bots = db_query("SELECT * FROM bots WHERE user_id = ?", (user_id,), fetchall=True)
        if not bots:
            bot.send_message(user_id, "📂 No bots found!")
            return
        text = "📂 <b>Your Bots</b>\n\n"
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for bot_data in bots:
            status = "🟢 Running" if bot_data[7] == "running" else "🔴 Stopped"
            text += f"• <b>{bot_data[2]}</b> ({bot_data[3]}) - {status}\n"
            keyboard.add(types.InlineKeyboardButton(bot_data[2], callback_data=f"bot_{bot_data[0]}_info"))
        bot.send_message(user_id, text, reply_markup=keyboard)
    
    elif data == "speed":
        bot.answer_callback_query(call.id)
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        text = f"⚡ <b>System</b>\nCPU: {cpu}%\nRAM: {mem.used/(1024**3):.2f}GB / {mem.total/(1024**3):.2f}GB"
        bot.send_message(user_id, text)
    
    elif data == "stats":
        bot.answer_callback_query(call.id)
        total = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ?", (user_id,), fetchone=True)[0]
        running = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND status = 'running'", (user_id,), fetchone=True)[0]
        text = f"📊 <b>Your Stats</b>\n\nTotal Bots: {total}\nRunning: {running}"
        bot.send_message(user_id, text)
    
    elif data.startswith("bot_"):
        parts = data.split("_")
        bot_id = int(parts[1])
        action = parts[2] if len(parts) > 2 else "info"
        
        if action == "info":
            bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
            if bot_data:
                text = f"📊 <b>{bot_data[2]}</b>\nType: {bot_data[3]}\nStatus: {bot_data[7]}\nPID: {bot_data[6] or 'N/A'}"
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                if bot_data[7] == "running":
                    keyboard.add(types.InlineKeyboardButton("⏹ Stop", callback_data=f"bot_{bot_id}_stop"))
                    keyboard.add(types.InlineKeyboardButton("🔄 Restart", callback_data=f"bot_{bot_id}_restart"))
                else:
                    keyboard.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"bot_{bot_id}_start"))
                keyboard.add(types.InlineKeyboardButton("🗑 Delete", callback_data=f"bot_{bot_id}_delete"))
                bot.send_message(user_id, text, reply_markup=keyboard)
        
        elif action == "start":
            success, msg = bot_manager.start_bot(bot_id)
            bot.send_message(user_id, f"✅ {msg}" if success else f"❌ {msg}")
        
        elif action == "stop":
            success, msg = bot_manager.stop_bot(bot_id)
            bot.send_message(user_id, f"✅ {msg}" if success else f"❌ {msg}")
        
        elif action == "restart":
            success, msg = bot_manager.restart_bot(bot_id)
            bot.send_message(user_id, f"✅ {msg}" if success else f"❌ {msg}")
        
        elif action == "delete":
            bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
            if bot_data:
                bot_manager.stop_bot(bot_id)
                if os.path.exists(bot_data[5]):
                    shutil.rmtree(bot_data[5])
                db_query("DELETE FROM bots WHERE id = ?", (bot_id,), commit=True)
                bot.send_message(user_id, "✅ Bot deleted!")
    
    # Admin callbacks
    elif data.startswith("admin_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        
        if data == "admin_users":
            users = db_query("SELECT * FROM users", fetchall=True)
            text = "👥 Users\n\n"
            for u in users[:20]:
                text += f"• {u[2]} (ID: {u[0]})\n"
            bot.send_message(user_id, text)
        
        elif data == "admin_stats":
            total_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
            total_bots = db_query("SELECT COUNT(*) FROM bots", fetchone=True)[0]
            bot.send_message(user_id, f"📊 Stats\nUsers: {total_users}\nBots: {total_bots}")
        
        elif data == "admin_broadcast":
            bot.send_message(user_id, "📢 Send broadcast message:")
            bot.register_next_step_handler(call.message, broadcast_message)
        
        elif data == "admin_add_user":
            bot.send_message(user_id, "➕ Enter user ID:")
            bot.register_next_step_handler(call.message, add_user)
        
        elif data == "admin_ban_user":
            bot.send_message(user_id, "➖ Enter user ID:")
            bot.register_next_step_handler(call.message, ban_user)
        
        elif data == "admin_user_files":
            bot.send_message(user_id, "📁 Enter user ID:")
            bot.register_next_step_handler(call.message, view_user_files)
        
        elif data == "admin_hosting_on":
            update_setting('hosting_status', 'online')
            bot.send_message(user_id, "🟢 Hosting ONLINE")
        
        elif data == "admin_hosting_off":
            update_setting('hosting_status', 'offline')
            bot.send_message(user_id, "🔴 Hosting OFFLINE")
        
        elif data == "admin_auto_on":
            update_setting('auto_approve', 'true')
            bot.send_message(user_id, "✅ Auto Approve ON")
        
        elif data == "admin_auto_off":
            update_setting('auto_approve', 'false')
            bot.send_message(user_id, "❌ Auto Approve OFF")
        
        elif data == "admin_pending":
            pending = db_query("SELECT * FROM pending_approvals WHERE status = 'pending'", fetchall=True)
            if not pending:
                bot.send_message(user_id, "📋 No pending approvals!")
                return
            text = f"📋 Pending ({len(pending)})\n\n"
            for p in pending:
                text += f"• User: {p[1]} | Bot: {p[2]} | File: {p[3]}\n"
            bot.send_message(user_id, text)
        
        elif data == "admin_photo":
            bot.send_message(user_id, "🖼 Send photo:")
            bot.register_next_step_handler(call.message, change_photo)
        
        elif data == "admin_caption":
            bot.send_message(user_id, "✏️ Send caption:")
            bot.register_next_step_handler(call.message, change_caption)
        
        elif data == "admin_backup":
            if os.path.exists(DB_PATH):
                with open(DB_PATH, 'rb') as f:
                    bot.send_document(user_id, f)
                bot.send_message(user_id, "💾 Backup sent!")
        
        elif data == "admin_restart":
            bot.send_message(user_id, "♻ Restarting...")
            os.execv(sys.executable, ['python'] + sys.argv)

# =========================
# ADMIN FUNCTIONS
# =========================
def broadcast_message(message):
    if message.text == '/cancel':
        return
    users = db_query("SELECT user_id FROM users", fetchall=True)
    sent = 0
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            sent += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Sent to {sent} users!")

def add_user(message):
    try:
        user_id = int(message.text.strip())
        get_user(user_id)
        bot.send_message(message.chat.id, f"✅ User {user_id} added!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def ban_user(message):
    try:
        user_id = int(message.text.strip())
        user = get_user(user_id)
        new_status = 0 if user[4] == 1 else 1
        db_query("UPDATE users SET is_banned = ? WHERE user_id = ?", (new_status, user_id), commit=True)
        bot.send_message(message.chat.id, f"✅ User {'banned' if new_status == 1 else 'unbanned'}!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def view_user_files(message):
    try:
        user_id = int(message.text.strip())
        folder = f"users/{user_id}"
        if not os.path.exists(folder):
            bot.send_message(message.chat.id, "❌ No files!")
            return
        files = []
        for root, dirs, filenames in os.walk(folder):
            for f in filenames:
                files.append(f)
        text = f"📁 Files ({len(files)})\n\n" + "\n".join(files[:20])
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def change_photo(message):
    if message.photo:
        update_setting('welcome_photo', message.photo[-1].file_id)
        bot.send_message(message.chat.id, "✅ Photo updated!")

def change_caption(message):
    update_setting('welcome_caption', message.text)
    bot.send_message(message.chat.id, "✅ Caption updated!")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 Starting Hosting Bot...")
        print("=" * 50)
        
        init_database()
        
        db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (ADMIN_ID,), commit=True)
        print(f"✅ Admin set: {ADMIN_ID}")
        print("✅ Bot is running!")
        print("=" * 50)
        
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()