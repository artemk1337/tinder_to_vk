"""
private - login, password and other
"""
from tqdm import tqdm
import vk_api
import re
import io
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image, ImageDraw
import time
from scipy.linalg import norm


import psycopg2
from contextlib import closing
from bs4 import BeautifulSoup
import requests


from utils.auth import Auth
from utils._bd import reset_db, create_db, show_db
from private import\
    Login, Password, Token,\
    database, user, password, host, port


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()


max_last_photos = 5
max_faces = 4
max_faces_before_save = 50


def analyze(id, x, current_link,
            aligned, ids, link, sex, curr_sex):
    c = 0
    # save_path=f'data/ids/{id_user}/face_{i}.png'
    x_aligned, prob = mtcnn(x, save_path=None, return_prob=True)
    if len(prob) == 1 and prob[0] is not None:
        # Уверенность 99% и выше
        if prob[0] > 0.99:
            aligned.append(x_aligned[0])
            ids.append(id)
            link.append(current_link)
            sex.append(curr_sex)
            c += 1
    elif x_aligned is not None:
        for k in range(len(prob)):
            # Уверенность 99% и выше
            if prob[k] >= 0.99:
                aligned.append(x_aligned[k])
                ids.append(id)
                link.append(current_link)
                sex.append(curr_sex)
                c += 1
    return c


def save_database(aligned, ids, link, sex):
    aligned = torch.stack(aligned).to(device)
    embeddings = resnet(aligned).detach().cpu().tolist()  # numpy()
    # dists = [[norm(e1 - e2) for e2 in embeddings] for e1 in embeddings]
    # print(pd.DataFrame(dists, columns=ids, index=ids))
    print('open')
    with closing(psycopg2.connect(
                          database=database,
                          user=user,
                          password=password,
                          host=host,
                          port=port
                        )) as conn:
        with conn.cursor() as cur:
            for i in range(len(ids)):
                cur.execute("""
                            INSERT INTO users
                            VALUES (%s, %s, %s, %s, %s)""",
                            (ids[i], embeddings[i], link[i], time.time(), sex[i])
                            )
            conn.commit()


def _download(url):
    p = requests.get(url)
    return Image.open(io.BytesIO(p.content)), url


def get_albums(vk, owner_id, max_count,
               aligned, ids, link):
    def get_albums():
        for album in vk.photos.getAlbums(owner_id=owner_id, need_system=1)['items']:
            photos = vk_tools.get_all(values={'owner_id': album['owner_id'], 'album_id': album['id'], 'photo_sizes': 1},
                                      method='photos.get', max_count=max_count)
            if re.search('Фотографии со страницы', album['title']) or re.search('Фотографии на стене', album['title']):
                albums.append({'name': album['title'],
                               'photos': [p['sizes'][-1]['url'] for p in photos['items']]})
        c_ = 0
        for album in albums:
            for i in range(len(album['photos'])):
                if i > max_last_photos or c_ > max_faces:
                    break
                img, url = _download(album["photos"][-i - 1])
                try:
                    c_ += analyze(owner_id, img, url,
                                  aligned, ids, link, sex, vk.users.get(user_ids=owner_id, fields=['sex'])[0]['sex'])
                except Exception as e:
                    print(e, '- BW mod?')
        return c_

    c = 0
    vk_tools = vk_api.VkTools(vk)
    albums = []
    try:
        c += get_albums()
    except Exception as e:
        print(e)
    return c


"""
reset_db()
create_db()
"""


if __name__ == '__main__':
    vk = Auth(login=Login, password=Password, auth_handler=True).ImplicitFlow()
    counter = 0
    aligned = []
    ids = []
    link = []
    sex = []

    for i in range(5, 10000):
        counter += get_albums(vk, i, 1000, aligned, ids, link)
        print(i, counter)
        if counter >= max_faces_before_save:
            save_database(aligned, ids, link, sex)
            aligned = []
            ids = []
            link = []
            counter = 0
            sex = []
    save_database(aligned, ids, link, sex)












