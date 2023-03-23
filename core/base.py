class CDict:

    def __init__(self):
        self._db = {}
        # 存储数据字典的键值列表，用于该字典摧毁前的数据唯一性
        self._db_keys = []
        self._index = 0

    def __repr__(self):
        return str(self._db)


    def __getitem__(self, item):
        ret = None
        try:
            ret = self._db[item]
        except KeyError as e:
            print('{} is not found!'.format(item))

        return ret

    def __setitem__(self, key, value):
        if key not in self._db_keys:
            self._db[key] = value
            self._db_keys.append(key)
        else:
            raise KeyError

    def __len__(self):
        return len(self._db)

    def generator(self):
        yield from self._db

    def pop(self):
        if len(self._db_keys) > 0:
            # get return and pop value from _db dict
            ret = self._db.pop(self._db_keys[self._index])
            self._index += 1
            return ret
        else:
            raise StopIteration

    def push(self, key, value):
        try:
            self._db[key] = value
            self._db_keys.append(key)
        except KeyError as e:
            print('{} Already exists!'.format(key))

    def ret_keys(self) -> list:
        return self._db_keys

    def ret_index(self):
        return self._index


