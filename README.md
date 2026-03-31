# 🔫 guns.lol Username Checker

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Engine-Selenium-orange?logo=selenium&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

A powerful, high-accuracy CLI tool to check for available usernames on guns.lol using Selenium with advanced detection logic.

## ⚠️ Important Note
- Usernames that start or end with characters such as ".", "-", or "_" are **Premium Aliases**. You need a premium account to claim these.
- This tool includes a toggle to filter these out so you don't waste time on names you can't claim for free.
- If the tool begins showing all usernames as **Claimed** regardless of availability, your IP has likely been rate-limited by guns.lol. To fix this, please **restart your VPN** or change your IP address.


## ⭐ Features
- **Selenium Engine:** Uses a modern headless browser for perfect site rendering and bypass.
- **Redirect Protection (NEW):** 100% accurate status checking. Detects if a username (like `egn`) is actually a redirect to another profile, preventing false positives.
- **Manual Delay (Interval):** Fully customizable delay settings to prevent IP rate-limiting.
- **GPU & Log Suppression:** Clean CLI experience – no "DevTools listening" or GPU fatal failure logs.
- **Premium Alias Filter:** Built-in option to skip usernames requiring Premium (starts/ends with `.` `-` `_`).
- **Wordlist Support:** Check specific usernames from `customlist.txt`.
- **Discord Webhooks:** Get instant notifications on your Discord server when an available username is found.

## 🛠️ Installation

1. **Prerequisites:** Ensure you have [Python 3.8+](https://www.python.org/) and Google Chrome installed.
2. **Clone & Setup:**
   ```bash
   git clone https://github.com/efekrbas/guns.lol-username-checker.git
   cd guns.lol-username-checker
   pip install -r requirements.txt
   ```
   *Or just run `install.bat` on Windows.*

## 🚀 How to Use

Run the script:
```bash
python gunslol.py
```

### Prompt Flow
1. **Username length** — Char count for random generation.
2. **Delay (Interval)** — Seconds between requests (Recommended: 0.1 - 0.5).
3. **Use customlist.txt?** — Load your own list of usernames.
4. **Filter Premium?** — Auto-skip names free users can't claim.
5. **Save to unclaimed.txt?** — Log hits to a file.
6. **Discord webhook?** — Real-time alerts via Discord.

## 📷 Preview

<p align="left">
  <img src="https://github.com/efekrbas/guns.lol-username-checker/blob/main/images/image1.png" alt="Checker Preview">
</p>

## 🙏 Acknowledgements
  - [@noivan0](https://github.com/noivan0) — Thanks for the filtering feature contributions.

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
