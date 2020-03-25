## 一.连接

### 1.安装PyMongo模块

```python
>>> pip install PyMongo
```

### 2.创建mongod实例对象

```python
>>> from pymongo import MongoClient
>>> client = MongoClient()
```

### 3连接到MongoDB数据库

```python
>>> client = MongoClient('localhost', 27017)
```

不指定端口默认为27017

---

## 二.查看

### 1.查看连接的MongoDB中所有的所有数据库

```python
>>> client.list_database_names()
```

返回的结果为一个列表对象

### 2.查看指定数据库中的所有集合

```python
>>> client['database'].list_collection_names()
```

返回的结果为一个列表对象

### 3.查看指定集合中的记录

#### 1.查询所有

```python
>>> client['database']['collection'].find()
```

#### 2.查询首个

```python
>>> client['database']['collection'].find_one()
```

#### 3.指定查询

```python
>>> client['database']['collection'].find({key:value})
>>> client['database']['collection'].find({},{key:value})   #查询除指定键值以外的键值
```

#### 4.高级查询

```python
>>> client['database']['collection'].find({key:{ "$gt": "H"}})
```

查询key字段中第一个字母ASCII值大于“H"的数据

#### 5.正则查询

```python
>>> client['database']['collection'].find({ key: {"$regex":"^R"}})
```

#### 6.限制查询

```python
>>> client['database']['collection'].find().limit(n)
>>> client['database']['collection'].find().sort(key)
```

返回结果为一个可迭代的Cursor对象

---

## 三.插入

### 1.插入一条记录到集合

```python
>>> client['database']['collection'].insert_one({key:value})
```

### 2.插入多条记录到集合

```python
>>> client['database']['collection'].insert_many(dict)
```

---

## 四.更新

### 1.更新一条记录的值

```python
>>> myquery = { "address": "Valley 345" }
>>> newvalues = { "$set": { "address": "Canyon 123" } }
>>> client['database']['collection'].update_one(myquery, newvalues)
```

### 2.更新多条记录的值

```python
>>> myquery = { "address": { "$regex": "^S" } }
>>> newvalues = { "$set": { "address": "Canyon 123" } }
>>> client['database']['collection'].update_many(myquery, newvalues)
```

---

## 五.删除

### 1.删除集合中的一条记录

```python
>>> myquery = { "address": "Valley 345" }
>>> client['database']['collection'].delete_one(myquery)
```

### 2.删除集合中的多条记录

```python
>>> myquery = { "address": { "$regex": "^S" } }
>>> client['database']['collection'].delete_many(myquery)
```

### 3.删除集合中的所有记录

```python
>>> client['database']['collection'].delete_many({})
```

### 4.删除指定集合

```python
>>> client['database']['collection'].drop()
```

### 5.删除指定数据库

```python
>>> client['database'].drop()
```

----

## 六.参考

【1】https://www.w3schools.com/python/python_mongodb_getstarted.asp

【2】 https://api.mongodb.com/python/current/tutorial.html#making-a-connection-with-mongoclient 