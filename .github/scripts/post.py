#!/usr/bin/env python
import telebot
from telebot import types
import os
import json
import datetime
import sys

DEVICE_ORDER = [
    "beyond0lte", "beyond1lte", "beyond2lte", "beyondx",
    "d1", "d1x", "d2s", "d2x", "f62"
]

def getConfig(config_name: str):
    return os.getenv(config_name)

try:
    BOT_TOKEN = getConfig("TELEGRAM_BOT_TOKEN")
    CHAT_IDS = [x for x in getConfig("TELEGRAM_CHANNEL_ID").split(" ")]
except (KeyError, AttributeError):
    print("Error: Ensure TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID are set.")
    exit(1)

BANNER_PATH = "./assets/rom-banner.jpg"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def get_ordinal_date_string(dt):
    day = dt.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return dt.strftime(f"{day}{suffix} %B %Y")

def format_size(size_bytes):
    if not size_bytes:
        return "N/A"
    gb = size_bytes / (1024 ** 3)
    return f"{gb:.2f} GB"

def process_device_files(file_paths: list):
    common_info = {}
    unique_devices = {}

    DEVICE_NAME_MAP = {
        "beyond0lte": "Galaxy S10e",
        "beyond1lte": "Galaxy S10",
        "beyond2lte": "Galaxy S10+",
        "beyondx": "Galaxy S10 5G",
        "d1": "Galaxy N10",
        "d1x": "Galaxy N10 5G",
        "d2s": "Galaxy N10+",
        "d2x": "Galaxy N10+ 5G",
        "f62": "Galaxy F62"
    }

    try:
        with open("changelog.md", "r") as f:
            device_changelog = f.read()
    except FileNotFoundError:
        device_changelog = "Changelog not found."

    for file_path in file_paths:
        try:
            with open(file_path, 'r') as device_file:
                raw_data = json.load(device_file)
                if 'response' in raw_data and isinstance(raw_data['response'], list):
                    info = raw_data['response'][0]
                else:
                    info = raw_data

                filename_base = os.path.basename(file_path)
                codename = filename_base.split('.')[0]
                device_name = DEVICE_NAME_MAP.get(codename, 'Unknown Device')

                download_link = f"https://projectinfinity-x.com/downloads/{codename}"

                version = info.get('version', '')
                timestamp = info.get('timestamp', 0)
                size = info.get('size', 0)
                md5 = info.get('md5', '')

                actual_filename = info.get('filename', '')
                json_download_url = info.get('download', '')
                is_gapps = 'gapps' in actual_filename.lower() or 'gapps' in json_download_url.lower()

                if codename not in unique_devices:
                    unique_devices[codename] = {
                        "device_name": device_name,
                        "codename": codename,
                        "download": download_link,
                        "version": version,
                        "vanilla_details": None,
                        "gapps_details": None
                    }

                details = {
                    "size": size,
                    "md5": md5,
                    "filename": actual_filename if actual_filename else "Unknown_Filename.zip"
                }

                if is_gapps:
                    unique_devices[codename]['gapps_details'] = details
                else:
                    unique_devices[codename]['vanilla_details'] = details

                if not common_info:
                    dt = datetime.datetime.now()
                    common_info = {
                        "rom_version": version if version else "3.4",
                        "datetime": dt,
                        "device_changelog": device_changelog
                    }
                elif not common_info.get('rom_version') and version:
                    common_info['rom_version'] = version

        except Exception as e:
            print(f"Could not process file {file_path}: {e}")
            continue

    return common_info, list(unique_devices.values())

def generate_post_content(common_info, device):
    date_str = get_ordinal_date_string(common_info['datetime'])
    ver = common_info.get('rom_version', '3.4')
    if not ver.startswith('v'): ver = f"v{ver}"

    msg = (f"<b>New Release of Project Infinity X {ver} for {device['device_name']} ({device['codename']}) is Up!</b>\n\n")
    msg += f"<b>By</b> <a href='https://t.me/FrEeRuNnEr4EvEr'>@FrEeRuNnEr4EvEr</a>\n\n"

    if common_info['device_changelog'] and common_info['device_changelog'].strip() != "Changelog not found.":
        msg += f"<b>Device Changelog:</b>\n"
        msg += f"{common_info['device_changelog']}\n\n"

    if device['vanilla_details']:
        d = device['vanilla_details']
        msg += f"▫️ <b>Variant:</b> Vanilla\n"
        msg += f"▫️ <b>File:</b> {d['filename']}\n"
        msg += f"▫️ <b>Size:</b> {format_size(d['size'])}\n"
        if d['md5']:
            msg += f"▫️ <b>MD5:</b> <code>{d['md5']}</code>\n"
        msg += "\n"

    if device['gapps_details']:
        d = device['gapps_details']
        msg += f"▫️ <b>Variant:</b> GAPPS (Google Apps Included)\n"
        msg += f"▫️ <b>File:</b> {d['filename']}\n"
        msg += f"▫️ <b>Size:</b> {format_size(d['size'])}\n"
        if d['md5']:
            msg += f"▫️ <b>MD5:</b> <code>{d['md5']}</code>\n"
        msg += "\n"

    msg += f"▫️ <b>Date:</b> {date_str}\n"
    msg += f"▫️ <b>Donate:</b> <a href='https://www.paypal.me/FrEeRuNnEr4EvEr2023'>PayPal</a>\n\n"

    msg += "⭐️ Wanna have a look at some ROM Screenshots? - <a href='https://projectinfinity-x.com/#screenshots'>Click Here</a>\n"
    msg += "💬 Reach Support If have any queries - <a href='https://t.me/FrEeRuNnEr4EvErHeLp'>Click Here</a>\n\n"

    msg += f"#Android16 #{device['codename']} @ProjectInfinityX"

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_dl = types.InlineKeyboardButton("Download", url=device['download'])
    btn_changelog = types.InlineKeyboardButton("Changelog (Source)", url="https://t.me/ProjectInfinityX/1610")
    btn_flash = types.InlineKeyboardButton("Flash Guide", url=device['download'])

    markup.add(btn_dl)
    markup.add(btn_changelog, btn_flash)

    return msg, markup

def send_post(chat_id, image, caption, markup):
    try:
        with open(image, "rb") as banner:
            bot.send_photo(chat_id=chat_id, photo=banner, caption=caption, reply_markup=markup)
            print(f"Successfully sent post to chat ID: {chat_id}")
    except Exception as e:
        print(f"Failed to send post to {chat_id}. Error: {e}")

if __name__ == "__main__":
    file_paths = sys.argv[1:]
    if not file_paths:
        print("No changed files provided. Exiting.")
        exit(1)

    print(f"Processing {len(file_paths)} device files...")
    common_info, device_list = process_device_files(file_paths)

    if not common_info:
        print("Could not gather info. Exiting.")
        exit(1)

    print(f"Generating posts for {len(device_list)} devices...")

    def sort_key(d):
        try:
            return DEVICE_ORDER.index(d['codename'])
        except ValueError:
            return len(DEVICE_ORDER)

    sorted_devices = sorted(device_list, key=sort_key)

    for device in sorted_devices:
        print(f"Sending post for {device['codename']}...")
        message, reply_markup = generate_post_content(common_info, device)

        for chat in CHAT_IDS:
            send_post(chat, BANNER_PATH, message, reply_markup)
