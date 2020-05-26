from contextlib import closing
from scipy.linalg import norm
import numpy as np
import torch
import time
import psycopg2
import sqlite3
from tqdm import tqdm
import threading


from private import\
    database, user, password, host, port


class DataBase:
    def __init__(self, type_, device, resnet):
        self.DB_type = type_
        self.device = device
        self.resnet = resnet
        self.data_tmp = []

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
                # cur.execute("""CREATE TYPE tensor""")
                cur.execute("""CREATE TABLE users (
                            key BIGSERIAL PRIMARY KEY,
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

    # Multithreading
    def find_person_parallel(self, target):
        def parse_bd(conn, data):
            with conn.cursor() as cur:
                print('Finding')
                cur.execute("""SELECT * FROM users""")
                for row in tqdm(cur):
                    data.append(row)

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
            return sorted(n_dists, key=lambda x: x[:][-1], reverse=True)[:10]

        def find_(conn):
            start = time.time()
            thread = threading.Thread(target=parse_bd,
                                      args=(conn, self.data_tmp))
            thread.start()
            dists = []
            while not self.data_tmp:
                pass
            while self.data_tmp:
                tmp = norm(target - np.asarray(self.data_tmp[0][1]))
                if tmp < 1:
                    dists.append([tmp, self.data_tmp[0][0],
                                  self.data_tmp[0][2], self.data_tmp[0][3]])
                del self.data_tmp[0]
            print(time.time() - start, 'sec')
            # dists = sorted(dists, key=lambda x: x[:][0])[:200]
            dists = new_dists(dists)
            #print(dists)
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
            return sorted(n_dists, key=lambda x: x[:][-1], reverse=True)[:10]

        def find_(conn):

            start = time.time()
            dists = []
            with conn.cursor() as cur:
                print('Finding')
                cur.execute("""SELECT tensor, id, link FROM users""")
                for tensor, id, link in tqdm(cur):
                    tmp = norm(arr - np.asarray(tensor))
                    if tmp < 1:
                        # print(key_)
                        dists.append([tmp, id, link])

            # Скорость работы одинакова
            '''
            start = time.time()
            dists = []
            keys_prob = []
            with conn.cursor() as cur:
                print('Finding')
                cur.execute("""SELECT key, tensor FROM users""")
                for key, tensor in tqdm(cur):
                    tmp = norm(arr - np.asarray(tensor))
                    if tmp < 1:
                        keys_prob.append((key, tmp))
                i = 0
                cur.execute(f"""SELECT id, link FROM users
                                WHERE key IN {tuple([x[0] for x in keys_prob])}""")
                for id, link in tqdm(cur):
                    dists.append([keys_prob[i][1], id, link])
                    i += 1
            del keys_prob
            '''

            print(time.time() - start, 'sec')
            # dists = sorted(dists, key=lambda x: x[:][0])[:200]
            dists = new_dists(dists)
            #print(dists)
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
                                INSERT INTO users (id, tensor, link, time_added, sex)
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
