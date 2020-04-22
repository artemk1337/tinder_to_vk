from contextlib import closing
from scipy.linalg import norm
import numpy as np
import torch
import time
import psycopg2
import sqlite3
from tqdm import tqdm

from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


from private import\
    Login, Password, Token,\
    database, user, password, host, port


class DataBase:
    def __init__(self, type_, device, resnet):
        self.DB_type = type_
        self.device = device
        self.resnet = resnet

    def reset_db(self):
        def reset_(conn):
            with conn.cursor() as cur:
                cur.execute("""DROP TABLE users""")
                conn.commit()
    
        if self.DB_type == "Postegre":
            with closing(psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
            )) as conn:
                reset_(conn)
        else:
            with closing(sqlite3.connect("database.db")) as conn:
                reset_(conn)

    def create_db(self):
        def create_(conn):
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

        if self.DB_type == "Postegre":
            with closing(psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
            )) as conn:
                create_(conn)
        else:
            with closing(sqlite3.connect("database.db")) as conn:
                create_(conn)

    def show_db(self):
        def show_(conn):
            with conn.cursor() as cur:
                cur.execute("""SELECT * FROM users""")
                for row in cur:
                    print(row)

        if self.DB_type == "Postegre":
            with closing(psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
            )) as conn:
                show_(conn)
        else:
            with closing(sqlite3.connect("database.db")) as conn:
                show_(conn)

    def find_person(self, arr):
        def new_dists(dists):
            n_dists = []
            i = 0
            while i < len(dists):
                n_dists.append(dists[i] + [1 - dists[i][0]])
                k = i + 1
                while k < len(dists):
                    if dists[i][1] == dists[k][1]:
                        n_dists[i][-1] += 1 - dists[k][0]
                        del dists[k]
                    else:
                        k += 1
                i += 1
            # return n_dists
            return sorted(n_dists, key=lambda x: x[:][-1], reverse=True)[:15]

        def find_(conn):
            dists = []
            with conn.cursor() as cur:
                print('Finding')
                cur.execute("""SELECT * FROM users""")
                start = time.time()
                for row in tqdm(cur):
                    tmp = norm(arr - np.asarray(row[1]))
                    if tmp < 1:
                        dists.append([tmp, row[0], row[2], row[3]])
                print(time.time() - start, 'sec')
            # dists = sorted(dists, key=lambda x: x[:][0])[:200]
            dists = new_dists(dists)
            print(dists)
            return dists

        if self.DB_type == "Postegre":
            with closing(psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
            )) as conn:
                dists = find_(conn)
        else:
            with closing(sqlite3.connect("database.db")) as conn:
                dists = find_(conn)
        return dists

    def save_db(self, aligned, ids, link, sex):
        def save(conn):
            with conn.cursor() as cur:
                for i in range(len(ids)):
                    cur.execute("""
                                INSERT INTO users
                                VALUES (%s, %s, %s, %s, %s)""",
                                (ids[i], embeddings[i], link[i], time.time(), sex[i])
                                )
                conn.commit()

        aligned = torch.stack(aligned).to(self.device)
        embeddings = self.resnet(aligned).detach().cpu().tolist()  # numpy()
        # For check:
        # dists = [[norm(e1 - e2) for e2 in embeddings] for e1 in embeddings]
        # print(pd.DataFrame(dists, columns=ids, index=ids))
        print('Open DataBase')
        if self.DB_type == "Postegre":
            with closing(psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
            ))as conn:
                save(conn)
        else:
            with closing(sqlite3.connect("database.db")) as conn:
                save(conn)
        print('Close DataBase')


if __name__ == "__main__":
    DB_type = "Postegre"
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(image_size=160, keep_all=True)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    img = Image.open('../image.jpg')
    x_aligned, prob = mtcnn(img, save_path=None, return_prob=True)
    embeddings = resnet(x_aligned[:1]).detach().cpu().numpy()
    print(embeddings.shape)
    print(DataBase(DB_type, device, resnet).find_person(embeddings[0]))
