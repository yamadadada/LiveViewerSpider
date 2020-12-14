import requests
from config import connect_db
import os
import math
import time

headers = {'User-Agent': 'User-Agent:Mozilla/5.0'}

bilibili_url = 'https://api.live.bilibili.com/room/v1/area/getRoomList'
bilibili_params = {'platform': 'web', 'cate_id': 0, 'sort_type': 'online', 'page_size': 30}

def init_bilibili():
    game_list = {}
    page = 1
    while True:
        params = bilibili_params
        params['area_id'] = 0
        params['page'] = page
        params['parent_area_id'] = 2
        r = requests.get(bilibili_url, params, headers=headers)
        # 判空，结束循环
        if not r.json()['data']:
            break
        # 遍历每一页的人数
        for j in r.json()['data']:
            if j['area_name'] not in game_list:
                game_list[j['area_name']] = "2_" + str(j['area_id'])
        page = page + 1

    page = 1
    while True:
        params = bilibili_params
        params['area_id'] = 0
        params['page'] = page
        params['parent_area_id'] = 3
        r = requests.get(bilibili_url, params, headers=headers)
        # 判空，结束循环
        if not r.json()['data']:
            break
        # 遍历每一页的人数
        for j in r.json()['data']:
            if j['area_name'] not in game_list:
                game_list[j['area_name']] = "3_" + str(j['area_id'])
        page = page + 1

    db = connect_db()
    cursor = db.cursor()
    # 插入数据前清空表
    deletesql = 'delete from init'
    cursor.execute(deletesql)
    for game, value in game_list.items():
        sql = "insert into init(game,bilibili) VALUES('%s', '%s')" % (game, value)
        cursor.execute(sql)
    db.commit()
    db.close()


def travel_bilibili(data, limit):
    flag = data.split("_")[0]
    value = data.split("_")[1]
    bilibili_params['parent_area_id'] = int(flag)
    i = 1
    total = 0
    retry = 0
    limit_count = 0
    # 遍历页数
    while True:
        params = bilibili_params
        params['area_id'] = value
        params['page'] = i
        try:
            if retry > 10:
                filename = os.path.dirname(__file__) + "/error.txt"
                with open(filename, "a") as f:
                    f.write("bili遍历【" + data + "】第" + str(i) + "页10次仍失败，取消遍历\n")
                break
            r = requests.get(bilibili_url, params, headers=headers, timeout=1)
            # 判空，结束循环
            if not r.json()['data']:
                break
            # 遍历每一页的人数
            for j in r.json()['data']:
                online = j['online']
                # 超过最低限制，记录次数，超过3次结束该游戏遍历
                if online < limit:
                    limit_count += 1
                    if limit_count > 3:
                        print('bilibili遍历完成，已遍历' + str(i) + '页')
                        return total
                else:
                    # y4 = 14x + 10000，人气/y = 人数
                    # total += online / math.pow(14 * online + 10000, 1.0 / 4)
                    total += online
        except Exception:
            retry += 1
            time.sleep(1)
            continue
        i = i + 1
        retry = 0
    print('bilibili遍历完成，已遍历' + str(i) + '页')
    return total
