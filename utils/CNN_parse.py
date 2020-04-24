import io
from PIL import Image
import requests
import vk_api
import re
from bs4 import BeautifulSoup
from tqdm import tqdm


# import requests
# import vk_api
# import re
# import io
# import psycopg2
# import sqlite3
# import time
# from scipy.linalg import norm
# import numpy as np
# from bs4 import BeautifulSoup


class FinderVK:
    def __init__(self, db_type, mtcnn,
                 resnet, data_base):
        self.db_type = db_type
        self.mtcnn = mtcnn
        self.resnet = resnet
        self.data_base = data_base
        self.STATUS_FINDER = "OFF"

    def _check_path_img(self, path, img):
        if path:
            return Image.open(path)
        if img:
            return img
        return None

    def finder(self, path=None, img=None):
        self.STATUS_FINDER = "ON"
        _img = self._check_path_img(path, img)
        if not _img:
            print("path or img mustn't be empty")
            return []
        x_aligned, prob = self.mtcnn(_img, save_path=None, return_prob=True)
        embeddings = self.resnet(x_aligned[:1]).detach().cpu().numpy()
        res = self.data_base.find_person(embeddings[0])
        self.STATUS_FINDER = "OFF"
        return res


class ResetDB:
    def __init__(self, data_base):
        self.data_base = data_base

    def reset_db_(self):
        try:
            self.data_base.reset_db()
        except:
            pass
        self.data_base.create_db()
        print("Success reset DataBase")


class ParsePageVK:
    def __init__(self, vk, vk_session, data_base, mtcnn,
                 max_last_photos=30, max_faces=20, min_faces_before_save=50):
        # Parameters
        self.max_last_photos = max_last_photos
        self.max_faces = max_faces
        self.min_faces_before_save = min_faces_before_save
        self.mtcnn = mtcnn
        self.vk = vk
        self.vk_session = vk_session
        self.data_base = data_base
        self.CURRENT_ID = None
        self.STATUS_PARSER = "OFF"

    def analyze(self, id, x, current_link, aligned, ids, link, sex, curr_sex):
        c = 0
        # save_path=f'data/ids/{id_user}/face_{i}.png'
        x_aligned, prob = self.mtcnn(x, save_path=None, return_prob=True)
        if len(prob) == 1 and prob[0] is not None:
            # Уверенность >= 99%
            if prob[0] >= 0.99:
                aligned.append(x_aligned[0])
                ids.append(id)
                link.append(current_link)
                sex.append(curr_sex)
                c += 1
        elif 1 < len(prob) < 15:
            for k in range(len(prob)):
                # Уверенность >= 99%
                if prob[k] >= 0.99:
                    aligned.append(x_aligned[k])
                    ids.append(id)
                    link.append(current_link)
                    sex.append(curr_sex)
                    c += 1
        return c

    def _download(self, url):
        p = requests.get(url)
        return Image.open(io.BytesIO(p.content)), url

    def get_albums(self, vk, owner_id, max_count, aligned, ids, link, sex):
        def get_avatar():
            soup = BeautifulSoup(self.vk_session.http.get(f'https://vk.com/id{owner_id}').text, 'lxml')
            s = (soup.find_all('div', id='page_avatar')[0]).find('img').get('src')
            c_ = 0
            img, url = self._download(s)
            try:
                c_ += self.analyze(owner_id, img, url,
                                   aligned, ids, link, sex,
                                   vk.users.get(user_ids=owner_id,
                                                fields=['sex'])[0]['sex']
                                   )
            except Exception as e:
                print(e, '- BW mod?')
            return c_

        def _get_albums():
            for album in vk.photos.getAlbums(owner_id=owner_id, need_system=1)['items']:
                photos = vk_tools.get_all(values={'owner_id': album['owner_id'],
                                                  'album_id': album['id'], 'photo_sizes': 1},
                                          method='photos.get', max_count=max_count)
                if re.search('Фотографии со страницы', album['title'])\
                        or re.search('Фотографии на стене', album['title']):
                    albums.append({'name': album['title'],
                                   'photos': [p['sizes'][-1]['url'] for p in photos['items']]})
            c_ = 0
            for album in albums:
                for i in range(len(album['photos'])):
                    if i >= self.max_last_photos or c_ >= self.max_faces:
                        break
                    img, url = self._download(album["photos"][-i - 1])
                    try:
                        c_ += self.analyze(owner_id, img, url,
                                           aligned, ids, link, sex,
                                           vk.users.get(user_ids=owner_id,
                                                        fields=['sex'])[0]['sex']
                                           )
                    except Exception as e:
                        print(e, '- BW mod?')
            return c_

        c = 0
        vk_tools = vk_api.VkTools(vk)
        albums = []
        try:
            c += _get_albums()
        except Exception as e:
            print(e, owner_id)
            try:
                if str(e)[:4] == "[30]":
                    c += get_avatar()
            except:
                pass
        return c

    def start_parsing(self, id_):
        counter = 0
        aligned, ids, link, sex = [], [], [], []
        print("Start parse")
        import pickle
        # 16888179
        with open("ids.txt", 'rb') as f:
            id_ = pickle.load(f)
        for i in tqdm(id_[id_.index(169115138):]):
            self.CURRENT_ID = i
            counter += self.get_albums(self.vk, i, 1000, aligned, ids, link, sex)
            print("id -", i, "persons -", counter)
            if counter >= self.min_faces_before_save:
                self.data_base.save_db(aligned, ids, link, sex)
                counter = 0
                aligned, ids, link, sex = [], [], [], []
        if ids:
            self.data_base.save_db(aligned, ids, link, sex)
        self.CURRENT_ID = None
        print("Finish parse")


