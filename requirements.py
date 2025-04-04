#region Telegram library


from telegram.ext import (
    Application, # Per il bot
    CommandHandler, # Per i comandi
    MessageHandler, # Per i messaggi
    ConversationHandler, # Per più handler concatenati (Può salvare il suo stato con PicklePersistance)
    ContextTypes, # Per avere il tipo di context (ContextTypes.DEFAULT)
    CallbackQueryHandler, # Per gestire il click di un bottone o simile
    filters, # Per filtrare gli Handler 
    PicklePersistence # Per un ConversationHandler, vedi https://gist.github.com/aahnik/6c9dd519c61e718e4da5f0645aa11ada#file-tg_conv_bot-py-L9
)
from telegram import (
    Update, # È il tipo che usiamo nei parametri dei metodi
    
    User, # Tipo che rappresenta un Utente
    Message, # Tipo che rappresenta un Messaggio
    InlineKeyboardButton, # Per le tastiere
    InlineKeyboardMarkup, # Per le tastiere
    
)

from telegram.constants import (
    ParseMode, # Per assegnare il parametro "parse_mode=" nei messaggi che il bot invia
)
#endregion

# Librerie esterne
import re
from requests import get


# Moduli interni 

# Modelli DB
from models.models import Request, RequestMessages, Gif, Comando, Utente, Rect, Optimize

# Utils
from utils.jsonUtils import load_configs, toJSON, fromJSON
from utils.log import log

# Constants
class Config:
    def __init__(self):
        self.TOKEN = load_configs()['token']  # TOKEN DEL BOT
        self.CANALE_LOG = load_configs()['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.
        self.BOT_INFO = get(f'https://api.telegram.org/bot{self.TOKEN}/getMe')
        self.BOT_USERNAME = fromJSON(self.BOT_INFO.text)['result']['username']
        
config = Config()

# Commands
from commands.doAlways import doAlways
import commands.richieste as richieste
import commands.gifs as gifs

# Jobs
from jobs.send_logs import send_logs_channel
from jobs.initialize import initialize
