from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import random
import string
import time
from colorama import Fore, init
import requests


init(autoreset=True)

def random_letters(n):
    """Rastgele harfler ve özel karakterlerden oluşan bir string oluşturur."""
    characters = string.ascii_lowercase + string.digits + "._-"
    return ''.join(random.choice(characters) for _ in range(n))

def check_user_status(letter_count, interval, save_to_file=True, webhook_url=None):
    """Kullanıcının belirlediği harf sayısı ve aralık ile kullanıcı durumunu kontrol eder."""
    base_url = "guns.lol/"
    
    # Chrome seçeneklerini ayarlıyoruz
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Arka planda çalıştır
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-images')  # Resimleri yükleme (hızlandırır)
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(10)  # Sayfa yükleme timeout'unu 10 saniyeye düşür
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"{Fore.RED}Chrome WebDriver bulunamadı. Lütfen ChromeDriver'ı yükleyin.{Fore.RESET}")
        print(f"Detay: {e}")
        return
    
    try:
        while True:
            random_suffix = random_letters(letter_count)
            url = base_url + random_suffix

            try:
                driver.get(f"https://{url}")
                
                # Sayfa içeriğinin yüklenmesi için bekleme (maksimum 5 saniye)
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.page_source and len(d.page_source) > 100
                    )
                except TimeoutException:
                    pass
                
                # Ekstra bekleme (JavaScript içeriğinin yüklenmesi için)
                time.sleep(2)  # Daha uzun bekleme - modal'ın yüklenmesi için
                
                # Sayfa kaynağını hem orijinal hem küçük harfle kontrol et
                page_source_original = driver.page_source
                page_text = page_source_original.lower()

                # ÖNCE Unclaimed kontrolü - eğer bu göstergeler varsa kesinlikle unclaimed'dir
                unclaimed_indicators_specific = [
                    "kullanıcı adı bulunamadı",  # Türkçe - en spesifik
                    "Kullanıcı adı bulunamadı",  # Türkçe orijinal
                    "aşağıdaki butonla bu kullanıcı adını kap!",  # Türkçe - spesifik
                    "Aşağıdaki butonla bu kullanıcı adını kap!",  # Türkçe orijinal
                    "claim this username by clicking on the button below!",  # İngilizce - spesifik
                    "Claim this username by clicking on the button below!"  # İngilizce orijinal
                ]
                
                # Hem orijinal hem küçük harfle kontrol et
                is_unclaimed = any(indicator in page_source_original for indicator in unclaimed_indicators_specific) or \
                               any(indicator in page_text for indicator in unclaimed_indicators_specific)
                
                # Eğer unclaimed değilse, claimed olarak kabul et
                # (Unclaimed göstergeleri yoksa sayfa muhtemelen claimed'dir)
                
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
                print(f"Error accessing https://{url}: {e}")
         
            time.sleep(interval)
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
