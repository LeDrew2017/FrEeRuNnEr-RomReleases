#!/usr/bin/env python
import telebot
import os
import json
import datetime
import sys
import re
from typing import List

# 1. Defined a fixed order for device listing.
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

def process_device_files(file_paths: list):
    """
    This function remains mostly unchanged to correctly process JSON files.
    """
    gapps_devices = []
    vanilla_devices = []
    common_info = {}
    codename_map = {}
    all_devices_raw = []

    # Definitive map for device codenames to names as a fallback
    DEVICE_NAME_MAP = {
        "beyond0lte": "Galaxy S10e",
        "beyond1lte": "Galaxy S10",
        "beyond2lte": "Galaxy S10+",
        "beyondx": "Galaxy S10 5G",
        "d1": "Galaxy N10",
        "d1x": "Galaxy N10 5G",
        "d2s": "Galaxy N10 +",
        "d2x": "Galaxy N10+ 5G",
        "f62": "Galaxy F62"
    }

    try:
        with open("changelog.md", "r") as f:
            device_changelog = f.read()
    except FileNotFoundError:
        device_changelog = "Changelog not found."

    # First pass: Gather all data and build the codename map
    for i, file_path in enumerate(file_paths):
        try:
            with open(file_path) as device_file:
                info = json.loads(device_file.read())['response'][0]
                codename = os.path.basename(file_path).split('.')[0].replace('_gapps', '')
                device_name = info.get('device_name', '')

                device_data = {
                    "device_name": device_name,
                    "codename": codename,
                    "download": info['download'],
                    "is_gapps": "gapps" in file_path.lower()
                }
                all_devices_raw.append(device_data)

                if device_name:
                    codename_map[codename] = device_name

                if i == 0:
                    version_match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{1,2})', info['download'])
                    common_info = {
                        "matrixx_version": version_match.group(1) if version_match else 'N/A',
                        "datetime": datetime.datetime.fromtimestamp(int(info['timestamp'])),
                        "device_changelog": device_changelog
                    }
                    if 'known_issues' in info:
                        common_info['known_issues'] = info['known_issues']
        except (FileNotFoundError, IndexError, KeyError) as e:
            print(f"Could not process file {file_path}: {e}")
            continue

    # Second pass: Populate missing names and sort into final lists
    for device in all_devices_raw:
        if not device['device_name']:
            device['device_name'] = codename_map.get(device['codename'], '')
        
        if not device['device_name']:
            device['device_name'] = DEVICE_NAME_MAP.get(device['codename'], 'Unknown Device')

        if device['is_gapps']:
            gapps_devices.append(device)
        else:
            vanilla_devices.append(device)

    return common_info, gapps_devices, vanilla_devices

# --- START OF MODIFICATIONS ---

# 2. Reverted to a single message generator that handles variants.
def generate_post_message(common_info, device_list, variant_type):
    """
    Generates a complete post message for a specific build variant (Gapps or Vanilla).
    """
    build_date = common_info['datetime'].strftime("%m/%d/%Y")

    # 3. Hardcoded developer name and link as requested.
    # Added "Gapps" to the title only if it's the Gapps variant.
    variant_title = " Gapps" if variant_type == "Gapps" else ""
    msg = (f"<b>OFFICIAL Project Matrixx v{common_info['matrixx_version']}{variant_title} A15 For Galaxy S10/N10 series and Galaxy F62 by "
           f"<a href='https://t.me/FrEeRuNnEr4EvEr'>@FrEeRuNnEr4EvEr</a></b>\n\n")

    msg += f"⚡️<b>Device Changelog {build_date}</b>⚡️\n"
    msg += f"<code>{common_info['device_changelog']}</code>\n\n"
    msg += "<b>Source Changelog</b> <a href='https://www.projectmatrixx.org/changelog'>HERE</a>\n"
    msg += "<b>Screenshots</b> <a href='https://www.projectmatrixx.org/gallery'>HERE</a>\n\n"

    if 'known_issues' in common_info:
        msg += f"<b>Known issues:</b> {common_info['known_issues']}\n\n"

    # Sort devices based on the predefined DEVICE_ORDER list
    def sort_key(d):
        try:
            return DEVICE_ORDER.index(d['codename'])
        except ValueError:
            return len(DEVICE_ORDER) # Place unknown devices at the end
            
    sorted_devices = sorted(device_list, key=sort_key)

    msg += f"<b>Downloads {variant_type}:</b>\n"
    for device in sorted_devices:
        # 4. Changed link format to make only the codename clickable.
        msg += f"<a href='{device['download']}'>{device['codename']}</a> ({device['device_name']})\n"
    msg += "\n"

    # 5. Add Gapps link ONLY to the Vanilla post.
    if variant_type == "Vanilla":
        msg += "<b>Gapps</b> <a href='https://sourceforge.net/projects/nikgapps/files/Releases/Android-15/11-Jun-2025/'>HERE</a>\n\n"

    # 6. Added a space after the "Note" and updated the recovery link.
    msg += "<b>Note:</b> Project-Matrixx recoveries are recommended to install. First time install, clean flash is mandatory.\n\n"
    msg += "<b>Project-Matrixx recoveries</b> <a href='https://drive.google.com/drive/folders/12dGe5d_F5ZII2cUS6Hd-rLBGXPZ2nMry'>HERE</a>\n\n"
    
    msg += "<b>YOU CANNOT USE TWRP TO FLASH PROJECT MATRIXX!</b>\n\n"

    msg += ("<b>Thanks:</b>\n"
            "<a href='https://t.me/linux4'>Linux4</a> for device trees and kernel\n"
            "<a href='https://t.me/sidex15'>SideX15</a> for susfs\n"
            "<a href='https://t.me/rifsxd'>RifsxD</a> for KernelSU-Next\n"
            "Project-Matrixx team\n"
            "All my testers")

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
    common_info, gapps_devices, vanilla_devices = process_device_files(file_paths)

    if not common_info:
        print("Could not gather common info from any file. Cannot generate post.")
        exit(1)

    # 7. Reverted main block to generate and send two separate posts.
    if gapps_devices:
        print("Generating Gapps post...")
        gapps_message = generate_post_message(common_info, gapps_devices, "Gapps")
        for chat in CHAT_IDS:
            send_post(chat, BANNER_PATH, gapps_message)
    else:
        print("No Gapps devices found to post.")

    if vanilla_devices:
        print("Generating Vanilla post...")
        vanilla_message = generate_post_message(common_info, vanilla_devices, "Vanilla")
        for chat in CHAT_IDS:
            send_post(chat, BANNER_PATH, vanilla_message)
    else:
        print("No Vanilla devices found to post.")
