from requirements import *
from peewee import fn

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


async def coupleGif(update:Update, context: ContextTypes.DEFAULT_TYPE, gif_type:str):
    if not await check_for_couple_gif(update.effective_message):
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

    