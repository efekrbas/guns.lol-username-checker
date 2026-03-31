from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import random
import string
import time
import re
from colorama import Fore, init
import requests
import os
import subprocess
from selenium.webdriver.chrome.service import Service
import zipfile
import shutil
import tempfile


init(autoreset=True)

def random_letters(n, filter_premium=False):
    """Generates a random string consisting of letters and special characters."""
    all_chars = string.ascii_lowercase + string.digits + "._-"
    base_chars = string.ascii_lowercase + string.digits
    
    if filter_premium:
        if n == 1:
            return random.choice(base_chars)
        # Baş ve sonu sadece harf/sayı olsun (Premium gerektirmeyenler)
        first = random.choice(base_chars)
        middle = ''.join(random.choice(all_chars) for _ in range(n - 2))
        last = random.choice(base_chars)
        return first + middle + last
    else:
        return ''.join(random.choice(all_chars) for _ in range(n))

def get_random_user_agent():
    """Returns a random user-agent to prevent rate limiting."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    ]
    return random.choice(user_agents)

def create_proxy_extension(proxy):
    """Creates a Chrome extension to handle authenticated proxies."""
    # Format: user:pass@ip:port or ip:port
    if '@' in proxy:
        auth, address = proxy.split('@')
        user, password = auth.split(':')
        host, port = address.split(':')
    else:
        host, port = proxy.split(':')
        user, password = "", ""

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (host, port, user, password)

    plugin_file = os.path.join(tempfile.gettempdir(), f'proxy_auth_plugin_{host}_{port}.zip')

    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_file

def get_driver(proxy=None):
    """Initializes and returns a Selenium WebDriver with optional proxy."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu-compositing')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--ignore-gpu-blocklist')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.page_load_strategy = 'eager'

    if proxy:
        if '@' in proxy: # Authenticated proxy
            plugin_file = create_proxy_extension(proxy)
            chrome_options.add_extension(plugin_file)
        else: # Simple proxy
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')

    service = Service(log_path=os.devnull)
    if os.name == 'nt':
        service.creation_flags = subprocess.CREATE_NO_WINDOW
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(10)
    driver.implicitly_wait(0)
    driver.set_script_timeout(3)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver
def check_user_status(letter_count, interval, wordlist=None, filter_premium=False, save_to_file=True, webhook_url=None, proxies=None):
    """Checks the status of usernames based on character count or list and interval."""
    base_url = "guns.lol/"
    
    proxy_index = 0
    current_proxy = proxies[proxy_index] if proxies else None
    
    try:
        driver = get_driver(current_proxy)
    except Exception as e:
        print(f"{Fore.RED}Error launching Chrome: {e}{Fore.RESET}")
        return
    
    try:
        request_count = 0
        usernames_to_check = wordlist if wordlist else None
        index = 0
        
        while True:
            if usernames_to_check is not None:
                if index >= len(usernames_to_check):
                    print(f"{Fore.CYAN}Wordlist check completed.{Fore.RESET}")
                    break
                current_suffix = usernames_to_check[index]
                index += 1
                
                if filter_premium:
                    if current_suffix[0] in "._-" or current_suffix[-1] in "._-":
                        print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}Skipping (Premium Alias){Fore.RESET}")
                        continue
            else:
                current_suffix = random_letters(letter_count, filter_premium)
            
            url = base_url + current_suffix
            request_count += 1

            try:
                max_retries = 2
                attempt = 0
                is_unclaimed = False
                is_error = False
                status = ""
                is_rate_limited = False
                
                while attempt < max_retries:
                    try:
                        time.sleep(random.uniform(0.5, 1.0))
                        
                        try:
                            driver.get(f"https://{url}")
                            time.sleep(1.5) 
                        except (TimeoutException, WebDriverException) as e:
                            print(f"{Fore.YELLOW}Connection error, switching proxy...{Fore.RESET}")
                            attempt += 1
                            if proxies:
                                proxy_index = (proxy_index + 1) % len(proxies)
                                current_proxy = proxies[proxy_index]
                                driver.quit()
                                driver = get_driver(current_proxy)
                            if attempt < max_retries:
                                continue
                            is_error = True
                            break
                        
                        # Detection Logic
                        page_title = driver.title.lower()
                        page_source = driver.page_source.lower()
                        
                        # Check for Rate Limiting / Cloudflare
                        if any(x in page_title for x in ["cloudflare", "just a moment", "access denied", "attention required"]) or \
                           any(x in page_source for x in ["too many requests", "blocked", "enable javascript", "verify you are human"]):
                            is_rate_limited = True
                            print(f"{Fore.YELLOW}Rate limit or Cloudflare detected, rotating proxy...{Fore.RESET}")
                            if proxies:
                                proxy_index = (proxy_index + 1) % len(proxies)
                                current_proxy = proxies[proxy_index]
                                driver.quit()
                                driver = get_driver(current_proxy)
                                attempt += 1
                                continue
                            else:
                                print(f"{Fore.RED}Rate limited and no more proxies available. Waiting 30s...{Fore.RESET}")
                                time.sleep(30)
                                attempt += 1
                                continue

                        is_unclaimed = False
                        is_error = False
                        
                        try:
                            current_url = driver.current_url.lower().rstrip('/')
                            if current_suffix.lower() not in current_url:
                                is_unclaimed = False 
                            else:
                                h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                                unclaimed_found = False
                                for h1 in h1_elements:
                                    if "username not found" in h1.text.lower():
                                        unclaimed_found = True
                                        break
                                
                                if unclaimed_found:
                                    is_unclaimed = True
                                else:
                                    # Title check
                                    if "everything you want" in page_title:
                                        is_unclaimed = True
                                    elif not page_title:
                                        is_error = True
                                    else:
                                        is_unclaimed = False 
                        except:
                            is_error = True

                        if not is_error or attempt >= max_retries - 1:
                            break
                        
                        attempt += 1
                        time.sleep(2)
                    except Exception:
                        attempt += 1
                        if attempt >= max_retries:
                            is_error = True
                            break
                        time.sleep(2)

                if is_rate_limited:
                    status = f"{Fore.YELLOW}Rate Limited/Blocked"
                elif is_error:
                    status = f"{Fore.YELLOW}error/timeout"
                elif is_unclaimed:
                    status = f"{Fore.GREEN}unclaimed"
                    if save_to_file:
                        with open("unclaimed.txt", "a") as file:
                            file.write(f"{current_suffix}\n")
                    if webhook_url:
                        embed = {"title": f"Available: {current_suffix} (https://guns.lol/{current_suffix})", "description": "github.com/efekrbas", "color": 0x9B59B6}
                        payload = {"embeds": [embed]}
                        try: requests.post(webhook_url, json=payload)
                        except: pass
                else:
                    status = f"{Fore.RED}claimed"
                
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - Status: {status}{Fore.RESET}")

            except Exception as e:
                error_msg = str(e)
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.RED}Error: {error_msg[:50]}...{Fore.RESET}")
         
            # Random delay
            random_delay = interval + random.uniform(0.5, 1.0)
            if request_count % 10 == 0:
                random_delay += random.uniform(1.0, 2.0)
            
            time.sleep(random_delay)
    finally:
        driver.quit()


def get_input(prompt, type_=str, validation=None, error_msg="Please enter a valid value."):
    while True:
        try:
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
            input(f"\n{Fore.CYAN}Press Enter to exit...{Fore.RESET}")
            exit()

try:
    letter_count = get_input(
        "How many letter usernames should be checked? (Example: 5): ",
        type_=int,
        validation=lambda x: x > 0,
        error_msg="Letter count must be a positive number."
    )

    interval = get_input(
        "Delay (in seconds *recommended 0.1*): ",
        type_=float,
        validation=lambda x: x >= 0,
        error_msg="Delay cannot be negative."
    )

    use_wordlist = get_input("Use customlist.txt? (Y/N): ", type_=bool)
    wordlist = None

    if use_wordlist:
        try:
            with open("customlist.txt", "r", encoding="utf-8") as file:
                wordlist = [line.strip() for line in file if line.strip()]
            if not wordlist:
                print(f"{Fore.YELLOW}customlist.txt is empty. Switching to random mode.{Fore.RESET}")
                use_wordlist = False
            else:
                print(f"{Fore.GREEN}{len(wordlist)} usernames loaded from customlist.txt.{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.RED}customlist.txt not found. Switching to random mode.{Fore.RESET}")
            use_wordlist = False

    filter_premium = get_input("Filter out usernames requiring Premium? (Starts/ends with '.', '-', '_') [Y/N]: ", type_=bool)

    save_to_file = get_input("Should unclaimed usernames be saved to unclaimed.txt? (Y/N): ", type_=bool)
    
    use_webhook = get_input("Should unclaimed usernames be sent to a Discord webhook? (Y/N): ", type_=bool)
    webhook_url = None
    if use_webhook:
        webhook_url = input("Enter your Discord webhook URL: ").strip()

    use_proxies = get_input("Use proxies from proxies.txt? (Y/N): ", type_=bool)
    proxies = None
    if use_proxies:
        try:
            with open("proxies.txt", "r", encoding="utf-8") as file:
                proxies = [line.strip() for line in file if line.strip()]
            if not proxies:
                print(f"{Fore.YELLOW}proxies.txt is empty. Continuing without proxies.{Fore.RESET}")
                proxies = None
            else:
                print(f"{Fore.GREEN}{len(proxies)} proxies loaded.{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.RED}proxies.txt not found. Continuing without proxies.{Fore.RESET}")
            proxies = None

    check_user_status(letter_count, interval, wordlist, filter_premium, save_to_file, webhook_url, proxies)
except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}Program terminated.{Fore.RESET}")
except Exception as e:
    print(f"{Fore.RED}An unexpected error occurred: {e}{Fore.RESET}")
finally:
    input(f"\n{Fore.CYAN}Press Enter to exit...{Fore.RESET}")
