from datetime import datetime
import requests
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import os  


TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY    = os.environ.get("GROQ_API_KEY")
OMDB_API_KEY    = os.environ.get("OMDB_API_KEY")
NEWS_API_KEY    = os.environ.get("NEWS_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
# ──────────────────────────────────────────────────

client = Groq(api_key=GROQ_API_KEY)
chat_histories = {}

# ── SYSTEM PROMPT ─────────────────────────────────
def get_system_prompt():
    return f"""You are ARIA (Artificial Response & Intelligence Assistant), a smart, friendly and helpful personal assistant on Telegram.

Today's date and time is: {datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}

🌐 LANGUAGE INSTRUCTIONS (Very Important):
- If the user writes in Telugu script (తెలుగు), reply in Telugu script
- If the user writes Telugu in English letters (like "nuvu evaru", "ela unnav", "meeru ela unnaru"), reply in Telugu but using English letters (Transliteration). Example: "Nenu ARIA ni! Meeru ela unnaru? 😊"
- If the user writes in Hindi script (हिंदी), reply in Hindi script
- If the user writes Hindi in English letters (like "tum kaun ho", "kya hal hai"), reply in Hindi using English letters. Example: "Main ARIA hun! Aap kaise hain? 😊"
- If the user writes in English, reply in English
- Always detect the language/style and match it exactly
- Never mix scripts unless user does it first

Your personality:
- Warm, friendly and professional
- Give concise and clear answers
- Use emojis occasionally 😊
- If you don't know something, say so honestly
- Always try to be helpful and positive
- You can suggest movies, help plan timetables, guide users step by step
- When creating timetables, make them clean and structured with proper time slots
- When guiding, give clear step by step instructions
"""

# ── BASIC COMMANDS ────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_histories[update.effective_user.id] = []
    await update.message.reply_text("Hi! I'm ARIA 🤖 Your personal AI assistant. How can I help you today?")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_histories[update.effective_user.id] = []
    await update.message.reply_text("Memory cleared! Fresh start 🧹")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🤖 *About ARIA*

*Name:* ARIA
*Full Form:* Artificial Response & Intelligence Assistant
*Purpose:* Your personal AI assistant
*Platform:* Telegram
*Powered by:* Groq AI (LLaMA 3.3)

I'm here to help you with anything! 💪
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime('%A, %B %d, %Y %I:%M %p')
    await update.message.reply_text(f"🕐 Current date & time:\n*{now}*", parse_mode='Markdown')

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Tell me a short funny joke!"}],
        max_tokens=100
    )
    await update.message.reply_text("😄 " + response.choices[0].message.content)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *ARIA - Your Personal Assistant*

*Commands:*
/start - Start fresh
/clear - Clear memory
/about - About ARIA
/time - Current date & time
/joke - Tell me a joke
/movies - Get movie suggestions
/news - Latest world news
/weather [city] - Get weather info
/timetable - Create your timetable
/guide - Get step by step guidance
/help - Show this menu

Just type any message to chat! 💬
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ── 🎬 MOVIES ─────────────────────────────────────
async def movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Fetching top movies for you...")
    try:
        popular_movies = ["Inception", "Interstellar", "The Dark Knight", "Avengers Endgame", "Oppenheimer"]
        text = "🎬 *Top Movie Recommendations:*\n\n"
        for i, title in enumerate(popular_movies, 1):
            url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
            res = requests.get(url).json()
            if res.get('Response') == 'True':
                text += f"{i}. *{res['Title']}* ⭐ {res['imdbRating']}/10\n"
                text += f"   🎭 {res['Genre']}\n"
                text += f"   📝 {res['Plot'][:80]}...\n\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not fetch movies: {str(e)}")

# ── 📰 NEWS ───────────────────────────────────────
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 Fetching latest world news...")
    try:
        url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=5&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        articles = res.get('articles', [])[:5]
        if not articles:
            await update.message.reply_text("⚠️ No news found at the moment. Try again later.")
            return
        text = "📰 *Latest World News:*\n\n"
        for i, article in enumerate(articles, 1):
            text += f"{i}. *{article['title']}*\n"
            text += f"   🗞 {article['source']['name']}\n\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not fetch news: {str(e)}")

# ── 🌤️ WEATHER ────────────────────────────────────
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🌤️ Please provide a city!\nExample: /weather Chennai")
        return
    city = " ".join(context.args)
    await update.message.reply_text(f"🌤️ Fetching weather for {city}...")
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()
        if res.get('cod') != 200:
            await update.message.reply_text("⚠️ City not found! Please check the city name and try again.")
            return
        text = f"""
🌤️ *Weather in {res['name']}, {res['sys']['country']}*

🌡️ Temperature: *{res['main']['temp']}°C*
🤔 Feels like: {res['main']['feels_like']}°C
💧 Humidity: {res['main']['humidity']}%
🌬️ Wind Speed: {res['wind']['speed']} m/s
☁️ Condition: {res['weather'][0]['description'].title()}
🌅 Min: {res['main']['temp_min']}°C | Max: {res['main']['temp_max']}°C
        """
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# ── 📅 TIMETABLE ──────────────────────────────────
async def timetable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    prompt = """The user wants to create a structured timetable. 
    Ask them these questions one by one:
    1. Are you a student or working professional?
    2. What time do you wake up and sleep?
    3. What are your fixed commitments? (college/work hours)
    4. What activities do you want to include? (study, exercise, hobbies etc.)
    Then create a detailed hour by hour timetable for them."""

    chat_histories[user_id].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": get_system_prompt()}] + chat_histories[user_id],
        max_tokens=1000
    )
    reply = response.choices[0].message.content
    chat_histories[user_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

# ── 🧭 GUIDE ──────────────────────────────────────
async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    prompt = """The user wants step by step guidance on something.
    Ask them what topic they need guidance on, then provide
    clear, numbered, actionable steps to help them achieve it."""

    chat_histories[user_id].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": get_system_prompt()}] + chat_histories[user_id],
        max_tokens=1000
    )
    reply = response.choices[0].message.content
    chat_histories[user_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

# ── 💬 HANDLE MESSAGES ────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    chat_histories[user_id].append({"role": "user", "content": user_message})
    history = chat_histories[user_id][-10:]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": get_system_prompt()}] + history,
            max_tokens=1000
        )
        reply = response.choices[0].message.content
        chat_histories[user_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(reply)

# ── APP SETUP ─────────────────────────────────────
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("time", time_command))
app.add_handler(CommandHandler("joke", joke))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("movies", movies))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("timetable", timetable))
app.add_handler(CommandHandler("guide", guide))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("ARIA is running... 🤖")
app.run_polling()