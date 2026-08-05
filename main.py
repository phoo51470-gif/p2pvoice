import os
import logging
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "✅ Bot (Groq Powered) အလုပ်လုပ်နေပါပြီ!\n\n"
        "🎙️ အသံဖိုင် (Voice Message) သို့မဟုတ် 📝 စာတိုများ ပို့ပေးပါ။ "
        "အင်္ဂလိပ် သို့မဟုတ် မြန်မာသို့ ဘာသာပြန်ပေးပါမည်။"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    await update.message.reply_text("🔄 ဘာသာပြန်နေပါသည်။ ခဏစောင့်ပါ...")

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate English text to natural Myanmar (Burmese) language, or Myanmar text to English directly without extra explanations."
                },
                {"role": "user", "content": user_text}
            ]
        )
        await update.message.reply_text(completion.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"❌ အမှားအယွင်းရှိပါသည်: {str(e)}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🎙️ အသံဖိုင်ကို လက်ခံရရှိပါသည်။ ဘာသာပြန်နေပါပြီ...")
    
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        file_path = "voice_input.ogg"
        await voice_file.download_to_drive(file_path)

        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3-turbo"
            )

        transcribed_text = transcription.text

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Translate the given text into natural Burmese (Myanmar language)."
                },
                {"role": "user", "content": transcribed_text}
            ]
        )

        translated_text = completion.choices[0].message.content

        await update.message.reply_text(
            f"🎙️ **ကြားရသော စာတို:**\n{transcribed_text}\n\n"
            f"🇲🇲 **မြန်မာဘာသာပြန်:**\n{translated_text}"
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ အသံ ဘာသာပြန်ရာတွင် အမှားအယွင်းရှိပါသည်: {str(e)}")

def main() -> None:
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("❌ Error: BOT_TOKEN သို့မဟုတ် GROQ_API_KEY ကို Render Environment Variable မှာ မတွေ့ပါ။")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("🤖 Groq Bot စတင်ပွဲထုတ်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
