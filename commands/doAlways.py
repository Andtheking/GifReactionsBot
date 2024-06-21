from telegram import Update
from telegram.ext import ContextTypes

from utils.log import log
from utils.db import queryGetFirst, queryNoReturn

from models.models import Utente
from utils.jsonUtils import load_configs
from telegram.constants import ChatType

# Questa funzione sarà eseguita prima di tutte le altre e per ogni messaggio che non è un comando
async def doAlways(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if load_configs()['test']:
        if message.chat.type != ChatType.PRIVATE and not message.chat_id in load_configs()['enabled_groups']:
            await message.chat.leave()
            return
    
    user = update.effective_user
    
    if user is None or message is None:
        return # Mi evito controlli futuri
        
    query_saved_user: Utente = Utente.select().where(Utente.id == user.id).first()
    if query_saved_user is None:
        query_saved_user = Utente.create(id = user.id, username = user.name)
        log(f"Inserito nel DB il seguente utente: {user.id},{user.name}", context.bot)
    
    if query_saved_user.username != user.name:
        query_saved_user.username = user.name
        query_saved_user.save()
    
    return user,message