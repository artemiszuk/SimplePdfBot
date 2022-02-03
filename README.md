# SimplePdfBot
This is a Telegram bot to create pdf along with many other utils

* **Language:** [Python3](https://www.python.org)
* **Library:** [Pyrogram](https://docs.pyrogram.org)

### Features:
- In PM Just Forward or Send any photo(s) and on giving /done command it will return the combined photos as pdf.
- Compress pdf with api from [ilovePDF](https://developer.ilovepdf.com/).
- Authenticate and un-Authenticate users with mongodb support.
- Logging for all operations in LOG_CHANNEL
- InterConvert Ebooks with different file formats(Check Details Below ↓)
<details open>
<summary>Supported Input Formats :</summary>
<br>
[ azw, azw3, azw4, cbz, cbr, cb7, cbc, chm, djvu, docx, epub, fb2, fbz, html, htmlz, lit, lrf, mobi, odt, pdf, prc, pdb, pml, rb, rtf, snb, tcr, txt, txtz ]
</details>
<details open>
<summary>Supported Output Formats :</summary>
<br>
[ azw3, epub, docx, fb2, htmlz, oeb, lit, lrf, mobi, pdb, pmlz, rb, pdf, rtf, snb, tcr, txt, txtz, zip ]
</details>

## Configs:
- `API_ID` - Get this from [@TeleORG_Bot](https://t.me/TeleORG_Bot)
- `API_HASH` - Get this from [@TeleORG_Bot](https://t.me/TeleORG_Bot)
- `BOT_TOKEN` - Get this from [@BotFather](https://t.me/BotFather)
- `LOG_CHANNEL` - A Telegram Channel/Group ID.
	- Make a Channel for Logging . We will use that as Database. Channel must be Private! Else you will be Copyright by [Telegram DMCA](https://t.me/dmcatelegram)!
- `MONGO_URI` - MongoDB Database URI
	- This for Saving UserIDs. When you will Broadcast, bot will forward the Broadcast to DB Users.
- `ILOVEPDF_API` - To Compress pdf files get api from [ilovePDF](https://developer.ilovepdf.com/)

### Deploy Now:
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/artemiszuk/SimplePdfBot)

## Commands:
```
start - Check alive status
help - How to Use The Bot
filename - Set custom filename for your pdf's
count - count pages and delete photos
convert - interconvert file formats
compress - compress pdf 
done - start making pdf

