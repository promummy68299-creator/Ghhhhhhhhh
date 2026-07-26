# bot.py - COMPLETE FIXED WITH DATABASE + PATH
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
import traceback
from datetime import datetime
from pathlib import Path

import telebot
from telebot import types
import psutil

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = "8510272747:AAEXAjySmpDGM7zKccRclG00Orcmsjr8kFw"
ADMIN_ID = 7924753922
UPDATES_CHANNEL = "https://t.me/channellelu_pro"
OWNER_USERNAME = "https://t.me/pro_tg01"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
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
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_date TEXT,
        is_banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        storage_limit INTEGER DEFAULT 1073741824
    )''')
    
    # Bots table
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
        is_approved INTEGER DEFAULT 1,
        is_flagged INTEGER DEFAULT 0
    )''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Logs table
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_id INTEGER,
        log_type TEXT,
        message TEXT,
        timestamp TEXT
    )''')
    
    # Pending approvals table
    c.execute('''CREATE TABLE IF NOT EXISTS pending_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_id INTEGER,
        file_name TEXT,
        file_size INTEGER,
        uploaded_at TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # Default settings
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('hosting_status', 'online'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('auto_approve', 'true'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_photo', ''))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_caption', ''))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('updates_button', UPDATES_CHANNEL))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('contact_button', OWNER_USERNAME))
    
    conn.commit()
    conn.close()
    
    # Create directories
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
# REPLY KEYBOARD
# =========================
def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton("📤 Upload Bot"),
        types.KeyboardButton("📂 My Bots")
    )
    keyboard.add(
        types.KeyboardButton("⚡ Speed"),
        types.KeyboardButton("📊 Statistics")
    )
    keyboard.add(
        types.KeyboardButton("📢 Updates"),
        types.KeyboardButton("☎ Contact")
    )
    return keyboard

def admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton("👥 Users"),
        types.KeyboardButton("📊 Stats")
    )
    keyboard.add(
        types.KeyboardButton("📢 Broadcast"),
        types.KeyboardButton("➕ Add User")
    )
    keyboard.add(
        types.KeyboardButton("➖ Ban User"),
        types.KeyboardButton("📁 User Files")
    )
    keyboard.add(
        types.KeyboardButton("🟢 Hosting ON"),
        types.KeyboardButton("🔴 Hosting OFF")
    )
    keyboard.add(
        types.KeyboardButton("✅ Auto Approve ON"),
        types.KeyboardButton("❌ Auto Approve OFF")
    )
    keyboard.add(
        types.KeyboardButton("📋 Pending"),
        types.KeyboardButton("🚨 Flagged")
    )
    keyboard.add(
        types.KeyboardButton("🖼 Change Photo"),
        types.KeyboardButton("✏ Change Caption")
    )
    keyboard.add(
        types.KeyboardButton("💾 Backup DB"),
        types.KeyboardButton("♻ Restart")
    )
    keyboard.add(
        types.KeyboardButton("📋 Hosting Logs"),
        types.KeyboardButton("🔙 Back to Main")
    )
    return keyboard

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
                bots = db_query("SELECT * FROM bots WHERE status = 'running' AND is_approved = 1 AND is_flagged = 0", fetchall=True)
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
                return False, "Bot not found in database"
            
            if bot_data[12] != 1:
                return False, "Bot not approved"
            if bot_data[13] == 1:
                return False, "Bot flagged as suspicious"
            
            user_id = bot_data[1]
            bot_name = bot_data[2]
            bot_type = bot_data[3]
            file_path = bot_data[4]
            folder_path = bot_data[5]
            
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            # Create log file
            log_file = os.path.join(folder_path, f"{bot_name}_log.txt")
            
            # Write initial log
            with open(log_file, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write(f"BOT START ATTEMPT\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write(f"Bot Name: {bot_name}\n")
                f.write(f"Bot Type: {bot_type}\n")
                f.write(f"File Path: {file_path}\n")
                f.write(f"Folder Path: {folder_path}\n")
                f.write("=" * 60 + "\n\n")
            
            # Install dependencies
            if bot_type == 'python':
                req_file = os.path.join(folder_path, 'requirements.txt')
                if os.path.exists(req_file):
                    with open(log_file, 'a') as f:
                        f.write("\n=== INSTALLING REQUIREMENTS ===\n")
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '-r', req_file],
                        cwd=folder_path,
                        capture_output=True,
                        text=True
                    )
                    with open(log_file, 'a') as f:
                        f.write(f"STDOUT:\n{result.stdout}\n")
                        f.write(f"STDERR:\n{result.stderr}\n")
                        f.write("=" * 60 + "\n")
            
            elif bot_type == 'node':
                pkg_file = os.path.join(folder_path, 'package.json')
                if os.path.exists(pkg_file):
                    with open(log_file, 'a') as f:
                        f.write("\n=== INSTALLING NPM PACKAGES ===\n")
                    result = subprocess.run(
                        ['npm', 'install'],
                        cwd=folder_path,
                        capture_output=True,
                        text=True
                    )
                    with open(log_file, 'a') as f:
                        f.write(f"STDOUT:\n{result.stdout}\n")
                        f.write(f"STDERR:\n{result.stderr}\n")
                        f.write("=" * 60 + "\n")
            
            # ========== START BOT ==========
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            with open(log_file, 'a') as f:
                f.write(f"\n=== STARTING BOT AT {datetime.now()} ===\n")
                f.write(f"Command: {sys.executable} {file_path}\n")
                f.write("=" * 60 + "\n")
                f.flush()
            
            if bot_type == 'python':
                process = subprocess.Popen(
                    [sys.executable, '-u', file_path],
                    cwd=folder_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env
                )
            elif bot_type == 'node':
                process = subprocess.Popen(
                    ['node', file_path],
                    cwd=folder_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
            else:
                return False, f"Unsupported bot type: {bot_type}"
            
            db_query(
                "UPDATE bots SET process_id = ?, status = 'running', last_started = ? WHERE id = ?",
                (process.pid, datetime.now().isoformat(), bot_id),
                commit=True
            )
            
            self.processes[bot_id] = process
            
            # ========== CAPTURE LOGS ==========
            def capture_logs_thread():
                try:
                    with open(log_file, 'a') as f:
                        f.write(f"\n=== LOG CAPTURE STARTED ===\n")
                        f.flush()
                        
                        while process.poll() is None:
                            line = process.stdout.readline()
                            if line:
                                line = line.strip()
                                if line:
                                    f.write(f"{datetime.now().isoformat()} - {line}\n")
                                    f.flush()
                                    
                                    db_query(
                                        "INSERT INTO logs (user_id, bot_id, log_type, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                                        (user_id, bot_id, 'stdout', line, datetime.now().isoformat()),
                                        commit=True
                                    )
                        
                        f.write(f"\n=== BOT EXITED AT {datetime.now()} ===\n")
                        f.write(f"Exit Code: {process.returncode}\n")
                        
                        remaining = process.stdout.read()
                        if remaining:
                            f.write(f"\n=== REMAINING OUTPUT ===\n{remaining}\n")
                        
                        f.write("=" * 60 + "\n")
                        f.flush()
                        
                except Exception as e:
                    logger.error(f"Log capture error: {e}")
                    with open(log_file, 'a') as f:
                        f.write(f"\n=== LOG CAPTURE ERROR ===\n{str(e)}\n")
            
            threading.Thread(target=capture_logs_thread, daemon=True).start()
            
            # ========== CHECK IF BOT IS RUNNING ==========
            time.sleep(3)
            
            if process.poll() is not None:
                with open(log_file, 'r') as f:
                    full_log = f.read()
                
                try:
                    with open(log_file, 'rb') as f:
                        bot.send_document(ADMIN_ID, f, caption=f"📋 Error Logs: {bot_name}")
                except:
                    pass
                
                error_msg = full_log[-500:] if len(full_log) > 500 else full_log
                db_query(
                    "INSERT INTO logs (user_id, bot_id, log_type, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (user_id, bot_id, 'error', f"Bot exited: {error_msg[:300]}", datetime.now().isoformat()),
                    commit=True
                )
                
                db_query(
                    "UPDATE bots SET status = 'error' WHERE id = ?",
                    (bot_id,),
                    commit=True
                )
                
                return False, f"Bot exited immediately.\n\n📋 Check logs below:\n\n{error_msg[:500]}"
            
            return True, f"Bot started successfully (PID: {process.pid})"
            
        except Exception as e:
            logger.error(f"Error starting bot {bot_id}: {e}")
            error_trace = traceback.format_exc()
            return False, f"Error: {str(e)}\n\n{error_trace[:200]}"

    def stop_bot(self, bot_id):
        try:
            bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
            if not bot_data:
                return False, "Bot not found"
            
            process_id = bot_data[6]
            if process_id:
                try:
                    os.kill(process_id, 15)
                    time.sleep(2)
                    try:
                        os.kill(process_id, 9)
                    except:
                        pass
                except:
                    pass
            
            db_query(
                "UPDATE bots SET process_id = ?, status = 'stopped' WHERE id = ?",
                (None, bot_id),
                commit=True
            )
            
            if bot_id in self.processes:
                del self.processes[bot_id]
            
            return True, "Bot stopped successfully"
        except Exception as e:
            return False, str(e)

    def restart_bot(self, bot_id):
        self.stop_bot(bot_id)
        time.sleep(2)
        return self.start_bot(bot_id)
    
    def get_bot_logs(self, bot_id, limit=50):
        logs = db_query(
            "SELECT * FROM logs WHERE bot_id = ? ORDER BY timestamp DESC LIMIT ?",
            (bot_id, limit),
            fetchall=True
        )
        return logs[::-1] if logs else []

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
📌 Use buttons below 👇"""
    
    keyboard = main_keyboard()
    if is_admin(user_id):
        keyboard.add(types.KeyboardButton("🔧 Admin Panel"))
    
    bot.send_message(user_id, caption, reply_markup=keyboard, parse_mode='HTML')

# =========================
# REPLY BUTTON HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "📤 Upload Bot":
        bot.send_message(user_id, "📤 Send your bot file!\n\nSupported: .py, .js, .zip")
    
    elif text == "📂 My Bots":
        show_my_bots(user_id)
    
    elif text == "⚡ Speed":
        show_speed(user_id)
    
    elif text == "📊 Statistics":
        show_stats(user_id)
    
    elif text == "📢 Updates":
        updates = get_setting('updates_button') or UPDATES_CHANNEL
        bot.send_message(user_id, f"📢 Updates Channel:\n{updates}")
    
    elif text == "☎ Contact":
        contact = get_setting('contact_button') or OWNER_USERNAME
        bot.send_message(user_id, f"☎ Contact Owner:\n{contact}")
    
    elif text == "🔧 Admin Panel":
        if is_admin(user_id):
            bot.send_message(user_id, "🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard(), parse_mode='HTML')
        else:
            bot.send_message(user_id, "❌ Admin access required!")
    
    elif text == "📋 Hosting Logs":
        if is_admin(user_id):
            show_hosting_logs(user_id)
        else:
            bot.send_message(user_id, "❌ Admin access required!")
    
    elif text == "🔙 Back to Main":
        start_command(message)
    
    elif text == "👥 Users" and is_admin(user_id):
        show_users(user_id)
    
    elif text == "📊 Stats" and is_admin(user_id):
        show_admin_stats(user_id)
    
    elif text == "📢 Broadcast" and is_admin(user_id):
        bot.send_message(user_id, "📢 Send broadcast message (or type /cancel):")
        bot.register_next_step_handler(message, broadcast_message)
    
    elif text == "➕ Add User" and is_admin(user_id):
        bot.send_message(user_id, "➕ Enter user ID to add:")
        bot.register_next_step_handler(message, add_user)
    
    elif text == "➖ Ban User" and is_admin(user_id):
        bot.send_message(user_id, "➖ Enter user ID to ban/unban:")
        bot.register_next_step_handler(message, ban_user_from_admin)
    
    elif text == "📁 User Files" and is_admin(user_id):
        bot.send_message(user_id, "📁 Enter user ID to view files:")
        bot.register_next_step_handler(message, view_user_files)
    
    elif text == "🟢 Hosting ON" and is_admin(user_id):
        update_setting('hosting_status', 'online')
        bot.send_message(user_id, "🟢 Hosting set to ONLINE!")
    
    elif text == "🔴 Hosting OFF" and is_admin(user_id):
        update_setting('hosting_status', 'offline')
        bot.send_message(user_id, "🔴 Hosting set to OFFLINE!")
    
    elif text == "✅ Auto Approve ON" and is_admin(user_id):
        update_setting('auto_approve', 'true')
        bot.send_message(user_id, "✅ Auto Approve turned ON!")
    
    elif text == "❌ Auto Approve OFF" and is_admin(user_id):
        update_setting('auto_approve', 'false')
        bot.send_message(user_id, "❌ Auto Approve turned OFF!")
    
    elif text == "📋 Pending" and is_admin(user_id):
        show_pending(user_id)
    
    elif text == "🚨 Flagged" and is_admin(user_id):
        show_flagged(user_id)
    
    elif text == "🖼 Change Photo" and is_admin(user_id):
        bot.send_message(user_id, "🖼 Send new welcome photo:")
        bot.register_next_step_handler(message, change_photo)
    
    elif text == "✏ Change Caption" and is_admin(user_id):
        bot.send_message(user_id, "✏️ Send new welcome caption:")
        bot.register_next_step_handler(message, change_caption)
    
    elif text == "💾 Backup DB" and is_admin(user_id):
        backup_database(user_id)
    
    elif text == "♻ Restart" and is_admin(user_id):
        bot.send_message(user_id, "♻ Restarting panel...")
        os.execv(sys.executable, ['python'] + sys.argv)
    
    else:
        if not text.startswith('/'):
            bot.send_message(user_id, "❌ Unknown command. Use /start")

# =========================
# SHOW HOSTING LOGS
# =========================
def show_hosting_logs(user_id):
    try:
        log_file = "bot.log"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
            
            if len(logs) > 4000:
                logs = logs[-4000:] + "\n\n... (truncated)"
            
            bot.send_message(
                user_id,
                f"📋 <b>Hosting Bot Logs</b>\n\n<code>{logs}</code>",
                parse_mode='HTML'
            )
        else:
            bot.send_message(user_id, "📋 No hosting logs found!")
        
        errors = db_query(
            "SELECT * FROM logs WHERE log_type = 'error' ORDER BY timestamp DESC LIMIT 20",
            fetchall=True
        )
        
        if errors:
            text = "🚨 <b>Recent Errors</b>\n\n"
            for err in errors:
                text += f"• {err[4][:19]} - {err[3][:100]}\n"
            bot.send_message(user_id, text, parse_mode='HTML')
            
    except Exception as e:
        bot.send_message(user_id, f"❌ Error reading logs: {str(e)}")

# =========================
# FILE HANDLER - FIXED PATH
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
        bot.send_message(user_id, "❌ Only .py, .js, .zip files supported!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload"))
    
    msg = bot.send_message(
        user_id,
        f"📝 <b>Enter Bot Name</b>\n\n"
        f"📂 File: {file_name}\n"
        f"📦 Size: {file_size/1024:.2f}KB\n"
        f"📝 Type: {bot_type}\n\n"
        f"Send bot name (letters, numbers, underscores only):",
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_bot_name, file_info, file_name, file_size, bot_type)

def process_bot_name(message, file_info, file_name, file_size, bot_type):
    user_id = message.from_user.id
    bot_name = message.text.strip()
    
    if bot_name == "/cancel" or bot_name == "❌ Cancel":
        bot.send_message(user_id, "❌ Upload cancelled!")
        return
    
    if not bot_name or not all(c.isalnum() or c == '_' for c in bot_name):
        bot.send_message(user_id, "❌ Invalid name! Use letters, numbers, underscores only.")
        return
    
    existing = db_query("SELECT * FROM bots WHERE user_id = ? AND bot_name = ?", (user_id, bot_name), fetchone=True)
    if existing:
        bot.send_message(user_id, f"❌ Bot '{bot_name}' already exists!")
        return
    
    try:
        downloaded_file = bot.download_file(file_info.file_path)
        
        # ========== FIX: CORRECT PATH ==========
        # Create folder: users/user_id/bot_name
        bot_folder = os.path.join("users", str(user_id), bot_name)
        os.makedirs(bot_folder, exist_ok=True)
        
        # File path: users/user_id/bot_name/file_name
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
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO bots (user_id, bot_name, bot_type, file_path, folder_path, status, created_at, is_approved, is_flagged) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, bot_name, bot_type, file_path, bot_folder, 'stopped', datetime.now().isoformat(), is_approved, 0)
        )
        bot_id = c.lastrowid
        conn.commit()
        
        c.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
        bot_check = c.fetchone()
        conn.close()
        
        if not bot_check:
            bot.send_message(user_id, "❌ Database error! Bot not saved. Try again.")
            return
        
        user_info = db_query("SELECT first_name, username FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        user_name = user_info[0] if user_info else "Unknown"
        
        admin_msg = f"""📥 <b>New Bot Uploaded</b>
👤 User: {user_name}
🆔 User ID: <code>{user_id}</code>
🤖 Bot Name: {bot_name}
📝 Type: {bot_type}
📂 File: {file_name}
📦 Size: {file_size/1024:.2f}KB
✅ Auto Approve: {'ON' if auto_approve == 'true' else 'OFF'}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚠️ <b>Review this file!</b>"""
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        if auto_approve == 'true':
            success, msg = bot_manager.start_bot(bot_id)
            
            if success:
                bot.send_message(user_id, f"✅ Bot '{bot_name}' started successfully!\n\n{msg}")
            else:
                bot.send_message(user_id, f"⚠️ Bot uploaded but failed to start!\n\n❌ Error: {msg}")
            
            keyboard.add(
                types.InlineKeyboardButton("🚨 Flag", callback_data=f"flag_{bot_id}"),
                types.InlineKeyboardButton("📥 Download", callback_data=f"download_{bot_id}")
            )
            keyboard.add(
                types.InlineKeyboardButton("👤 Ban User", callback_data=f"banuser_{user_id}"),
                types.InlineKeyboardButton("🗑 Delete", callback_data=f"deletebot_{bot_id}")
            )
            
            try:
                with open(file_path, 'rb') as f:
                    bot.send_document(ADMIN_ID, f, caption=admin_msg, reply_markup=keyboard)
            except:
                bot.send_message(ADMIN_ID, admin_msg, reply_markup=keyboard)
        else:
            db_query(
                "INSERT INTO pending_approvals (user_id, bot_id, file_name, file_size, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, bot_id, file_name, file_size, datetime.now().isoformat()),
                commit=True
            )
            
            keyboard.add(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{bot_id}"),
                types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{bot_id}")
            )
            keyboard.add(
                types.InlineKeyboardButton("📥 Download", callback_data=f"download_{bot_id}"),
                types.InlineKeyboardButton("🚨 Flag", callback_data=f"flag_{bot_id}")
            )
            
            try:
                with open(file_path, 'rb') as f:
                    bot.send_document(ADMIN_ID, f, caption=admin_msg, reply_markup=keyboard)
            except:
                bot.send_message(ADMIN_ID, admin_msg, reply_markup=keyboard)
            
            bot.send_message(user_id, f"⏳ Bot '{bot_name}' uploaded! Pending admin approval.")
    
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
    
    if data == "cancel_upload":
        bot.answer_callback_query(call.id, "❌ Upload cancelled!")
        bot.edit_message_text("❌ Upload cancelled!", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return
    
    if data.startswith("flag_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        bot_id = int(data.split("_")[1])
        flag_bot(call, bot_id)
        return
    
    elif data.startswith("banuser_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        target_user = int(data.split("_")[1])
        ban_user_from_callback(call, target_user)
        return
    
    elif data.startswith("deletebot_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        bot_id = int(data.split("_")[1])
        delete_bot_from_admin(call, bot_id)
        return
    
    elif data.startswith("download_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        bot_id = int(data.split("_")[1])
        download_bot_file(call, bot_id)
        return
    
    elif data.startswith("approve_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        bot_id = int(data.split("_")[1])
        approve_bot(call, bot_id)
        return
    
    elif data.startswith("reject_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        bot_id = int(data.split("_")[1])
        reject_bot(call, bot_id)
        return
    
    elif data.startswith("bot_"):
        parts = data.split("_")
        bot_id = int(parts[1])
        action = parts[2] if len(parts) > 2 else "info"
        
        if action == "info":
            show_bot_info(user_id, bot_id)
        elif action == "start":
            start_user_bot(user_id, bot_id)
        elif action == "stop":
            stop_user_bot(user_id, bot_id)
        elif action == "restart":
            restart_user_bot(user_id, bot_id)
        elif action == "delete":
            delete_user_bot(user_id, bot_id)
        elif action == "logs":
            show_bot_logs(user_id, bot_id)

# =========================
# ADMIN ACTION FUNCTIONS
# =========================
def flag_bot(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    bot_manager.stop_bot(bot_id)
    db_query("UPDATE bots SET is_flagged = 1, status = 'flagged' WHERE id = ?", (bot_id,), commit=True)
    
    user_id = bot_data[1]
    bot_name = bot_data[2]
    
    try:
        bot.send_message(user_id, f"🚨 Your bot '{bot_name}' has been <b>FLAGGED</b> as suspicious!\n\n❌ Bot stopped.\n📞 Contact admin.", parse_mode='HTML')
    except:
        pass
    
    bot.edit_message_text(f"🚨 Bot '{bot_name}' flagged!", chat_id=call.from_user.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id, "🚨 Flagged!")

def ban_user_from_callback(call, target_user):
    user = get_user(target_user)
    if not user:
        bot.send_message(call.from_user.id, "❌ User not found!")
        return
    
    db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_user,), commit=True)
    
    bots = db_query("SELECT id FROM bots WHERE user_id = ?", (target_user,), fetchall=True)
    for bot_data in bots:
        bot_manager.stop_bot(bot_data[0])
    
    try:
        bot.send_message(target_user, "🚨 <b>You have been BANNED!</b>\n\n❌ Your bots stopped.", parse_mode='HTML')
    except:
        pass
    
    bot.edit_message_text(f"✅ User {target_user} BANNED!", chat_id=call.from_user.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id, "✅ Banned!")

def delete_bot_from_admin(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    user_id = bot_data[1]
    bot_name = bot_data[2]
    folder_path = bot_data[5]
    
    bot_manager.stop_bot(bot_id)
    
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    db_query("DELETE FROM bots WHERE id = ?", (bot_id,), commit=True)
    db_query("DELETE FROM logs WHERE bot_id = ?", (bot_id,), commit=True)
    
    try:
        bot.send_message(user_id, f"🗑 Your bot '{bot_name}' has been <b>DELETED</b> by admin!", parse_mode='HTML')
    except:
        pass
    
    bot.edit_message_text(f"🗑 Bot '{bot_name}' deleted!", chat_id=call.from_user.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id, "🗑 Deleted!")

def download_bot_file(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    file_path = bot_data[4]
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            bot.send_document(call.from_user.id, f, caption=f"📥 {os.path.basename(file_path)}")
        bot.answer_callback_query(call.id, "📥 Downloaded!")
    else:
        bot.send_message(call.from_user.id, "❌ File not found!")

def approve_bot(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    db_query("UPDATE bots SET is_approved = 1, is_flagged = 0 WHERE id = ?", (bot_id,), commit=True)
    db_query("UPDATE pending_approvals SET status = 'approved' WHERE bot_id = ?", (bot_id,), commit=True)
    
    user_id = bot_data[1]
    bot_name = bot_data[2]
    
    success, msg = bot_manager.start_bot(bot_id)
    
    try:
        bot.send_message(user_id, f"✅ Bot '{bot_name}' APPROVED!\n\n{msg}")
    except:
        pass
    
    bot.edit_message_text(f"✅ Bot '{bot_name}' approved!", chat_id=call.from_user.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id, "✅ Approved!")

def reject_bot(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    user_id = bot_data[1]
    bot_name = bot_data[2]
    folder_path = bot_data[5]
    
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    db_query("DELETE FROM bots WHERE id = ?", (bot_id,), commit=True)
    db_query("DELETE FROM pending_approvals WHERE bot_id = ?", (bot_id,), commit=True)
    
    try:
        bot.send_message(user_id, f"❌ Bot '{bot_name}' REJECTED!")
    except:
        pass
    
    bot.edit_message_text(f"❌ Bot '{bot_name}' rejected!", chat_id=call.from_user.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id, "❌ Rejected!")

# =========================
# USER BOT FUNCTIONS
# =========================
def show_my_bots(user_id):
    bots = db_query("SELECT * FROM bots WHERE user_id = ?", (user_id,), fetchall=True)
    if not bots:
        bot.send_message(user_id, "📂 No bots found!\n\nUse Upload button to add one.")
        return
    
    text = "📂 <b>Your Bots</b>\n\n"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    for bot_data in bots:
        status = "🟢 Running" if bot_data[7] == "running" else "🔴 Stopped" if bot_data[7] == "stopped" else "🚨 Flagged"
        if bot_data[12] == 0:
            status = "⏳ Pending"
        text += f"• <b>{bot_data[2]}</b> ({bot_data[3]}) - {status}\n"
        keyboard.add(types.InlineKeyboardButton(bot_data[2], callback_data=f"bot_{bot_data[0]}_info"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def show_bot_info(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    status_text = bot_data[7]
    if bot_data[13] == 1:
        status_text = "🚨 FLAGGED"
    elif bot_data[12] == 0:
        status_text = "⏳ Pending"
    
    text = f"""📊 <b>{bot_data[2]}</b>
📝 Type: {bot_data[3]}
🔢 PID: {bot_data[6] or 'N/A'}
🔴 Status: {status_text}
📅 Created: {bot_data[8]}
🔄 Started: {bot_data[9] or 'Never'}"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    if bot_data[12] == 1 and bot_data[13] == 0:
        if bot_data[7] == "running":
            keyboard.add(
                types.InlineKeyboardButton("⏹ Stop", callback_data=f"bot_{bot_id}_stop"),
                types.InlineKeyboardButton("🔄 Restart", callback_data=f"bot_{bot_id}_restart")
            )
        else:
            keyboard.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"bot_{bot_id}_start"))
    
    keyboard.add(
        types.InlineKeyboardButton("📋 Logs", callback_data=f"bot_{bot_id}_logs"),
        types.InlineKeyboardButton("🗑 Delete", callback_data=f"bot_{bot_id}_delete")
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Back", callback_data="my_bots"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def start_user_bot(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    if bot_data[13] == 1:
        bot.send_message(user_id, "🚨 Bot flagged! Cannot start.")
        return
    
    if bot_data[12] != 1:
        bot.send_message(user_id, "⏳ Bot pending approval!")
        return
    
    if get_hosting_status() == 'offline':
        bot.send_message(user_id, "🔴 Hosting offline!")
        return
    
    success, msg = bot_manager.start_bot(bot_id)
    bot.send_message(user_id, f"✅ {msg}" if success else f"❌ {msg}")
    show_bot_info(user_id, bot_id)

def stop_user_bot(user_id, bot_id):
    success, msg = bot_manager.stop_bot(bot_id)
    bot.send_message(user_id, f"✅ {msg}" if success else f"❌ {msg}")
    show_bot_info(user_id, bot_id)

def restart_user_bot(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    if bot_data[13] == 1:
        bot.send_message(user_id, "🚨 Bot flagged! Cannot restart.")
        return
    
    if get_hosting_status() == 'offline':
        bot.send_message(user_id, "🔴 Hosting offline!")
        return
    
    success, msg = bot_manager.restart_bot(bot_id)
    bot.send_message(user_id, f"✅ {msg}" if success else f"❌ {msg}")
    show_bot_info(user_id, bot_id)

def delete_user_bot(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    bot_manager.stop_bot(bot_id)
    
    if os.path.exists(bot_data[5]):
        shutil.rmtree(bot_data[5])
    
    db_query("DELETE FROM bots WHERE id = ?", (bot_id,), commit=True)
    db_query("DELETE FROM logs WHERE bot_id = ?", (bot_id,), commit=True)
    
    bot.send_message(user_id, "✅ Bot deleted!")
    show_my_bots(user_id)

def show_bot_logs(user_id, bot_id):
    logs = bot_manager.get_bot_logs(bot_id, 50)
    if not logs:
        bot.send_message(user_id, "📋 No logs available!")
        return
    
    text = "📋 <b>Recent Logs</b>\n\n"
    for log in logs:
        text += f"{log[4][:19]} - {log[3]}\n"
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (truncated)"
    
    bot.send_message(user_id, text)

def show_speed(user_id):
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    text = f"""⚡ <b>System Status</b>
💻 CPU: {cpu}%
🧠 RAM: {mem.used/(1024**3):.2f}GB / {mem.total/(1024**3):.2f}GB
💾 Disk: {disk.used/(1024**3):.2f}GB / {disk.total/(1024**3):.2f}GB"""
    
    bot.send_message(user_id, text)

def show_stats(user_id):
    total = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ?", (user_id,), fetchone=True)[0]
    running = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND status = 'running'", (user_id,), fetchone=True)[0]
    pending = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND is_approved = 0", (user_id,), fetchone=True)[0]
    flagged = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND is_flagged = 1", (user_id,), fetchone=True)[0]
    
    text = f"""📊 <b>Your Statistics</b>
📦 Total Bots: {total}
🟢 Running: {running}
⏳ Pending: {pending}
🚨 Flagged: {flagged}
🔴 Stopped: {total - running - pending - flagged}"""
    
    bot.send_message(user_id, text)

# =========================
# ADMIN FUNCTIONS
# =========================
def show_users(user_id):
    users = db_query("SELECT * FROM users", fetchall=True)
    text = "👥 <b>Users</b>\n\n"
    
    for u in users[:20]:
        bots_count = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ?", (u[0],), fetchone=True)[0]
        flagged = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND is_flagged = 1", (u[0],), fetchone=True)[0]
        text += f"• {u[2]} (ID: {u[0]})\n  Bots: {bots_count} | Flagged: {flagged} | Banned: {'✅' if u[4] else '❌'}\n\n"
    
    if len(users) > 20:
        text += f"... and {len(users)-20} more"
    
    bot.send_message(user_id, text)

def show_admin_stats(user_id):
    total_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
    total_bots = db_query("SELECT COUNT(*) FROM bots", fetchone=True)[0]
    running_bots = db_query("SELECT COUNT(*) FROM bots WHERE status = 'running'", fetchone=True)[0]
    pending_bots = db_query("SELECT COUNT(*) FROM bots WHERE is_approved = 0", fetchone=True)[0]
    flagged_bots = db_query("SELECT COUNT(*) FROM bots WHERE is_flagged = 1", fetchone=True)[0]
    
    text = f"""📊 <b>System Statistics</b>
👥 Users: {total_users}
📦 Bots: {total_bots}
🟢 Running: {running_bots}
⏳ Pending: {pending_bots}
🚨 Flagged: {flagged_bots}
🔴 Stopped: {total_bots - running_bots - pending_bots - flagged_bots}
💾 DB Size: {os.path.getsize(DB_PATH)/1024:.2f}KB"""
    
    bot.send_message(user_id, text)

def show_pending(user_id):
    pending = db_query("SELECT * FROM pending_approvals WHERE status = 'pending'", fetchall=True)
    if not pending:
        bot.send_message(user_id, "📋 No pending approvals!")
        return
    
    text = f"📋 <b>Pending Approvals ({len(pending)})</b>\n\n"
    for p in pending:
        text += f"• User: {p[1]} | Bot: {p[2]} | File: {p[3]}\n"
    
    bot.send_message(user_id, text)

def show_flagged(user_id):
    flagged = db_query("SELECT * FROM bots WHERE is_flagged = 1", fetchall=True)
    if not flagged:
        bot.send_message(user_id, "✅ No flagged bots!")
        return
    
    text = f"🚨 <b>Flagged Bots ({len(flagged)})</b>\n\n"
    for b in flagged:
        text += f"• {b[2]} (User: {b[1]})\n  Status: {b[7]}\n\n"
    
    bot.send_message(user_id, text)

def broadcast_message(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Cancelled!")
        return
    
    users = db_query("SELECT user_id FROM users", fetchall=True)
    sent = 0
    failed = 0
    
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    bot.send_message(message.chat.id, f"✅ Sent: {sent}\n❌ Failed: {failed}")

def add_user(message):
    try:
        user_id = int(message.text.strip())
        get_user(user_id)
        bot.send_message(message.chat.id, f"✅ User {user_id} added!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def ban_user_from_admin(message):
    try:
        user_id = int(message.text.strip())
        user = get_user(user_id)
        if not user:
            bot.send_message(message.chat.id, "❌ User not found!")
            return
        
        new_status = 0 if user[4] == 1 else 1
        db_query("UPDATE users SET is_banned = ? WHERE user_id = ?", (new_status, user_id), commit=True)
        
        if new_status == 1:
            bots = db_query("SELECT id FROM bots WHERE user_id = ?", (user_id,), fetchall=True)
            for bot_data in bots:
                bot_manager.stop_bot(bot_data[0])
        
        status_text = "banned" if new_status == 1 else "unbanned"
        bot.send_message(message.chat.id, f"✅ User {user_id} {status_text}!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def view_user_files(message):
    try:
        user_id = int(message.text.strip())
        folder = os.path.join("users", str(user_id))
        
        if not os.path.exists(folder):
            bot.send_message(message.chat.id, "❌ No files!")
            return
        
        files = []
        for root, dirs, filenames in os.walk(folder):
            for f in filenames:
                path = os.path.join(root, f)
                size = os.path.getsize(path)
                rel_path = os.path.relpath(path, folder)
                files.append(f"📄 {rel_path} ({size/1024:.2f}KB)")
        
        if not files:
            bot.send_message(message.chat.id, "📁 Empty folder!")
            return
        
        text = f"📁 <b>User {user_id} Files</b>\n\n"
        text += "\n".join(files[:30])
        if len(files) > 30:
            text += f"\n\n... and {len(files)-30} more"
        
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def change_photo(message):
    if message.photo:
        update_setting('welcome_photo', message.photo[-1].file_id)
        bot.send_message(message.chat.id, "✅ Photo updated!")
    else:
        bot.send_message(message.chat.id, "❌ Send a photo!")

def change_caption(message):
    update_setting('welcome_caption', message.text)
    bot.send_message(message.chat.id, "✅ Caption updated!")

def backup_database(user_id):
    if os.path.exists(DB_PATH):
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, backup_file)
        with open(backup_file, 'rb') as f:
            bot.send_document(user_id, f)
        os.remove(backup_file)
        bot.send_message(user_id, "💾 Database backup sent!")
    else:
        bot.send_message(user_id, "❌ Database not found!")

# =========================
# HELP COMMAND
# =========================
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        """📚 <b>Help</b>
/start - Welcome message
/admin - Admin panel
/help - This message

📤 <b>Upload Bot</b>
Send .py, .js, or .zip file

⚡ <b>Features</b>
• Auto install dependencies
• Auto restart on crash
• Live logs
• File manager

📞 Support: @pro_tg01""",
        parse_mode='HTML'
    )

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 Starting 24x7 Hosting Bot...")
        print("=" * 60)
        
        # Force re-create database
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print("✅ Old database removed")
        
        init_database()
        db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (ADMIN_ID,), commit=True)
        
        print(f"✅ Admin set: {ADMIN_ID}")
        print("✅ Bot is running!")
        print("=" * 60)
        
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()