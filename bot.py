import re
import aiohttp
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========== CONFIGURE THESE ===========
API_ID = 29569239  # your api_id from my.telegram.org
API_HASH = "b2407514e15f24c8ec2c735e8018acd7"
BOT_TOKEN = "7617922225:AAE7xRwHXK--FWUo_MdlaKm1ZT-7gkuu4Nk"  # Get a new one from @BotFather

SOURCE_GROUPS = [-1002621183707]  # Telegram group ID where the bot listens for messages
TARGET_CHANNEL = -1002871766358   # Must be an integer (no quotes), and bot must be an admin

MAIN_CHANNEL_LINK = "https://t.me/approvedccm"
BACKUP_CHANNEL_LINK = "https://t.me/+70mI9Ce2U_JlMGJl"
# =======================================

# Enable logging to see issues
logging.basicConfig(level=logging.INFO)

app = Client("scrbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= Utility Functions ===================

async def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "scheme": data.get("scheme", "UNKNOWN").upper(),
                        "type": data.get("type", "UNKNOWN").upper(),
                        "brand": data.get("brand", "UNKNOWN").upper(),
                        "bank": data.get("bank", "UNKNOWN"),
                        "country": data.get("country_name", "UNKNOWN"),
                        "flag": data.get("country_flag", "🌍"),
                    }
    except Exception as e:
        logging.warning(f"BIN lookup failed: {e}")
    return {
        "scheme": "UNKNOWN", "type": "UNKNOWN", "brand": "UNKNOWN",
        "bank": "UNKNOWN", "country": "UNKNOWN", "flag": "🌍"
    }

def extract_credit_cards(text):
    pattern = r'(\d{13,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})'
    return re.findall(pattern, text or "")

def format_card_message(cc, bin_info):
    card_number, month, year, cvv = cc
    bin_number = card_number[:6]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        "[ϟ] 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 𝐒𝐜𝐫𝐚𝐩𝐩𝐞𝐫\n"
        "━━━━━━━━━━━━━\n"
        f"[ϟ] 𝗖𝗖 - <code>{card_number}|{month}|{year}|{cvv}</code>\n"
        "[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀 : APPROVED ✅\n"
        "[ϟ] 𝗚𝗮𝘁𝗲 - Stripe Auth\n"
        "━━━━━━━━━━━━━\n"
        f"[ϟ] 𝗕𝗶𝗻 : {bin_number}\n"
        f"[ϟ] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : {bin_info['country']} {bin_info['flag']}\n"
        f"[ϟ] 𝗜𝘀𝘀𝘂𝗲𝗿 : {bin_info['bank']}\n"
        f"[ϟ] 𝗧𝘆𝗽𝗲 : {bin_info['type']} - {bin_info['brand']}\n"
        "━━━━━━━━━━━━━\n"
        f"[ϟ] 𝗧𝗶𝗺𝗲 : {timestamp}\n"
        "[ϟ] 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗱 𝗕𝘆 : Bᴜɴɴʏ"
    )

# ================= Listener ===================

@app.on_message(filters.chat(SOURCE_GROUPS))
async def cc_scraper(client, message):
    text = message.text or message.caption
    cards = extract_credit_cards(text)
    if not cards:
        return

    for cc in cards:
        bin_number = cc[0][:6]
        bin_info = await get_bin_info(bin_number)
        msg = format_card_message(cc, bin_info)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Main Channel", url=MAIN_CHANNEL_LINK),
                InlineKeyboardButton("Backup Channel", url=BACKUP_CHANNEL_LINK),
            ]
        ])

        try:
            await app.send_message(
                TARGET_CHANNEL,
                msg,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            logging.error(f"Send error: {e} -- retrying without parse_mode")
            try:
                await app.send_message(
                    TARGET_CHANNEL,
                    msg,
                    reply_markup=keyboard
                )
            except Exception as e2:
                logging.error(f"Second send attempt failed: {e2}")

# ================ Run Bot ==================

print("✅ Bot is running. Press Ctrl+C to stop.")
app.run()
