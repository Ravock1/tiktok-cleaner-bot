import os
import re
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

def limpar_link_tiktok(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=10
        )

        final_url = response.url.split("?")[0]

        return final_url

    except Exception as e:
        return f"Erro: {e}"

async def tratar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.is_bot:
        return

    texto = update.message.text

    urls = re.findall(r'https?://\S+', texto)

    if not urls:
        return

    respostas = []

    for url in urls:
        if "tiktok.com" in url:
            link_limpo = limpar_link_tiktok(url)
            respostas.append(link_limpo)

    if respostas:
        await update.message.reply_text(
            "\n".join(respostas),
            reply_to_message_id=update.message.message_id
        )

app = ApplicationBuilder().token(BOT_TOKEN).build()

handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    tratar_mensagem
)

app.add_handler(handler)

print("Bot rodando...")
app.run_polling()
