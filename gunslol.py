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


init(autoreset=True)

def random_letters(n, filter_premium=False):
    """Rastgele harfler ve özel karakterlerden oluşan bir string oluşturur."""
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
    """Rastgele bir user-agent döndürür - rate limit'i önlemek için."""
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

def check_user_status(letter_count, interval, wordlist=None, filter_premium=False, save_to_file=True, webhook_url=None):
    """Kullanıcının belirlediği harf sayısı/liste ve aralık ile kullanıcı durumunu kontrol eder."""
    base_url = "guns.lol/"
    
    # Chrome seçeneklerini ayarlıyoruz
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Arka planda çalıştır (Yeni modern mod)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu-compositing') # GPU kompozitleme kapat
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-images')  # Resimleri yükleme - hızlandırır
    chrome_options.add_argument('--disable-gpu')  # GPU kullanımını devre dışı bırak
    chrome_options.add_argument('--disable-software-rasterizer') # Yazılımsal renderers kapat
    chrome_options.add_argument('--ignore-gpu-blocklist') # GPU blok listesini yoksay
    chrome_options.add_argument('--disable-extensions')  # Uzantıları devre dışı bırak
    chrome_options.add_argument('--log-level=3')  # Sadece kritik hataları göster
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # İlk user-agent'i ayarla
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.page_load_strategy = 'eager'  # Hızlı yükleme - DOM hazır olunca devam et
    
    try:
        # DevTools ve diğer terminal mesajlarını sistem seviyesinde susturmak için
        service = Service(log_path=os.devnull)
        if os.name == 'nt': # Sadece Windows için
            service.creation_flags = subprocess.CREATE_NO_WINDOW
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(10)  # Süreyi 10 saniyeye çıkardık
        driver.implicitly_wait(0)
        driver.set_script_timeout(3)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"{Fore.RED}Chrome WebDriver bulunamadı. Lütfen ChromeDriver'ı yükleyin.{Fore.RESET}")
        print(f"Detay: {e}")
        return
    
    try:
        request_count = 0
        
        # Eğer wordlist varsa ona göre dön, yoksa sonsuz döngü (random) yap
        usernames_to_check = wordlist if wordlist else None
        index = 0
        
        while True:
            if usernames_to_check is not None:
                if index >= len(usernames_to_check):
                    print(f"{Fore.CYAN}Wordlist check completed.{Fore.RESET}")
                    break
                current_suffix = usernames_to_check[index]
                index += 1
                
                # Wordlist kontrolünde filtreleme aktifse geç
                if filter_premium:
                    if current_suffix[0] in "._-" or current_suffix[-1] in "._-":
                        print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}Skipping (Premium Alias){Fore.RESET}")
                        continue
            else:
                current_suffix = random_letters(letter_count, filter_premium)
            
            url = base_url + current_suffix
            request_count += 1

            try:
                # Retry mekanizması
                max_retries = 2
                attempt = 0
                is_unclaimed = False
                is_error = False
                status = ""
                
                while attempt < max_retries:
                    try:
                        # Her istekte user-agent değiştir (rate limit'i önlemek için)
                        try:
                            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                                "userAgent": get_random_user_agent()
                            })
                        except:
                            pass
                        
                        # Her istekten önce bekleme (rate limit'i önlemek için)
                        time.sleep(random.uniform(0.5, 1.0))
                        
                        # Sayfa yükleme
                        try:
                            driver.get(f"https://{url}")
                            # Sayfanın en azından bir kısmının yüklendiğinden emin olalım
                            time.sleep(1.0) # Bekleme süresini artırdık
                        except (TimeoutException, WebDriverException):
                            attempt += 1
                            if attempt < max_retries:
                                time.sleep(2)
                                continue
                            is_error = True
                            break
                        
                        # Durum tespiti - En sağlam yöntemler:
                        is_unclaimed = False
                        is_error = False
                        
                        try:
                            # 1. URL Kontrolü (Yönlendirme varsa alınmıştır)
                            current_url = driver.current_url.lower().rstrip('/')
                            if current_suffix.lower() not in current_url:
                                is_unclaimed = False # Alınmış ve başka yere yönlendirilmiş
                            else:
                                # 2. Sayfa içeriğinde "Username not found" başlığını ara
                                h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                                unclaimed_found = False
                                for h1 in h1_elements:
                                    if "username not found" in h1.text.lower() or "kullanıcı adı bulunamadı" in h1.text.lower():
                                        unclaimed_found = True
                                        break
                                
                                if unclaimed_found:
                                    is_unclaimed = True
                                else:
                                    # 3. Sayfa başlığını kontrol et (Ek önlem)
                                    # Unclaimed sayfa başlığı sabittir: "guns.lol: everything you want..." veya "çözüm burada"
                                    page_title = driver.title.lower()
                                    unclaimed_titles = [
                                        "guns.lol: everything you want, right here.",
                                        "guns.lol: istediğin her şey burada.",
                                        "guns.lol: istedigin her sey burada."
                                    ]
                                    
                                    if any(ut in page_title for ut in unclaimed_titles):
                                        is_unclaimed = True
                                    elif not page_title:
                                        is_error = True
                                    else:
                                        is_unclaimed = False # Diğer durumlarda alınmış kabul et
                        except:
                            is_error = True

                        # Eğer hata almadıysak veya son denemeyse döngüden çık
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

                if is_error:
                    status = f"{Fore.YELLOW}error/timeout"
                elif is_unclaimed:
                    status = f"{Fore.GREEN}unclaimed"
                
                    if save_to_file:
                        with open("unclaimed.txt", "a") as file:
                            file.write(f"{current_suffix}\n")
                
                    if webhook_url:
                        embed = {
                            "title": f"Available: {current_suffix} (https://guns.lol/{current_suffix})",
                            "description": f"github.com/efekrbas",
                            "color": 0x9B59B6
                        }
                        payload = {"embeds": [embed]}
                        try:
                            requests.post(webhook_url, json=payload)
                        except:
                            pass
                else:
                    status = f"{Fore.RED}claimed"
                
                print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - Status: {status}{Fore.RESET}")

            except Exception as e:
                # Genel hata yakalama - programın durmaması için
                error_msg = str(e)
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.YELLOW}Timeout - Skipping{Fore.RESET}")
                else:
                    print(f"URL: {Fore.MAGENTA}{base_url}{current_suffix} - {Fore.RED}Error: {error_msg[:50]}...{Fore.RESET}")
         
            # Rastgele delay ekle
            random_delay = interval + random.uniform(0.5, 1.0)
            if request_count % 10 == 0:
                random_delay += random.uniform(2.0, 4.0)
                print(f"{Fore.YELLOW}Rate limit prevention: waiting {random_delay:.2f} seconds...{Fore.RESET}")
            elif request_count % 5 == 0:
                random_delay += random.uniform(0.5, 1.5)
            
            time.sleep(random_delay)
    finally:
        driver.quit()


try:
    letter_count = int(input("How many letter usernames should be checked? (Example: 5): "))
    if letter_count <= 0:
        print("Harf sayısı pozitif bir sayı olmalıdır.")
        exit()

    interval = float(input("Delay (in seconds *recommended 0.1*): "))
    if interval < 0:
        print("Saniye aralığı negatif olamaz.")
        exit()

    use_wordlist = input("Use customlist.txt? (Y/N): ").strip().lower() == 'y'
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

    filter_premium = input("Filter out usernames requiring Premium? (Starts/ends with '.', '-', '_') [Y/N]: ").strip().lower() == 'y'

    save_to_file = input("Should unclaimed usernames be saved to unclaimed.txt? (Y/N): ").strip().lower() == 'y'
    use_webhook = input("Should unclaimed usernames be sent to a Discord webhook? (Y/N): ").strip().lower()
    webhook_url = None
    if use_webhook == 'y':
        webhook_url = input("Enter your Discord webhook URL: ").strip()

    check_user_status(letter_count, interval, wordlist, filter_premium, save_to_file, webhook_url)
except ValueError:
    print("Lütfen geçerli bir değer girin.")
except KeyboardInterrupt:
    print("\nProgram durduruldu.")
