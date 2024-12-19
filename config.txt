from os import getenv


API_ID = int(getenv("API_ID", "26850449"))
API_HASH = getenv("API_HASH", "72a730c380e68095a8549ad7341b0608")
BOT_TOKEN = getenv("BOT_TOKEN", "7022426709:AAGiFvBN5QmCFldWjT7LZo3IWj3ezDo4ycY")
OWNER_ID = list(map(int, getenv("OWNER_ID", "7091230649 6107581019").split()))
MONGO_DB = getenv("MONGO_DB", "mongodb+srv://restriction:5etQWbo745v2oNg2@cluster0.7dxrthz.mongodb.net/?retryWrites=true&w=majority")

CHANNEL_ID = int(getenv("CHANNEL_ID", "-1002405071668"))
PREMIUM_LOGS = int(getenv("PREMIUM_LOGS", "-1002192816506"))
