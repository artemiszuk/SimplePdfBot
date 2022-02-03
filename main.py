import os
import sys
import shutil
import img2pdf
import asyncio
import traceback
from handlers.database import db
from pylovepdf.ilovepdf import ILovePdf
import subprocess
from pyromod import listen
from handlers.tools import str_to_b64, b64_to_str, retrieve, get_file_list
from pyrogram import Client, filters, errors, idle, errors
from pyrogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)


api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

# p = subprocess.Popen(["python3", "-m", "http.server"])
app = Client("account", api_id=api_id, api_hash=api_hash, bot_token=bot_token)




class Var(object):
    AUTH_USERS = []
    log_c = int(os.environ.get("LOG_CHANNEL"))
    pdf_api = os.environ.get("ILOVEPDF_API")
    owner = os.environ.get("OWNER_ID")

class Messages:
    startm = "**📌MAIN MENU**\n\nHi ! This is PDF Bot \n\n__Click Help for how to use__"
    helpm = "I can convert images into pdf file. Send or Forward photos. When sending is completed click done button to get your PDF file\n\nSend /done when you are done sending all photos.\nTo check number of photos and delete photos just use /count \nTo Set Custom FileName use /filename\n/compress : Reply to Pdf to compress [Uses api from ILovePdf]"


class CustomFilters:
    auth_users = filters.create(
        lambda _, __, message: message.from_user.id in Var.AUTH_USERS
    )
    owner = filters.create(
        lambda _, __, message: str(message.from_user.id) in ["1645049777"]
    )


async def init():
    await custom_logger("----------------Starting Bot-------------------")
    text = "\n-------------------------------------------"
    text += "\nInitializing User list"
    Var.AUTH_USERS = list(await db.get_all_users())
    text += f"\nAuthenticated Users List = {Var.AUTH_USERS}" 
    text += "\n-------------------------------------------"
    await custom_logger(text)

async def custom_logger(msg):
  sys.stdout.write(msg)
  await app.send_message(Var.log_c,f"`{msg}`")

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
    if "_" not in message.text:
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
    else:
        encoded_string = message.text.split("_")[-1]
        file_id, share_link = await retrieve(app, Var.log_c, encoded_string)
        await message.reply_document(
            file_id, caption=f"[(. ❛ ᴗ ❛.) Share Link 📝]({share_link})"
        )


@app.on_message(filters.command(["auth"]) & CustomFilters.owner)
async def auth(client, message):
    try:
        if len(message.text.split()) == 1:
            return await message.reply("ID Field Empty")
        id = int(message.text.split()[-1])
        if id in Var.AUTH_USERS:
            return await message.reply("User Already Authenticated !")
        await db.add_user(id)
        await init()
        await message.reply("User Authenticated")
    except Exception as e:
        await message.reply(str(e))


@app.on_message(filters.command(["unauth"]) & CustomFilters.owner)
async def auth(client, message):
    try:
        if len(message.text.split()) == 1:
            return await message.reply("ID Field Empty")
        id = int(message.text.split()[-1])
        if id in Var.AUTH_USERS:
            await db.delete_user(id)
            await init()
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
        sys.stdout.write("Not a Photo")
        return
    await message.download(file_name=f"Photos/{message.from_user.id}/")


@app.on_message(
    filters.command(["filename"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def onname(client, message):
    user_id = message.from_user.id
    namef = await app.ask(user_id, "__Enter FileName :__")
    await message.reply(f"**Pdf Names will now be :** __{namef.text}__")
    await db.update_fname(user_id, namef.text)
    x = await db.get_user_dict(user_id)
    sys.stdout.write("Filename for ", user_id, "=", x["fname"])


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


@app.on_message(
    filters.command(["compress"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def compress(client, message):
    user_id = message.from_user.id
    if message.reply_to_message is None:
        return await message.reply("**Reply to the pdf you want to compress...**")
    elif (message.reply_to_message.document is None) or (
        message.reply_to_message.document.file_name.endswith(".pdf") == False
    ):
        return await message.reply("**Not a pdf file ‼**")

    if os.path.isdir(f"Compressed/{user_id}") or os.path.isdir(f"Compress/{user_id}"):
        return await message.reply("Please wait for previous task.. ‼")

    if not os.path.isdir(f"Compressed/{user_id}"):
        os.makedirs(f"Compress/{user_id}")

    bot_msg = await message.reply("__Trying to Compress...__")
    try:
      doc_from_user = message.reply_to_message
      await doc_from_user.download(file_name=f"Compress/{user_id}/")
      ilovepdf = ILovePdf(Var.pdf_api, verify_ssl=True)
      task = ilovepdf.new_task("compress")
      task.add_file(f"Compress/{user_id}/{doc_from_user.document.file_name}")
      task.set_output_folder(f"Compressed/{user_id}")

      task.execute()
      task.download()
      await bot_msg.edit("__Compression Done...__")

    except errors.MessageNotModified:
      await bot_msg.edit("__Compression Done ...__")
      pass
    
    except Exception as e:
      await bot_msg.edit(str(e))
      pass
    
    flist = os.listdir(f"Compressed/{user_id}")
    doc = await app.send_document(Var.log_c, f"Compressed/{user_id}/{flist[-1]}")
    await doc.reply(
        f"__Pdf Compress Requested By [{message.from_user.first_name}](https://t.me/{message.from_user.username})__",
        disable_web_page_preview=True,
    )

    encoded_string = str_to_b64(str(doc.message_id))
    file_id, share_link = await retrieve(app, Var.log_c, encoded_string)
    await bot_msg.edit("__Uploading Now__...")
    await asyncio.sleep(1)
    await message.reply_document(
        file_id, caption=f"[(. ❛ ᴗ ❛.) Share Link 📝]({share_link})"
    )

    task.delete_current_task()
    await bot_msg.delete()
    shutil.rmtree(f"Compress/{user_id}")
    shutil.rmtree(f"Compressed/{user_id}")
    


@app.on_message(
    filters.command(["done"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def ondone(client, message):
    user_id = message.from_user.id
    bot_msg = await message.reply("__Checking...__")
    await asyncio.sleep(3)
    if not os.path.isdir(f"Photos/{user_id}"):
        await bot_msg.edit("No Photos sent by you !")
        return
    flist = []
    x = await db.get_user_dict(user_id)
    pdfname = x["fname"]
    pdfpath = f"{user_id}/{pdfname}.pdf"

    if not os.path.isdir(str(user_id)):
        os.makedirs(str(user_id))

    try:
        filelist = os.listdir(f"Photos/{user_id}")
        for file in filelist:
            flist.append(f"Photos/{user_id}/{file}")
        with open(f"{pdfpath}", "wb") as f:
            f.write(img2pdf.convert([i for i in flist]))
    except Exception :
        await custom_logger(traceback.format_exc())
        shutil.rmtree(str(user_id))
    else:
        await bot_msg.edit(f"Created Pdf with {len(flist)} files ")
        await asyncio.sleep(3)
        await bot_msg.edit("Uploading ...")
        doc = await app.send_document(
            Var.log_c,
            pdfpath,
            thumb=flist[0],
        )
        await doc.reply(
            f"__Pdf Requested By [{message.from_user.first_name}](https://t.me/{message.from_user.username})__",
            disable_web_page_preview=True,
        )

        encoded_string = str_to_b64(str(doc.message_id))
        file_id, share_link = await retrieve(app, Var.log_c, encoded_string)
        await asyncio.sleep(1)
        await message.reply_document(
            file_id, caption=f"[(. ❛ ᴗ ❛.) Share Link 📝]({share_link})"
        )
        await bot_msg.delete()
        shutil.rmtree(str(user_id))
        shutil.rmtree(f"Photos/{user_id}/")

@app.on_message(
    filters.command(["convert"])
    & filters.private
    & (CustomFilters.auth_users | CustomFilters.owner)
)
async def onconvert(client, message):
    sys.stdout.write(os.getcwd())
    user_id = message.from_user.id
    input_formats = ["azw","azw3", "azw4", "cbz", "cbr", "cb7", "cbc", "chm", "djvu", "docx", "epub", "fb2", "fbz", "html", "htmlz", "lit", "lrf", "mobi", "odt", "pdf", "prc", "pdb", "pml", "rb", "rtf", "snb", "tcr", "txt", "txtz"]
    output_formats = ['azw3', 'epub', 'docx', 'fb2', 'htmlz', 'oeb', 'lit', 'lrf', 'mobi', 'pdb', 'pmlz', 'rb', 'pdf', 'rtf', 'snb', 'tcr', 'txt', 'txtz', 'zip']
    
    if os.path.isdir(f"Convert/{user_id}"):
        return await message.reply("**Wait Until Previous TAsk finishes ‼**")

    if message.reply_to_message is None:
        return await message.reply(f"**Reply `/convert format` to the file you want to convert\n\nList Of Input Formats **:\n`[ {', '.join(map(str,input_formats))} ]`\n\n **List Of Output Formats** : \n`[ {', '.join(map(str,output_formats))} ]`")
    elif (message.reply_to_message.document is None) or (
        os.path.splitext(message.reply_to_message.document.file_name)[-1][1:] not in input_formats
    ):
        return await message.reply("**Not a Valid Input file ‼**")
    elif (len(message.text.split()) != 2 or message.text.split()[1] not in output_formats):
        return await message.reply("**Not a Valid Command  ‼**")
    exten = message.text.split()[1]

    if exten == os.path.splitext(message.reply_to_message.document.file_name)[-1][1:]:
        return await message.reply("**Output Format Cannot be Same ‼**")
    out_path = ""
    bot_msg = await message.reply(f"__Trying to convert to {exten} 📝...__")
    doc = message.reply_to_message
    try:
        out_path = f"Convert/{user_id}/"
        await doc.download(file_name=out_path)
        
        flist = os.listdir(out_path)
        out_file = os.path.splitext(flist[-1])[0] + f".{exten}"
        command_to_exec = f"cd {out_path} ; ebook-convert '{flist[-1]}' '{out_file}' ;"
        sys.stdout.write(command_to_exec)
        proc = await asyncio.create_subprocess_shell(command_to_exec)
        await proc.wait()
        
        out_path += out_file
    except Exception as e :
        await bot_msg.edit(str(e))
    #print(out_path)
    await bot_msg.edit("Uploading 📤...")
    doc = await app.send_document(
            Var.log_c,
            out_path
        )
    await doc.reply(
            f"__{exten} Conversion Requested By [{message.from_user.first_name}](https://t.me/{message.from_user.username})__",
            disable_web_page_preview=True,
        )
    encoded_string = str_to_b64(str(doc.message_id))
    file_id, share_link = await retrieve(app, Var.log_c, encoded_string)
    await asyncio.sleep(1)
    await message.reply_document(
        file_id, caption=f"[(. ❛ ᴗ ❛.) Share Link 📝]({share_link})"
    )
    await bot_msg.delete()
    shutil.rmtree(f"Convert/{user_id}/")



app.start()
asyncio.ensure_future(init())
idle()
#await custom_logger("----------------Stopping Bot------------------")
app.stop()