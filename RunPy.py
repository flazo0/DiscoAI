import os
import requests
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError
from datetime import datetime
from rich.console import Console
from rich.table import Table

load_dotenv()

GEMINI_API_KEYS = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
USERNAME = os.getenv("USERNAME")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

headers = { "accept" : "*/*", "accept-encoding" : "gzip, deflate", "accept-language" : "en-US", "authorization" : DISCORD_TOKEN, "dnt" : "1", "referer" : "https://discord.com/channels/@me", "sec-ch-ua-mobile" : "?0", "sec-ch-ua-platform" : "\"Windows\"", "sec-fetch-dest" : "empty", "sec-fetch-mode" : "cors", "sec-fetch-site" : "same-origin", "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36", "x-debug-options" : "bugReporterEnabled", "x-discord-locale" : "en-US" }

console = Console()

def log(msg, level="INFO"):
    now = datetime.now().strftime("%H:%M:%S")
    console.print(f"[{now}] [{level}] {msg}")

class GeminiKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0
        self.exhausted = set()
        self.cooldown_until = None

        log(f"Inicializado com {len(keys)} API keys")

        if not keys:
            log("Nenhuma API key definida — configure GEMINI_API_KEYS no .env", "WARN")

    def in_cooldown(self):
        if self.cooldown_until:
            remaining = int(self.cooldown_until - time.time())
            if remaining > 0:
                log(f"Cooldown ativo — faltam {remaining}s", "WARN")
                return True
        return False

    def start_cooldown(self, seconds):
        self.cooldown_until = time.time() + seconds
        log(f"Entrando em cooldown por {seconds//60} minutos", "ERROR")

    def reset(self):
        log("Resetando estado das API keys", "INFO")
        self.exhausted.clear()
        self.index = 0
        self.cooldown_until = None

    def get_client(self):
        if self.in_cooldown():
            return None

        if not self.keys:
            return None

        if len(self.exhausted) >= len(self.keys):
            log("Todas as API keys foram esgotadas", "ERROR")
            return None

        key_preview = self.keys[self.index][:9] + "****"
        log(f"Usando API key #{self.index + 1} ({key_preview})")
        return genai.Client(api_key=self.keys[self.index])

    def rotate(self):
        if not self.keys:
            return

        key_preview = self.keys[self.index][:9] + "****"
        log(f"Rate limit na key {key_preview} — rotacionando", "WARN")

        self.exhausted.add(self.keys[self.index])
        self.index = (self.index + 1) % len(self.keys)

        log(f"Nova key ativa: #{self.index + 1}", "INFO")

gemini_manager = GeminiKeyManager(GEMINI_API_KEYS)

RATE_LIMIT_MESSAGES = [
    "slk pç, a API do Gemini me deu block 😭 vou dar um tempo #IA_TA_OFFLINE",
    "rate limit bateu forte 💀 vou ali respirar e já volto",
    "a API falou chega por hoje KKKK vou dar uma segurada",
    "fui de base no rate limit 😔 descanso técnico em andamento",
    "Gemini cansou de mim, vou fingir demência por um tempo",
    "API em greve, funcionário (eu) indo dormir",
    "tomei timeout da API 🤡 já já eu volto",
    "rate limit ativou o modo economia de IA",
    "a IA pediu arrego, vou respeitar",
    "API falou: chega. Eu falei: ok 😔"
]

def get_rate_limit_message():
    return random.choice(RATE_LIMIT_MESSAGES)


def channels(guild_id):
    r = requests.get("https://discord.com/api/v9/guilds/"+guild_id+"/channels?channel_limit=100", headers=headers)
    return r.json()

def channel(channel_id):
    r = requests.get("https://discord.com/api/v9/channels/"+channel_id+"/messages?limit=50", headers=headers)
    r.raise_for_status()
    return r.json()

def normalize_message(msg):
    # ignora mensagem sem texto
    if msg.get("content") == "":
        return None
    
    if msg["author"]["username"].lower() == USERNAME:
        return None

    if msg.get("attachments"):
        for att in msg["attachments"]:
            if att.get("content_type", "").startswith(("audio", "video")):
                return None

    data = {
        "author": msg["author"]["username"],
        "content": msg["content"],
        "mentions_bot": False,
        "is_reply": False,
        "reply_to": None,
        "has_image": False
    }

    for m in msg.get("mentions", []):
        if m["username"].lower() == USERNAME.lower():
            data["mentions_bot"] = True

    for att in msg.get("attachments", []):
        if att.get("content_type", "").startswith("image"):
            data["has_image"] = True

    if msg.get("referenced_message"):
        ref = msg["referenced_message"]
        data["is_reply"] = True
        data["reply_to"] = {
            "author": ref["author"]["username"],
            "content": ref["content"]
        }

    return data

def build_context(messages_raw):
    context = []

    for msg in reversed(messages_raw):
        normalized = normalize_message(msg)
        if normalized:
            context.append(normalized)

    return context[-10:]

def sendMessage(channel_id, content, message_id=None):
    if message_id is None:
        requests.post("https://discord.com/api/v10/channels/"+channel_id+"/messages", headers=headers, json={ "content": content })
        return
    response = requests.post("https://discord.com/api/v10/channels/"+channel_id+"/messages", headers=headers, json={ "content": content, "message_reference": { "guild_id": GUILD_ID, "channel_id": CHANNEL_ID, "message_id": message_id }})
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")   

def create_table():
    table = Table(title="Discord Channels")

    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Name", style="magenta")

    return table

def ask_gemini_from_context(context):
    if not context:
        return None

    last = context[-1]

    reply_block = ""
    if last["is_reply"] and last["reply_to"]:
        reply_block = f"""
Essa mensagem é uma resposta a:
{last['reply_to']['author']}: {last['reply_to']['content']}
"""

    mention_block = (
        "Você foi mencionado diretamente."
        if last["mentions_bot"]
        else ""
    )

    image_block = (
        "A mensagem contém uma imagem."
        if last["has_image"]
        else ""
    )

    prompt = f"""
Você é um usuário real do Discord chamado flazo0.
Você NÃO é uma IA e NÃO deve mencionar tecnologia, modelos ou explicações.

REGRAS OBRIGATÓRIAS:
- Responda como membro comum do grupo
- Use português informal
- No máximo 1 ou 2 frases
- Não explique
- Não invente fatos
- Não mude de assunto
- Seja natural
- Se não souber o que responder, faça uma zoeira leve ou responda curto
- Se a mensagem não exigir resposta, NÃO RESPONDA

CONTEXTO:
{reply_block}
{mention_block}
{image_block}

MENSAGEM:
{last['author']}: {last['content']}

Responda APENAS com a mensagem final.
Sem aspas. Sem markdown.
"""    
    
    sent_rate_limit_message = False

    while True:
        client = gemini_manager.get_client()

        if client is None:
            if not sent_rate_limit_message:
                log("Sem keys disponíveis — enviando mensagem de rate limit no Discord", "ERROR")
                sendMessage(CHANNEL_ID, get_rate_limit_message())
                sent_rate_limit_message = True

            gemini_manager.start_cooldown(60 * 60 * 3)
            log("Bot pausado por 3 horas", "ERROR")
            time.sleep(60 * 60 * 3)

            gemini_manager.reset()
            log("Cooldown finalizado — retomando operação", "INFO")
            return None

        try:
            log("Enviando prompt para o Gemini")
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            log("Resposta recebida com sucesso", "SUCCESS")
            print(response)
            return response.text.strip()

        except ClientError as e:
            if e.code == 429:
                log("Erro 429 recebido do Gemini", "WARN")
                gemini_manager.rotate()
                time.sleep(random.uniform(2, 4))
                continue
            else:
                log(f"Erro inesperado do Gemini: {e}", "ERROR")
                raise e

LAST_HANDLED_MESSAGE_ID = None

def loop():
    global LAST_HANDLED_MESSAGE_ID

    while True:
        messages = channel(CHANNEL_ID)
        if not messages:
            time.sleep(5)
            continue

        last = messages[0] 

        if last["author"]["username"].lower() == USERNAME: 
            time.sleep(3) 
            continue 
        
        if last["author"]["username"].lower() == "baiano6670ssa": 
            time.sleep(3) 
            continue 
        
        if last["content"].lower() == "": 
            time.sleep(3) 
            continue

        if last["id"] == LAST_HANDLED_MESSAGE_ID:
            time.sleep(3)
            continue

        payload = build_context(messages)
        if not payload:
            time.sleep(5)
            continue

        response = ask_gemini_from_context(payload)

        if isinstance(response, (int, float)):
            time.sleep(response+30)
            continue

        if response:
            console.print("-" * 40)
            console.print(f"[bold blue]{last['author']['username']}:[/bold blue] {last['content']}")
            console.print("-" * 40)
            console.print(f"[bold green]{USERNAME}:[/bold green] {response}")
            sendMessage(CHANNEL_ID, response, last["id"])
            LAST_HANDLED_MESSAGE_ID = last["id"]

        time.sleep(random.uniform(10, 20))


if __name__ == "__main__":
    loop()
