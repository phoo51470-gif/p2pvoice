import os
import logging
import uuid
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Render Environment Variables ထဲကနေ ဆွဲယူခြင်း
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Client စတင်ခြင်း
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Render Web Service Port မမှားရအောင် Flask App ထည့်သွင်းခြင်း
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running perfectly as a Web Service!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎙️ အသံဖိုင် (Voice သို့မဟုတ် Audio File) ပို့ပေးပါ၊ မူရင်းပြောသည့်အတိုင်း စာအဖြစ် ပြောင်းပေးပါမည်။"
    )

# အသံဖိုင် ဖတ်ပြီး မူရင်းအတိုင်း စာပြောင်းပေးမည့် Function
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file_path = f"voice_{uuid.uuid4().hex}.ogg"
    
    try:
        if update.message.voice:
            voice_file = await context.bot.get_file(update.message.voice.file_id)
        elif update.message.audio:
            voice_file = await context.bot.get_file(update.message.audio.file_id)
        else:
            return

        await voice_file.download_to_drive(file_path)

        # Whisper Model ကို ဘာသာမပြန်ဘဲ မူရင်းအသံအတိုင်း စာပြောင်းခိုင်းခြင်း
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                response_format="text",
                temperature=0.0
            )

        transcribed_text = str(transcription).strip()

        await update.message.reply_text(
            f"📝 **အသံဖိုင်မှ စာပြောင်းလဲချက်:**\n\n{transcribed_text}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ အသံကို စာပြောင်းရာတွင် အမှားအယွင်းရှိပါသည်: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def main() -> None:
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("❌ Error: BOT_TOKEN သို့မဟုတ် GROQ_API_KEY ကို မတွေ့ပါ။")
        return

    # Web Service Port မိစေရန် Flask Server ကို Background Thread ဖြင့် Run ခြင်း
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("🤖 Voice-to-Text Bot (Web Service) စတင်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
