#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
import telebot

# ─── SET YOUR TOKEN HERE ──────────────────────
BOT_TOKEN = '8829210946:AAHyN5M79HHoFtvpGyI9wK4r0ldTRadUF5s'   # <-- CHANGE THIS
# ──────────────────────────────────────────────

if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    print("❌ ERROR: BOT_TOKEN not set! Exiting.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start_cmd(msg):
    bot.reply_to(msg, "✅ Bot is alive! /start works.")

if __name__ == '__main__':
    logger.info("Test bot starting...")
    try:
        bot.infinity_polling(timeout=60, threaded=False)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        sys.exit(1)