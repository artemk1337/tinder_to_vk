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

from auth import Auth
from private import Login, Password, Token


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()


max_last_photos = 5
max_faces = 5
counter = 0


database = "vk"
user = "postgres"
password = "123"
host = "localhost"
port = "5432"


def analyze(id, x, current_link,
            aligned, ids, link):
    c = 0
    # save_path=f'data/ids/{id_user}/face_{i}.png'
    x_aligned, prob = mtcnn(x, save_path=None, return_prob=True)
    if len(prob) == 1 and prob[0] is not None:
        # Уверенность 99% и выше
        if prob[0] > 0.99:
            aligned.append(x_aligned[0])
            ids.append(id)
            link.append(current_link)
            c += 1
    elif x_aligned is not None:
        for k in range(len(prob)):
            # Уверенность 99% и выше
            if prob[k] > 0.99:
                aligned.append(x_aligned[k])
                ids.append(id)
                link.append(current_link)
                c += 1
    return c


def save_database(aligned, ids, link):
    aligned = torch.stack(aligned).to(device)
    embeddings = resnet(aligned).detach().cpu().tolist()  # numpy()
    # dists = [[norm(e1 - e2) for e2 in embeddings] for e1 in embeddings]
    # print(pd.DataFrame(dists, columns=ids, index=ids))
    print('open')
    with closing(psycopg2.connect(
                          database="vk",
                          user="postgres",
                          password="123",
                          host="localhost",
                          port="5432"
                        )) as conn:
        with conn.cursor() as cur:
            for i in range(len(ids)):
                cur.execute("""
                            INSERT INTO users
                            VALUES (%s, %s, %s, %s)""",
                            (i, embeddings[i], link[i], time.time())
                            )
            conn.commit()


def get_albums(vk, owner_id, max_count,
               aligned, ids, link):
    def _download(url):
        p = requests.get(url)
        return Image.open(io.BytesIO(p.content)), url

    def get_albums():
        c_ = 0
        for album in vk.photos.getAlbums(owner_id=owner_id, need_system=1)['items']:
            photos = vk_tools.get_all(values={'owner_id': album['owner_id'], 'album_id': album['id'], 'photo_sizes': 1},
                                      method='photos.get', max_count=max_count)
            if re.search('Фотографии со страницы', album['title']) or re.search('Фотографии на стене', album['title']):
                albums.append({'name': album['title'],
                               'photos': [p['sizes'][-1]['url'] for p in photos['items']]})
        for album in albums:
            for i in range(len(album['photos'])):
                if i > max_last_photos or c_ > max_faces:
                    break
                img, url = _download(album["photos"][-i - 1])
                c_ += analyze(owner_id, img, url,
                                  aligned, ids, link)
        return c_

    def get_avatar(id):
        c_ = 0
        page = requests.get(f'https://vk.com/id{id}')
        # Success - 200
        if page.status_code != 200:
            return 0
        soup = BeautifulSoup(page.text, "html.parser")
        return c_
        # Need fix problems with Auth!
        pass

    c = 0
    vk_tools = vk_api.VkTools(vk)
    albums = []
    user = vk.users.get(user_ids=owner_id, fields=['photo_id'])[0]
    try:
        if user['can_access_closed'] is True:
            try:
                c += get_albums()
            except Exception as e:
                print(e)
        else:
            pass
    except Exception as e1:
        print('BLOCKED USER')

    return c


def reset_db():
    with closing(psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
    )) as conn:
        with conn.cursor() as cur:
            cur.execute("""DROP TABLE users""")
            conn.commit()


def create_db():
    with closing(psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
    )) as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE users (
                        id              integer,
                        tensor          float[],
                        link            text,
                        time_added      integer
                        )""")
            conn.commit()


def show_db():
    with closing(psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
    )) as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT * FROM users""")
            for row in cur:
                print(row)



vec = []
res = []
with closing(psycopg2.connect(
                          database=database,
                          user=user,
                          password=password,
                          host=host,
                          port=port
                        )) as conn:
    with conn.cursor() as cur:
        cur.execute("""SELECT * FROM users""")
        start = time.time()
        for row in cur:
            x = np.asarray(row[1])
            break
        for row in cur:
            vec.append(np.asarray(row[1]))
            # res.append(norm(x - np.asarray(row[1])))
        for i in vec:
            res.append(norm(x - i))
        print(time.time() - start)

print(res)


quit()

reset_db()
create_db()


vk = Auth(login=Login, password=Password, auth_handler=True).ImplicitFlow()


counter = 0
aligned = []
ids = []
link = []

for i in range(1, 100):
    counter += get_albums(vk, i, 1000,
                          aligned, ids, link)
    print(i, counter)
    if counter >= 50:
        save_database(aligned, ids, link)
        aligned = []
        ids = []
        link = []
        counter = 0
        quit()

save_database(aligned, ids, link)

