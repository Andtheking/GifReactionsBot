# from ..requirements import *

from pathlib import Path
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent))

from requirements import *
import asyncio
import time
import shutil
import gif_coordinates
import os

path = (Path(__file__).parent.parent / 'misc').resolve()

if __name__ == "__main__":
    a = input("--> ")
    
    if a.strip() == "test":
        g = Gif.select().join(Comando)
        start_time = time.time()
        for i in g:
            asyncio.run(i.stampaNomi("Andtheking","HypotheticalGirl", test=True))
        print("Gif 2 --- %s seconds ---" % (time.time() - start_time))
        
    elif "test" in a:
        g = Gif.select().join(Comando).where(Comando.comando == a.replace('test','').strip())
        for i in g:
            asyncio.run(i.stampaNomi("Andtheking","HypotheticalGirl", test=True))
            
    elif a == "new gif":
        possibilita = [p.comando for p in Comando.select()]
        
        t = input("Tipo della gif? ")
        while not t in possibilita:
            print("Errato. I tipi accettati sono:\n\t", ', '.join(possibilita))
            t = input("Tipo della gif? ")

        comando = Comando.select().where(Comando.comando == t).first()
        last_gif_id = Gif.select().join(Comando).where(Comando.comando == comando).order_by(Gif.gif_type_id.desc()).first().gif_type_id
        
        p = input("Percorso della gif? ")
        while not os.path.isfile(p) or not (p[-1:-5:-1] == "fig." or p[-1:-5:-1] == "4pm."):
            print("Non è una gif. Riprova")
            p = input("Percorso della gif? ")

        if p[-1:-5:-1] == "4pm.":
            import mp4togif
            mp4togif.main(p)
        else:
            shutil.move(p,path.joinpath("working_dir/converted.gif").resolve())
        
        p = str(path.joinpath("working_dir/converted.gif").resolve())
        
        super_big_g = Gif(
            percorso=f"gifs/{t}/{t}{last_gif_id + 1}.gif",
            fontsize=33,
            stroke=2,
            comando=comando,
            gif_type_id=last_gif_id+1
        )
        
        
        print("Ok ora prendi le coordinate")
        c = [Rect(gif=super_big_g, A_x = k[0], A_y = k[1], B_x = k[2], B_y = k[3]) for k in gif_coordinates.main(p)]
        
        path = str(path.joinpath(f"gifs/{t}/{t}{last_gif_id + 1}.gif").resolve())
        os.rename(p,path)
        
        super_big_g.save()
        for i in c:
            i.save()

    elif a == "list":
        for a in Comando.select():
            print(a)