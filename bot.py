import os
import html
import logging
import asyncio
import feedparser

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable is missing")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# Public RSS feeds.
# BBC Sport publishes football and wider sports RSS feeds.
FEEDS = {
    "football": {
        "name": "⚽ Football News",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    },
    "sports": {
        "name": "🏆 Sports News",
        "url": "https://feeds.bbci.co.uk/sport/rss.xml",
    },
}

# ---------------------------------------------------------
# Main menu
# ---------------------------------------------------------

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⚽ Football News",
                callback_data="football"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏆 Sports News",
                callback_data="sports"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="refresh"
            ),
        ],
    ])


# ---------------------------------------------------------
# Fetch RSS news
# ---------------------------------------------------------

async def fetch_news(category: str, limit: int = 5):
    feed_info = FEEDS.get(category)

    if not feed_info:
        return []

    def read_feed():
        return feedparser.parse(feed_info["url"])

    feed = await asyncio.to_thread(read_feed)

    articles = []

    for entry in feed.entries[:limit]:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")

        if not link:
            continue

        articles.append({
            "title": title,
            "link": link,
        })

    return articles


# ---------------------------------------------------------
# Format news
# ---------------------------------------------------------

def format_news(category: str, articles):
    feed_info = FEEDS[category]

    if not articles:
        return (
            f"<b>{feed_info['name']}</b>\n\n"
            "Sorry, no news is available right now.\n"
            "Please try again later."
        )

    lines = [
        f"<b>{feed_info['name']}</b>",
        "",
        "Latest updates:",
        "",
    ]

    for index, article in enumerate(articles, start=1):
        title = html.escape(article["title"])
        link = html.escape(article["link"], quote=True)

        lines.append(
            f"{index}. <a href=\"{link}\">{title}</a>"
        )

    lines.extend([
        "",
        "📰 News source: BBC Sport",
        "",
        "Use the buttons below to browse more updates.",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------
# /start
# ---------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "⚽ <b>Welcome to Football & Sports News!</b>\n\n"
        "Get the latest football and sports updates directly "
        "inside Telegram.\n\n"
        "Choose a category below:"
    )

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(),
    )


# ---------------------------------------------------------
# /football
# ---------------------------------------------------------

async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ Getting the latest football news..."
    )

    articles = await fetch_news("football")

    await update.message.reply_text(
        format_news("football", articles),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=main_keyboard(),
    )


# ---------------------------------------------------------
# /sports
# ---------------------------------------------------------

async def sports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ Getting the latest sports news..."
    )

    articles = await fetch_news("sports")

    await update.message.reply_text(
        format_news("sports", articles),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=main_keyboard(),
    )


# ---------------------------------------------------------
# Buttons
# ---------------------------------------------------------

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    if query.data == "football":
        articles = await fetch_news("football")

        await query.edit_message_text(
            format_news("football", articles),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=main_keyboard(),
        )

    elif query.data == "sports":
        articles = await fetch_news("sports")

        await query.edit_message_text(
            format_news("sports", articles),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=main_keyboard(),
        )

    elif query.data == "refresh":
        articles = await fetch_news("football")

        await query.edit_message_text(
            format_news("football", articles),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=main_keyboard(),
        )


# ---------------------------------------------------------
# Error handler
# ---------------------------------------------------------

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.exception(
        "Telegram update caused an error",
        exc_info=context.error,
    )


# ---------------------------------------------------------
# Bot startup
# ---------------------------------------------------------

async def post_init(application):
    commands = [
        BotCommand("start", "Open the sports news menu"),
        BotCommand("football", "Latest football news"),
        BotCommand("sports", "Latest sports news"),
    ]

    await application.bot.set_my_commands(commands)


def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("football", football)
    )

    application.add_handler(
        CommandHandler("sports", sports)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_error_handler(error_handler)

    logger.info("Sports news bot is starting...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
