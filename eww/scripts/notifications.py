#!/usr/bin/env python

import datetime
import os
import dbus
import gi
import typing
import json
import argparse
import subprocess

gi.require_version("GdkPixbuf", "2.0")

from gi.repository import GdkPixbuf, Gio, GLib
from dbus.mainloop.glib import DBusGMainLoop
from html.parser import HTMLParser
from apps import get_gtk_icon

log_file = os.path.expandvars("$XDG_CACHE_HOME/notifications.json")
cache_dir = os.path.expandvars("$XDG_CACHE_HOME/image_data")
os.makedirs(cache_dir, exist_ok=True)

active_popups = {}

def clean_text(text):
    class HTMLTagStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.text = []

        def handle_data(self, data):
            self.text.append(data)

        def get_text(self):
            return "".join(self.text)

    stripper = HTMLTagStripper()
    stripper.feed(text)
    text = stripper.get_text()

    return text.strip()

def save_img_byte(px_args: typing.Iterable, save_path: str):
    GdkPixbuf.Pixbuf.new_from_bytes(
        width=px_args[0],
        height=px_args[1],
        has_alpha=px_args[3],
        data=GLib.Bytes(px_args[6]),
        colorspace=GdkPixbuf.Colorspace.RGB,
        rowstride=px_args[2],
        bits_per_sample=px_args[4],
    ).savev(save_path, "png")

def notification_callback(bus, message):
    args = message.get_args_list()

    details = {
        "id": datetime.datetime.now().strftime("%s"),
        "app": args[0] or None,
        "summary": clean_text(args[3]) or None,
        "body": clean_text(args[4]) or None,
        "time": datetime.datetime.now().strftime("%H:%M"),
    }

    if args[2].strip():
        if os.path.isfile(args[2]) or args[2].startswith("file://"):
            details["image"] = args[2]
        else:
            details["image"] = get_gtk_icon(args[2])
    else:
        details["image"] = None

    if "image-data" in args[6]:
        details["image"] = f"{cache_dir}/{details['id']}.png"
        save_img_byte(args[6]["image-data"], details["image"])

    save_notification(details)
    save_popup(details)

def update_eww(data):
    output_json = json.dumps(data, indent=2)
    subprocess.run(["eww", "update", f"notifications={output_json}"])
    with open(log_file, "w") as log:
        log.write(output_json)

def read_log_file():
    empty = {"count": 0, "notifications": [], "popups": []}
    try:
        with open(log_file, "r") as log:
            return json.load(log)
    except FileNotFoundError:
        with open(log_file, "w") as log:
            json.dump(empty, log)
        return empty

def save_notification(notification):
    current = read_log_file()
    current["notifications"].insert(0, notification)
    current["count"] = len(current["notifications"])
    update_eww(current)

    update_eww(current)
    
def remove_notification(id):
    current = read_log_file()
    current["notifications"] = [n for n in current["notifications"] if n["id"] != id]
    current["count"] = len(current["notifications"])
    
    update_eww(current)

def clear_notifications():
    data = {"count": 0, "notifications": [], "popups": []}
    
    update_eww(data)

def save_popup(notification):
    global active_popups

    current = read_log_file()
    if len(current["popups"]) >= 3:
        oldest_popup = current["popups"].pop()
        remove_notification(oldest_popup["id"])

    current["popups"].insert(0, notification)
    update_eww(current)

    popup_id = notification["id"]
    active_popups[popup_id] = GLib.timeout_add_seconds(10, remove_popup, popup_id)

def remove_popup(popup_id):
    global active_popups

    current = read_log_file()
    current["popups"] = [n for n in current["popups"] if n["id"] != popup_id]
    update_eww(current)

    active_popups.pop(popup_id, None)

def notification_loop():
    DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    bus.add_match_string_non_blocking(
        "eavesdrop=true, interface='org.freedesktop.Notifications', member='Notify'"
    )
    bus.add_message_filter(notification_callback)

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        bus.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rmid", type=str, help="Remove notification by ID")
    parser.add_argument("--init", action="store_true", help="Start the loop")
    parser.add_argument("--clear", action="store_true", help="Clear the log file")
    parser.add_argument("--open", action="store_true", help="Update eww if its empy")
    args = parser.parse_args()

    if args.rmid:
        remove_notification(args.rmid)
        remove_popup(args.rmid)

    if args.init:
        notification_loop()

    if args.clear:
        clear_notifications()
        
    if args.open:
        curent = read_log_file()
        update_eww(curent)