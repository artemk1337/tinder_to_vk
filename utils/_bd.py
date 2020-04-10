import psycopg2
from contextlib import closing
from scipy.linalg import norm
import numpy as np
import torch
import pandas as pd
import time

from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


from private import\
    Login, Password, Token,\
    database, user, password, host, port


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
            """Sex: 2 - man, 1 - woman, 0 - None"""
            cur.execute("""CREATE TABLE users (
                        id              integer,
                        tensor          float[],
                        link            text,
                        time_added      integer,
                        sex             integer
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


def find_person(arr):
    dists = []
    with closing(psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
    )) as conn:
        with conn.cursor() as cur:
            print('Finding')
            cur.execute("""SELECT * FROM users""")
            start = time.time()
            for row in cur:

                tmp = norm(arr - np.asarray(row[1]))
                if tmp < 1:
                    dists.append([tmp, row[0], row[2], row[3]])
            print(time.time() - start, 'sec')
    print(dists)  # 10-14


if __name__ == "__main__":
    mtcnn = MTCNN(image_size=160, keep_all=True)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()

    img = Image.open('../target/test.jpg')
    x_aligned, prob = mtcnn(img, save_path=None, return_prob=True)
    embeddings = resnet(x_aligned[:1]).detach().cpu().numpy()
    print(embeddings.shape)
    find_person(embeddings[0])



