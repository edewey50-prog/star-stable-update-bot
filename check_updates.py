import json
import os
import re
import urllib.request
from html import unescape

NEWS_URL = "https://api.starstable.com/news"
STATE_FILE = "last_update.txt"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def fetch_news():
    request = urllib.request.Request(
        NEWS_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def find_game_updates(html):
    pattern = re.compile(
        r'href="([^"]+)"[^>]*>.*?'
        r'(?:Game Update).*?'
        r'<h[1-6][^>]*>(.*?)</h[1-6]>',
        re.IGNORECASE | re.DOTALL
    )

    updates = []

    for link, title in pattern.findall(html):
        title = clean_text(title)

        if link.startswith("/"):
            link = "https://www.starstable.com" + link

        updates.append({
            "title": title,
            "url": link
        })

    return updates


def load_last_update():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as file:
        return file.read().strip()


def save_last_update(update_url):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        file.write(update_url)


def send_to_discord(update):
    if not WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not configured.")

    payload = {
        "content": "➶ **NEW STAR STABLE GAME UPDATE!**",
        "embeds": [
            {
                "title": update["title"],
                "url": update["url"],
                "description": (
                    "A new **Star Stable Game Update** has been posted! 🐴\n\n"
                    "Click the title above to read the full update."
                )
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "StarStableUpdateBot/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()


def main():
    html = fetch_news()
    updates = find_game_updates(html)

    if not updates:
        raise RuntimeError("No Star Stable Game Update articles were found.")

    newest = updates[0]
    last_update = load_last_update()

    # First run: remember the current update without posting an old article.
    if last_update is None:
        save_last_update(newest["url"])
        print("Initial Game Update saved:", newest["title"])
        return

    if newest["url"] == last_update:
        print("No new Game Update.")
        return

    send_to_discord(newest)
    save_last_update(newest["url"])
    print("Posted new Game Update:", newest["title"])


if __name__ == "__main__":
    main()
