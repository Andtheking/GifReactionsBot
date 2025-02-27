from requirements import *
from peewee import fn
from asyncio import Future

async def check_for_couple_gif(message: Message):
    if message.reply_to_message is None:
        await message.reply_text("Devi usare questo comando in risposta a qualcuno...")
        return False
    if message.reply_to_message.from_user == message.from_user:
        await message.reply_text("Non usare il comando con te stesso...")
        return False
    if message.reply_to_message.from_user.username == config.BOT_USERNAME:
        await message.reply_text("Non usare il comando su di me!")
        return False
    
    return True

request_counter = {}

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE, mex:str):
    chi_propone = update.effective_user.id
    chi_riceve = update.effective_message.reply_to_message.from_user.id

    # Inizializza il contatore per la chat se non esiste
    if chi_riceve not in request_counter:
        request_counter[chi_riceve] = 0
    request_counter[chi_riceve] += 1

    m = await update.effective_message.reply_to_message.reply_text(mex)
    # Crea un identificatore univoco per ogni richiesta (contatore incluso)
    richiesta_id = m.id

    # Crea un Future per aspettare la risposta
    future = Future()

    # Salva i dati della richiesta (chi ha proposto, chi riceve) in chat_data
    context.chat_data[richiesta_id] = {
        "chi_propone": chi_propone,
        "chi_riceve": chi_riceve,
        "future": future
    }

    # Crea la tastiera con i due bottoni (Accetta/Rifiuta)
    keyboard = [
        [InlineKeyboardButton("Accetta ✅", callback_data=f"accept_{update.effective_chat.id}_{richiesta_id}"),
         InlineKeyboardButton("Rifiuta ❌", callback_data=f"reject_{update.effective_chat.id}_{richiesta_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await m.edit_text(text=mex, reply_markup=reply_markup)
    # Invia il messaggio all'utente ricevente con i bottoni
    

    return await future  # Restituisci il Future, che verrà risolto quando l'utente risponde

# Funzione che gestisce la risposta (Accetta/Rifiuta)
async def ask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    
    # Estrai l'ID della richiesta (accetta o rifiuta) dal callback_data
    callback_data = query.data.split("_")
    risposta = callback_data[0]  # "accept" o "reject"
    chat_id = int(callback_data[1])
    risposta_id = int(callback_data[2])

    if not update.effective_chat.id == chat_id:
        await query.answer()
        return
    
    # Ottieni i dati da context.chat_data utilizzando l'ID della richiesta univoco
    richiesta = context.chat_data.get(query.message.message_id, None)

    if richiesta:
        # Recupera l'utente che ha proposto l'abbraccio
        chi_propone = richiesta['chi_propone']
        chi_riceve = richiesta['chi_riceve']
        if chi_riceve != query.from_user.id:
            await query.answer("Non è per te!")
            return
        
        future = richiesta['future']

        # Controlla la risposta (Accetta o Rifiuta)
        if risposta == "accept":
            risposta_bool = True  # Accetta l'abbraccio
            await query.edit_message_text(text="Accettato!")
        elif risposta == "reject":
            risposta_bool = False  # Rifiuta l'abbraccio
            await query.edit_message_text(text="Rifiutato.")

        # Risolvi il Future con la risposta
        future.set_result(risposta_bool)

        # Rimuovi la richiesta dai dati di chat_data
        del context.chat_data[risposta_id]
    else:
        await query.answer()
        pass



    

async def singleGif(update:Update, context: ContextTypes.DEFAULT_TYPE, gif_type:str):
    if update.effective_message.from_user.id == 872910322:
        await update.effective_message.reply_text("suca")

    m = await update.effective_message.reply_text("Processing...")
    testo = update.effective_message.text

    await make_gif(
        gif_type,
        update.effective_message,
        nomi = (
            update.effective_message.from_user.name.replace("@",""),
        ),
        text=testo[testo.index(' '):] if ' ' in testo else ""
        )
    await m.delete()


ASK = ['hug', 'patpat']

async def coupleGif(update:Update, context: ContextTypes.DEFAULT_TYPE, gif_type:str):
    if not await check_for_couple_gif(update.effective_message):
        return
    
    if (gif_type in ASK):
        if (gif_type == 'hug'):
            mex = '{utente} vorrebbe abbracciarti...'
        elif (gif_type == 'patpat'):
            mex = '{utente} vorrebbe farti patpat...'
        
        if not await ask(update, context, mex.format(utente=update.effective_sender.name)):
            return
    
    m = await update.effective_message.reply_text("Processing...")
    testo = update.effective_message.text
    await make_gif(
        gif_type,
        update.effective_message,
        nomi = ( 
            update.effective_message.from_user.name.replace("@",""), 
            update.effective_message.reply_to_message.from_user.name.replace("@","")
        ),
        text=testo[testo.index(' '):] if ' ' in testo else ""
    )
    await m.delete()   
    
    
async def make_gif(type_gif, message: Message, nomi: tuple[str], text = ""):
    x = re.search('type:(.+)',text)
    if x:
        tipo = x.group(1)
    
    text = re.sub('type:(.+)','',text).strip()
    if x:
        chosen_gif: Gif = Gif.select().join(Comando).where((Comando.comando == type_gif) & (Gif.gif_type_id == int(tipo))).first()
   
    if not x or not chosen_gif:
        chosen_gif: Gif = Gif.select().join(Comando).where(Comando.comando == type_gif).order_by(fn.Random()).limit(1).first()
        
    

    modified_names = []
    for nome in nomi:
        a = nome
        if " " in nome:
            a = nome.split(" ")[0]
        modified_names.append(a)
    
    already = alreadySent(chosen_gif, *nomi)
    
    if len(text.strip()) > 0:
        text = f"{message.from_user.name} dice: {text.strip()}"
        text = text[0:1023]
        
    if not already:
        code = await chosen_gif.stampaNomi(*modified_names)
        
        if len(nomi) < 2:
            try:
                a = await message.reply_animation(f"misc/output/out{code}.gif",caption=text)    
            except:
                a = await message.chat.send_animation(f"misc/output/out{code}.gif",caption=text)
        else:
            try:
                a = await message.reply_to_message.reply_animation(f"misc/output/out{code}.gif",caption=text)
            except:
                a = await message.chat.send_animation(f"misc/output/out{code}.gif",caption=text)

        Optimize.create(
            animation = toJSON(a.animation),
            names = toJSON(list(modified_names)),
            gif = chosen_gif
        )
        
    else:
        if len(nomi) < 2:
            try:
                await message.reply_animation(already,caption=text)
            except:
                await message.chat.send_animation(already,caption=text)
        else:
            try:
                await message.reply_to_message.reply_animation(already,caption=text)
            except:
                await message.chat.send_animation(already,caption=text)

    
    

def alreadySent(gif, *nomi) -> str:
    asasd = toJSON(list(nomi))
    test: Optimize = Optimize.select().where((Optimize.gif == gif) & (Optimize.names == toJSON(list(nomi)))).first()

    if test:
        return fromJSON(test.animation)
    return None

    