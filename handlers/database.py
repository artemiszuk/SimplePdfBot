# (c) @AbirHasan2005 & @artemiszuk
import os
import motor.motor_asyncio

uri = os.environ.get("MONGO_URI")


class Database:
    def __init__(self, uri):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.dba = self._client["mydatabase"]
        self.col = self.dba["pdfbot"]

    def new_user(self, id):
        return dict(_id=id, fname=str(id))

    async def update_fname(self, id, name):
        user = await self.col.find_one({"_id": id})
        self.col.update_one({"_id": id}, {"$set": {"fname": name}})

    async def get_user_dict(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user

    async def add_user(self, id):
        user = self.new_user(id)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return True if user else False

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def print_all_docs(self):
        cursor = self.col.find({})
        count = await self.total_users_count()
        for user in await cursor.to_list(count):
            print(user)

    async def get_all_users(self):
        ulist = []
        cursor = self.col.find({})
        count = await self.total_users_count()
        for user in await cursor.to_list(count):
            ulist.append(user["_id"])
        return ulist

    async def delete_user(self, user_id):
        await self.col.delete_many({"_id": int(user_id)})


db = Database(uri)
