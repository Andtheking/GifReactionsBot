import telegram

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

from models.models import db, Request, RequestMessages
from utils.answerMessage import rispondi
from utils.jsonUtils import toJSON, load_configs

class RequestStatuses:
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2
    ADDED = 3
    


async def request(update: Update, context: ContextTypes.DEFAULT_TYPE): # dopo che fa /request
    messaggio = update.effective_message
    chat = update.effective_chat
    
    if chat.id < 0:
        await rispondi(
            messaggio=messaggio,
            text='Usa questo comando in chat privata con il bot!'
        )
        return
    
    await rispondi(
        messaggio=messaggio,
        text='Ok, ora mandami il nome della categoria che riguarda la gif (hug, patpat, sip... così via). Annulla con /cancel'
    )
    return 1

#categoria_e_richiestaGiff
async def cat_e_ricGif(update: Update, context: ContextTypes.DEFAULT_TYPE): # Dopo che ha mandato la categoria
    messaggio = update.effective_message
    chat = update.effective_chat
    
    context.user_data['requesting'] = { 'category': messaggio.text }
    await rispondi(
        messaggio=messaggio,
        text='Bene, nel caso tu abbia sbagliato a scrivere puoi sempre scrivere /cancel e ricominciare.\n\nOra mandami la gif.'
    )
    return 2


    
async def save_Richiesta(update: Update, context: ContextTypes.DEFAULT_TYPE): # Dopo che ha mandato la gif
    messaggio = update.effective_message
    chat = update.effective_chat
    
    
    with db.atomic():
        req = Request.create(
            user_id = messaggio.from_user.id,
            category = context.user_data['requesting']['category'],
            gif = toJSON(messaggio.animation),
            status = RequestStatuses.PENDING
        )
        
        user_message = RequestMessages.create(
            user_id=messaggio.from_user.id, 
            message_id=messaggio.id,
            request = req,
            is_admin = False
        )
        
        await messaggio.reply_text(
            "Ok, richiesta effettuata. Puoi annullarla col bottone qui sotto",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('❌ Annulla richiesta', callback_data=f'annulla_richiesta:{req.id}')
                    ]
                ]
            )
        )
        
        
        KEYBOARD_ADMIN_REQUEST = [
            [ InlineKeyboardButton('👍 Accetta',callback_data=f'request:accept:{req.id}'), InlineKeyboardButton('❌ Rifiuta',callback_data=f'request:decline:{req.id}')],
            [ InlineKeyboardButton('✅ Aggiunto',callback_data=f'request:added:{req.id}') ]
        ]
        
        for admin in load_configs()["BOT_ADMINS"]:
            try:
                admin_messages = (
                    await context.bot.send_message(
                        chat_id = admin,
                        text = \
                            f"#richiesta #req{req.id}\n" +
                            "\n" +
                            f"L'utente {messaggio.from_user.name} con #id{messaggio.from_user.id} richiede l'aggiunta della gif qui di seguito " +
                            f"per la categoria: {req.category}",
                        reply_markup = InlineKeyboardMarkup(KEYBOARD_ADMIN_REQUEST)
                    ),
                    await context.bot.send_animation(
                        chat_id = admin,
                        animation = messaggio.animation
                    )
                )
                
                admin_message = RequestMessages.create(user_id=int(admin), message_id=admin_messages[0].id, is_admin=True, request = req)
                admin_gif_message = RequestMessages.create(user_id=int(admin),message_id=admin_messages[1].id, is_admin=True, request = req)
                
            except:
                pass
        
    
    return ConversationHandler.END

async def richiesta_accettata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    request_id = int(data[data.rfind(':')+1:])
    req: Request = Request.select().where(Request.id == request_id).first()
    if req == None:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"#ERROR\n\nLa richiesta con id #req{request_id} non è stata trovata.",
        )
        return

    req.status = RequestStatuses.ACCEPTED
    
    mex = RequestMessages.select().join(Request).where(RequestMessages.request == req and RequestMessages.user_id == req.user_id).first()
    await context.bot.send_message(
        text="La tua richiesta è stata accettata! Quando sarà disponibile nel bot ti invierò un messaggio",
        reply_to_message_id=mex.message_id,
        chat_id=mex.user_id
    )
    
    for admin in load_configs()["BOT_ADMINS"]:
        await context.bot.send_message (
            chat_id=admin,
            text=f"La richiesta #req{req.id} è stata accettata dall'admin {query.from_user.name}."
        )
    
    await query.answer()

async def richiesta_rifiutata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    request_id = int(data[data.rfind(':')+1:])
    req: Request = Request.select().where(Request.id == request_id).first()
    if req == None:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"#ERROR\n\nLa richiesta con id #req{request_id} non è stata trovata.",
        )
        return
    
    req.status = RequestStatuses.ACCEPTED
    
    mex: RequestMessages = RequestMessages.select().join(Request).where(RequestMessages.request == req and RequestMessages.user_id == req.user_id).first()
    
    await context.bot.send_message(
        chat_id=mex.user_id,
        text="Mi dispiace, la tua richiesta è stata rifiutata...",
        reply_to_message_id=mex.message_id,
    )

    for admin in load_configs()["BOT_ADMINS"]:
        await context.bot.send_message (
            chat_id=admin,
            text=f"La richiesta #req{req.id} è stata rifiutata dall'admin {query.from_user.name}."
        )
    await query.answer()

async def richiesta_aggiunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    request_id = int(data[data.rfind(':')+1:])
    req: Request = Request.select().where(Request.id == request_id).first()
    mex: RequestMessages = RequestMessages.select().join(Request).where(RequestMessages.request == req and RequestMessages.user_id == req.user_id).first()
     
    if req == None:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"#ERROR\n\nLa richiesta con id #req{request_id} non è stata trovata.",
        )
        return
    
    # TODO Fare in modo che quando un admin segna come disponibile una gif, gli venga richiesto il comando in cui essa è disponibile.
    req.status = RequestStatuses.ADDED
    await context.bot.send_message(
        chat_id=mex.user_id,
        text="La tua richiesta è ora disponibile nel bot!",
        reply_to_message_id=mex.message_id # TODO Inserire in questo messaggio il comando in cui è disponibile.
    )
    
    for admin in load_configs()["BOT_ADMINS"]:
        await context.bot.send_message (
            chat_id=admin,
            text=f"La richiesta #req{req.id} è stata segnalta come aggiunta dall'admin {query.from_user.name}."
        )
    
    await query.answer()

async def annulla_richiesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    request_id = int(data[data.rfind(':')+1:])
    req: Request = Request.select().where(Request.id == request_id).first()
    
    messages: RequestMessages = req.messages
    
    for mex in messages: 
        if mex.is_admin:
            await context.bot.delete_message(mex.user_id, mex.message_id)
            mex.delete()
    
    req.delete()
    
    await query.message.reply_text(
        text="Richiesta annullata correttamente!"
    )
    
    await query.answer()
    
    
