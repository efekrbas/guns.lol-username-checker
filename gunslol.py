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
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
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
                
                # Sayfanın yüklenmesini bekliyoruz (maksimum 30 saniye)
                try:
                    WebDriverWait(driver, 30).until(
                        lambda d: "Please wait" not in d.page_source or "verify" not in d.page_source.lower()
                    )
                except TimeoutException:
                    pass
                
                # Biraz daha bekleyip sayfanın tam yüklenmesini sağlıyoruz
                time.sleep(2)
                
                page_text = driver.page_source.lower()

                # Claimed kontrolü - belirli metinler varsa claimed'dir
                claimed_indicators = [
                    "join discord.gg/guns to display your status",
                    "please connect your discord account"
                ]
                is_claimed = any(indicator in page_text for indicator in claimed_indicators)

                # Unclaimed kontrolü - "Claim this username by clicking on the button below!" metnini ara
                unclaimed_indicator = "claim this username by clicking on the button below!"
                
                # Eğer claimed değilse ve unclaimed göstergesi varsa unclaimed'dir
                is_unclaimed = not is_claimed and unclaimed_indicator in page_text
                
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
