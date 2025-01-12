# GLI SERVE ffmpeg, gifski, waifu2x

import subprocess
import os
from pathlib import Path
from PIL import Image
import shutil

import cv2
from cv2 import VideoCapture

def get_fps(path):
    cap = None
    try:
        cap = VideoCapture(path)
        return int(cap.get(cv2.CAP_PROP_FPS))
    except Exception as e:
        print(e)

output_path = str((Path(__file__).parent.parent / 'misc' / 'working_dir').resolve()).replace(" ","?")

FFMPEG_COMMAND = "ffmpeg -i {input} {resize}frames/frame%04d.png"
FFMPEG_RESIZE = "-vf scale=420:-1"

GIFSKI_COMMAND = "gifski -o converted.gif --fps {fps} --width 420 {folder}/*.png" 


def make_gif(folder, fps):
    gifski = [a.replace("?"," ") for a in GIFSKI_COMMAND.format(folder=folder, fps=fps).split(" ")]
    subprocess.Popen(gifski).wait()
    return os.getcwd() + "\\converted.gif"

def waifu2x_gif(input_folder: str, fps):
    for i,frame in enumerate([k for k in os.listdir(input_folder)]):
        inpt = (input_folder+f"\\{frame}").replace(" ","?")
        command = "waifu2x -i {inpt} -o enhanced/enhanced-{num}.png -n {noise} -s {scale}".format(
            inpt=inpt,
            noise="1",
            scale="2",
            num=i
        )
        print(subprocess.list2cmdline([a.replace("?"," ") for a in command.split(" ")]))
        subprocess.Popen([a.replace("?"," ") for a in command.split(" ")], shell=True).wait()
    return make_gif("enhanced",fps=fps)

# TODO: Aggiornare gli argomenti di make_gif in modo da inserire gli fps della gif con get_fps(path)

def main(path_to_mp4):
    last_path = os.getcwd()
    os.chdir(output_path.replace("?"," "))
    if not os.path.exists(os.getcwd()+ "\\frames"):
        os.mkdir(os.getcwd() + "\\frames")
    if not os.path.exists(os.getcwd()+ "\\enhanced"):
        os.mkdir(os.getcwd() + "\\enhanced")

    ffmpeg = [a.replace("?"," ") for a in FFMPEG_COMMAND.format(input = path_to_mp4, resize="").split(" ")] # Senza resize
    subprocess.Popen(ffmpeg).wait()

    if path_to_mp4[-1:-5:-1] == "4pm.":
        gif_path = make_gif("frames", get_fps(path_to_mp4))
    else:
        gif_path = path_to_mp4

    with Image.open(gif_path) as img:
        size = img.size
    
    while size[0] < 420:
        path = waifu2x_gif(output_path.replace("?"," ") + "\\frames", get_fps(gif_path))        
        with Image.open(path) as img:
            size = img.size
   
    shutil.rmtree(str(Path(output_path+"/frames").resolve()).replace("?"," "))
    shutil.rmtree(str(Path(output_path+"/enhanced").resolve()).replace("?"," "))
    
    os.chdir(last_path)
    return output_path

if __name__ == "__main__":
    main(r"c:\Users\andre\Desktop\animation.gif.mp4")