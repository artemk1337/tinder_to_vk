import io
from PIL import Image
import requests
import vk_api
import re


class ParsePageVK:
    def __init__(self, max_last_photos, max_faces, max_faces_before_save, mtcnn):
        # Parameters
        self.max_last_photos = max_last_photos
        self.max_faces = max_faces
        self.max_faces_before_save = max_faces_before_save
        self.mtcnn = mtcnn

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
        elif x_aligned is not None:
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
        def get_albums():
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
                    if i > self.max_last_photos or c_ > self.max_faces:
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
            c += get_albums()
        except Exception as e:
            print(e)
        return c
