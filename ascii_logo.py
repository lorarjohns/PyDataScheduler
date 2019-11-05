import sys
from PIL import Image

def pydata_pride():
    file = "pydata-logo-final.png"
    img = Image.open(file)
    
    # resize
    w, h = img.size
    aspect = h/w
    new_w = 120
    new_h = int(aspect * new_w * 0.5)
    
    img = img.resize((new_w, int(new_h)))
    
    img = img.convert('L')
    
    px = img.getdata()
    
    # replace
    chars = ["#","=","-","v","!","~","+","|","%","*","!",":",".",r"/",r"\\"]
    new_px = ''.join([chars[p//25] for p in px])
    
    # split = new width
    ascii = [new_px[index:index + new_w] for index in range(0, len(new_px), new_w)]
    ascii = "\n".join(ascii)
    print(ascii)
    
    with open("ascii.txt", "w") as f:
        f.write(ascii)
    
if __name__ == "__main__":
    print(ascii)