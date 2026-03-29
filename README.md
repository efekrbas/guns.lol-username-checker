# 🔫 guns.lol Username Checker

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Maintained: Yes](https://img.shields.io/badge/Maintained-Yes-brightgreen.svg)

A fast CLI tool to check for available usernames on guns.lol.

## ⚠️ Important Note
- Usernames that start or end with characters such as ".", "-", or "_" can only be used in the alias section. (If you don't have a premium, you need to purchase a premium for alias.)

## ⭐ Features
- **Robust Detection:** Uses content-based verification (checking for "Username not found" header) to prevent false positives.
- **Customlist Support:** Option to check specific usernames from `customlist.txt`.
- **Premium Character Filter:** Toggle to skip usernames starting/ending with `.`, `-`, `_` — avoids non-claimable results for free users.
- **Discord Integration:** Send available usernames directly to your Discord server via webhooks.
- **Rate Limit Prevention:** Intelligent delays and user-agent rotation.

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
2. **Delay** — Seconds between requests (recommended: 0.1)
3. **Use customlist.txt?** — Load usernames from file instead of random
4. **Save to unclaimed.txt?** — Log available usernames to a file
5. **Discord webhook?** — Send notifications to Discord
6. **Filter Premium aliases?** — Skip usernames starting/ending with `.` `-` `_`

## 📷 Preview

<p align="left">
  <img src="https://github.com/efekrbas/guns.lol-username-checker/blob/main/images/image1.png" alt="Checker Preview">
</p>

## 🙏 Acknowledgements
- [@noivan0](https://github.com/noivan0) — For his comprehensive code review and alias filtering suggestion.

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
