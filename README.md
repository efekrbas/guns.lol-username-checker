# 🔫 guns.lol Username Checker

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Maintained: Yes](https://img.shields.io/badge/Maintained-Yes-brightgreen.svg)

A fast CLI tool to check for available usernames on guns.lol.

## ⚠️ Important Note
- Usernames that start or end with characters such as ".", "-", or "_" can only be used in the alias section. (If you don't have a premium, you need to purchase a premium for alias.)

## ⭐ Features
- **Cloudflare Bypass:** Uses `cloudscraper` to completely bypass Cloudflare protection without the heavy overhead of Selenium.
- **Robust Detection:** 100% accurate status checking by relying on precise `<title>` tags to avoid false positives (handles Premium and custom pages perfectly).
- **Proxy Support (NEW):** Optional proxy integration (`proxies.txt`) with Round-Robin IP rotation. Skip rate limits instantly!
- **Customlist Support:** Option to check specific usernames from `customlist.txt`.
- **Premium Character Filter:** Toggle to skip usernames starting/ending with `.`, `-`, `_` — avoids non-claimable results for free users.
- **Discord Integration:** Send available usernames directly to your Discord server via webhooks.
- **Smart Rate Limiting:** Built-in 80s dynamic cooldown system for IP protection when running without proxies.

## 🛠️ Installation

1. **Prerequisites:** Ensure you have [Python 3.8+](https://www.python.org/) installed.
2. **Clone the Repository:**
   ```bash
   git clone https://github.com/efekrbas/guns.lol-username-checker.git
   cd guns.lol-username-checker
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or simply run `install.bat` on Windows.

## 🚀 How to Use

Run the script and follow the on-screen prompts:
```bash
python gunslol.py
```

### Prompt Flow
1. **Username length** — How many characters (e.g. 3)
2. **Use customlist.txt?** — Load usernames from file instead of random
3. **Save to unclaimed.txt?** — Log available usernames to a file
4. **Discord webhook?** — Send notifications to Discord
5. **Filter Premium aliases?** — Skip usernames starting/ending with `.` `-` `_`
6. **Use proxies.txt?** — Use a list of proxies to bypass rate limits instantly (`ip:port` or `user:pass@ip:port` format)

## 📷 Preview

<p align="left">
  <img src="https://github.com/efekrbas/guns.lol-username-checker/blob/main/images/image1.png" alt="Checker Preview">
</p>

## 🙏 Acknowledgements
- [@noivan0](https://github.com/noivan0) — For his comprehensive code review, alias filtering suggestion, and the brilliant idea to migrate from Selenium to a request-based architecture!

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
