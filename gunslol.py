from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service

import random
import string
import time
import re
import os
import sys
import ctypes
import json
import tempfile
import shutil
import atexit
import subprocess
from urllib.parse import quote

import requests
from colorama import Fore, init
from pystyle import Anime, Colors, Colorate, Center, System, Write

purple_static = ['150;0;255'] * 24

intro_text = r'''
 
                      _     _                                             _           _           
  __ _ _  _ _ _  ___ | |___| |  _  _ ___ ___ _ _ _ _  __ _ _ __  ___   __| |_  ___ __| |_____ _ _ 
 / _` | || | ' \(_-<_| / _ \ | | || (_-</ -_) '_| ' \/ _` | '  \/ -_) / _| ' \/ -_) _| / / -_) '_|
 \__, |\_,_|_||_/__(_)_\___/_|  \_,_/__/\___|_| |_||_\__,_|_|_|_\___| \__|_||_\___\__|_\_\___|_|  
 |___/                                                                                                
                                github.com/efekrbas/guns.lol-username-checker

                                               > Press Enter                                         
'''

def show_header():
    System.Clear()
    print(Colorate.Vertical(purple_static, intro_text.split('> Press Enter')[0]))


init(autoreset=True)

def is_double_clicked():
    """Check if script was launched by double-clicking (Windows only)."""
    if os.name != 'nt':
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        process_list = (ctypes.c_uint * 1)()
        count = kernel32.GetConsoleProcessList(process_list, 1)
        return count <= 1
    except Exception:
        return False

_launched_by_double_click = is_double_clicked()

_active_driver = None
_temp_extension_dir = None

def _cleanup():
    global _active_driver, _temp_extension_dir
    try:
        if _active_driver:
            _active_driver.quit()
            _active_driver = None
    except Exception:
        pass
    try:
        if _temp_extension_dir and os.path.exists(_temp_extension_dir):
            shutil.rmtree(_temp_extension_dir, ignore_errors=True)
            _temp_extension_dir = None
    except Exception:
        pass
    if os.name == 'nt':
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

atexit.register(_cleanup)

if os.name == 'nt':
    def _console_handler(event):
        _cleanup()
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        _handler_func = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)(_console_handler)
        kernel32.SetConsoleCtrlHandler(_handler_func, True)
    except Exception:
        pass

def random_letters(n, filter_premium=False):
    """Generates a random string consisting of letters and special characters."""
    all_chars = string.ascii_lowercase + string.digits + "._-"
    base_chars = string.ascii_lowercase + string.digits
    
    if filter_premium:
        if n == 1:
            return random.choice(base_chars)
        first = random.choice(base_chars)
        middle = ''.join(random.choice(all_chars) for _ in range(n - 2))
        last = random.choice(base_chars)
        return first + middle + last
    else:
        return ''.join(random.choice(all_chars) for _ in range(n))

def get_random_user_agent():
    """Returns a random modern user-agent."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'
    ]
    return random.choice(user_agents)

def load_proxies(path="proxies.txt"):
    """Loads authenticated HTTP proxies in host:port:username:password format."""
    proxies = []

    with open(path, "r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line or line.startswith(("#", "//")):
                continue

            parts = line.split(":", 3)
            if len(parts) != 4:
                raise ValueError(
                    f"Invalid proxy format on line {line_number}; expected host:port:username:password."
                )

            host, port_text, username, password = (part.strip() for part in parts)
            if not host or not username or not password:
                raise ValueError(f"Missing proxy data on line {line_number}.")
            try:
                port = int(port_text)
            except ValueError:
                raise ValueError(f"Invalid proxy port on line {line_number}.")
            if not 1 <= port <= 65535:
                raise ValueError(f"Invalid proxy port on line {line_number}.")

            proxies.append({
                "host": host,
                "port": port,
                "username": username,
                "password": password,
            })

    if not proxies:
        raise ValueError("proxies.txt does not contain any usable proxies.")
    return proxies

def create_pac_proxy_extension(proxies, extension_dir):
    """Creates a lightweight Chrome extension that rotates through all proxies via PAC script."""
    manifest = {
        "manifest_version": 3,
        "name": "Proxy PAC Rotation",
        "version": "1.0.0",
        "permissions": ["proxy", "webRequest", "webRequestAuthProvider"],
        "host_permissions": ["<all_urls>"],
        "background": {"service_worker": "background.js"},
    }
    servers_json = json.dumps([{"host": p["host"], "port": p["port"]} for p in proxies])
    creds_json = json.dumps({
        f"{p['host']}:{p['port']}": {"username": p["username"], "password": p["password"]}
        for p in proxies
    })

    pac_data = f"""
var proxyServers = {servers_json};
var reqCount = 0;
function FindProxyForURL(url, host) {{
    if (host === "localhost" || host === "127.0.0.1") return "DIRECT";
    if (proxyServers.length === 0) return "DIRECT";
    var p1 = proxyServers[reqCount % proxyServers.length];
    var p2 = proxyServers[(reqCount + 1) % proxyServers.length];
    var p3 = proxyServers[(reqCount + 2) % proxyServers.length];
    reqCount = (reqCount + 1) % proxyServers.length;
    return "PROXY " + p1.host + ":" + p1.port + "; PROXY " + p2.host + ":" + p2.port + "; PROXY " + p3.host + ":" + p3.port;
}}
"""
    proxy_config = json.dumps({"mode": "pac_script", "pacScript": {"data": pac_data}})
    background = f"""
const proxyCredentials = {creds_json};
chrome.proxy.settings.set({{ value: {proxy_config}, scope: "regular" }});
chrome.webRequest.onAuthRequired.addListener(
  (details, callback) => {{
    const k = `${{details.challenger.host}}:${{details.challenger.port}}`;
    callback(proxyCredentials[k] ? {{ authCredentials: proxyCredentials[k] }} : {{}});
  }},
  {{ urls: ["<all_urls>"] }},
  ["asyncBlocking"]
);
"""

    with open(os.path.join(extension_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    with open(os.path.join(extension_dir, "background.js"), "w", encoding="utf-8") as f:
        f.write(background)

def get_requests_proxy_config(proxy):
    """Builds requests-compatible proxy URLs, escaping credentials safely."""
    username = quote(proxy["username"], safe="")
    password = quote(proxy["password"], safe="")
    proxy_url = f"http://{username}:{password}@{proxy['host']}:{proxy['port']}"
    return {"http": proxy_url, "https": proxy_url}

def send_discord_webhook(webhook_url, username, proxies=None):
    """Sends discord notification."""
    embed = {
        "title": f"Available: {username} (https://guns.lol/{username})",
        "description": "github.com/efekrbas",
        "color": 0x9B59B6
    }
    payload = {"embeds": [embed]}
    try:
        req_proxy = random.choice(proxies) if proxies else None
        req_opts = {"proxies": get_requests_proxy_config(req_proxy)} if req_proxy else {}
        requests.post(webhook_url, json=payload, timeout=5, **req_opts)
    except Exception:
        pass

def check_user_status(letter_count, interval, customlist=None, filter_premium=False, save_to_file=True, webhook_url=None, proxies=None):
    """Checks usernames with ultra-lightweight Chrome engine to bypass Cloudflare smoothly with zero lag."""
    global _active_driver, _temp_extension_dir
    base_url = "guns.lol/"

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-translate')
    chrome_options.add_argument('--js-flags=--max-old-space-size=128')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--lang=en-US')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.page_load_strategy = 'eager'

    if proxies:
        _temp_extension_dir = tempfile.mkdtemp(prefix="gunslol_proxy_")
        create_pac_proxy_extension(proxies, _temp_extension_dir)
        chrome_options.add_argument(f'--load-extension={_temp_extension_dir}')
    else:
        chrome_options.add_argument('--disable-extensions')

    service = Service(log_path=os.devnull)
    if os.name == 'nt':
        service.creation_flags = subprocess.CREATE_NO_WINDOW

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        _active_driver = driver
        driver.set_page_load_timeout(14)
        driver.implicitly_wait(0)
        driver.set_script_timeout(4)
    except Exception as e:
        print(f"{Fore.RED}Error launching Chrome: {e}{Fore.RESET}")
        return

    try:
        usernames_to_check = customlist if customlist else None
        index = 0
        total_checked = 0

        while True:
            if usernames_to_check is not None:
                if index >= len(usernames_to_check):
                    print(f"\n{Fore.CYAN}Customlist check completed. {total_checked} usernames checked.{Fore.RESET}")
                    break
                current_suffix = usernames_to_check[index]
                index += 1

                if filter_premium:
                    if current_suffix[0] in "._-" or current_suffix[-1] in "._-":
                        print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}Skipping (Premium Alias){Fore.RESET}")
                        continue
            else:
                current_suffix = random_letters(letter_count, filter_premium)

            url = f"https://{base_url}{current_suffix}"
            max_retries = 3
            attempt = 0
            is_unclaimed = False
            is_error = False

            while attempt < max_retries:
                try:
                    driver.get(url)

                    # Cloudflare / Proof of Work challenge auto-wait (up to 6.0s)
                    deadline = time.time() + 6.0
                    while time.time() < deadline:
                        title_now = driver.title.lower()
                        if "please wait" in title_now or not title_now:
                            time.sleep(0.3)
                        else:
                            break

                    title = driver.title.lower()
                    if not title or "please wait" in title:
                        attempt += 1
                        try:
                            driver.execute_script("window.stop();")
                        except Exception:
                            pass
                        time.sleep(0.8)
                        continue

                    # Auto-detect and handle rate limits (cool down token bucket)
                    if "rate limit" in title or "too many requests" in title:
                        attempt += 1
                        try:
                            driver.execute_script("window.stop();")
                        except Exception:
                            pass
                        time.sleep(2.5)
                        continue

                    # Accurate detection: check visible rendered text in H1 tags
                    # (Avoid checking page_source directly because Next.js JS bundles include translation words)
                    h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                    h1_texts = [h.text.lower() for h in h1_elements if h.text]

                    is_unclaimed = False
                    for t in h1_texts:
                        if "username not found" in t or "kullanıcı adı bulunamadı" in t or "bulunamadı" in t:
                            is_unclaimed = True
                            break

                    # Fallback check on visible body text if no H1
                    if not is_unclaimed and not h1_texts:
                        try:
                            body_txt = driver.find_element(By.TAG_NAME, "body").text.lower()
                            if "kullanıcı adı bulunamadı" in body_txt or "username not found" in body_txt:
                                is_unclaimed = True
                        except Exception:
                            pass

                    is_error = False
                    break
                except (TimeoutException, WebDriverException):
                    attempt += 1
                    try:
                        driver.execute_script("window.stop();")
                    except Exception:
                        pass
                    if attempt >= max_retries:
                        is_error = True
                        break
                    time.sleep(1.5)
                except Exception:
                    attempt += 1
                    if attempt >= max_retries:
                        is_error = True
                        break
                    time.sleep(1.5)

            if is_error:
                status = f"{Fore.YELLOW}error/timeout"
            elif is_unclaimed:
                status = f"{Fore.GREEN}unclaimed"
                if save_to_file:
                    with open("unclaimed.txt", "a", encoding="utf-8") as f:
                        f.write(f"{current_suffix}\n")
                if webhook_url:
                    send_discord_webhook(webhook_url, current_suffix, proxies)
            else:
                status = f"{Fore.RED}claimed"

            print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} {Fore.WHITE}- Status: {status}{Fore.RESET}")
            total_checked += 1

            # Dynamic delay (prevents Cloudflare/guns.lol rate limits on proxies and home IP)
            if interval > 0:
                time.sleep(interval)
            elif proxies:
                time.sleep(random.uniform(0.25, 0.45))
            else:
                time.sleep(random.uniform(0.8, 1.2))

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program terminated.{Fore.RESET}")
    finally:
        _cleanup()


def get_input(prompt, type_=str, validation=None, error_msg="Please enter a valid value."):
    while True:
        try:
            show_header()
            value = input(prompt).strip()
            if type_ == bool:
                if value.lower() == 'y':
                    return True
                elif value.lower() == 'n':
                    return False
                else:
                    raise ValueError
            
            converted_value = type_(value)
            if validation and not validation(converted_value):
                raise ValueError
            return converted_value
        except (ValueError, EOFError):
            print(f"{Fore.RED}{error_msg}{Fore.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Program terminated.{Fore.RESET}")
            exit()

def main():
    try:
        Anime.Fade(Center.Center(intro_text), purple_static, Colorate.Vertical, interval=.035, enter=True)
        
        letter_count = get_input(
            "Enter username length (e.g. 3, 4, 5): ",
            type_=int,
            validation=lambda x: x > 0,
            error_msg="Please enter a valid value."
        )

        interval = get_input(
            "Delay (in seconds *recommended 0*): ",
            type_=float,
            validation=lambda x: x >= 0,
            error_msg="Please enter a valid value."
        )

        use_customlist = get_input("Use customlist.txt? (Y/N): ", type_=bool, error_msg="Please enter Y or N.")
        customlist = None

        if use_customlist:
            try:
                with open("customlist.txt", "r", encoding="utf-8") as file:
                    customlist = [line.strip() for line in file if line.strip() and not line.strip().startswith("//")]
                if not customlist:
                    print(f"{Fore.YELLOW}customlist.txt is empty. Switching to random mode.{Fore.RESET}")
                    use_customlist = False
                else:
                    print(f"{Fore.GREEN}{len(customlist)} usernames loaded from customlist.txt.{Fore.RESET}")
            except FileNotFoundError:
                print(f"{Fore.RED}customlist.txt not found. Switching to random mode.{Fore.RESET}")
                use_customlist = False

        use_proxy = get_input("Use proxies.txt? (Y/N): ", type_=bool, error_msg="Please enter Y or N.")
        proxies = None
        proxy_count = 0
        if use_proxy:
            try:
                proxies = load_proxies()
                proxy_count = len(proxies)
            except (FileNotFoundError, ValueError) as e:
                print(f"{Fore.RED}Could not load proxies.txt: {e}{Fore.RESET}")
                raise SystemExit(1)

        filter_premium = get_input("Filter out usernames requiring Premium? (Starts/ends with '.', '-', '_') [Y/N]: ", type_=bool, error_msg="Please enter Y or N.")

        save_to_file = get_input("Should unclaimed usernames be saved to unclaimed.txt? (Y/N): ", type_=bool, error_msg="Please enter Y or N.")
        
        use_webhook = get_input("Should unclaimed usernames be sent to a Discord webhook? (Y/N): ", type_=bool, error_msg="Please enter Y or N.")
        webhook_url = None
        if use_webhook:
            webhook_url = get_input(
                "Enter your Discord webhook URL: ",
                validation=lambda x: x.startswith("https://discord.com/api/webhooks/") or x.startswith("https://discordapp.com/api/webhooks/"),
                error_msg="Please enter a valid Discord webhook URL (https://discord.com/api/webhooks/...)."
            )

        print()
        if proxies:
            print(f"{Fore.GREEN}{proxy_count} proxies loaded. Requests will rotate across them.{Fore.RESET}")
        check_user_status(letter_count, interval, customlist, filter_premium, save_to_file, webhook_url, proxies)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program terminated.{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}{Fore.RESET}")
    finally:
        if _launched_by_double_click:
            print(f"\n{Fore.CYAN}Press any key to exit...{Fore.RESET}")
            os.system("pause >nul")

if __name__ == "__main__":
    main()
