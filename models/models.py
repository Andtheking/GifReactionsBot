from peewee import *
from PIL import Image, ImageFont, ImageDraw, ImageSequence
import io
from uuid import uuid4
from pathlib import Path

# Connettiamo al database SQLite

db_path = (Path(__file__).parent.parent / 'secret' / 'Database.db').resolve()
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db
        
class Utente(BaseModel):
    id = IntegerField(primary_key=True)
    username = TextField()

class Comando(BaseModel):
    comando = CharField(primary_key=True)

class Gif(BaseModel):
    id = AutoField()
    percorso = CharField()
    fontsize = IntegerField()
    stroke = IntegerField()
    comando = ForeignKeyField(Comando, backref='gifs')
    gif_type_id = IntegerField()
    
    def getName(self) -> str:
        return self.percorso.split("\\")[-1]
    
    async def stampaNomi(self, *nomi, test = False) -> str:
        im = Image.open((Path('misc') / self.percorso.replace('\\','/')).resolve())
        # A list of the frames to be outputted
        frames = []
        
        # 315 * 498 : 32 = im.width * im.height : x
        # 32 * im.width * im.height / 156.870
        # 32 * im.width / 315
        gifWidth = im.width
        gifHeight = im.height
        ratio = gifWidth/gifHeight
        
        fontSize = self.fontsize
        
        
        print (f"{self.comando}{self.gif_type_id} fontSize: {str(fontSize)} w x h {gifWidth} x {gifHeight}")
        font = ImageFont.truetype(str((Path(__file__).parent.parent / 'misc' / 'arial.ttf').resolve()),fontSize)
        
        nomi_nuovi = []
        coord_nuove = []
        diff = len(nomi) - len(self.rettangoli) 
        rettangoli = [NotImplemented]*max(0, diff) + self.rettangoli
        
        for c,n in zip(rettangoli, nomi):
            start_coordinates = (c.A_x,c.A_y)  # Coordinate di inizio
            end_coordinates = (c.B_x,c.B_y)  # Coordinate di fine

            image_width, image_height = im.size

            d = ImageDraw.Draw(im)
            
            text_width = d.textlength(
                n,
                font
            )
            
            text_height = fontSize
            
            # text_width, text_height = d.textsize(
            #     n,
            #     font=font,
            #     stroke_width=self.stroke,
            # )


            rectangle_width = end_coordinates[0] - start_coordinates[0]
            rectangle_height = end_coordinates[1] - start_coordinates[1]

            rectangle_x = start_coordinates[0]
            rectangle_y = start_coordinates[1]

            if text_width < rectangle_width:
                rectangle_x += (rectangle_width - text_width) // 2

            if text_height < rectangle_height:
                rectangle_y += (rectangle_height - text_height) // 2
            
            if text_width > rectangle_width:
                n = self._fit_text_in_rectangle(n,font,fontSize,rectangle_width, rectangle_height, d)
            
            nomi_nuovi.append(n)
            coord_nuove.append((rectangle_x,rectangle_y))

        # Loop over each frame in the animated image
        for frame in ImageSequence.Iterator(im):
            # Draw the text on the frame
            frame = frame.convert('RGBA')
            
            d = ImageDraw.Draw(frame)
            
            for c,n in zip(coord_nuove, nomi_nuovi):
                d.text(
                    (
                        c[0],
                        c[1]
                    ),
                    n,
                    font=font,
                    # 2 : 32 = x : font_size
                    stroke_width=self.stroke,
                    stroke_fill="#000000"
                    
                )
            
            # However, 'frame' is still the animated image with many frames
            # It has simply been seeked to a later frame
            # For our list of frames, we only want the current frame
            
            # Saving the image without 'save_all' will turn it into a single frame image, and we can then re-open it
            # To be efficient, we will save it to a stream, rather than to file
            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            
            # Then append the single frame image to a list of frames
            frames.append(frame)
        
        # Save the frames as a new image
        uuid = str(uuid4())
        nome = f"out{uuid}.gif"
        
        if test:
            nome = "test_"+self.comando.comando+str(self.gif_type_id)+".gif"
        
        frames[0].save(
            'misc/output/'+nome, 
            save_all=True, 
            append_images=frames[1:], 
            loop=0, 
            optimize=False, 
            fps=self.get_avg_fps(im),
            disposal=im.info.get('disposal', 0), 
            palette=im.getpalette(), 
            size=im.size, 
            mode=im.mode
        )
        return uuid

    def get_avg_fps(self, PIL_Image_object):
        """ Returns the average framerate of a PIL Image object """
        PIL_Image_object.seek(0)
        frames = duration = 0
        while True:
            try:
                frames += 1
                duration += PIL_Image_object.info['duration']
                PIL_Image_object.seek(PIL_Image_object.tell() + 1)
            except EOFError:
                return frames / duration * 1000
        return None

    def _fit_text_in_rectangle(self, text, font,fontSize, rectangle_width, rectangle_height, d: ImageDraw):
        w = d.textlength(text,
                        font=font)
        while text and (w > rectangle_width):
            text = text[:-1]  # Rimuovi l'ultimo carattere del testo finché non rientra nel rettangolo
            w = d.textlength(text,
                        font=font)

        return text

class Rect(BaseModel):
    A_x = IntegerField()
    A_y = IntegerField()
    B_x = IntegerField()
    B_y = IntegerField()
    gif = ForeignKeyField(Gif, backref='rettangoli')


class Request(BaseModel):
    id = AutoField()
    gif = TextField()
    status = IntegerField()
    user_id = IntegerField()
    category = TextField()

class RequestMessages(BaseModel):
    message_id = IntegerField()
    user_id = IntegerField()
    request = ForeignKeyField(Request, backref="messages")
    is_admin = BooleanField(default=False)
    
    class Meta:
        primary_key=CompositeKey('user_id', 'message_id')

class Optimize(BaseModel):
    animation = TextField()
    gif = ForeignKeyField(Gif)
    names = TextField()


def insert_data_by_json(json_data):
    for comando_name, gifs in json_data.items():
        # Inserisci il comando
        comando = Comando.create(comando=comando_name)
        
        for gif_data in gifs:
            # Inserisci la GIF
            gif = Gif.create(
                percorso=gif_data['path'],
                fontsize=gif_data['fontsize'],
                stroke=gif_data['stroke'],
                comando=comando
            )
            
            # Inserisci le coordinate
            for coord in gif_data['coords']['py/tuple']:
                Rect.create(
                        gif=gif,
                        A_x=coord['inizio']['py/tuple'][0], 
                        A_y=coord['inizio']['py/tuple'][1],
                        B_x=coord['fine']['py/tuple'][0], 
                        B_y=coord['fine']['py/tuple'][1]
                    )
                
def delete_gif(gif, type_id):
    
    to_delete = Gif.select().join(Comando).where((Gif.gif_type_id == type_id) & (Comando.comando == gif))
    optimize_associated = Optimize.select().where(Optimize.gif == to_delete)
    rects = Rect.select().where(Rect.gif == to_delete)
    
    for a in to_delete:
        a.delete_instance(recursive=True)

# Funzione per generare le query INSERT
def genera_query_insert(model_class):
    # Ottieni tutte le righe del modello
    rows = model_class.select()

    # Crea le query INSERT per ogni riga
    query_insert = []
    for row in rows:
        try:
            valori = ", ".join([f"'{getattr(row, col)}'" if getattr(row, col) is not None else "NULL"
                            for col in row._meta.fields])
            query = f"INSERT INTO {model_class._meta.table_name} ({', '.join(row._meta.fields)}) VALUES ({valori});"
            query_insert.append(query)
        except:
            print('idgaf')

    return query_insert



if __name__ == '__main__':
    # Esempio di utilizzo
    db.connect()
    
    m = [Gif, Rect]
    for x in m:
        queries = genera_query_insert(x)

        # Stampa le query
        for query in queries:
            print(query)

    db.close()
    exit()

    import asyncio
    
    try:
        prompt = input('Che gif vuoi cancellare? Scrivi "tipo numero" --> ').split(" ")
    except:
        print("Esplodo.")
        quit()
        
    try:
        input(f"Sicuro? Stai cancellando {prompt[0]}{int(prompt[1])} eh... Premi invio se sei sicuro. ")
        delete_gif(prompt[0],int(prompt[1]))
    except:
        print("Esplodo 2")
        quit()
   
   
    # # Serviva per incrementare il campo gif_type_id quando ho aggiunto il campo nuovo.
    # for comando in Comando.select():
    #     id = 1
    #     gifs: list[Gif] = Gif.select().where(Gif.comando == comando).order_by(Gif.id)
    #     for gif in gifs: 
    #         gif.gif_type_id = id
    #         gif.save()
    #         id += 1
   
    
    # db.connect()
    # hug_gifs: list[Gif] = Gif.select().join(Comando).where(Comando.comando == 'hug')
    
    # g = hug_gifs[0]
    # asyncio.run(g.stampaNomi("Andrea","Unknown",test=True))
    
    # for c in g.rettangoli:
    #     print(f'{c.A_x};{c.A_y} -> {c.B_x};{c.B_y}')
    
    """region insert
    insert_data_by_json(
                {
    "slap": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\slap\\slap1.gif",
            "name": "slap1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                25,
                                35
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                239,
                                89
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                241,
                                9
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                472,
                                54
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\slap\\slap2.gif",
            "name": "slap2",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                254,
                                145
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                496,
                                181
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                5,
                                34
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                248,
                                72
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\slap\\slap3.gif",
            "name": "slap3",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                261,
                                104
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                493,
                                203
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                33,
                                37
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                240,
                                106
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "hug": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug1.gif",
            "name": "hug1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                169,
                                10
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                441,
                                32
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                42,
                                224
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                292,
                                273
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug2.gif",
            "name": "hug2",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                39,
                                66
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                262,
                                142
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                195,
                                437
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                464,
                                488
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug3.gif",
            "name": "hug3",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                195,
                                62
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                434,
                                141
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                80,
                                361
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                332,
                                456
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug4.gif",
            "name": "hug4",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                148,
                                49
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                347,
                                105
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                147,
                                320
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                348,
                                408
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug5.gif",
            "name": "hug5",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                247,
                                15
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                527,
                                108
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                29,
                                423
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                306,
                                519
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug6.gif",
            "name": "hug6",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                255,
                                62
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                455,
                                140
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                77,
                                17
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                278,
                                95
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug7.gif",
            "name": "hug7",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                197,
                                24
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                406,
                                96
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                25,
                                218
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                250,
                                293
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hug\\hug8.gif",
            "name": "hug8",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                156,
                                5
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                384,
                                66
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                17,
                                165
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                258,
                                234
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "cry": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\cry\\cry1.gif",
            "name": "cry1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                123,
                                37
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                430,
                                37
                            ]
                        }
                    }
                ]
            },
            "fontsize": 42,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\cry\\cry2.gif",
            "name": "cry2",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                14,
                                2
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                402,
                                74
                            ]
                        }
                    }
                ]
            },
            "fontsize": 38,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\cry\\cry3.gif",
            "name": "cry3",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                3,
                                2
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                418,
                                62
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "patpat": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\patpat\\patpat1.gif",
            "name": "patpat1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                16,
                                16
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                286,
                                106
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                196,
                                201
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                437,
                                269
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\patpat\\patpat2.gif",
            "name": "patpat2",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                31,
                                17
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                257,
                                57
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                205,
                                184
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                407,
                                230
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        },
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\patpat\\patpat3.gif",
            "name": "patpat3",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                4,
                                85
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                280,
                                160
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                124,
                                262
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                414,
                                303
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "sip": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\sip\\sip1.gif",
            "name": "sip1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                113,
                                4
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                274,
                                58
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "teehee": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\teehee\\teehee1.gif",
            "name": "teehee1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                157,
                                10
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                372,
                                79
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "punch": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\punch\\punch1.gif",
            "name": "punch1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                161,
                                178
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                425,
                                229
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                3,
                                13
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                257,
                                71
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ],
    "hit": [
        {
            "py/object": "__main__.GIF",
            "path": "gifs\\hit\\hit1.gif",
            "name": "hit1",
            "coords": {
                "py/tuple": [
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                6,
                                39
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                244,
                                78
                            ]
                        }
                    },
                    {
                        "py/object": "__main__.Coordinate",
                        "inizio": {
                            "py/tuple": [
                                169,
                                71
                            ]
                        },
                        "fine": {
                            "py/tuple": [
                                421,
                                115
                            ]
                        }
                    }
                ]
            },
            "fontsize": 33,
            "stroke": 2
        }
    ]
}
)
    endregion"""
    
    db.close()