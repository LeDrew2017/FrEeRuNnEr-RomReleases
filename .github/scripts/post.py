#!/usr/bin/env python
import telebot
import os
import json
import datetime
import sys
import re

DEVICE_ORDER = [
    "beyond0lte", "beyond1lte", "beyond2lte", "beyondx",
    "d1", "d1x", "d2s", "d2x", "f62"
]

DEVICE_NAME_MAP = {
    "beyond0lte": "Galaxy S10e",
    "beyond1lte": "Galaxy S10",
    "beyond2lte": "Galaxy S10+",
    "beyondx": "Galaxy S10 5G",
    "d1": "Galaxy Note 10",
    "d1x": "Galaxy Note 10 5G",
    "d2s": "Galaxy Note 10+",
    "d2x": "Galaxy Note 10+ 5G",
    "f62": "Galaxy F62"
}

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

def process_device_files(file_paths: list):
    all_devices = []
    common_info = {}

    # Try to read changelog
    try:
        with open("changelog.md", "r") as f:
            device_changelog = f.read().strip()
    except FileNotFoundError:
        device_changelog = "No changelog available"

    for i, file_path in enumerate(file_paths):
        try:
            with open(file_path) as device_file:
                info = json.loads(device_file.read())['response'][0]
                codename = os.path.basename(file_path).split('.')[0]
                
                # Get full device name from JSON, fallback to map
                full_device_name = info.get('device', '')
                if not full_device_name:
                    full_device_name = DEVICE_NAME_MAP.get(codename, 'Unknown')
                
                device_data = {
                    "device_name": full_device_name,
                    "codename": codename,
                    "download": info['download'],
                }
                all_devices.append(device_data)

                # Extract common info from first file
                if i == 0:
                    common_info = {
                        "version": info.get('version', 'N/A'),
                        "datetime": datetime.datetime.fromtimestamp(int(info['timestamp'])),
                        "device_changelog": device_changelog,
                        "maintainer": info.get('maintainer', ''),
                        "telegram": info.get('telegram', ''),
                        "forum": info.get('forum', ''),
                        "gapps": info.get('gapps', ''),
                        "recovery": info.get('recovery', '')
                    }
        except (FileNotFoundError, IndexError, KeyError) as e:
            print(f"Could not process file {file_path}: {e}")
            continue

    return common_info, all_devices


def generate_post_message(common_info, device_list):
    # Get maintainer telegram handle
    maintainer_handle = common_info.get('telegram', '').replace('https://t.me/', '@')
    if not maintainer_handle.startswith('@'):
        maintainer_handle = '@lIlIlIlIlIlIlIlIllIIll'  # fallback

    # Header
    msg = f"<b>OFFICIAL crDroid v{common_info['version']} A16 by {maintainer_handle}</b>\n\n"

    # Changelog
    msg += f"<b>Changelog:</b>\n{common_info['device_changelog']}\n\n"

    # Downloads section
    def sort_key(d):
        try:
            return DEVICE_ORDER.index(d['codename'])
        except ValueError:
            return len(DEVICE_ORDER)

    sorted_devices = sorted(device_list, key=sort_key)

    msg += "<b>Downloads:</b>\n"
    for device in sorted_devices:
        # Use the full device name from JSON
        msg += f"<a href='{device['download']}'>{device['codename']}</a>  ({device['device_name']})\n"
    
    msg += "\n"

    # Note section
    msg += "<b>Note:</b> crDroid recoveries are recommended to install, can be found inside the rom package. First time install, clean flash is mandatory.\n\n"
    msg += "<b>GAPPS ARE NOT INCLUDED</b>\n\n"

    # Support channels
    msg += "Join my support channel: @metamorfoseado\n"
    msg += "Join my support group: @crdroidpx\n\n"

    # Thanks section
    msg += "<b>Thanks:</b>\n"
    msg += "@Linux4 for device trees\n"
    msg += "@FreeRunner4ever for kernel\n"
    msg += "All testers"

    # Check message length (Telegram limit is 1024 for captions with photos)
    if len(msg) > 1000:
        print(f"Warning: Message length is {len(msg)} characters. May need truncation.")
    
    return msg

def send_post(chat_id, image, caption):
    try:
        with open(image, "rb") as banner:
            bot.send_photo(chat_id=chat_id, photo=banner, caption=caption)
            print(f"Successfully sent post to chat ID: {chat_id}")
    except Exception as e:
        print(f"Failed to send post to {chat_id}. Error: {e}")

if __name__ == "__main__":
    file_paths = sys.argv[1:]
    if not file_paths:
        print("No changed files provided. Exiting.")
        exit(1)

    print(f"Processing {len(file_paths)} device files...")

    common_info, all_devices = process_device_files(file_paths)

    if not common_info or not all_devices:
        print("Could not gather info or find any devices. Cannot generate post.")
        exit(1)

    print("Generating post...")
    message = generate_post_message(common_info, all_devices)
    
    print("\n=== Generated Message ===")
    print(message)
    print(f"\n=== Message Length: {len(message)} characters ===\n")
    
    for chat in CHAT_IDS:
        send_post(chat, BANNER_PATH, message)
