import requests
from config import connect_db
import os

headers = {'User-Agent': 'User-Agent:Mozilla/5.0'}

douyu_url = "https://www.douyu.com/gapi/rkc/directory/"


def init_douyu():
    game_list = {}
    for i in range(1, 550):
        r = requests.get(douyu_url + "2_" + str(i) + "/1", headers=headers)
        if not r.json()['data']['rl']:
            continue
        category = r.json()['data']['rl'][0]['cid1']
        if category == 1 or category == 9 or category == 15:
            game_list[r.json()['data']['rl'][0]['c2name']] = "2_" + str(i)

    db = connect_db()
    cursor = db.cursor()
    for game, value in game_list.items():
        sql = "insert into init(game, douyu) VALUES('%s', '%s') on DUPLICATE key update douyu='%s'" % (game, value,
                                                                                                       value)
        cursor.execute(sql)
    db.commit()
    db.close()


def get_part_douyu(start, end):
    game_list = {}
    if start > end:
        return
    while start <= end:
        r = requests.get(douyu_url + "2_" + str(start) + "/1", headers=headers)
        if not r.json()['data']['rl']:
            start += 1
            continue
        category = r.json()['data']['rl'][0]['cid1']
        if (category == 1 or category == 9 or category == 15) and len(r.json()['data']['rl']) > 1:
            g1 = r.json()['data']['rl'][0]['c2name']
            g2 = r.json()['data']['rl'][1]['c2name']
            if g1 == g2:
                game_list["2_" + str(start)] = g1
                print("【2_" + str(start) + ": " + g1 + "】")
        start += 1
    return game_list


def get_not_in_db(start, end):
    game_list = get_part_douyu(start, end)
    db = connect_db()
    cursor = db.cursor()
    sql = "select gid, douyu from init where douyu is not null"
    cursor.execute(sql)
    results = cursor.fetchall()
    already_in = []
    for result in results:
        already_in.append(result[1])
    for key, game in game_list.items():
        if key not in already_in:
            print(game + ": " + key)


def travel_douyu(data, limit):
    i = 1
    total = 0
    retry = 0
    limit_count = 0
    # 遍历页数
    while True:
        if retry > 10:
            filename = os.path.dirname(__file__) + "/error.txt"
            with open(filename, "a") as f:
                f.writelines("douyu遍历【" + data + "】第" + i + "页10次仍失败，取消遍历\n")
            break
        try:
            r = requests.get(douyu_url + data + "/" + str(i), headers=headers, timeout=5)
        except Exception:
            retry += 1
            continue
        page = r.json()['data']['pgcnt']
        if page == 0 or i > page:
            break
        if not r.json()['data']['rl']:
            break
        # 遍历单独一页的人数
        for j in r.json()['data']['rl']:
            online = int(j['ol'])
            # 超过最低限制，记录次数，超过3次结束该游戏遍历
            if online < limit:
                limit_count += 1
                if limit_count > 3:
                    print('douyu遍历完成，已遍历' + str(i) + '页')
                    return total
            else:
                # y = 10000 / (x / 10000 + 19.9) + 10，人气/y = 人数
                total += online / (10000 / (online / 10000 + 19.9) + 10)
        if i >= page:
            break
        i = i + 1
        retry = 0
    print('douyu遍历完成，已遍历' + str(i) + '页')
    return total


