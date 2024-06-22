from requirements import *

TOKEN = load_configs()['token']  # TOKEN DEL BOT
CANALE_LOG = load_configs()['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # /start
    await doAlways(update,context)
    
    await update.message.reply_text(f'Benvenuto! Usa /help@{context.bot.username} per scoprire come funziona il bot!')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): # /help
    await doAlways(update,context)
    
    await update.message.reply_text("""
Provalo in un gruppo! 
Interazioni a 2 (da usare in risposta a qualcuno):

- /hit
- /hug
- /patpat
- /punch
- /slap

Reazioni (gif con una sola persona):

- /cry
- /sip
- /teehee
""")

# Segnala quando il bot crasha, con motivo del crash
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log(f'Update "{update}" caused error "{context.error}"',context.bot, "error")

def cancel(action: str): 
    async def thing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user,message = await doAlways(update,context)
        await message.reply_text(f"Ok, azione \"{action}\" annullata")
        return ConversationHandler.END
    return thing




def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    handlers = {
        "start": MessageHandler(filters.Regex(re.compile(r"^[!.\/]start",re.IGNORECASE)),start),
        "help": MessageHandler(filters.Regex(re.compile(r"^[!.\/]help",re.IGNORECASE)),help),
    }
    
    application.add_handler(
        ConversationHandler(
            entry_points = [CommandHandler("request",richieste.request)],
            states={
                1: [MessageHandler(filters=~filters.COMMAND, callback=richieste.cat_e_ricGif)],
                2: [MessageHandler(filters=filters.ANIMATION, callback=richieste.save_Richiesta)]
            },
            fallbacks=[CommandHandler('cancel',cancel('richiesta'))]
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=richieste.richiesta_accettata, 
            pattern='request:accept'
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=richieste.richiesta_rifiutata, 
            pattern='request:decline'
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            callback=richieste.richiesta_aggiunta, 
            pattern='request:added'
        )
    )
    # annulla_richiesta:
    
    application.add_handler(
        CallbackQueryHandler(
            callback=richieste.annulla_richiesta,
            pattern="annulla_richiesta:.+"
        )
    )

    couple_command = [
        "slap","hug","patpat","punch", "hit"
    ]
    single_command = [
        "cry","teehee","sip"
    ]
    
    for command in couple_command:
        handlers[command] = MessageHandler(
            filters=filters.Regex(re.compile(r"^[!.\/]g"+command,re.IGNORECASE)), callback=lambda update,context,cmd=command: gifs.coupleGif(update,context,cmd)
        )
    for command in single_command:
        handlers[command] = MessageHandler(
            filters=filters.Regex(re.compile(r"^[!.\/]g"+command,re.IGNORECASE)), callback=lambda update,context,cmd=command: gifs.singleGif(update,context,cmd)
        )
            
    for v in handlers.values():
        application.add_handler(v,0)
    
    # Se non cadi in nessun handler, vieni qui
    application.add_handler(MessageHandler(filters=filters.ALL, callback=doAlways),1)
    
    application.add_error_handler(error) # Definisce la funzione che gestisce gli errori
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    

    if not load_configs()['test']:
        jq.run_repeating(
            callback=send_logs_channel,
            interval=60
        )

    jq.run_once(
        callback = initialize,
        when = 1
    )

    
    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 
    
# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non da un altro programma
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()
