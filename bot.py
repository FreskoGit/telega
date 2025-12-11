import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("8451214426:AAFl9kIhSiLNRZoNkdJk1Okz5myaSFPGeQ8")
# Укажите ваш HTTPS URL здесь (после деплоя на Vercel)
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://telega-three.vercel.app/")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем кнопку для открытия Mini App
    keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Открыть XBanking",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("❓ Помощь", callback_data="help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎉 *Добро пожаловать в XBanking!*

Привет, {user.first_name}! XBanking — это ваш портал для управления NFT и крипто-активами в Telegram.

✨ *Возможности:*
• Просмотр NFT маркетплейса
• Управление вашими NFT
• Реферальная система
• Баланс в TON

Нажмите кнопку ниже, чтобы открыть мини-приложение и начать работу!
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📚 *Помощь по XBanking*

*Основные команды:*
/start - Начать работу с ботом
/help - Показать это сообщение
/stats - Показать статистику

*В мини-приложении вы можете:*
• Просматривать NFT на маркетплейсе
• Управлять своими NFT
• Использовать реферальную систему
• Отслеживать баланс TON

*Поддержка:*
При возникновении проблем свяжитесь с нами через:
@support_username
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    stats_text = """
📊 *Статистика XBanking*

*Пользователи:* 1,234+
*NFT на маркетплейсе:* 5,678+
*Объем торгов:* 12,345 TON
*Активные пользователи:* 789

*Обновлено:* только что
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        await stats_command(update, context)
    elif query.data == "help":
        await help_command(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка. Пожалуйста, попробуйте позже."
        )

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчики callback кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("🤖 Бот запущен...")
    print(f"🌐 Web App URL: {WEB_APP_URL}")
    print("✅ Бот готов к работе! Откройте Telegram и найдите своего бота.")
    
    application.run_polling(allowed_updates=Update.ALL_UPDATES)

if __name__ == "__main__":
    main()