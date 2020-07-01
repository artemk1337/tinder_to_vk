import io
from PIL import Image
import requests
import vk_api
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import datetime
import time
import numpy as np
import pandas as pd
import torch


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
    def __init__(self, vk, vk_session, data_base, mtcnn, resnet, device,
                 max_last_photos=50, max_faces=50, min_faces_before_save=50,
                 max_faces_one_photo=3, last_seen_range=2629743):
        # Parameters
        self.max_last_photos = max_last_photos
        self.max_faces = max_faces
        self.min_faces_before_save = min_faces_before_save
        self.last_seen_range = last_seen_range
        self.max_faces_one_photo = max_faces_one_photo
        self.mtcnn = mtcnn
        self.resnet = resnet
        self.device = device
        self.vk = vk
        self.vk_session = vk_session
        self.data_base = data_base
        self.CURRENT_ID = None
        self.STATUS_PARSER = "OFF"

    ### <===== OLD PART =====> ###
    def analyze(self, id, x, current_link, aligned, ids, link, sex, curr_sex):
        def sucess(c, k):
            aligned.append(x_aligned[k])
            ids.append(id)
            link.append(current_link)
            sex.append(curr_sex)
            c += 1
            return c

        c = 0
        # save_path=f'data/ids/face{str(time.time()).split(".")[-1]}/{id}.jpg'
        x_aligned, prob = self.mtcnn(x, save_path=None, return_prob=True)
        if len(prob) == 1 and prob[0] is not None:
            # Уверенность >= 99%
            if prob[0] >= 0.99:
                c = sucess(c, 0)
        elif 1 < len(prob) < 5:
            for k in range(len(prob)):
                # Уверенность >= 99%
                if prob[k] >= 0.99:
                    c = sucess(c, k)
        print(c)
        return c

    def _download(self, url):
        p = requests.get(url)
        return Image.open(io.BytesIO(p.content))

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
            if str(e) == "Can't load items. Check access to requested items":
                print("PROBLEMS WITH CONNECTION. "
                      "RESTART VK ACCOUNT")
                quit()
                exit()
        return c

    ### <===== NEW PART =====> ###
    def analyze_photo(self, owner_id, img, vectors, url, url_photos):
        # save_path=f'data/ids/face{str(time.time()).split(".")[-1]}/{id}.jpg'
        x_aligned, prob = self.mtcnn(img, save_path=None, return_prob=True)
        if len(prob) == 1 and prob[0] is not None:
            # Уверенность > 99%
            if prob[0] > 0.99:
                #print(x_aligned.shape)
                vectors += self.resnet(x_aligned).detach().cpu().tolist()
                url_photos += [url]
        elif 1 < len(prob) < self.max_faces_one_photo:
            for k in range(len(prob)):
                # Уверенность > 99%
                if prob[k] > 0.99:
                    #print(x_aligned.shape)
                    vectors += self.resnet(x_aligned[k:k+1]).detach().cpu().tolist()
                    url_photos += [url]
        return vectors, url_photos

    def get_face(self, owner_id, max_count, aligned, ids, sex, links):
        def _get_id_sex_person_(ids, sex):
            ids += [owner_id]
            sex += [self.vk.users.get(user_ids=owner_id, fields=['sex'])[0]['sex']]

        def _download_photo_(url):
            p = requests.get(url)
            return Image.open(io.BytesIO(p.content)), url

        def _find_best_vector_(embeddings, url_photos):
            #print(embeddings.shape)
            dists = [[(e1 - e2).norm().item() for e2 in embeddings] for e1 in embeddings]
            df = pd.DataFrame(dists,
                              columns=url_photos,
                              index=url_photos)
            tmp = [np.median(df[i]) for i in df]
            tmp_ = sorted(tmp, key=lambda x: x, reverse=False)
            # df.to_csv('data/table.csv')
            key = tmp.index(tmp_[0])
            links.append(url_photos[key])
            aligned.append(embeddings[key].tolist())
            _get_id_sex_person_(ids, sex)
            if len(tmp) > 1:
                key = tmp.index(tmp_[0])
                links.append(url_photos[key])
                aligned.append(embeddings[key].tolist())
                _get_id_sex_person_(ids, sex)
            if len(tmp) > 2:
                key = tmp.index(tmp_[0])
                links.append(url_photos[key])
                aligned.append(embeddings[key].tolist())
                _get_id_sex_person_(ids, sex)
            del tmp, tmp_
            assert len(links) == len(aligned) == len(ids) == len(sex), "ASSERT ERROR 1"

        vk_tools = vk_api.VkTools(self.vk)
        url_photos = []
        albums = []
        vectors = []
        try:
            for album in self.vk.photos.getAlbums(owner_id=owner_id, need_system=1)['items']:
                photos = vk_tools.get_all(values={'owner_id': album['owner_id'],
                                                  'album_id': album['id'], 'photo_sizes': 1},
                                          method='photos.get', max_count=max_count)
                if re.search('Фотографии со страницы', album['title']) \
                        or re.search('Фотографии на стене', album['title']):
                    albums.append({'name': album['title'],
                                   'photos': [p['sizes'][-1]['url'] for p in photos['items']]})
            for album in albums:
                for i in range(len(album['photos'])):
                    if i >= self.max_last_photos:
                        break
                    img, url = _download_photo_(album["photos"][-i - 1])
                    try:
                        vectors, url_photos = self.analyze_photo(owner_id, img, vectors,
                                                     url, url_photos)
                    except Exception as e:
                        print('Error 2:', e, '- BW mod?')
            if vectors:
                _find_best_vector_(torch.tensor(vectors).to(self.device), url_photos)
            return 1
        except Exception as e:
            print('Error 1:', e, owner_id)
            try:
                if str(e)[:4] == "[30]":
                    soup = BeautifulSoup(self.vk_session.http.get(f'https://vk.com/id{owner_id}').text, 'lxml')
                    img = (soup.find_all('div', id='page_avatar')[0]).find('img').get('src')
                    img, url = _download_photo_(img)
                    try:
                        vectors, url_photos = self.analyze_photo(owner_id, img, vectors, url, url_photos)
                    except Exception as e:
                        print('Error 2:', e, '- BW mod?')
                    if vectors:
                        _find_best_vector_(torch.tensor(vectors).to(self.device), url_photos, links)
                    return 1
            except:
                pass
            if str(e) == "Can't load items. Check access to requested items":
                print("PROBLEMS WITH CONNECTION. "
                      "RESTART VK ACCOUNT")
                # exit()
            return 0

    def start_parsing(self, ids, path=None):
        if path is not None:
            ids = np.load('data/ids_from_group_' + path + '.npy')

        collected_faces = 0
        aligned, current_ids, sex, links = [], [], [], []
        print("Start parse")
        start_index = list(ids).index(386780555)
        for i in (ids[start_index:]):
            self.CURRENT_ID = i
            collected_faces += self.get_face(i, 1000, aligned, current_ids, sex, links)
            print("id -", i, "persons -", collected_faces)
            if collected_faces >= self.min_faces_before_save:
                self.data_base.save_db(aligned, current_ids, sex, links)
                collected_faces = 0
                aligned, current_ids, sex, links = [], [], [], []
        if current_ids:
            self.data_base.save_db(aligned, current_ids, sex, links)
            collected_faces = 0
            del aligned, current_ids, sex, links
        self.CURRENT_ID = None
        print("Finish parse")

    def parse_ids_from_group(self, url, fields=['last_seen']):
        list_ids = []
        i = 0
        count = 1000
        import sys
        max_i = sys.maxsize
        while i < max_i:
            users = self.vk.groups.getMembers(group_id=url, offset=i, count=count, fields=fields, sort='id_desc')
            max_i = users['count']

            list_ids += [k['id'] if k.get('last_seen', None) and
                         time.time() - int(k['last_seen']['time']) < self.last_seen_range
                         else k['id'] if not k.get('last_seen', None) else None
                         for k in users['items']
                         ]
            i += count
        list_ids = np.asarray([i for i in list_ids if i])
        print(len(list_ids))
        np.save(f'data/ids_from_group_{url}', list_ids)
