#! /usr/bin/env python3.7.4
#  使用协程异步读写mysql数据
#  使用日志、异常追踪、协程模块
#  创建数据库、表、存储过程记录在asyncioMysql_SQL中

import asyncio
import logging
import logging.handlers
import random
import time
import traceback

import aiomysql
import pymysql

logger = None


# 日志配置：记录器、处理程序、过滤器和格式化程序

def init_logger():
    global logger

    # 创建记录器
    logger = logging.getLogger('python_mysql')
    # 指定记录器处理的最低严重性日志消息
    logger.setLevel(logging.DEBUG)

    # 定义处理程序,并添加到记录器
    # logger_hander = logging.handlers.RotatingFileHandler(
    #     filename="python_mysql.log", maxBytes=20*1024, backupCount=10)

    logger_hander = logging.StreamHandler()
    logger.addHandler(logger_hander)

    # 格式化程序，添加到处理程序
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logger_hander.setFormatter(formatter)


# 自定义数据库类
class Pymariadb():
    def __init__(self, host, port, db, user, passwd):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.passwd = passwd

        self.pool = None

    async def connet_db_pool(self):
        self.pool = await aiomysql.create_pool(
            host=self.host, port=3306, db=self.db, user=self.user, password=self.passwd, autocommit=False, minsize=1, maxsize=10)

    # 获取游标
    async def get_cur(self):
        conn = await self.pool.acquire()
        cur = await conn.cursor()
        return conn, cur

    # 执行查询
    # 定义局部变量conn、cur，避免程序在异步处理时变量名冲突
    async def select(self, num=1):
        try:
            conn, cur = await self.get_cur()

            # 调用存储过程 (查询"Alinas"并限制输出一行)
            await cur.execute("call testData.pro_query;")

            # 打印当前协程num方便输出观察
            logger.info(f"{num}-获取数据！")
            for i in (await cur.fetchall()):
                print(i)
        except:
            logger.warn("从数据表中获取数据错误！")
            traceback.print_exc()
        finally:
            if cur:
                print(id(conn))
                await cur.close()
                await self.pool.release(conn)

    async def insert(self, num=1):

        # 准备协程数据
        brand = random.choice(
            ["Alinas", "Bibiq", "Cawu", "Dolo", "Elay", "Fisa", "Gogo", "Hila", "Imay"])

        price = random.randint(1, 1000)*random.random()

        try:
            conn, cur = await self.get_cur()

            # 调用存储过程（插入随机数据到mysql）
            await cur.execute(f"call pro_create('{brand}',{price});")
            await conn.commit()

            # 打印当前协程num方便输出观察
            logger.info(f"{num}-插入数据！")
        except:
            logger.warning("从数据表中插入数据错误！")
            traceback.print_exc()
        finally:
            if cur:
                print(id(conn))
                await cur.close()
                await self.pool.release(conn)


async def main(row):

    list = []
    db = Pymariadb(host="127.0.0.1", port=3306,
                   db="testData", user="remoter", passwd="123456")
    await db.connet_db_pool()

    for i in range(1, row+1):

        # 构造函数列表
        task = asyncio.create_task(db.select(i))
        #task = asyncio.create_task(db.insert(i))
        list.append(task)

    # 并发执行多任务
    await asyncio.gather(*list)


if __name__ == "__main__":
    init_logger()
    start = time.time()

    # 定义写入和读取mysql数据的次数
    row = 10000

    asyncio.run(main(row))
    print("耗时：", time.time()-start)
