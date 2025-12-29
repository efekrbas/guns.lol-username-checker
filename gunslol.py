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


init(autoreset=True)

def random_letters(n):
    """Rastgele harfler ve özel karakterlerden oluşan bir string oluşturur."""
    characters = string.ascii_lowercase + string.digits + "._-"
    return ''.join(random.choice(characters) for _ in range(n))

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

def check_user_status(letter_count, interval, save_to_file=True, webhook_url=None):
    """Kullanıcının belirlediği harf sayısı ve aralık ile kullanıcı durumunu kontrol eder."""
    base_url = "guns.lol/"
    
    # Chrome seçeneklerini ayarlıyoruz
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Arka planda çalıştır
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-images')  # Resimleri yükleme - hızlandırır
    chrome_options.add_argument('--disable-gpu')  # GPU kullanımını devre dışı bırak
    chrome_options.add_argument('--disable-extensions')  # Uzantıları devre dışı bırak
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # İlk user-agent'i ayarla
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.page_load_strategy = 'eager'  # Hızlı yükleme - DOM hazır olunca devam et
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(3)  # Çok kısa timeout
        driver.implicitly_wait(0)  # Implicit wait yok
        driver.set_script_timeout(2)  # Çok kısa script timeout
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"{Fore.RED}Chrome WebDriver bulunamadı. Lütfen ChromeDriver'ı yükleyin.{Fore.RESET}")
        print(f"Detay: {e}")
        return
    
    try:
        request_count = 0
        while True:
            random_suffix = random_letters(letter_count)
            url = base_url + random_suffix
            request_count += 1

            try:
                # Her istekte user-agent değiştir (rate limit'i önlemek için)
                try:
                    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": get_random_user_agent()
                    })
                except:
                    pass
                
                # Her istekten önce bekleme (rate limit'i önlemek için)
                time.sleep(random.uniform(0.3, 0.7))
                
                # Sayfa yükleme - timeout yok, direkt devam et
                try:
                    driver.get(f"https://{url}")
                except (TimeoutException, WebDriverException):
                    # Timeout olsa bile devam et
                    pass
                
                # Sayfa başlığını al - bekleme yok
                page_title = ""
                try:
                    page_title = driver.title
                except:
                    pass
                
                # Sayfa başlığına göre kontrol et
                # Eğer sayfa başlığında "@" işareti yoksa unclaimed'dir, varsa claimed'dir
                is_unclaimed = "@" not in page_title if page_title else False
                
                if is_unclaimed:
                    status = f"{Fore.GREEN}unclaimed"
                
                    if save_to_file:
                        with open("unclaimed.txt", "a") as file:
                            file.write(f"{url}\n")
               
                    if webhook_url:
                        embed = {
                            "title": f"Available: {random_suffix} (https://guns.lol/{random_suffix})",
                            "description": f"github.com/efekrbas",
                            "color": 0x9B59B6  # Mor renk
                        }
                        payload = {
                            "embeds": [embed],
                        }
                        try:
                            requests.post(webhook_url, json=payload)
                        except Exception as e:
                            print(f"Webhook gönderimi başarısız: {e}")
                else:
                    status = f"{Fore.RED}claimed"
            
                print(f"URL: {Fore.MAGENTA}{base_url}{random_suffix} - Status: {status}{Fore.RESET}")

            except Exception as e:
                # Genel hata yakalama - programın durmaması için
                error_msg = str(e)
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    print(f"URL: {Fore.MAGENTA}{base_url}{random_suffix} - {Fore.YELLOW}Timeout - Skipping{Fore.RESET}")
                else:
                    print(f"URL: {Fore.MAGENTA}{base_url}{random_suffix} - {Fore.RED}Error: {error_msg[:50]}...{Fore.RESET}")
         
            # Rastgele delay ekle - rate limit'i önlemek için
            # Base interval + rastgele 0.5-1.0 saniye (daha uzun)
            random_delay = interval + random.uniform(0.5, 1.0)
            
            # Her 10 istekte bir daha uzun bekleme (rate limit'i önlemek için)
            if request_count % 10 == 0:
                random_delay += random.uniform(2.0, 4.0)
                print(f"{Fore.YELLOW}Rate limit prevention: waiting {random_delay:.2f} seconds...{Fore.RESET}")
            
            # Her 5 istekte bir orta bekleme
            elif request_count % 5 == 0:
                random_delay += random.uniform(0.5, 1.5)
            
            time.sleep(random_delay)
    finally:
        driver.quit()


try:
    letter_count = int(input("How many letter usernames should be checked? (Example: 5): "))
    if letter_count <= 0:
        print("Harf sayısı pozitif bir sayı olmalıdır.")
    else:
        interval = float(input("Delay (in seconds *recommended 0.1*): "))
        if interval <= 0:
            print("Saniye aralığı pozitif bir sayı olmalıdır.")
        else:
            save_to_file = input("Should unclaimed usernames be saved to unclaimed.txt? (Y/N): ").strip().lower() == 'y'
            use_webhook = input("Should unclaimed usernames be sent to a Discord webhook? (Y/N): ").strip().lower()
            webhook_url = None
            if use_webhook == 'y':
                webhook_url = input("Enter your Discord webhook URL: ").strip()


            check_user_status(letter_count, interval, save_to_file, webhook_url)
except ValueError:
    print("Lütfen geçerli bir sayı girin.")
