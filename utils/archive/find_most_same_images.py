import cv2
import numpy as np
import os
from auth import Auth
from private import Login, Password, Token
from json_dop import load_json
from progress.bar import IncrementalBar, Bar, ChargingBar, FillingSquaresBar, FillingCirclesBar,\
    PixelBar, ShadyBar
from tqdm import tqdm
import time


vk = Auth(token=Token).Client_credentials_flow()
template = cv2.imread('target/1.jpg', 0)
g_counter = 0


def find_same(template, img_rgb, root):
    def success():
        global g_counter
        g_counter += 1
        tmp = ''
        if os.path.isdir('target'):
            tmp += 'target/'
        cv2.imwrite(f'{tmp}Detected_{g_counter}.jpg', img_rgb)
        with open(f'{tmp}info.txt', 'a', encoding='utf8') as f:
            f.write(f'{g_counter}:' + root.split('/')[-1] + '\n')
        # print('Success')

    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    w, h = template.shape[::-1]

    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)

    for pt in zip(*loc[::-1]):
        cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 255, 255), 2)
        # Dop for my situation, try to find first enter:
        success()
        break
    # cv2.imwrite('Detected.jpg', img_rgb)


max_len = len(os.listdir('data'))

bar = PixelBar(max=max_len)


for root, dirs, f in os.walk('data'):
    def check_last_login(root):
        a = vk.users.get(user_ids=root.split('\\')[-1], fields='last_seen', v=5.103)[0]['last_seen']['time']
        if time.time() - a < 86400:
            return True
        return False

    counter = 0
    if root.split('\\')[-1] != 'data' and check_last_login(root) is True:
        for i in f:
            root = root.replace("\\", "/")
            # print(f'{root}/{i}')
            # print(os.path.isfile(f'{root}/{i}'))
            with open(f'{root}/{i}', 'rb') as file:
                bytes = bytearray(file.read())
            numpyarray = np.asarray(bytes, dtype=np.uint8)
            # img_rgb = cv2.imread(f'{root}/{i}')
            img_rgb = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)
            try:
                find_same(template, img_rgb, root)
            except Exception as e:\
                pass
    bar.next()












