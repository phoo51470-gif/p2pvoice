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

        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3-turbo",
                # 👇 ဒီနေရာတွေမှာ ထည့်ပေးလိုက်လို့ တခြားဘာသာစကား လျှောက်မပြောင်းတော့ပါဘူး
                prompt="Transcribe the exact audio spoken in Spanish, English, Korean, or any language.",
                temperature=0.0
            )

        transcribed_text = transcription.text

        await update.message.reply_text(
            f"📝 **အသံဖိုင်မှ စာပြောင်းလဲချက်:**\n\n{transcribed_text}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ အသံကို စာပြောင်းရာတွင် အမှားအယွင်းရှိပါသည်: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
