#!/usr/bin/env python
import telebot
import os
import json
import datetime
import sys
import re
from typing import List

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
    all_devices = []
    common_info = {}
    codename_map = {}

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

    for i, file_path in enumerate(file_paths):
        try:
            with open(file_path) as device_file:
                info = json.loads(device_file.read())['response'][0]
                codename = os.path.basename(file_path).split('.')[0]
                device_name = info.get('device_name', '')

                device_data = {
                    "device_name": device_name,
                    "codename": codename,
                    "download": info['download'],
                }
                all_devices.append(device_data)

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

    for device in all_devices:
        if not device['device_name']:
            device['device_name'] = codename_map.get(device['codename'], DEVICE_NAME_MAP.get(device['codename'], 'Unknown Device'))

    return common_info, all_devices


def generate_post_message(common_info, device_list):
    build_date = common_info['datetime'].strftime("%m/%d/%Y")

    msg = (f"<b>OFFICIAL CrDroid v{common_info['matrixx_version']} A16 For Galaxy S10/N10 series and Galaxy F62 by "
           f"@pesadelo_certo (https://t.me/pesadelo_certo)</b>\n\n")

    msg += f"⚡️<b>Device Changelog {build_date}</b>⚡️\n"
    msg += f"{common_info['device_changelog']}\n\n"
    msg += "<b>Source Changelog</b> HERE (https://crdroid.net/blog/2025-09-21-crDroid-12-is-now-ready)\n"
    msg += "<b>Screenshots</b> HERE (https://crdroid.net/)\n\n"

    if 'known_issues' in common_info:
        msg += f"<b>Known issues:</b> {common_info['known_issues']}\n\n"

    def sort_key(d):
        try:
            return DEVICE_ORDER.index(d['codename'])
        except ValueError:
            return len(DEVICE_ORDER)

    sorted_devices = sorted(device_list, key=sort_key)

    msg += f"<b>Downloads Vanilla:</b>\n"
    for device in sorted_devices:
        msg += f"<a href='{device['download']}'>{device['codename']}</a> ({device['device_name']})\n"
    msg += "\n"

    msg += "<b>Gapps</b> HERE (https://sourceforge.net/projects/nikgapps/files/Releases/Android-16/16-Jul-2025/)\n\n"
    msg += "<b>Note:</b> CrDroid recoveries are recommended to install. First time install, clean flash is mandatory.\n\n"
    msg += "<b>CrDroid recoveries</b> HERE (https://sourceforge.net/projects/crdroid/files/)\n\n"
    msg += "<b>YOU CANNOT USE TWRP TO FLASH CRDROID!</b>\n\n"
    msg += ("<b>Thanks:</b>\n"
            "Linux4 (https://t.me/linux4) for device trees and kernel\n"
            "SideX15 (https://t.me/sidex15) for susfs\n"
            "RifsxD (https://t.me/rifsxd) for KernelSU-Next\n"
            "CrDroid team\n"
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

    common_info, all_devices = process_device_files(file_paths)

    if not common_info or not all_devices:
        print("Could not gather info or find any devices. Cannot generate post.")
        exit(1)

    print("Generating post...")
    message = generate_post_message(common_info, all_devices)
    for chat in CHAT_IDS:
        send_post(chat, BANNER_PATH, message)
