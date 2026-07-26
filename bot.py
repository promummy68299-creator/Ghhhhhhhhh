# bot.py - Complete Production Ready Hosting Bot
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
from typing import Dict, List, Optional, Tuple

import telebot
from telebot import types
import psutil

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = "8840844556:AAGE7ZARs6Bq2WfyQ5KKx-KtP2ZdOYE71uw"
ADMIN_ID = 7924753922  # Apni ID dalo
OWNER_USERNAME = "@pro_tg01"
UPDATES_CHANNEL = "@channellelu_pro"

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
        last_name TEXT,
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
        FOREIGN KEY (user_id) REFERENCES users (user_id)
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
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (bot_id) REFERENCES bots (id)
    )''')
    
    # Pending approvals
    c.execute('''CREATE TABLE IF NOT EXISTS pending_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_id INTEGER,
        file_name TEXT,
        file_size INTEGER,
        uploaded_at TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (bot_id) REFERENCES bots (id)
    )''')
    
    # Insert default settings
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('hosting_status', 'online'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('auto_approve', 'true'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_photo', ''))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_caption', ''))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('updates_button', UPDATES_CHANNEL))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('contact_button', OWNER_USERNAME))
    
    conn.commit()
    conn.close()
    
    # Create directories
    os.makedirs('hosting', exist_ok=True)
    os.makedirs('users', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('pending', exist_ok=True)
    
    logger.info("Database initialized")

# =========================
# DATABASE HELPERS
# =========================
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
            last_name = user_info.last_name or ""
        except:
            username = ""
            first_name = ""
            last_name = ""
        
        db_query(
            "INSERT INTO users (user_id, username, first_name, last_name, joined_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, datetime.now().isoformat()),
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
    return user[6] == 1 if user else False

def get_hosting_status():
    return get_setting('hosting_status') or 'online'

def get_auto_approve():
    return get_setting('auto_approve') or 'true'

# =========================
# FILE MANAGEMENT
# =========================
def get_user_folder(user_id):
    folder = f"users/{user_id}"
    os.makedirs(folder, exist_ok=True)
    return folder

def get_bot_folder(user_id, bot_name):
    folder = f"users/{user_id}/{bot_name}"
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_storage_usage(user_id):
    folder = get_user_folder(user_id)
    total = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total

def get_user_storage_limit(user_id):
    user = get_user(user_id)
    return user[7] if user else 1073741824

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
                    bot_id = bot_data[0]
                    process_id = bot_data[6]
                    
                    if process_id:
                        try:
                            os.kill(process_id, 0)
                        except OSError:
                            logger.info(f"Bot {bot_data[2]} crashed, restarting...")
                            self.restart_bot(bot_id)
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
            
            # Install dependencies
            if bot_type == 'python':
                req_file = os.path.join(folder_path, 'requirements.txt')
                if os.path.exists(req_file):
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_file], 
                                 capture_output=True, text=True)
            elif bot_type == 'node':
                pkg_file = os.path.join(folder_path, 'package.json')
                if os.path.exists(pkg_file):
                    subprocess.run(['npm', 'install'], cwd=folder_path, capture_output=True, text=True)
            
            # Start process
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
            
            return True, f"Bot started successfully (PID: {process.pid})"
        
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
            
            return True, "Bot stopped successfully"
        
        except Exception as e:
            return False, str(e)

    def restart_bot(self, bot_id):
        self.stop_bot(bot_id)
        time.sleep(2)
        return self.start_bot(bot_id)

    def get_bot_logs(self, bot_id, limit=100):
        logs = db_query(
            "SELECT * FROM logs WHERE bot_id = ? ORDER BY timestamp DESC LIMIT ?",
            (bot_id, limit),
            fetchall=True
        )
        return logs[::-1]

bot_manager = BotManager()

# =========================
# START COMMAND
# =========================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    get_user(user_id)
    
    # Auto-unban
    if is_banned(user_id):
        db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,), commit=True)
        bot.send_message(user_id, "✅ You have been unbanned automatically!")
    
    # Get settings
    welcome_photo = get_setting('welcome_photo')
    welcome_caption = get_setting('welcome_caption')
    updates_button = get_setting('updates_button') or UPDATES_CHANNEL
    contact_button = get_setting('contact_button') or OWNER_USERNAME
    hosting_status = get_hosting_status()
    auto_approve = get_auto_approve()
    
    first_name = message.from_user.first_name or "User"
    used = get_user_storage_usage(user_id)
    limit = get_user_storage_limit(user_id)
    used_mb = used / (1024 * 1024)
    limit_mb = limit / (1024 * 1024)
    
    # Count bots
    total_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ?", (user_id,), fetchone=True)[0]
    running_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND status = 'running'", (user_id,), fetchone=True)[0]
    
    # Prepare caption
    if welcome_caption:
        caption = welcome_caption.replace('{first_name}', first_name).replace('{user_id}', str(user_id))
        caption = caption.replace('{used}', f"{used_mb:.2f}MB").replace('{limit}', f"{limit_mb:.2f}MB")
        caption = caption.replace('{total_bots}', str(total_bots)).replace('{running_bots}', str(running_bots))
    else:
        caption = f"""🔥 <b>24x7 Hosting Bot</b>

👋 Welcome {first_name}

🟢 <b>Status:</b> {hosting_status.upper()}
✅ <b>Auto Approve:</b> {'ON' if auto_approve == 'true' else 'OFF'}

🆔 <b>User ID:</b>
<code>{user_id}</code>

📂 <b>Storage Used:</b>
{used_mb:.2f}MB / {limit_mb:.2f}MB

📦 <b>Your Bots:</b>
Total: {total_bots} | Running: {running_bots}

⚡ <b>Features</b>
• Python & NodeJS Hosting
• Auto Install Dependencies
• 24x7 Uptime
• Live Logs
• Auto Restart
• File Manager
• Storage Tracking

👇 Use buttons below"""
    
    # Create keyboard
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
    
    # Send message
    if welcome_photo:
        try:
            bot.send_photo(user_id, welcome_photo, caption=caption, reply_markup=keyboard)
            return
        except:
            pass
    
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
    
    auto_approve = get_auto_approve()
    hosting_status = get_hosting_status()
    
    bot.send_message(
        user_id,
        f"""🔧 <b>Admin Panel</b>

🟢 Hosting: {hosting_status.upper()}
✅ Auto Approve: {'ON' if auto_approve == 'true' else 'OFF'}

Select an option:""",
        reply_markup=keyboard
    )

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
    
    # Check storage
    used = get_user_storage_usage(user_id)
    limit = get_user_storage_limit(user_id)
    if used + file_size > limit:
        bot.send_message(user_id, f"❌ Storage limit exceeded! {used/(1024*1024):.2f}MB / {limit/(1024*1024):.2f}MB")
        return
    
    # Check file type
    if file_name.endswith('.zip'):
        bot_type = 'zip'
    elif file_name.endswith('.py'):
        bot_type = 'python'
    elif file_name.endswith('.js'):
        bot_type = 'node'
    else:
        bot.send_message(user_id, "❌ Only .zip, .py, .js files supported!")
        return
    
    # Ask for bot name
    msg = bot.reply_to(message, "📝 Enter bot name (letters, numbers, underscores only):")
    bot.register_next_step_handler(msg, process_bot_name, file_info, file_name, file_size, bot_type)

def process_bot_name(message, file_info, file_name, file_size, bot_type):
    user_id = message.from_user.id
    bot_name = message.text.strip()
    
    if not bot_name or not all(c.isalnum() or c == '_' for c in bot_name):
        bot.send_message(user_id, "❌ Invalid name! Use letters, numbers, underscores only.")
        return
    
    # Check duplicate
    existing = db_query("SELECT * FROM bots WHERE user_id = ? AND bot_name = ?", (user_id, bot_name), fetchone=True)
    if existing:
        bot.send_message(user_id, f"❌ Bot '{bot_name}' already exists!")
        return
    
    try:
        # Download file
        downloaded_file = bot.download_file(file_info.file_path)
        bot_folder = get_bot_folder(user_id, bot_name)
        file_path = os.path.join(bot_folder, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # Extract zip
        if bot_type == 'zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(bot_folder)
            
            # Find main file
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
            
            # Move main file to root
            main_name = os.path.basename(main_file)
            new_path = os.path.join(bot_folder, main_name)
            shutil.move(main_file, new_path)
            file_path = new_path
        
        # Auto approve
        auto_approve = get_auto_approve()
        is_approved = 1 if auto_approve == 'true' else 0
        
        # Save to database
        db_query(
            """INSERT INTO bots 
            (user_id, bot_name, bot_type, file_path, folder_path, status, created_at, is_approved) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, bot_name, bot_type, file_path, bot_folder, 'stopped', datetime.now().isoformat(), is_approved),
            commit=True
        )
        
        bot_id = db_query("SELECT last_insert_rowid()", fetchone=True)[0]
        
        if auto_approve == 'true':
            # Auto start
            success, msg = bot_manager.start_bot(bot_id)
            if success:
                bot.send_message(user_id, f"✅ Bot '{bot_name}' started successfully!\n\n{msg}")
            else:
                bot.send_message(user_id, f"⚠️ Bot uploaded but failed to start!\n\nError: {msg}")
            
            # Notify admin
            admin_msg = f"📥 <b>New Bot (Auto-Approved)</b>\n\n"
            admin_msg += f"👤 User: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
            admin_msg += f"🆔 ID: {user_id}\n"
            admin_msg += f"🤖 Bot: {bot_name}\n"
            admin_msg += f"📝 Type: {bot_type}\n"
            admin_msg += f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            bot.send_message(ADMIN_ID, admin_msg)
        else:
            # Pending approval
            db_query(
                "INSERT INTO pending_approvals (user_id, bot_id, file_name, file_size, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, bot_id, file_name, file_size, datetime.now().isoformat()),
                commit=True
            )
            
            bot.send_message(
                user_id,
                f"⏳ Bot '{bot_name}' uploaded!\n\n📝 Status: <b>Pending Approval</b>\n\nAdmin will review shortly.",
            )
            
            # Notify admin with buttons
            admin_msg = f"📥 <b>New Bot - Pending Approval</b>\n\n"
            admin_msg += f"👤 User: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
            admin_msg += f"🆔 ID: {user_id}\n"
            admin_msg += f"🤖 Bot: {bot_name}\n"
            admin_msg += f"📝 Type: {bot_type}\n"
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{bot_id}"),
                types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{bot_id}")
            )
            keyboard.add(
                types.InlineKeyboardButton("📥 Download", callback_data=f"download_{bot_id}")
            )
            
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error uploading bot: {e}")
        bot.send_message(user_id, f"❌ Error: {str(e)}")

# =========================
# CALLBACK HANDLER
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ You are banned!")
        return
    
    # Approve/Reject/Download handlers
    if data.startswith("approve_"):
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
    
    elif data.startswith("download_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        bot_id = int(data.split("_")[1])
        download_bot_file(call, bot_id)
        return
    
    # User actions
    if data == "upload":
        bot.answer_callback_query(call.id)
        if get_hosting_status() == 'offline':
            bot.send_message(user_id, "🔴 Hosting is offline!")
            return
        auto_approve = get_auto_approve()
        status = "Auto-Approved" if auto_approve == 'true' else "Manual Approval"
        bot.send_message(
            user_id,
            f"📤 <b>Upload Your Bot</b>\n\n"
            f"✅ Mode: {status}\n\n"
            f"Supported:\n"
            f"• .zip (Python/Node.js)\n"
            f"• .py (Python)\n"
            f"• .js (Node.js)\n\n"
            f"Send your file now!",
        )
    
    elif data == "my_bots":
        bot.answer_callback_query(call.id)
        show_my_bots(user_id)
    
    elif data == "speed":
        bot.answer_callback_query(call.id)
        show_speed(user_id)
    
    elif data == "stats":
        bot.answer_callback_query(call.id)
        show_stats(user_id)
    
    # Bot actions
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
        elif action == "rename":
            bot.send_message(user_id, "📝 Enter new name:")
            bot.register_next_step_handler(call.message, rename_bot, bot_id)
        elif action == "files":
            show_bot_files(user_id, bot_id)
    
    # Admin actions
    elif data.startswith("admin_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        admin_callback_handler(call)

# =========================
# APPROVAL FUNCTIONS
# =========================
def approve_bot(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    db_query("UPDATE bots SET is_approved = 1 WHERE id = ?", (bot_id,), commit=True)
    db_query("UPDATE pending_approvals SET status = 'approved' WHERE bot_id = ?", (bot_id,), commit=True)
    
    user_id = bot_data[1]
    bot_name = bot_data[2]
    
    # Start bot
    success, msg = bot_manager.start_bot(bot_id)
    
    # Notify user
    try:
        user_msg = f"✅ Your bot '{bot_name}' has been <b>APPROVED</b>!"
        if success:
            user_msg += f"\n\n{msg}"
        bot.send_message(user_id, user_msg)
    except:
        pass
    
    bot.edit_message_text(
        f"✅ Bot '{bot_name}' approved and started!",
        chat_id=call.from_user.id,
        message_id=call.message.message_id
    )
    bot.answer_callback_query(call.id, "✅ Approved!")

def reject_bot(call, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ?", (bot_id,), fetchone=True)
    if not bot_data:
        bot.send_message(call.from_user.id, "❌ Bot not found!")
        return
    
    user_id = bot_data[1]
    bot_name = bot_data[2]
    folder_path = bot_data[5]
    
    # Delete files
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    # Delete from database
    db_query("DELETE FROM bots WHERE id = ?", (bot_id,), commit=True)
    db_query("DELETE FROM pending_approvals WHERE bot_id = ?", (bot_id,), commit=True)
    
    # Notify user
    try:
        bot.send_message(user_id, f"❌ Your bot '{bot_name}' has been <b>REJECTED</b>.")
    except:
        pass
    
    bot.edit_message_text(
        f"❌ Bot '{bot_name}' rejected!",
        chat_id=call.from_user.id,
        message_id=call.message.message_id
    )
    bot.answer_callback_query(call.id, "❌ Rejected!")

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
        bot_id = bot_data[0]
        bot_name = bot_data[2]
        bot_type = bot_data[3]
        status = bot_data[7]
        is_approved = bot_data[12]
        
        status_emoji = "🟢" if status == "running" else "🔴" if status == "stopped" else "🟡"
        if is_approved == 0:
            status_emoji = "⏳"
            status = "Pending"
        
        text += f"{status_emoji} <b>{bot_name}</b> ({bot_type})\n"
        text += f"  Status: {status}\n\n"
        
        keyboard.add(
            types.InlineKeyboardButton(f"📊 {bot_name}", callback_data=f"bot_{bot_id}_info")
        )
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def show_bot_info(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    bot_id, _, bot_name, bot_type, file_path, folder_path, process_id, status, created_at, last_started, memory, cpu, is_approved = bot_data
    
    status_emoji = "🟢" if status == "running" else "🔴" if status == "stopped" else "🟡"
    if is_approved == 0:
        status_emoji = "⏳"
        status = "Pending Approval"
    
    text = f"""📊 <b>Bot: {bot_name}</b>

📝 Type: {bot_type}
📂 Folder: {folder_path}
📄 File: {os.path.basename(file_path)}
🔢 PID: {process_id or 'N/A'}
{status_emoji} Status: {status}
✅ Approved: {'Yes' if is_approved == 1 else 'No'}
📅 Created: {created_at}
🔄 Last Started: {last_started or 'Never'}
💾 Memory: {memory or 0}MB
⚡ CPU: {cpu or 0}%"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    
    if is_approved == 1:
        if status == 'running':
            buttons.append(types.InlineKeyboardButton("⏹ Stop", callback_data=f"bot_{bot_id}_stop"))
            buttons.append(types.InlineKeyboardButton("🔄 Restart", callback_data=f"bot_{bot_id}_restart"))
        else:
            buttons.append(types.InlineKeyboardButton("▶️ Start", callback_data=f"bot_{bot_id}_start"))
        
        buttons.append(types.InlineKeyboardButton("📋 Logs", callback_data=f"bot_{bot_id}_logs"))
        buttons.append(types.InlineKeyboardButton("📁 Files", callback_data=f"bot_{bot_id}_files"))
    
    buttons.append(types.InlineKeyboardButton("✏️ Rename", callback_data=f"bot_{bot_id}_rename"))
    buttons.append(types.InlineKeyboardButton("🗑 Delete", callback_data=f"bot_{bot_id}_delete"))
    
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("🔙 Back", callback_data="my_bots"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def start_user_bot(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    if bot_data[12] != 1:
        bot.send_message(user_id, "❌ Bot not approved!")
        return
    
    if get_hosting_status() == 'offline':
        bot.send_message(user_id, "🔴 Hosting is offline!")
        return
    
    success, msg = bot_manager.start_bot(bot_id)
    if success:
        bot.send_message(user_id, f"✅ Bot started!\n\n{msg}")
    else:
        bot.send_message(user_id, f"❌ Failed to start!\n\n{msg}")
    
    show_bot_info(user_id, bot_id)

def stop_user_bot(user_id, bot_id):
    success, msg = bot_manager.stop_bot(bot_id)
    if success:
        bot.send_message(user_id, "✅ Bot stopped!")
    else:
        bot.send_message(user_id, f"❌ Failed to stop!\n\n{msg}")
    show_bot_info(user_id, bot_id)

def restart_user_bot(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    if bot_data[12] != 1:
        bot.send_message(user_id, "❌ Bot not approved!")
        return
    
    if get_hosting_status() == 'offline':
        bot.send_message(user_id, "🔴 Hosting is offline!")
        return
    
    success, msg = bot_manager.restart_bot(bot_id)
    if success:
        bot.send_message(user_id, f"✅ Bot restarted!\n\n{msg}")
    else:
        bot.send_message(user_id, f"❌ Failed to restart!\n\n{msg}")
    show_bot_info(user_id, bot_id)

def delete_user_bot(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    bot_manager.stop_bot(bot_id)
    
    folder_path = bot_data[5]
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    db_query("DELETE FROM bots WHERE id = ?", (bot_id,), commit=True)
    db_query("DELETE FROM logs WHERE bot_id = ?", (bot_id,), commit=True)
    db_query("DELETE FROM pending_approvals WHERE bot_id = ?", (bot_id,), commit=True)
    
    bot.send_message(user_id, "✅ Bot deleted!")
    show_my_bots(user_id)

def show_bot_logs(user_id, bot_id):
    logs = bot_manager.get_bot_logs(bot_id)
    
    if not logs:
        bot.send_message(user_id, "📋 No logs available!")
        return
    
    text = f"📋 <b>Bot Logs (Last {len(logs)})</b>\n\n"
    for log in logs[-50:]:
        timestamp = log[4]
        message = log[3]
        log_type = log[2]
        emoji = "ℹ️" if log_type == "stdout" else "⚠️"
        text += f"{emoji} [{timestamp}] {message}\n"
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (truncated)"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔄 Refresh", callback_data=f"bot_{bot_id}_logs"))
    keyboard.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_{bot_id}_info"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def show_bot_files(user_id, bot_id):
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    folder_path = bot_data[5]
    if not os.path.exists(folder_path):
        bot.send_message(user_id, "❌ Folder not found!")
        return
    
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for f in filenames:
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            rel_path = os.path.relpath(path, folder_path)
            files.append(f"📄 {rel_path} ({size/1024:.2f}KB)")
    
    if not files:
        bot.send_message(user_id, "📁 No files found!")
        return
    
    text = f"📁 <b>Bot Files: {bot_data[2]}</b>\n\n"
    text += "\n".join(files[:30])
    if len(files) > 30:
        text += f"\n\n... and {len(files)-30} more"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_{bot_id}_info"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def rename_bot(message, bot_id):
    user_id = message.from_user.id
    new_name = message.text.strip()
    
    if not new_name or not all(c.isalnum() or c == '_' for c in new_name):
        bot.send_message(user_id, "❌ Invalid name!")
        return
    
    existing = db_query("SELECT * FROM bots WHERE user_id = ? AND bot_name = ?", (user_id, new_name), fetchone=True)
    if existing:
        bot.send_message(user_id, f"❌ '{new_name}' already exists!")
        return
    
    bot_data = db_query("SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id), fetchone=True)
    if not bot_data:
        bot.send_message(user_id, "❌ Bot not found!")
        return
    
    old_folder = bot_data[5]
    new_folder = f"users/{user_id}/{new_name}"
    
    if os.path.exists(old_folder):
        os.rename(old_folder, new_folder)
    
    db_query(
        "UPDATE bots SET bot_name = ?, folder_path = ? WHERE id = ?",
        (new_name, new_folder, bot_id),
        commit=True
    )
    
    bot.send_message(user_id, f"✅ Renamed to '{new_name}'!")
    show_bot_info(user_id, bot_id)

# =========================
# SPEED & STATS
# =========================
def show_speed(user_id):
    bots = db_query("SELECT id, bot_name, status, memory_usage, cpu_usage FROM bots WHERE user_id = ? AND is_approved = 1", (user_id,), fetchall=True)
    
    text = "⚡ <b>Bot Performance</b>\n\n"
    
    if not bots:
        text += "No running bots."
    else:
        for bot_data in bots:
            bot_name = bot_data[1]
            status = bot_data[2]
            memory = bot_data[3] or 0
            cpu = bot_data[4] or 0
            memory_mb = memory / 1024 if memory else 0
            text += f"• <b>{bot_name}</b>\n"
            text += f"  Status: {status}\n"
            text += f"  CPU: {cpu:.1f}%\n"
            text += f"  Memory: {memory_mb:.2f}MB\n\n"
    
    # System stats
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    text += f"📊 <b>System</b>\n"
    text += f"CPU: {cpu_percent}%\n"
    text += f"RAM: {memory.used/(1024**3):.2f}GB / {memory.total/(1024**3):.2f}GB\n"
    text += f"Disk: {disk.used/(1024**3):.2f}GB / {disk.total/(1024**3):.2f}GB"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="speed"))
    keyboard.add(types.InlineKeyboardButton("🔙 Back", callback_data="my_bots"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

def show_stats(user_id):
    total_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ?", (user_id,), fetchone=True)[0]
    running_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND status = 'running'", (user_id,), fetchone=True)[0]
    pending_bots = db_query("SELECT COUNT(*) FROM bots WHERE user_id = ? AND is_approved = 0", (user_id,), fetchone=True)[0]
    used = get_user_storage_usage(user_id)
    limit = get_user_storage_limit(user_id)
    
    user = get_user(user_id)
    
    text = f"""📊 <b>Your Statistics</b>

📦 Total Bots: {total_bots}
🟢 Running: {running_bots}
⏳ Pending: {pending_bots}
🔴 Stopped: {total_bots - running_bots - pending_bots}

💾 Storage: {used/(1024*1024):.2f}MB / {limit/(1024*1024):.2f}MB
📅 Joined: {user[4]}"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="stats"))
    keyboard.add(types.InlineKeyboardButton("🔙 Back", callback_data="my_bots"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

# =========================
# ADMIN CALLBACK HANDLER
# =========================
def admin_callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    if data == "admin_users":
        users = db_query("SELECT * FROM users ORDER BY joined_date DESC", fetchall=True)
        text = "👥 <b>Users</b>\n\n"
        for user in users[:20]:
            text += f"• <a href='tg://user?id={user[0]}'>{user[2] or user[0]}</a>\n"
            text += f"  ID: {user[0]}\n"
            text += f"  Bots: {db_query('SELECT COUNT(*) FROM bots WHERE user_id = ?', (user[0],), fetchone=True)[0]}\n"
            text += f"  Banned: {'Yes' if user[6] else 'No'}\n\n"
        
        if len(users) > 20:
            text += f"\n... and {len(users)-20} more"
        
        bot.send_message(user_id, text)
    
    elif data == "admin_stats":
        total_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        total_bots = db_query("SELECT COUNT(*) FROM bots", fetchone=True)[0]
        running_bots = db_query("SELECT COUNT(*) FROM bots WHERE status = 'running'", fetchone=True)[0]
        pending_bots = db_query("SELECT COUNT(*) FROM bots WHERE is_approved = 0", fetchone=True)[0]
        total_logs = db_query("SELECT COUNT(*) FROM logs", fetchone=True)[0]
        
        text = f"""📊 <b>System Statistics</b>

👥 Users: {total_users}
📦 Bots: {total_bots}
🟢 Running: {running_bots}
⏳ Pending: {pending_bots}
🔴 Stopped: {total_bots - running_bots - pending_bots}
📋 Logs: {total_logs}
💾 DB Size: {os.path.getsize(DB_PATH)/1024:.2f}KB"""
        
        bot.send_message(user_id, text)
    
    elif data == "admin_pending":
        pending = db_query(
            """SELECT p.*, b.bot_name, b.bot_type, u.first_name 
               FROM pending_approvals p 
               JOIN bots b ON p.bot_id = b.id 
               JOIN users u ON p.user_id = u.user_id 
               WHERE p.status = 'pending'""",
            fetchall=True
        )
        
        if not pending:
            bot.send_message(user_id, "📋 No pending approvals!")
            return
        
        text = f"📋 <b>Pending Approvals ({len(pending)})</b>\n\n"
        for p in pending:
            text += f"• <b>{p[7]}</b> ({p[8]})\n"
            text += f"  User: {p[9]} (ID: {p[1]})\n"
            text += f"  File: {p[3]}\n\n"
        
        keyboard = types.InlineKeyboardMarkup()
        for p in pending:
            bot_id = p[2]
            keyboard.add(
                types.InlineKeyboardButton(f"✅ {p[7]}", callback_data=f"approve_{bot_id}"),
                types.InlineKeyboardButton(f"❌ Reject", callback_data=f"reject_{bot_id}")
            )
        
        bot.send_message(user_id, text, reply_markup=keyboard)
    
    elif data == "admin_broadcast":
        bot.send_message(user_id, "📢 Send broadcast message (or /cancel):")
        bot.register_next_step_handler(call.message, broadcast_message)
    
    elif data == "admin_add_user":
        bot.send_message(user_id, "➕ Enter user ID to add:")
        bot.register_next_step_handler(call.message, add_user)
    
    elif data == "admin_ban_user":
        bot.send_message(user_id, "➖ Enter user ID to ban/unban:")
        bot.register_next_step_handler(call.message, ban_user)
    
    elif data == "admin_user_files":
        bot.send_message(user_id, "📁 Enter user ID to view files:")
        bot.register_next_step_handler(call.message, view_user_files)
    
    elif data == "admin_hosting_on":
        update_setting('hosting_status', 'online')
        bot.send_message(user_id, "🟢 Hosting set to ONLINE!")
        admin_command(call.message)
    
    elif data == "admin_hosting_off":
        running_bots = db_query("SELECT id FROM bots WHERE status = 'running'", fetchall=True)
        for bot_data in running_bots:
            bot_manager.stop_bot(bot_data[0])
        update_setting('hosting_status', 'offline')
        bot.send_message(user_id, "🔴 Hosting set to OFFLINE!")
        admin_command(call.message)
    
    elif data == "admin_auto_on":
        update_setting('auto_approve', 'true')
        bot.send_message(user_id, "✅ Auto Approve turned ON!")
        admin_command(call.message)
    
    elif data == "admin_auto_off":
        update_setting('auto_approve', 'false')
        bot.send_message(user_id, "❌ Auto Approve turned OFF!")
        admin_command(call.message)
    
    elif data == "admin_photo":
        bot.send_message(user_id, "🖼 Send new welcome photo:")
        bot.register_next_step_handler(call.message, change_welcome_photo)
    
    elif data == "admin_caption":
        bot.send_message(
            user_id,
            "✏️ Send new caption (use variables:\n"
            "{first_name}, {user_id}, {used}, {limit}, {total_bots}, {running_bots})"
        )
        bot.register_next_step_handler(call.message, change_welcome_caption)
    
    elif data == "admin_backup":
        if os.path.exists(DB_PATH):
            backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(DB_PATH, backup)
            with open(backup, 'rb') as f:
                bot.send_document(user_id, f)
            os.remove(backup)
            bot.send_message(user_id, "💾 Database backup sent!")
        else:
            bot.send_message(user_id, "❌ Database not found!")
    
    elif data == "admin_restart":
        bot.send_message(user_id, "♻ Restarting...")
        os.execv(sys.executable, ['python'] + sys.argv)

# =========================
# ADMIN FUNCTIONS
# =========================
def broadcast_message(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Broadcast cancelled!")
        return
    
    users = db_query("SELECT user_id FROM users", fetchall=True)
    sent = 0
    failed = 0
    
    bot.send_message(message.chat.id, f"📢 Broadcasting to {len(users)} users...")
    
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    bot.send_message(message.chat.id, f"✅ Done!\nSent: {sent}\nFailed: {failed}")

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
        if not user:
            bot.send_message(message.chat.id, "❌ User not found!")
            return
        
        new_status = 0 if user[6] == 1 else 1
        db_query("UPDATE users SET is_banned = ? WHERE user_id = ?", (new_status, user_id), commit=True)
        
        status_text = "banned" if new_status == 1 else "unbanned"
        bot.send_message(message.chat.id, f"✅ User {user_id} {status_text}!")
        
        if new_status == 1:
            bots = db_query("SELECT id FROM bots WHERE user_id = ?", (user_id,), fetchall=True)
            for bot_data in bots:
                bot_manager.stop_bot(bot_data[0])
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def view_user_files(message):
    try:
        user_id = int(message.text.strip())
        folder = get_user_folder(user_id)
        
        if not os.path.exists(folder):
            bot.send_message(message.chat.id, "❌ Folder not found!")
            return
        
        files = []
        for root, dirs, filenames in os.walk(folder):
            for f in filenames:
                path = os.path.join(root, f)
                size = os.path.getsize(path)
                rel_path = os.path.relpath(path, folder)
                files.append(f"📄 {rel_path} ({size/1024:.2f}KB)")
        
        if not files:
            bot.send_message(message.chat.id, "📁 No files!")
            return
        
        text = f"📁 <b>User {user_id} Files</b>\n\n"
        text += "\n".join(files[:30])
        if len(files) > 30:
            text += f"\n\n... and {len(files)-30} more"
        
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def change_welcome_photo(message):
    if message.photo:
        file_id = message.photo[-1].file_id
        update_setting('welcome_photo', file_id)
        bot.send_message(message.chat.id, "✅ Photo updated!")
    else:
        bot.send_message(message.chat.id, "❌ Send a photo!")

def change_welcome_caption(message):
    caption = message.text
    update_setting('welcome_caption', caption)
    bot.send_message(message.chat.id, "✅ Caption updated!")

# =========================
# HELP COMMAND
# =========================
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        """📚 <b>Help</b>

/start - Welcome
/admin - Admin panel
/help - This message

📤 <b>Hosting</b>
Upload .py, .js, or .zip files to host your bots!

✅ <b>Features</b>
• Auto dependency install
• 24x7 uptime
• Auto restart on crash
• Live logs
• File manager
• Storage tracking

For support: @owner""",
    )

# =========================
# ERROR HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_message(
        message.chat.id,
        "❌ Unknown command. Use /start or /help"
    )

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 Starting 24x7 Hosting Bot...")
        print("=" * 60)
        
        init_database()
        print("✅ Database initialized")
        
        # Set admin
        db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (ADMIN_ID,), commit=True)
        print(f"✅ Admin set: {ADMIN_ID}")
        
        print("✅ Bot is running!")
        print("=" * 60)
        
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()