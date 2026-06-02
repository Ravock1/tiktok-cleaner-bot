import os
import re
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

# Token do Telegram
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
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url.split("?")[0]
        return final_url
    except Exception as e:
        return f"Erro: {e}"

def limpar_link_facebook(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url
        parsed_url = urlparse(final_url)

        # Se o Facebook forçar tela de login, retorna o caminho limpo
        if "login" in parsed_url.path:
             return final_url.split("?")[0]

        # Lista branca de parâmetros essenciais do Facebook (incluindo view_single para stories)
        parametros_essenciais = ['v', 'id', 'story_fbid', 'set', 'post_id', 'fbid', 'view_single']
        
        query_params = parse_qs(parsed_url.query)
        parametros_limpos = {k: v[0] for k, v in query_params.items() if k in parametros_essenciais}
        
        nova_query = urlencode(parametros_limpos)
        
        # Reconstrói a URL sem rastreadores e forçando a remoção do fragmento '#'
        url_limpa = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            nova_query,
            "" 
        ))

        return url_limpa.rstrip('/')
    except Exception as e:
        return f"Erro: {e}"

def tratar_link_redes_sociais(url):
    """
    Trata links do X, Twitter, Bluesky (com embeds) e limpa rastreadores do Instagram (exceto stories).
    """
    url_limpa = url.replace("www.", "")
    
    # 1. X / Twitter (FixupX / FxTwitter)
    if "twitter.com" in url_limpa and "/status/" in url_limpa:
        return url_limpa.replace("twitter.com", "fxtwitter.com").split("?")[0]
        
    elif "x.com" in url_limpa and "/status/" in url_limpa:
        return url_limpa.replace("x.com", "fixupx.com").split("?")[0]
        
    # 2. Bluesky (FxBsky)
    elif "bsky.app" in url_limpa and "/post/" in url_limpa:
        return url_limpa.replace("bsky.app", "fxbsky.app").split("?")[0]
        
    # 3. Instagram (Limpando rastreadores para reels, posts e tv; stories são ignorados)
    elif "instagram.com" in url_limpa:
        if "/p/" in url_limpa or "/reel" in url_limpa or "/tv/" in url_limpa:
            # Só retorna algo se existir a interrogação para ser cortada
            if "?" in url_limpa:
                return url_limpa.split("?")[0]
            
    return None

async def tratar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # Ignora mensagens de outros bots
    if update.message.from_user.is_bot:
        return

    texto = update.message.text
    if not texto:
        return

    # Extrai todas as URLs do texto
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
                
        # Fluxo 2: Facebook
        elif "facebook.com" in url or "fb.watch" in url:
            link_limpo = limpar_link_facebook(url)
            if link_limpo and not link_limpo.startswith("Erro:") and link_limpo != url:
                respostas.append(link_limpo)
                
        # Fluxo 3: X, Twitter, Bluesky e Instagram
        else:
            link_modificado = tratar_link_redes_sociais(url)
            if link_modificado and link_modificado != url:
                respostas.append(link_modificado)

    # Se houve modificações úteis, o bot responde no grupo
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
        
        handler = MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_mensagem)
        app.add_handler(handler)
        
        print("Bot rodando e aguardando links (TikTok, Facebook, X, Bluesky, Instagram)...")
        app.run_polling()
