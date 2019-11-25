import requests
from config import connect_db
import os
import time

headers = {'User-Agent': 'User-Agent:Mozilla/5.0'}

huya_url = "https://www.huya.com/cache.php"
huya_params = {'m': 'LiveList', 'do': 'getLiveListByPage', 'tagAll': 0}


def init_huya():
    game_list = {}

    # 爬取网络游戏
    page = 1
    while True:
        params = huya_params
        params['gameId'] = 100023
        params['page'] = page
        r = requests.get(huya_url, params, headers=headers)
        if not r.json()['data']['datas']:
            break
        for j in r.json()['data']['datas']:
            if j['gameFullName'] not in game_list:
                game_list[j['gameFullName']] = str(j['gid'])
        page = page + 1

    # 爬取手机游戏
    page = 1
    while True:
        params = huya_params
        params['gameId'] = 100004
        params['page'] = page
        r = requests.get(huya_url, params, headers=headers)
        if not r.json()['data']['datas']:
            break
        for j in r.json()['data']['datas']:
            if j['gameFullName'] not in game_list:
                game_list[j['gameFullName']] = str(j['gid'])
        page = page + 1

    # 爬取单机游戏
    page = 1
    while True:
        params = huya_params
        params['gameId'] = 100002
        params['page'] = page
        r = requests.get(huya_url, params, headers=headers)
        if not r.json()['data']['datas']:
            break
        for j in r.json()['data']['datas']:
            if j['gameFullName'] not in game_list:
                game_list[j['gameFullName']] = str(j['gid'])
        page = page + 1

    db = connect_db()
    cursor = db.cursor()
    for game, value in game_list.items():
        sql = "insert into init(game, huya) VALUES('%s', '%s') on DUPLICATE key update huya='%s'" % (game, value, value)
        cursor.execute(sql)
    db.commit()
    db.close()


def travel_huya(data, limit):
    page = 1
    total = 0
    retry = 0
    limit_count = 0
    #  遍历页数
    while True:
        params = huya_params
        params['page'] = page
        params['gameId'] = data
        try:
            if retry > 10:
                filename = os.path.dirname(__file__) + "/error.txt"
                with open(filename, "a") as f:
                    f.write("huya遍历【" + data + "】第" + str(page) + "页10次仍失败，取消遍历\n")
                break
            r = requests.get(huya_url, params, headers=headers, timeout=5)
            if not r.json()['data']['datas']:
                break
            for j in r.json()['data']['datas']:
                online = int(j['totalCount'])
                # 超过最低限制，记录次数，超过3次结束该游戏遍历
                if online < limit:
                    limit_count += 1
                    if limit_count > 3:
                        print('huya遍历完成，已遍历' + str(page) + '页')
                        return total
                else:
                    # y = 4000 / (x / 10000 - 2.99) + 50，人气/y = 人数
                    total += online / (4000 / (online / 10000 - 2.99) + 50)
        except Exception:
            retry += 1
            time.sleep(5)
            continue
        page = page + 1
        retry = 0
    print('huya遍历完成，已遍历' + str(page) + '页')
    return total
