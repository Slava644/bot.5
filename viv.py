import json
import urllib.request
import urllib.parse
import time
import os
import random
import ssl

# 🔐 Ваші налаштування:
TOKEN = '7099223221:AAHOMnklX4l1o5KXC-aezY4Z8e3dAEJreqU'
ADMIN_ID = 1496554517
URL = f'https://api.telegram.org/bot{TOKEN}/'
DATA_FILE = 'data.json'

context = ssl.create_default_context()

# Завантаження та збереження даних
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Надсилання повідомлення
def send_message(chat_id, text, keyboard=None, inline_keyboard=None):
    payload = {
        'chat_id': chat_id,
        'text': text,
    }

    if keyboard:
        payload['reply_markup'] = json.dumps({
            'keyboard': keyboard,
            'resize_keyboard': True
        }, ensure_ascii=False)

    elif inline_keyboard:
        payload['reply_markup'] = json.dumps({
            'inline_keyboard': inline_keyboard
        }, ensure_ascii=False)

    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(URL + 'sendMessage', data=data)
    try:
        with urllib.request.urlopen(req, context=context) as response:
            return response.read()
    except Exception as e:
        print("❌ ПОМИЛКА надсилання повідомлення:", e)

# Відповідь на inline callback
def answer_callback_query(callback_id, text):
    data = urllib.parse.urlencode({
        'callback_query_id': callback_id,
        'text': text,
        'show_alert': False
    }).encode()
    req = urllib.request.Request(URL + 'answerCallbackQuery', data=data)
    with urllib.request.urlopen(req, context=context) as response:
        return response.read()

# Отримання оновлень
def get_updates(offset=None):
    try:
        url = URL + 'getUpdates'
        if offset:
            url += f'?offset={offset}'
        with urllib.request.urlopen(url, context=context) as response:
            return json.loads(response.read())
    except Exception as e:
        print("❌ ПОМИЛКА отримання оновлень:", e)
        return {}

# Основна функція
def main():
    offset = None
    data = load_data()
    print("✅ Бот запущено!")

    menu_keyboard = [["🎰 Спін"], ["👤 Профіль", "🛍 Магазин"]]

    products = {
        'shop_1': {'name': '60 UC', 'price': 200},
        'shop_2': {'name': '360 UC', 'price': 1000},
        'shop_3': {'name': '660 UC', 'price': 2000},
        'shop_4': {'name': '1800 UC', 'price': 6000},
    }

    while True:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            print("⬅️ Отримано:", update)
            if "message" in update:
                message = update["message"]
                user = message.get("from", {})
                chat_id = message.get("chat", {}).get("id")
                user_id = str(user.get("id"))
                username = user.get("username") or user.get("first_name")
                text = message.get("text", "").strip().lower()

                if not chat_id or not text:
                    continue

                if user_id not in data:
                    data[user_id] = {
                        "username": username,
                        "points": 0,
                        "spins": 0,
                        "last_spin": 0
                    }

                if text in ["/start", "start"]:
                    send_message(chat_id, "👋 Привіт! Обери дію з меню:", keyboard=menu_keyboard)

                elif text in ["/spean", "спін", "🎰 спін"]:
                    current_time = time.time()
                    last_spin = data[user_id].get("last_spin", 0)

                    if current_time - last_spin < 86400:
                        remaining = int((86400 - (current_time - last_spin)) // 3600)
                        send_message(chat_id, f"⏳ Ви вже крутили. Спробуйте через {remaining} год.")
                    else:
                        points = random.randint(-10, 10)
                        data[user_id]["points"] += points
                        data[user_id]["spins"] += 1
                        data[user_id]["last_spin"] = current_time
                        save_data(data)
                        send_message(chat_id, f"🎰 Ви виграли {points} балів!")

                elif text in ["/profile", "профіль", "👤 профіль"]:
                    u = data[user_id]
                    msg = f"👤 {u['username']}\nБали: {u['points']}\nСпіни: {u['spins']}"
                    send_message(chat_id, msg)

                elif text in ["/shop", "магазин", "🛍 магазин"]:
                    inline = [
                        [{"text": "1️⃣ 60 UC", "callback_data": "shop_1"}],
                        [{"text": "2️⃣ 360 UC", "callback_data": "shop_2"}],
                        [{"text": "3️⃣ 660 UC", "callback_data": "shop_3"}],
                        [{"text": "4️⃣ 1800 UC", "callback_data": "shop_4"}]
                    ]
                    send_message(chat_id, "🛍 Виберіть товар:", inline_keyboard=inline)

                elif text.startswith("/nah "):
                    target = message["text"].split("/nah ", 1)[1].strip()
                    if target.startswith("@"): send_message(chat_id, f"{target}, нах")

                elif text.startswith("/ydar "):
                    target = message["text"].split("/ydar ", 1)[1].strip()
                    if target.startswith("@"): send_message(chat_id, f"{target}, получай удар 🥊")

            elif "callback_query" in update:
                query = update["callback_query"]
                callback_data = query["data"]
                callback_id = query["id"]
                user = query["from"]
                chat_id = query["message"]["chat"]["id"]
                user_id = str(user["id"])
                username = user.get("username") or user.get("first_name")

                if callback_data in products:
                    product = products[callback_data]
                    if data[user_id]["points"] >= product["price"]:
                        data[user_id]["points"] -= product["price"]
                        save_data(data)

                        answer_callback_query(callback_id, f"✅ Ви купили {product['name']}")
                        send_message(chat_id, f"🎁 Ви купили {product['name']} за {product['price']} балів!")
                        send_message(ADMIN_ID, f"🛒 {username} купив {product['name']}")
                    else:
                        answer_callback_query(callback_id, "❌ Недостатньо балів")

            offset = update["update_id"] + 1
        time.sleep(1)

if __name__ == "__main__":
    main()
