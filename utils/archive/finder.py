import os

from auth import Auth
from json_dop import load_json, save_json

from private import Token, Login, Password


vk = Auth(login=Login, password=Password, auth_handler=True).ImplicitFlow()


def find_users(q, sort=0, offset=0, count=1000, fields=None, city=1, country=1, sex=0,
               age_from=None, age_to=None, has_photo=1, birth_month=None, status=None,
               hometown=None):
    info = vk.users.search(q=q, sort=sort, v=5.103, offset=offset, count=count,
                           fields=fields, city=city, country=country, sex=sex,
                           age_from=age_from, age_to=age_to, has_photo=has_photo,
                           birth_month=birth_month, status=status, hometown=hometown,)
    return info


def finder(q, sort=0, offset=0, count=1000, fields=None, city=1, country=1, sex=0, age_from=14, age_to=80, has_photo=1,
           hometown=None):
    def alg():
        info = find_users(q, 0, offset, count, fields, city, country, sex,
                          i, i, has_photo, birth_month, status, hometown)
        items = {'users': info['items']}
        tmp = items
        if os.path.isfile(f'users_find_{q}.json'):
            tmp = load_json(f'users_find_{q}.json')
            for j in range(len(items['users'])):
                if items['users'][j]['id'] not in [tmp['users'][x]['id'] for x in range(len(tmp['users']))]:
                    print('Success', items['users'][j]['id'])
                    tmp['users'].append(items['users'][j])
        print(f'items - {len(items["users"])}, tmp - {len(tmp["users"])}')
        save_json(f'users_find_{q}.json', tmp)

    birth_month = None
    status = None
    info = find_users(q, sort, offset, count, fields, city, country, sex, age_from, age_to,
                      has_photo, birth_month, status, hometown)
    counter = info['count']
    for i in range(age_from, age_to + 1):
        if counter > 1000:
            for birth_month in [x if x > 0 else None for x in range(13)]:
                if counter > 10000:
                    for status in [y if y > 0 else None for y in range(9)]:
                        alg()
                else:
                    alg()
        else:
            alg()
