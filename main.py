import os
import logging
import uuid
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

# /start နှိပ်ရင်ပြမယ့် Message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎙️ အသံဖိုင် (Voice Message) ပို့ပေးပါ၊ စာအဖြစ် ပြောင်းပေးပါမည် (Voice to Text)။"
    )

# အသံဖိုင် သီးသန့် ဘာသာပြန်ပေးမည့် Function
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # အသံဖိုင်အမည် မထပ်အောင် ဖိုင်နာမည် အသစ်ထုတ်ပေးခြင်း
    file_path = f"voice_{uuid.uuid4().hex}.ogg"
    
    try:
        # Telegram ထဲက အသံဖိုင်ကို ဒေါင်းလုဒ်ဆွဲခြင်း
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        await voice_file.download_to_drive(file_path)

        # Groq Whisper (Voice to Text) သုံးပြီး စာအဖြစ်ပြောင်းခြင်း
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3-turbo"
            )

        transcribed_text = transcription.text

        # ပြောင်းထားတဲ့ စာကိုပဲ ရီပလိုင်း ပြန်ပေးခြင်း
        await update.message.reply_text(
            f"📝 **အသံဖိုင်မှ စာပြောင်းလဲချက်:**\n\n{transcribed_text}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ အသံကို စာပြောင်းရာတွင် အမှားအယွင်းရှိပါသည်: {str(e)}")

    finally:
        # ဒေါင်းထားတဲ့ အသံဖိုင်ကို ပြန်ဖျက်ခြင်း
        if os.path.exists(file_path):
            os.remove(file_path)

def main() -> None:
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("❌ Error: BOT_TOKEN သို့မဟုတ် GROQ_API_KEY ကို မတွေ့ပါ။")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # /start Command ကို လက်ခံမည်
    app.add_handler(CommandHandler("start", start))
    
    # ❌ စာသား (Text) တွေကို လုံးဝ Ignore လုပ်ထားသည် (ဂရုထဲမှာ စာရေးရင် ဘာမှပြန်မလုပ်ပါ)
    # ✅ အသံဖိုင် (Voice) ရောက်လာမှသာ handle_voice ကို သွားပါမည်
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("🤖 Voice-to-Text Bot စတင်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
