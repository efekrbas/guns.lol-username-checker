import requests
import random
import string
import time
from colorama import Fore, init

# colorama'yı başlat
init(autoreset=True)

def random_letters(n):
    """Rastgele harfler ve özel karakterlerden oluşan bir string oluşturur."""
    characters = string.ascii_lowercase + string.digits + "._-"
    return ''.join(random.choice(characters) for _ in range(n))

def check_user_status(letter_count, interval, save_to_file=True, webhook_url=None):
    """Kullanıcının belirlediği harf sayısı ve aralık ile kullanıcı durumunu kontrol eder."""
    base_url = "guns.lol/"
    while True:
        # Rastgele harf sayısına göre URL oluştur
        random_suffix = random_letters(letter_count)
        url = base_url + random_suffix

        try:
            # Web sitesine istek gönder
            response = requests.get(f"https://{url}")

            if "This user is not claimed" in response.text:
                status = f"{Fore.GREEN}unclaimed"
                # Unclaimed kullanıcı adını dosyaya yaz
                if save_to_file:
                    with open("unclaimed.txt", "a") as file:
                        file.write(f"{url}\n")
                # Discord webhook'a unclaimed kullanıcı adı gönder
                if webhook_url:
                    payload = {"content": f"Unclaimed username found: {url} @everyone"}
                    try:
                        requests.post(webhook_url, json=payload)
                    except Exception as e:
                        print(f"Webhook gönderimi başarısız: {e}")
            else:
                status = f"{Fore.RED}claimed"

            # URL'yi mor renkte ve diğer kısmı varsayılan renkte yazdır
            print(f"URL: {Fore.MAGENTA}{base_url}{random_suffix} - Status: {status}{Fore.RESET}")

        except Exception as e:
            print(f"Error accessing https://{url}: {e}")

        # Kullanıcının belirlediği saniye aralığına göre bekle
        time.sleep(interval)

# Kullanıcıdan harf sayısı ve kontrol aralığı bilgilerini al
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

            # Fonksiyonu kullanıcıdan alınan bilgilerle çalıştır
            check_user_status(letter_count, interval, save_to_file, webhook_url)
except ValueError:
    print("Lütfen geçerli bir sayı girin.")
