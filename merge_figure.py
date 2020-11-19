import numpy as np
from PIL import Image
import os

def merge(src, size, name='test.png'):
    assert len(src) <= np.prod(size), '請確認合併後的大小'

    imgs = [Image.open(i) for i in src]
    while len(imgs)< np.prod(size):
        imgs.append(None)
    
    xr, yr = imgs[0].size
    nx, ny = size
    i = 0
    outImg = Image.new('RGB', (nx*xr, ny*yr), (255,255,255,255))
    print(outImg)
    for ix in range(nx):
        for iy in range(ny):
            img = imgs[i]

            position = [ix*xr, iy*yr, xr+ix*xr, yr+iy*yr]
            #print(position)
            outImg.paste(img, position)
            i+=1

    outImg.save(name)
    return outImg
    

if __name__ == '__main__':
    basepath = '/Users/jen/GD_simenvi/SimEnvi/Project/108E23_CTSP/50.Work/AIRBOX_routine/figure'
    files = [os.path.join(basepath, i) for i in os.listdir(basepath) if '濃度比較' in i and '環保署' not in i]
    a = merge(files, (1,4))
