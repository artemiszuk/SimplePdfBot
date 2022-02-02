# (c) @ballicipluck & @AbirHasan2005
import os
from base64 import standard_b64encode, standard_b64decode


def str_to_b64(__str: str) -> str:
    str_bytes = __str.encode("ascii")
    bytes_b64 = standard_b64encode(str_bytes)
    b64 = bytes_b64.decode("ascii")
    return b64


def b64_to_str(b64: str) -> str:
    bytes_b64 = b64.encode("ascii")
    bytes_str = standard_b64decode(bytes_b64)
    __str = bytes_str.decode("ascii")
    return __str


async def retrieve(app, log_c, encoded_string):
    message_id = int(b64_to_str(encoded_string))
    bot = await app.get_me()
    bot_username = bot.username
    to_send = await app.get_messages(chat_id=log_c, message_ids=message_id)
    file_id = to_send.document.file_id
    share_link = f"https://t.me/{bot_username}?start=pdfshare_{encoded_string}"
    return file_id, share_link


async def get_file_list(user_id):
    filelist = (
        os.listdir(f"Photos/{user_id}") if os.path.isdir(f"Photos/{user_id}") else []
    )
    return filelist
