#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
import time
import sys
from functools import wraps

import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== ONLY 2 VALUES TO SET ==========
BOT_TOKEN = '8829210946:AAFKpvBcvJ1xDRHnDdLHHrtIYIDqsWeUYDk'           # ⚠️ CHANGE THIS
API_URL = 'https://linkvio.gt.tc'           # ⚠️ CHANGE THIS
# ===========================================

if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    print("❌ ERROR: BOT_TOKEN not set! Exiting.")
    sys.exit(1)

API_KEY = 'f8a7d9e3c4b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1'
FORCE_JOIN_CHANNEL = ''   # optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

def force_join_required(func):
    @wraps(func)
    def wrapper(msg, *args, **kwargs):
        if not FORCE_JOIN_CHANNEL:
            return func(msg, *args, **kwargs)
        try:
            ch = FORCE_JOIN_CHANNEL.lstrip('@')
            member = bot.get_chat_member(f'@{ch}', msg.from_user.id)
            if member.status in ['member', 'administrator', 'creator']:
                return func(msg, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Force join error: {e}")
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_JOIN_CHANNEL.lstrip('@')}"))
        bot.reply_to(msg, f"🚫 Please join {FORCE_JOIN_CHANNEL} first.", reply_markup=kb)
        return None
    return wrapper

def api_call(endpoint, method='GET', payload=None, params=None):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {'X-API-Key': API_KEY}
    if payload:
        headers['Content-Type'] = 'application/json'
    for attempt in range(3):
        try:
            if method.upper() == 'POST':
                r = requests.post(url, json=payload, headers=headers, timeout=10)
            else:
                r = requests.get(url, params=params, headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    return {'error': 'API unreachable'}

def get_admin():
    return api_call('admin').get('admin_id')

def set_admin(admin_id):
    return api_call('admin/set', method='POST', payload={'admin_id': str(admin_id)})

def get_user_stats(user_id):
    return api_call('stats/user', params={'user_id': str(user_id)})

def get_admin_stats():
    return api_call('stats/admin')

def shorten_url(url, user_id):
    return api_call('shorten', method='POST', payload={'url': url, 'user_id': str(user_id)})

@bot.message_handler(commands=['start'])
@force_join_required
def start_cmd(msg):
    user_id = msg.from_user.id
    admin = get_admin()
    if admin is None:
        resp = set_admin(user_id)
        if resp and resp.get('success'):
            bot.reply_to(msg, f"👑 You are now the admin of this bot!")
        else:
            bot.reply_to(msg, "⚠️ Could not set admin. Please try again.")
    else:
        bot.reply_to(msg, f"👋 Hello {msg.from_user.first_name}!\nSend me a URL to shorten.\nUse /help for commands.")

@bot.message_handler(commands=['help'])
@force_join_required
def help_cmd(msg):
    text = (
        "📖 **Commands**\n"
        "/start – welcome\n"
        "/help – this message\n"
        "/stats – show your links with click counts\n"
        "🔗 Just send any HTTP/HTTPS URL and I'll shorten it."
    )
    bot.reply_to(msg, text)

@bot.message_handler(commands=['stats'])
@force_join_required
def stats_cmd(msg):
    user_id = msg.from_user.id
    data = get_user_stats(user_id)
    reply = ""
    admin = get_admin()
    if str(user_id) == str(admin):
        admin_data = get_admin_stats()
        if 'error' not in admin_data:
            reply += f"📊 **Admin Stats**\nTotal links: {admin_data.get('total_links',0)}\nTotal clicks: {admin_data.get('total_clicks',0)}\n\n"
    if 'error' not in data and 'links' in data:
        links = data['links']
        if links:
            total_clicks = sum(link['clicks'] for link in links)
            reply += f"📈 **Your Links**\nTotal: {len(links)} links, {total_clicks} clicks\n\n"
            for link in links[:10]:
                reply += f"🔗 <code>{link['shortcode']}</code> → {link['clicks']} clicks\n"
            if len(links) > 10:
                reply += f"... and {len(links)-10} more."
        else:
            reply += "📭 You haven't created any links yet."
    else:
        reply += "❌ Could not retrieve your stats."
    bot.reply_to(msg, reply, parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
@force_join_required
def handle_url(msg):
    url = msg.text.strip()
    if not re.match(r'^https?://', url):
        bot.reply_to(msg, "❌ Invalid URL. Use http:// or https://")
        return
    bot.send_chat_action(msg.chat.id, 'typing')
    result = shorten_url(url, msg.from_user.id)
    if result and 'shortcode' in result:
        short = f"{API_URL.rstrip('/')}/{result['shortcode']}"
        bot.reply_to(msg, f"✅ Short link: <a href='{short}'>{short}</a>", disable_web_page_preview=True)
    else:
        bot.reply_to(msg, "❌ Error shortening. Please try again.")

if __name__ == '__main__':
    logger.info("Bot starting...")
    try:
        # ✅ FIX: removed threaded=False and extra arguments
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        sys.exit(1)