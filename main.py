import os
import logging
import uuid
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎙️ အသံဖိုင် ပို့ပေးပါ၊ မူရင်းအသံအတိုင်း စာအဖြစ် ပြောင်းပေးပါမည်။"
    )

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

        # Whisper Model ကို မူရင်းစကားအတိုင်းပဲ စာပြောင်းခိုင်းခြင်း
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3", # v3-turbo ထက် ပိုတိကျတဲ့ v3 ကို သုံးထားပါတယ်
                response_format="text",
                temperature=0.0
            )

        # response_format="text" သုံးထားလို့ တိုက်ရိုက် Text ရပါမယ်
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

    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("🤖 Voice-to-Text Bot စတင်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
