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
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
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

def tratar_link_redes_sociais(url):
    """
    Trata links do X, Twitter e Bluesky.
    Só altera a URL se for uma postagem, ignorando links de perfil.
    """
    # Removemos um eventual www. para não duplicar e facilitar a substituição
    url_limpa = url.replace("www.", "")
    
    # Lógica para X / Twitter (só atua se tiver /status/ indicando que é um post)
    if "twitter.com" in url_limpa and "/status/" in url_limpa:
        return url_limpa.replace("twitter.com", "fxtwitter.com")
        
    elif "x.com" in url_limpa and "/status/" in url_limpa:
        return url_limpa.replace("x.com", "fixupx.com")
        
    # Lógica para Bluesky (só atua se tiver /post/ indicando que é um post)
    elif "bsky.app" in url_limpa and "/post/" in url_limpa:
        return url_limpa.replace("bsky.app", "fxbsky.app")
        
    # Retorna None se for só perfil ou não for de nenhuma dessas redes
    return None

async def tratar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message.from_user.is_bot:
        return

    texto = update.message.text
    if not texto:
        return

    urls = re.findall(r'https?://\S+', texto)

    if not urls:
        return

    respostas = []

    for url in urls:
        # Fluxo 1: TikTok
        if "tiktok.com" in url:
            link_limpo = limpar_link_tiktok(url)
            
            if link_limpo and not link_limpo.startswith("Erro:") and link_limpo != url:
                respostas.append(link_limpo)
        
        # Fluxo 2: X, Twitter e Bluesky
        else:
            link_modificado = tratar_link_redes_sociais(url)
            
            # Se a função retornou uma URL válida (não é apenas perfil)
            if link_modificado:
                respostas.append(link_modificado)

    if respostas:
        await update.message.reply_text(
            "\n".join(respostas),
            reply_to_message_id=update.message.message_id
        )

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Erro: A variável de ambiente BOT_TOKEN não foi definida.")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            tratar_mensagem
        )

        app.add_handler(handler)

        print("Bot rodando e aguardando links (TikTok, X, Twitter, Bluesky)...")
        app.run_polling()
