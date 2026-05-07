import telebot
from telebot import types
import yt_dlp
import os

# التوكن الخاص بك
API_TOKEN = '8780076470:AAGNtBSu8EuKybpvg-k-gIfUtKUa8IgoLAM'
bot = telebot.TeleBot(API_TOKEN)

# تخزين روابط المستخدمين وخياراتهم
user_data = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (f"أهلاً بك يا {user_name} في بوت التحميل الشامل! 📥\n\n"
                    "يمكنني التحميل من يوتيوب، تيك توك، فيسبوك ومعظم المنصات.\n"
                    "فقط أرسل لي رابط الفيديو لنبدأ.")
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def handle_link(message):
    url = message.text
    user_data[message.chat.id] = {'url': url}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    # أزرار الدقة
    resolutions = [
        ("144p", "144"), ("360p", "360"), 
        ("480p", "480"), ("720p", "720"), 
        ("1080p", "1080"), ("أعلى دقة", "best")
    ]
    
    btns = [types.InlineKeyboardButton(text=r[0], callback_data=r[1]) for r in resolutions]
    audio_btn = types.InlineKeyboardButton("موسيقى/صوت MP3 🎵", callback_data="mp3")
    
    markup.add(*btns)
    markup.add(audio_btn)
    
    bot.send_message(message.chat.id, "اختر الجودة المطلوبة أو تحويل لصوت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "يرجى إرسال الرابط مرة أخرى.")
        return

    url = user_data[chat_id]['url']
    choice = call.data
    
    bot.edit_message_text("جاري التجهيز والتحميل... قد يستغرق ذلك وقتاً حسب الحجم ⏳", chat_id, call.message.message_id)
    
    file_name = f"download_{chat_id}"
    
    # إعدادات yt-dlp المتطورة
    ydl_opts = {
        'outtmpl': f"{file_name}.%(ext)s",
        'writesubtitles': True, # تنزيل الترجمة
        'allsubtitles': False,
        'slang': ['ar', 'en'], # محاولة جلب العربية أو الإنجليزية
        'quiet': True,
        'no_warnings': True,
    }

    if choice == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif choice == "best":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    else:
        # اختيار دقة معينة أو أقل منها إذا لم تتوفر
        ydl_opts['format'] = f'bestvideo[height<={choice}]+bestaudio/best[height<={choice}]'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # في حال تحويل الصوت، الاسم يتغير لـ mp3
            if choice == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"

        # إرسال الملف
        with open(filename, 'rb') as f:
            if choice == "mp3":
                bot.send_audio(chat_id, f, caption="تم التحميل بواسطة بوت عدي")
            else:
                bot.send_video(chat_id, f, caption=f"الدقة المطلوبة: {choice if choice!='best' else 'أعلى جودة'}")
        
        # التنظيف
        os.remove(filename)
        bot.delete_message(chat_id, call.message.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"عذراً، حدث خطأ: {str(e)}")

print("البوت المطور يعمل الآن...")
bot.polling(none_stop=True)
