import os
import shutil
import img2pdf
import asyncio
import pymongo
import subprocess
from pyromod import listen
from pyrogram import Client, filters, errors, idle
from pyrogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)


class Var(object):
    AUTH_USERS = dict()
    filename = dict()


mongouri = os.environ.get("MONGO_URI")

myclient = pymongo.MongoClient(mongouri)
mydb = myclient["mydatabase"]
mycol = mydb["pdfbot"]
print(mydb.list_collection_names())
Var.AUTH_USERS = mycol.find_one()
print(Var.AUTH_USERS["users"])

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

#p = subprocess.Popen(["python3", "-m", "http.server"])
app = Client("account", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

print("Starting Bot")


class Messages:
    startm = "**📌MAIN MENU**\n\nHi ! This is PDF Bot \n\n__Click Help for how to use__"
    helpm = "I can convert images into pdf file. Send or Forward photos. When sending is completed click done button to get your PDF file\n\nSend /done when you are done sending all photos.\nTo check number of photos and delete photos just use /count \nTo Set Custom FileName use /filename"


class CustomFilters:
    auth_users = filters.create(
        lambda _, __, message: message.from_user.id in Var.AUTH_USERS["users"]
    )
    owner = filters.create(
        lambda _, __, message: str(message.from_user.id) in ["1645049777"]
    )


@app.on_callback_query()
async def button(client, cmd: CallbackQuery):
    cb_data = cmd.data
    if "help" in cb_data:
        await cmd.message.edit(
            Messages.helpm,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back ◀", callback_data="start")]]
            ),
        )
    elif "start" in cb_data:
        await cmd.message.edit(
            Messages.startm,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Help ❓", callback_data="help"),
                        InlineKeyboardButton("Close ❌", callback_data="close"),
                    ]
                ]
            ),
        )
    elif "close" in cb_data:
        await cmd.message.delete()

    elif "rmlast" in cb_data:
        user_id = cmd.from_user.id
        filelist = await get_file_list(user_id)
        last_photo = f"Photos/{user_id}/{filelist[-1]}"
        os.remove(last_photo)
        filelist = await get_file_list(user_id)
        count = len(filelist)
        msg = ""

        if count > 0:
            buttons_markup = []
            for file in filelist:
                msg += f"\n`🖼 {os.path.basename(file)}`"

            buttons_markup.append(
                [
                    InlineKeyboardButton(f"Close ❌", callback_data="close"),
                    InlineKeyboardButton(f"Remove Last 🗑", callback_data="rmlast"),
                ]
            )

            await cmd.message.edit(
                f"__Below Are list of photos sent by you__ 🔽\n{msg}",
                reply_markup=InlineKeyboardMarkup(buttons_markup),
            )
        else:
            await cmd.message.edit(f"Number of images from you : {count}")


@app.on_message(
    filters.command(["start"]) & (CustomFilters.auth_users | CustomFilters.owner)
)
async def start(client, message):
    await message.reply(
        Messages.startm,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Help ❓", callback_data="help"),
                    InlineKeyboardButton("Close ❌", callback_data="close"),
                ]
            ]
        ),
    )


def keyExists(user_id):
    x = mycol.find_one({"_id": user_id})
    if x is None:
        return False
    else:
        return True


@app.on_message(filters.command(["auth"]) & CustomFilters.owner)
async def auth(client, message):
    try:
        if len(message.text.split()) == 1:
            return await message.reply("ID Field Empty")
        id = int(message.text.split()[-1])
        if id in Var.AUTH_USERS["users"]:
            return await message.reply("User Already Authenticated !")
        myquery = {"_id": "1"}
        newvalues = {"$push": {"users": id}}
        mycol.update_one(myquery, newvalues)
        Var.AUTH_USERS = mycol.find_one({"_id": "1"})
        print("New list :", Var.AUTH_USERS["users"])
        await message.reply("User Authenticated")
    except Exception as e:
        await message.reply(str(e))


@app.on_message(filters.command(["unauth"]) & CustomFilters.owner)
async def auth(client, message):
    try:
        if len(message.text.split()) == 1:
            return await message.reply("ID Field Empty")
        id = int(message.text.split()[-1])
        if id in Var.AUTH_USERS["users"]:
            myquery = {"_id": "1"}
            newvalues = {"$pull": {"users": id}}
            mycol.update_one(myquery, newvalues)
            Var.AUTH_USERS = mycol.find_one({"_id": "1"})
            print("New list :", Var.AUTH_USERS["users"])
            await message.reply("User Un-Authenticated")
        else:
            return await message.reply("User does not exist")
    except Exception as e:
        await message.reply(str(e))


@app.on_message(
    filters.command(["help"]) & (CustomFilters.auth_users | CustomFilters.owner)
)
async def help(client, message):
    await start(client, message)


@app.on_message(
    (filters.photo | filters.document)
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def onphoto(client, message):
    if message.photo is None:
        exten = os.path.splitext(message.document.file_name)[1]
    if message.photo is None and exten not in (".jpg", ".jpeg"):
        print("Not a Photo")
        return
    await message.download(file_name=f"Photos/{message.from_user.id}/")


@app.on_message(
    filters.command(["filename"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def onname(client, message):
    print("filename")
    user_id = message.from_user.id
    namef = await app.ask(user_id, "__Enter FileName :__")
    await message.reply(f"Pdf Names will now be : __{namef.text}__")
    if keyExists(user_id):
        print("User filename exists")
        x = mycol.find_one({"_id": user_id})
        mycol.update_one({"_id": user_id}, {"$set": {"fname": namef.text}})
    else:
        print("User filename not exists")
        mycol.insert_one({"_id": user_id, "fname": namef.text})
    x = mycol.find_one({"_id": user_id})
    print("Filename for ", user_id, "=", x)
    Var.filename[user_id] = x["fname"]


@app.on_message(
    filters.command(["count"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def countfiles(client, message):
    bot_msg = await message.reply("__Checking ...__")
    await asyncio.sleep(2)
    user_id = message.from_user.id
    filelist = await get_file_list(user_id)
    count = len(filelist)
    buttons_markup = []
    msg = ""
    if count > 0:
        for file in filelist:
            msg += f"\n`🖼 {os.path.basename(file)}`"

        buttons_markup.append(
            [
                InlineKeyboardButton("Close ❌", callback_data="close"),
                InlineKeyboardButton(f"Remove Last 🗑", callback_data="rmlast"),
            ]
        )

        await bot_msg.edit(
            f"__Below Are list of photos sent by you__ 🔽\n{msg}",
            reply_markup=InlineKeyboardMarkup(buttons_markup),
        )
    else:
        await bot_msg.edit(f"Number of images from you : {count}")


async def get_file_list(user_id):
    filelist = (
        os.listdir(f"Photos/{user_id}") if os.path.isdir(f"Photos/{user_id}") else []
    )
    return filelist


@app.on_message(
    filters.command(["done"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def ondone(client, message):
    user_id = message.from_user.id
    bot_msg = await message.reply("__Checking__")
    if not os.path.isdir(f"Photos/{user_id}"):
        await bot_msg.edit("No Photos sent by you !")
        return
    flist = []
    if keyExists(user_id):
        x = mycol.find_one({"_id": user_id})
        pdfname = x["fname"]
        print(pdfname)
    else:
        pdfname = str(user_id)
    try:
        filelist = os.listdir(f"Photos/{user_id}")
        for file in filelist:
            flist.append(f"Photos/{user_id}/{file}")
        with open(f"{pdfname}.pdf", "wb") as f:
            f.write(img2pdf.convert([i for i in flist]))
    except Exception as e:
        print(e)
        await bot_msg.edit(str(e))
        os.remove(f"{pdfname}.pdf")
    else:
        await asyncio.sleep(3)
        await bot_msg.edit(f"Created Pdf with {len(flist)} files ")
        await asyncio.sleep(3)
        await bot_msg.edit("Uploading ...")
        await message.reply_document(f"{pdfname}.pdf", thumb=flist[0])
        await bot_msg.delete()
        os.remove(f"{pdfname}.pdf")
        shutil.rmtree(f"Photos/{user_id}/")


app.run()
print("Stopping Bot")
