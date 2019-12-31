import time
from config import connect_db
from bilibili import travel_bilibili
from douyu import travel_douyu
from huya import travel_huya
import os
import datetime
import threading
import random


bilibili_limit = 100
douyu_limit = 5000
huya_limit = 40000


def thread_travel(id, item, type):
    if type == 1:
        item['bilibili'] += travel_bilibili(id, bilibili_limit)
    elif type == 2:
        item['douyu'] += travel_douyu(id, douyu_limit)
    else:
        item['huya'] += travel_huya(id, huya_limit)


pretime = time.time()
# 连接数据库
db = connect_db()
db.autocommit(True)
cursor = db.cursor()
# 查出各游戏的参数,status为0表示遍历，为1表示不再遍历
sql = "select bilibili, douyu, huya, game, gid, status from init where status <= 3"
cursor.execute(sql)
games = cursor.fetchall()

# 查出已不再遍历的游戏
sql = "select bilibili, douyu, huya, game, gid, status from init where status > 3"
cursor.execute(sql)
remain_games = cursor.fetchall()
# 抽取10％的游戏做复活处理
resurrection_list = random.sample(remain_games, k=int(len(remain_games) * 0.0625))
print("本次共对" + str(len(resurrection_list)) + "个游戏做复活尝试：")
for r in resurrection_list:
    print("【" + str(r[4]) + "】" + str(r[3]))
print("---------------------------------------")
games = games + tuple(resurrection_list)

all_total = 0
bili_total = 0
douyu_total = 0
huya_total = 0
for game_info in games:
    item = {'bilibili': 0, 'douyu': 0, 'huya': 0, 'total': 0}
    game_id = game_info[4]
    game_name = game_info[3]
    status = int(game_info[5])
    # 使用最多3个线程遍历
    threads = []
    if game_info[0] is not None:
        print("bilibili正在遍历游戏：" + game_name)
        # 多个参数用，分割
        bilibili_id_list = game_info[0].split(',')
        for bilibili_id in bilibili_id_list:
            # 创建多线程，启动，遍历
            thread = threading.Thread(target=thread_travel, args=(bilibili_id, item, 1))
            threads.append(thread)
            thread.start()
    if game_info[1] is not None:
        print("斗鱼正在遍历游戏：" + game_name)
        douyu_id_list = game_info[1].split(',')
        for douyu_id in douyu_id_list:
            # 创建多线程，启动，遍历
            thread = threading.Thread(target=thread_travel,args=(douyu_id, item, 2))
            threads.append(thread)
            thread.start()
    if game_info[2] is not None:
        print("虎牙正在遍历游戏：" + game_name)
        huya_id_list = game_info[2].split(',')
        for huya_id in huya_id_list:
            # 创建多线程，启动，遍历
            thread = threading.Thread(target=thread_travel, args=(huya_id, item, 3))
            threads.append(thread)
            thread.start()
    for i in range(len(threads)):
        threads[i].join()

    # douyu验错机制
    if item['huya'] > 50000 and item['douyu'] > 10 * item['huya']:
        pre_data = item['douyu']
        item['douyu'] = 10 * item['huya']
        filename = os.path.dirname(__file__) + "/douyuerror.txt"
        with open(filename, "a") as f:
            f.write("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "][" + str(game_id) + "]" + game_name +
                    "数据有误，修正前数据为：" + str(pre_data) + ", 修正后数据为：" + str(item['douyu']) + "\n")

    bili_total += item['bilibili']
    douyu_total += item['douyu']
    huya_total += item['huya']
    item['total'] = item['bilibili'] + item['douyu'] + item['huya']
    print("---------------------------------------")
    all_total += item['total']

    # 如果为0，则记录一次失败次数，并记录到数据库中
    if item['total'] == 0:
        status += 1
        sql = "update init set status = '{}' where gid='{}'".format(status, game_id)
        cursor.execute(sql)
        # 如果次数超过3次，则不再遍历该游戏，并记录到日志
        if status > 3:
            filename = os.path.dirname(__file__) + "/log.txt"
            with open(filename, "a") as f:
                f.write("[" + str(game_id) + "]" + game_name + "遍历结果为空，以后不再遍历[" + datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S") + "]\n")
    # 如果不为0且status不为0，则将status置为0
    elif status > 0:
        sql = "update init set status = 0 where gid='{}'".format(game_id)
        cursor.execute(sql)

    # 插入数据库
    sql = "insert into result(gid, game_name, total, bilibili, douyu, huya) VALUES('{}', '{}', '{}', '{}', '{}', '{}')"\
        .format(game_id, game_name, item['total'], item['bilibili'], item['douyu'], item['huya'])
    cursor.execute(sql)

# 总结
travel_time = time.time() - pretime
sql = "insert into summary(total, bili_total, douyu_total, huya_total, game_count, travel_time) VALUES('{}', '{}', '{}', '{}', '{}', '{}')"\
        .format(all_total, bili_total, douyu_total, huya_total, str(len(games)), str(travel_time))
cursor.execute(sql)
db.close()
print("爬取完成，共遍历" + str(len(games)) + "个游戏，使用" + str(travel_time) + "秒")
