import os
from flask import Flask
from threading import Thread
import telebot
import requests
import time
from telebot.apihelper import ApiException

# Dummy Web Server (Render က Port ရှာတွေ့အောင် လုပ်ပေးခြင်း)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Server ကို စတင်ရန်
keep_alive()

TOKEN = "8861250979:AAFcPjnlmgzHEx9BjlCM7q7X4YOVry-c_Uw"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "မင်္ဂလာပါ! အသံဖိုင် (သို့) Voice ပို့ပေးပါက စာသားအဖြစ် ပြောင်းပေးပါမည်။ (Group ထဲတွင် Bot ကို Reply လုပ်၍ (သို့မဟုတ်) Mention ခေါ်၍ အသံပို့ပေးပါ)")

@bot.message_handler(content_types=['voice', 'audio'])
def handle_voice(message):
    chat_type = message.chat.type
    
    if chat_type in ['group', 'supergroup']:
        bot_username = bot.get_me().username
        is_mentioned = message.caption and f"@{bot_username}" in message.caption
        is_replied = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        
        if not is_mentioned and message.text:
            is_mentioned = f"@{bot_username}" in message.text

        if not (is_mentioned or is_replied):
            return

    try:
        bot.reply_to(message, "🎙️ အသံဖိုင်ကို စစ်ဆေးနေပါသည်...")

        if message.voice:
            file_info = bot.get_file(message.voice.file_id)
            file_ext = "voice.ogg"
        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)
            file_ext = "audio.mp3"
        else:
            bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ မှန်ကန်သော အသံဖိုင် (Voice / Audio) ကို ပို့ပေးပါ။")
            return

        downloaded_file = bot.download_file(file_info.file_path)

        with open(file_ext, "wb") as f:
            f.write(downloaded_file)

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        
        with open(file_ext, "rb") as audio_file:
            files = {"file": (file_ext, audio_file, "audio/ogg")}
            data = {"model": "whisper-large-v3"}
            
            response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            transcript = response.json().get("text", "စာသားအဖြစ် ပြောင်းလဲ၍ မရပါ။")
            bot.reply_to(message, f"📝 **ပြောင်းလဲထားသော စာသား:**\n\n{transcript}", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ အမှားအယွင်းရှိပါသည်: {response.text}")

        if os.path.exists(file_ext):
            os.remove(file_ext)

    except Exception as e:
        print(f"Voice Handle Error: {e}")
        try:
            bot.reply_to(message, f"⚠️ ချို့ယွင်းချက်ရှိပါသည်: ခဏစောင့်ပြီး ပြန်ကြိုးစားပေးပါ။")
        except:
            pass

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_type = message.chat.type
    
    if chat_type in ['group', 'supergroup']:
        bot_username = bot.get_me().username
        if message.text and f"@{bot_username}" in message.text:
            bot.reply_to(message, "အသံဖိုင် ပို့ပါ၊ ဘာကူညီရမလဲ။")
        return
    else:
        bot.reply_to(message, "အသံဖိုင် (သို့) Voice ပို့ပေးပါ၊ စာသားအဖြစ် ပြောင်းပေးပါမည်။")

if __name__ == '__main__':
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=90, long_polling_timeout=90)
        except ApiException as e:
            print(f"Telegram API Error occurred: {e}")
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"Network Connection Error occurred: {e}")
            time.sleep(10)
        except Exception as e:
            print(f"Unexpected Error occurred: {e}")
            time.sleep(5)
