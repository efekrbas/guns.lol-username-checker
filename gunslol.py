import cloudscraper
import random
import string
import time
import re
from colorama import Fore, init
import requests


init(autoreset=True)

# Characters that require a Premium alias on guns.lol
PREMIUM_CHARS = set('._-')

def random_letters(n):
    """Rastgele harfler ve özel karakterlerden oluşan bir string oluşturur."""
    characters = string.ascii_lowercase + string.digits + "._-"
    return ''.join(random.choice(characters) for _ in range(n))

def get_random_user_agent():
    """Rastgele bir user-agent döndürür."""
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

def check_username(scraper, username):
    """Tek bir kullanıcı adını kontrol eder."""
    url = f"https://guns.lol/{username}"
    try:
        resp = scraper.get(url, timeout=15)
        
        if resp.status_code in (401, 403, 429):
            return 'ratelimit', f"HTTP {resp.status_code}"
        
        if resp.status_code != 200:
            return 'error', f"HTTP {resp.status_code}"
        
        text_lower = resp.text.lower()
        title_match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""

        # En güvenilir yöntem sadece başlığı kontrol etmektir.
        # "username not found" string'i JS bundle'larında tüm sayfalarda yüklü gelir, bu yüzden HTML'de aranmamalı.
        if title.lower() == "guns.lol: everything you want, right here.":
            return 'unclaimed', None
        else:
            return 'claimed', None
            
    except requests.exceptions.Timeout:
        return 'error', "Timeout"
    except requests.exceptions.ConnectionError:
        return 'error', "Bağlantı hatası"
    except Exception as e:
        return 'error', str(e)[:50]

def create_scraper(proxy=None):
    """Yeni bir cloudscraper oturumu oluşturur."""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    scraper.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    
    if proxy:
        scraper.proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
    return scraper

def check_user_status(letter_count, wordlist=None, save_to_file=True, webhook_url=None, filter_premium=False, proxies_list=None):
    """Kullanıcının belirlediği harf sayısı/liste ile kullanıcı durumunu kontrol eder."""
    base_url = "guns.lol/"
    
    proxy_index = 0
    current_proxy = proxies_list[proxy_index] if proxies_list else None
    scraper = create_scraper(current_proxy)
    
    try:
        request_count = 0
        backoff_level = 0
        max_backoff_level = 4
        
        usernames_to_check = wordlist if wordlist else None
        index = 0
        
        while True:
            if usernames_to_check is not None:
                if index >= len(usernames_to_check):
                    print(f"{Fore.CYAN}Wordlist check completed.{Fore.RESET}")
                    break
                current_suffix = usernames_to_check[index]
            else:
                current_suffix = random_letters(letter_count)

            # Premium Alias Filter
            if filter_premium and (current_suffix[0] in PREMIUM_CHARS or current_suffix[-1] in PREMIUM_CHARS):
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}SKIPPED (premium alias){Fore.RESET}")
                index += 1
                continue

            request_count += 1
            scraper.headers.update({'User-Agent': get_random_user_agent()})
            status, error_detail = check_username(scraper, current_suffix)

            is_timeout_err = error_detail and ('Timeout' in error_detail or 'Bağlantı' in error_detail)

            if status == 'ratelimit' or (status == 'error' and is_timeout_err):
                if proxies_list:
                    # Proxy varsa anında sonrakine geç (bekleme yok)
                    proxy_index = (proxy_index + 1) % len(proxies_list)
                    current_proxy = proxies_list[proxy_index]
                    print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}{status} ({error_detail}). Switching proxy...{Fore.RESET}")
                    scraper = create_scraper(current_proxy)
                    continue
                else:
                    if status == 'ratelimit':
                        backoff_level = min(backoff_level + 1, max_backoff_level)
                        wait_time = 70 + (backoff_level * 10) + random.uniform(0, 5)
                        
                        print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}RATE LIMITED ({error_detail}){Fore.RESET}")
                        print(f"{Fore.YELLOW}⏳ Waiting {wait_time:.0f}s... (level {backoff_level}/{max_backoff_level}){Fore.RESET}")
                        
                        scraper = create_scraper()
                        time.sleep(wait_time)
                        continue
                    else:
                        detail = f" ({error_detail})" if error_detail else ""
                        print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}error{detail}{Fore.RESET}")
                        index += 1
                        
            elif status == 'error':
                detail = f" ({error_detail})" if error_detail else ""
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}error{detail}{Fore.RESET}")
                index += 1
                    
            elif status == 'unclaimed':
                backoff_level = max(0, backoff_level - 1)
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - Status: {Fore.GREEN}unclaimed{Fore.RESET}")
                
                if save_to_file:
                    with open("unclaimed.txt", "a") as file:
                        file.write(f"{base_url}{current_suffix}\n")
           
                if webhook_url:
                    embed = {
                        "title": f"Available: {current_suffix} (https://guns.lol/{current_suffix})",
                        "description": f"github.com/efekrbas",
                        "color": 0x9B59B6
                    }
                    payload = {"embeds": [embed]}
                    try:
                        requests.post(webhook_url, json=payload)
                    except Exception as e:
                        print(f"Webhook gönderimi başarısız: {e}")
                index += 1
            else:
                backoff_level = max(0, backoff_level - 1)
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - Status: {Fore.RED}claimed{Fore.RESET}")
                index += 1
        
            # Sabit delay: 6-10 saniye arası (dakikada ~7-8 istek)
            delay = random.uniform(6.0, 10.0)
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Program stopped.{Fore.RESET}")


def ask_yn(prompt):
    """Ask a Y/N question and only accept 'y' or 'n' as valid input."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ('y', 'n'):
            return answer == 'y'
        print(f"{Fore.RED}Please enter a valid value.{Fore.RESET}")


try:
    while True:
        try:
            letter_count = int(input("How many letter usernames should be checked? (Example: 5): "))
            if letter_count > 0:
                break
            print(f"{Fore.RED}Please enter a valid value.{Fore.RESET}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid value.{Fore.RESET}")

    use_wordlist = ask_yn("Use customlist.txt? (Y/N): ")
    wordlist = None

    if use_wordlist:
        try:
            with open("customlist.txt", "r", encoding="utf-8") as file:
                wordlist = [line.strip() for line in file if line.strip() and not (line.strip().startswith("//") or line.strip().startswith("#") or line.strip().startswith(";"))]
            if not wordlist:
                print(f"{Fore.YELLOW}customlist.txt is empty. Switching to random mode.{Fore.RESET}")
                use_wordlist = False
            else:
                print(f"{Fore.GREEN}{len(wordlist)} usernames loaded from customlist.txt.{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.RED}customlist.txt not found. Switching to random mode.{Fore.RESET}")
            use_wordlist = False

    filter_premium = ask_yn("Filter out usernames requiring Premium? (Starts/ends with '.', '-', '_') [Y/N]: ")

    save_to_file = ask_yn("Should unclaimed usernames be saved to unclaimed.txt? (Y/N): ")
    use_webhook = ask_yn("Should unclaimed usernames be sent to a Discord webhook? (Y/N): ")
    webhook_url = None
    if use_webhook:
        while True:
            webhook_url = input("Enter your Discord webhook URL: ").strip()
            if webhook_url.startswith("https://discord.com/api/webhooks/") or webhook_url.startswith("https://discordapp.com/api/webhooks/"):
                break
            print(f"{Fore.RED}Please enter a valid value.{Fore.RESET}")

    use_proxies = ask_yn("Use proxies from proxies.txt? (Y/N): ")
    proxies_list = None
    if use_proxies:
        try:
            with open("proxies.txt", "r", encoding="utf-8") as file:
                proxies_list = [line.strip() for line in file if line.strip() and not (line.strip().startswith("//") or line.strip().startswith("#"))]
            if not proxies_list:
                print(f"{Fore.YELLOW}proxies.txt is empty. Switching to IP mode (no proxies).{Fore.RESET}")
                proxies_list = None
            else:
                print(f"{Fore.GREEN}{len(proxies_list)} proxies loaded from proxies.txt.{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.RED}proxies.txt not found. Switching to IP mode (no proxies).{Fore.RESET}")
            proxies_list = None

    check_user_status(letter_count, wordlist, save_to_file, webhook_url, filter_premium, proxies_list)
except KeyboardInterrupt:
    print(f"\n{Fore.RED}Program stopped.{Fore.RESET}")
