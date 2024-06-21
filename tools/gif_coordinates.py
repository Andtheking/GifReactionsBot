import cv2
import copy
import pyperclip

# define mouse callback function to draw circle
rects = {}
drawing = False
nRect = 0
def mouse_event(event, x, y, flags, param):
    global ix, iy, drawing, rects, frames, nRect
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix = x
        iy = y
      
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        nRect += 1

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        if len(rects)> 0 and f"rect-{nRect}" in rects:
            rects.pop(f"rect-{nRect}")
        rects[f"rect-{nRect}"] = ((ix,iy,x,y))

    elif event == cv2.EVENT_RBUTTONDOWN:
        to_remove = []
        for rect in rects:
            rX1 = rects[rect][0]
            rY1 = rects[rect][1]
            rX2 = rects[rect][2]
            rY2 = rects[rect][3]

            if rX1 <= x <= rX2 or rX2 <= x <= rX1:
                if rY1 <= y <= rY2 or rY2 <= y <= rY1:
                    to_remove.append(rect)

        for i in to_remove:
            rects.pop(i)
    
    elif event == cv2.EVENT_MBUTTONDOWN:
        for rect in rects:
            if rects[rect][0] <= x <= rects[rect][2] and rects[rect][1] <= y <= rects[rect][3]:
                print(f"Coordinate del rettangolo cliccato: {rects[rect][0]},{rects[rect][1]} {rects[rect][2]},{rects[rect][3]}")
                pyperclip.copy(f"{rects[rect][0]},{rects[rect][1]} {rects[rect][2]},{rects[rect][3]}")


def main(gif_path):
    global backups, frames
    cv2.namedWindow("wind")
    cv2.setMouseCallback("wind", mouse_event)

    # capture the animated gif
    gif = cv2.VideoCapture(gif_path)
    
    frames = [] # Metterò i frame in un array in modo da poterli scorrere

    ret, frame = gif.read()  # ret=True finché ci sono frame da leggere
    while ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frames.append(frame)
        ret, frame = gif.read()

    original_copy = copy.deepcopy(frames) # Faccio una copia senza nessuna modifica
    iFrame = 0 # Tengo il conto dei frame
    

    while iFrame < len(frames):
        frames = copy.deepcopy(original_copy)
        if len(rects) > 0:
            for rect in rects:
                cv2.rectangle(
                    img = frames[iFrame],
                    pt1 = (rects[rect][0],rects[rect][1]), 
                    pt2 = (rects[rect][2],rects[rect][3]),
                    color = (255,0,0), 
                    thickness = 2
                )
        
                size, _ = cv2.getTextSize(
                    text="Andtheking",
                    fontFace=cv2.FONT_HERSHEY_COMPLEX,
                    fontScale=1,
                    thickness=1
                )

                text_w = size[0]
                text_h = size[1]
                rect_w = rects[rect][2] - rects[rect][0]
                rect_h = rects[rect][3] - rects[rect][1]
                x = rects[rect][0] + (rect_w - text_w) // 2
                y = rects[rect][1] + (rect_h - text_h) // 2
                # rectangle(rect_left, rect_top, rect_right, rect_bottom);
                # outtextxy(x, y, textstring);


                cv2.putText(
                    img = frames[iFrame],
                    text="Andtheking",
                    org=(x,y+size[1]),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX,
                    fontScale=1,
                    color=(255,0,0)
                )
        
        cv2.imshow("wind",frames[iFrame])

        key = cv2.waitKey(27)
        if cv2.getWindowProperty("wind", cv2.WND_PROP_VISIBLE) < 1:
            break
        if key == 27:
            break
        elif key == 99 or key == 99-32:
            print("Info sulla gif:"+
                  f"\n  W: {frames[0].shape[1]}"+
                  f"\n  H: {frames[0].shape[0]} "
                )

        iFrame += 1
        if iFrame == len(frames):
            iFrame = 0

    cv2.destroyAllWindows()
    
    return list(rects.values())

if __name__ == "__main__":
    main("gifs/cry/cry1.gif")
    