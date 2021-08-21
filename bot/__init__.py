import logging
import os
import threading
import time
import random
import string
import subprocess

import aria2p
import telegram.ext as tg
from dotenv import load_dotenv
from pyrogram import Client
from telegraph import Telegraph

import psycopg2
from psycopg2 import Error

import socket
import faulthandler
faulthandler.enable()

socket.setdefaulttimeout(600)

botStartTime = time.time()
if os.path.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],
                    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

load_dotenv('config.env')

Interval = []


def getConfig(name: str):
    return os.environ[name]

def mktable():
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        sql = "CREATE TABLE users (uid bigint, sudo boolean DEFAULT FALSE);"
        cur.execute(sql)
        conn.commit()
        LOGGER.info("Table Created!")
    except Error as e:
        LOGGER.error(e)
        exit(1)

try:
    if bool(getConfig('_____REMOVE_THIS_LINE_____')):
        logging.error('The README.md file there to be read! Exiting now!')
        exit()
except KeyError:
    pass

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret="",
    )
)

DOWNLOAD_DIR = None
BOT_TOKEN = None

download_dict_lock = threading.Lock()
status_reply_dict_lock = threading.Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}
# Stores list of users and chats the bot is authorized to use in
AUTHORIZED_CHATS = set()
SUDO_USERS = set()
if os.path.exists('authorized_chats.txt'):
    with open('authorized_chats.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            AUTHORIZED_CHATS.add(int(line.split()[0]))
if os.path.exists('sudo_users.txt'):
    with open('sudo_users.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            SUDO_USERS.add(int(line.split()[0]))
try:
    achats = getConfig('AUTHORIZED_CHATS')
    achats = achats.split(" ")
    for chats in achats:
        AUTHORIZED_CHATS.add(int(chats))
except:
    pass
try:
    schats = getConfig('SUDO_USERS')
    schats = schats.split(" ")
    for chats in schats:
        SUDO_USERS.add(int(chats))
except:
    pass
try:
    BOT_TOKEN = getConfig('BOT_TOKEN')
    parent_id = getConfig('GDRIVE_FOLDER_ID')
    DOWNLOAD_STATUS_UPDATE_INTERVAL = int(getConfig('DOWNLOAD_STATUS_UPDATE_INTERVAL'))
    OWNER_ID = int(getConfig('OWNER_ID'))
    AUTO_DELETE_MESSAGE_DURATION = int(getConfig('AUTO_DELETE_MESSAGE_DURATION'))
    TELEGRAM_API = getConfig('TELEGRAM_API')
    TELEGRAM_HASH = getConfig('TELEGRAM_HASH')
    UPSTREAM_REPO = getConfig('UPSTREAM_REPO')
    UPSTREAM_BRANCH = getConfig('UPSTREAM_BRANCH')
    
except KeyError as e:
    LOGGER.error("One or more env variables missing! Exiting now")
    exit(1)
try:
    DB_URI = getConfig('DATABASE_URL')
    if len(DB_URI) == 0:
        raise KeyError
except KeyError:
    logging.warning('Database not provided!')
    DB_URI = None
if DB_URI is not None:
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        sql = "SELECT * from users;"
        cur.execute(sql)
        rows = cur.fetchall()  #returns a list ==> (uid, sudo)
        for row in rows:
            AUTHORIZED_CHATS.add(row[0])
            if row[1]:
                SUDO_USERS.add(row[0])
    except Error as e:
        if 'relation "users" does not exist' in str(e):
            mktable()
        else:
            LOGGER.error(e)
            exit(1)
    finally:
        cur.close()
        conn.close()

LOGGER.info("Generating USER_SESSION_STRING")
app = Client(':memory:', api_id=int(TELEGRAM_API), api_hash=TELEGRAM_HASH, bot_token=BOT_TOKEN)

#Generate Telegraph Token
sname = ''.join(random.SystemRandom().choices(string.ascii_letters, k=8))
LOGGER.info("Generating TELEGRAPH_TOKEN using '" + sname + "' name")
telegraph = Telegraph()
telegraph.create_account(short_name=sname)
telegraph_token = telegraph.get_access_token()

try:
    STATUS_LIMIT = getConfig('STATUS_LIMIT')
    if len(STATUS_LIMIT) == 0:
        raise KeyError
    else:
        STATUS_LIMIT = int(getConfig('STATUS_LIMIT'))
except KeyError:
    STATUS_LIMIT = None
try:
    MEGA_API_KEY = getConfig('MEGA_API_KEY')
except KeyError:
    logging.warning('MEGA API KEY not provided!')
    MEGA_API_KEY = None
try:
    MEGA_EMAIL_ID = getConfig('MEGA_EMAIL_ID')
    MEGA_PASSWORD = getConfig('MEGA_PASSWORD')
    if len(MEGA_EMAIL_ID) == 0 or len(MEGA_PASSWORD) == 0:
        raise KeyError
except KeyError:
    logging.warning('MEGA Credentials not provided!')
    MEGA_EMAIL_ID = None
    MEGA_PASSWORD = None
try:
    HEROKU_API_KEY = getConfig('HEROKU_API_KEY')
except KeyError:
    logging.warning('HEROKU API KEY not provided!')
    HEROKU_API_KEY = None
try:
    HEROKU_APP_NAME = getConfig('HEROKU_APP_NAME')
except KeyError:
    logging.warning('HEROKU APP NAME not provided!')
    HEROKU_APP_NAME = None
try:
    UPTOBOX_TOKEN = getConfig('UPTOBOX_TOKEN')
except KeyError:
    logging.warning('UPTOBOX_TOKEN not provided!')
    UPTOBOX_TOKEN = None
try:
    INDEX_URL = getConfig('INDEX_URL')
    if len(INDEX_URL) == 0:
        INDEX_URL = None
except KeyError:
    INDEX_URL = None
try:
    TORRENT_DIRECT_LIMIT = getConfig('TORRENT_DIRECT_LIMIT')
    if len(TORRENT_DIRECT_LIMIT) == 0:
        TORRENT_DIRECT_LIMIT = None
except KeyError:
    TORRENT_DIRECT_LIMIT = None
try:
    CLONE_LIMIT = getConfig('CLONE_LIMIT')
    if len(CLONE_LIMIT) == 0:
        CLONE_LIMIT = None
except KeyError:
    CLONE_LIMIT = None
try:
    MEGA_LIMIT = getConfig('MEGA_LIMIT')
    if len(MEGA_LIMIT) == 0:
        MEGA_LIMIT = None
except KeyError:
    MEGA_LIMIT = None
try:
    TAR_UNZIP_LIMIT = getConfig('TAR_UNZIP_LIMIT')
    if len(TAR_UNZIP_LIMIT) == 0:
        TAR_UNZIP_LIMIT = None
except KeyError:
    TAR_UNZIP_LIMIT = None
try:
    BUTTON_FOUR_NAME = getConfig('BUTTON_FOUR_NAME')
    BUTTON_FOUR_URL = getConfig('BUTTON_FOUR_URL')
    if len(BUTTON_FOUR_NAME) == 0 or len(BUTTON_FOUR_URL) == 0:
        raise KeyError
except KeyError:
    BUTTON_FOUR_NAME = None
    BUTTON_FOUR_URL = None
try:
    BUTTON_FIVE_NAME = getConfig('BUTTON_FIVE_NAME')
    BUTTON_FIVE_URL = getConfig('BUTTON_FIVE_URL')
    if len(BUTTON_FIVE_NAME) == 0 or len(BUTTON_FIVE_URL) == 0:
        raise KeyError
except KeyError:
    BUTTON_FIVE_NAME = None
    BUTTON_FIVE_URL = None
try:
    BUTTON_SIX_NAME = getConfig('BUTTON_SIX_NAME')
    BUTTON_SIX_URL = getConfig('BUTTON_SIX_URL')
    if len(BUTTON_SIX_NAME) == 0 or len(BUTTON_SIX_URL) == 0:
        raise KeyError
except KeyError:
    BUTTON_SIX_NAME = None
    BUTTON_SIX_URL = None
try:
    STOP_DUPLICATE = getConfig('STOP_DUPLICATE')
    if STOP_DUPLICATE.lower() == 'true':
        STOP_DUPLICATE = True
    else:
        STOP_DUPLICATE = False
except KeyError:
    STOP_DUPLICATE = False
try:
    VIEW_LINK = getConfig('VIEW_LINK')
    if VIEW_LINK.lower() == 'true':
        VIEW_LINK = True
    else:
        VIEW_LINK = False
except KeyError:
    VIEW_LINK = False
try:
    IS_TEAM_DRIVE = getConfig('IS_TEAM_DRIVE')
    if IS_TEAM_DRIVE.lower() == 'true':
        IS_TEAM_DRIVE = True
    else:
        IS_TEAM_DRIVE = False
except KeyError:
    IS_TEAM_DRIVE = False
try:
    USE_SERVICE_ACCOUNTS = getConfig('USE_SERVICE_ACCOUNTS')
    if USE_SERVICE_ACCOUNTS.lower() == 'true':
        USE_SERVICE_ACCOUNTS = True
    else:
        USE_SERVICE_ACCOUNTS = False
except KeyError:
    USE_SERVICE_ACCOUNTS = False
try:
    BLOCK_MEGA_FOLDER = getConfig('BLOCK_MEGA_FOLDER')
    if BLOCK_MEGA_FOLDER.lower() == 'true':
        BLOCK_MEGA_FOLDER = True
    else:
        BLOCK_MEGA_FOLDER = False
except KeyError:
    BLOCK_MEGA_FOLDER = False
try:
    BLOCK_MEGA_LINKS = getConfig('BLOCK_MEGA_LINKS')
    if BLOCK_MEGA_LINKS.lower() == 'true':
        BLOCK_MEGA_LINKS = True
    else:
        BLOCK_MEGA_LINKS = False
except KeyError:
    BLOCK_MEGA_LINKS = False
try:
    SHORTENER = getConfig('SHORTENER')
    SHORTENER_API = getConfig('SHORTENER_API')
    if len(SHORTENER) == 0 or len(SHORTENER_API) == 0:
        raise KeyError
except KeyError:
    SHORTENER = None
    SHORTENER_API = None

IGNORE_PENDING_REQUESTS = False
try:
    if getConfig("IGNORE_PENDING_REQUESTS").lower() == "true":
        IGNORE_PENDING_REQUESTS = True
except KeyError:
    pass
try:
    FINISHED_PROGRESS_STR = getConfig('FINISHED_PROGRESS_STR')
    if len(FINISHED_PROGRESS_STR) == 0:
        FINISHED_PROGRESS_STR = '●'
except KeyError:
    FINISHED_PROGRESS_STR = '●'
try:
    UNFINISHED_PROGRESS_STR = getConfig('UNFINISHED_PROGRESS_STR')
    if len(UNFINISHED_PROGRESS_STR) == 0:
        UNFINISHED_PROGRESS_STR = '○'
except KeyError:
    UNFINISHED_PROGRESS_STR = '○'
try:
    TIMEZONE = getConfig('TIMEZONE')
    if len(TIMEZONE) == 0:
        TIMEZONE = None
except KeyError:
    TIMEZONE = 'Asia/Kuala_Lumpur'
try:
    TOKEN_PICKLE_URL = getConfig('TOKEN_PICKLE_URL')
    if len(TOKEN_PICKLE_URL) == 0:
        TOKEN_PICKLE_URL = None
    else:
        out = subprocess.run(["wget", "-q", "-O", "token.pickle", TOKEN_PICKLE_URL])
        if out.returncode != 0:
            logging.error(out)
except KeyError:
    TOKEN_PICKLE_URL = None

try:
    ACCOUNTS_ZIP_URL = getConfig('ACCOUNTS_ZIP_URL')
    if len(ACCOUNTS_ZIP_URL) == 0:
        ACCOUNTS_ZIP_URL = None
    else:
        out = subprocess.run(["wget", "-q", "-O", "accounts.zip", ACCOUNTS_ZIP_URL])
        if out.returncode != 0:
            logging.error(out)
            raise KeyError
        subprocess.run(["unzip", "-q", "-o", "accounts.zip"])
        os.remove("accounts.zip")
except KeyError:
    ACCOUNTS_ZIP_URL = None

try:
    RESTARTED_GROUP_ID2 = getConfig('RESTARTED_GROUP_ID2')
    if len(RESTARTED_GROUP_ID2) == 0:
        RESTARTED_GROUP_ID2 = None
except KeyError:
    RESTARTED_GROUP_ID2 = '-1001437939580'

try:
    RESTARTED_GROUP_ID = getConfig('RESTARTED_GROUP_ID')
    if len(RESTARTED_GROUP_ID) == 0:
        RESTARTED_GROUP_ID = None
except KeyError:
    RESTARTED_GROUP_ID = '-1001437939580'

try:
    START_BOT = getConfig('START_BOT')
    if len(START_BOT) == 0:
        START_BOT = None
except KeyError:
    START_BOT = 'start'

try:
    MIRROR_BOT = getConfig('MIRROR_BOT')
    if len(MIRROR_BOT) == 0:
        MIRROR_BOT = None
except KeyError:
    MIRROR_BOT = 'mirror'

try:
    UNZIP_BOT = getConfig('UNZIP_BOT')
    if len(UNZIP_BOT) == 0:
        UNZIP_BOT = None
except KeyError:
    UNZIP_BOT = 'unzip'

try:
    TARMIR_BOT = getConfig('TARMIR_BOT')
    if len(TARMIR_BOT) == 0:
        TARMIR_BOT = None
except KeyError:
    TARMIR_BOT = 'tarmir'

try:
    CANCEL_BOT = getConfig('CANCEL_BOT')
    if len(CANCEL_BOT) == 0:
        CANCEL_BOT = None
except KeyError:
    CANCEL_BOT = 'cancel'

try:
    CANCEL_ALL_BOT = getConfig('CANCEL_ALL_BOT')
    if len(CANCEL_ALL_BOT) == 0:
        CANCEL_ALL_BOT = None
except KeyError:
    CANCEL_ALL_BOT = 'cancelall'

try:
    LIST_BOT = getConfig('LIST_BOT')
    if len(LIST_BOT) == 0:
        LIST_BOT = None
except KeyError:
    LIST_BOT = 'list'

try:
    STATUS_BOT = getConfig('STATUS_BOT')
    if len(STATUS_BOT) == 0:
        STATUS_BOT = None
except KeyError:
    STATUS_BOT = 'status'

try:
    USERS_BOT = getConfig('USERS_BOT')
    if len(USERS_BOT) == 0:
        USERS_BOT = None
except KeyError:
    USERS_BOT = 'users'

try:
    AUTH_BOT = getConfig('AUTH_BOT')
    if len(AUTH_BOT) == 0:
        AUTH_BOT = None
except KeyError:
    AUTH_BOT = 'auth'

try:
    UNAUTH_BOT = getConfig('UNAUTH_BOT')
    if len(UNAUTH_BOT) == 0:
        UNAUTH_BOT = None
except KeyError:
    UNAUTH_BOT = 'unauth'

try:
    ADDSUDO_BOT = getConfig('ADDSUDO_BOT')
    if len(ADDSUDO_BOT) == 0:
        ADDSUDO_BOT = None
except KeyError:
    ADDSUDO_BOT = 'addsudo'

try:
    RMSUDO_BOT = getConfig('RMSUDO_BOT')
    if len(RMSUDO_BOT) == 0:
        RMSUDO_BOT = None
except KeyError:
    RMSUDO_BOT = 'rmsudo'

try:
    PING_BOT = getConfig('PING_BOT')
    if len(PING_BOT) == 0:
        PING_BOT = None
except KeyError:
    PING_BOT = 'ping'

try:
    RESTART_BOT = getConfig('RESTART_BOT')
    if len(RESTART_BOT) == 0:
        RESTART_BOT = None
except KeyError:
    RESTART_BOT = 'restart'

try:
    STATS_BOT = getConfig('STATS_BOT')
    if len(STATS_BOT) == 0:
        STATS_BOT = None
except KeyError:
    STATS_BOT = 'stats'

try:
    HELP_BOT = getConfig('HELP_BOT')
    if len(HELP_BOT) == 0:
        HELP_BOT = None
except KeyError:
    HELP_BOT = 'help'

try:
    LOG_BOT = getConfig('LOG_BOT')
    if len(LOG_BOT) == 0:
        LOG_BOT = None
except KeyError:
    LOG_BOT = 'logs'

try:
    SPEEDTEST_BOT = getConfig('SPEEDTEST_BOT')
    if len(SPEEDTEST_BOT) == 0:
        SPEEDTEST_BOT = None
except KeyError:
    SPEEDTEST_BOT = 'speedtest'

try:
    CLONE_BOT = getConfig('CLONE_BOT')
    if len(CLONE_BOT) == 0:
        CLONE_BOT = None
except KeyError:
    CLONE_BOT = 'clone'

try:
    COUNT_BOT = getConfig('COUNT_BOT')
    if len(COUNT_BOT) == 0:
        COUNT_BOT = None
except KeyError:
    COUNT_BOT = 'count'

try:
    YTDL_BOT = getConfig('YTDL_BOT')
    if len(YTDL_BOT) == 0:
        YTDL_BOT = None
except KeyError:
    YTDL_BOT = 'ytdl'

try:
    DELETE_BOT = getConfig('DELETE_BOT')
    if len(DELETE_BOT) == 0:
        DELETE_BOT = None
except KeyError:
    DELETE_BOT = 'delete'

try:
    TARYTDL_BOT = getConfig('TARYTDL_BOT')
    if len(TARYTDL_BOT) == 0:
        TARYTDL_BOT = None
except KeyError:
    TARYTDL_BOT = 'tarytdl'

try:
    USAGE_BOT = getConfig('USAGE_BOT')
    if len(USAGE_BOT) == 0:
        USAGE_BOT = None
except KeyError:
    USAGE_BOT = 'usage'

try:
    TARYTDL_BOT = getConfig('TARYTDL_BOT')
    if len(TARYTDL_BOT) == 0:
        TARYTDL_BOT = None
except KeyError:
    TARYTDL_BOT = 'tarytdl'

try:
    MEDIAINFO_BOT = getConfig('MEDIAINFO_BOT')
    if len(MEDIAINFO_BOT) == 0:
        MEDIAINFO_BOT = None
except KeyError:
    MEDIAINFO_BOT = 'mediainfo'

try:
    CONFIG_BOT = getConfig('CONFIG_BOT')
    if len(CONFIG_BOT) == 0:
        CONFIG_BOT = None
except KeyError:
    CONFIG_BOT = 'config'

try:
    SHELL_BOT = getConfig('SHELL_BOT')
    if len(SHELL_BOT) == 0:
        SHELL_BOT = None
except KeyError:
    SHELL_BOT = 'shell'

try:
    UPDATE_BOT = getConfig('UPDATE_BOT')
    if len(UPDATE_BOT) == 0:
        UPDATE_BOT = None
except KeyError:
    UPDATE_BOT = 'update'

try:
    EXEHELP_BOT = getConfig('EXEHELP_BOT')
    if len(EXEHELP_BOT) == 0:
        EXEHELP_BOT = None
except KeyError:
    EXEHELP_BOT = 'exehelp'

try:
    TSHELP_BOT = getConfig('TSHELP_BOT')
    if len(TSHELP_BOT) == 0:
        TSHELP_BOT = None
except KeyError:
    TSHELP_BOT = 'tshelp'

try:
    INDEX_BUTTON = getConfig('INDEX_BUTTON')
    if len(INDEX_BUTTON) == 0:
        INDEX_BUTTON = None
except KeyError:
    INDEX_BUTTON = '⚡ Index Link ⚡'

try:
    BOT_USERNAME = getConfig('BOT_USERNAME')
    if len(BOT_USERNAME) == 0:
        BOT_USERNAME = None
except KeyError:
    BOT_USERNAME = '@mirrorbot'

try:
    BOT_NAME = getConfig('BOT_NAME')
    if len(BOT_NAME) == 0:
        BOT_NAME = None
except KeyError:
    BOT_NAME = 'Mirror Bot'

try:
    BOT_USERNAME = getConfig('BOT_USERNAME')
    if len(BOT_USERNAME) == 0:
        BOT_USERNAME = None
except KeyError:
    BOT_USERNAME = '@mirrorbot'

try:
    CHANNEL_LINK = getConfig('CHANNEL_LINK')
    if len(CHANNEL_LINK) == 0:
        CHANNEL_LINK = None
except KeyError:
    CHANNEL_LINK = 'https://t.me/AnimeRepublic74'

try:
    SUPPORT_LINK = getConfig('SUPPORT_LINK')
    if len(SUPPORT_LINK) == 0:
        SUPPORT_LINK = None
except KeyError:
    SUPPORT_LINK = 'https://t.me/AnimeRepublicMLR'

try:
    GD_INFO = getConfig('GD_INFO')
    if len(GD_INFO) == 0:
        GD_INFO = None
except KeyError:
    GD_INFO = 'Uploaded by Mirrorbot'

try:
    ORDER_SORT = getConfig('ORDER_SORT')
    if len(ORDER_SORT) == 0:
        ORDER_SORT = None
except KeyError:
    ORDER_SORT = 'modifiedTime desc'

try:
    GD_BUTTON = getConfig('GD_BUTTON')
    if len(GD_BUTTON) == 0:
        GD_BUTTON = None
except KeyError:
    GD_BUTTON = '☁️ Google Drive ☁️'

try:
    INDEX_BUTTON = getConfig('INDEX_BUTTON')
    if len(INDEX_BUTTON) == 0:
        INDEX_BUTTON = None
except KeyError:
    INDEX_BUTTON = '⚡ Index Link ⚡'

try:
    VIEW_BUTTON = getConfig('VIEW_BUTTON')
    if len(VIEW_BUTTON) == 0:
        VIEW_BUTTON = None
except KeyError:
    VIEW_BUTTON = '🌐 View Link 🌐'

try:
    TITLE_NAME = getConfig('TITLE_NAME')
    if len(TITLE_NAME) == 0:
        TITLE_NAME = None
except KeyError:
    TITLE_NAME = 'List Downloaded'

try:
    AUTHOR_NAME = getConfig('AUTHOR_NAME')
    if len(AUTHOR_NAME) == 0:
        AUTHOR_NAME = None
except KeyError:
    AUTHOR_NAME = 'Mirror Bot'

try:
    AUTHOR_URL = getConfig('AUTHOR_URL')
    if len(AUTHOR_URL) == 0:
        AUTHOR_URL = None
except KeyError:
    AUTHOR_URL = ''

try:
    TELEGRAPH_DRIVE = getConfig('TELEGRAPH_DRIVE')
    if len(TELEGRAPH_DRIVE) == 0:
        TELEGRAPH_DRIVE = None
except KeyError:
    TELEGRAPH_DRIVE = 'DRIVE'

try:
    TELEGRAPH_INDEX = getConfig('TELEGRAPH_INDEX')
    if len(TELEGRAPH_INDEX) == 0:
        TELEGRAPH_INDEX = None
except KeyError:
    TELEGRAPH_INDEX = 'INDEX'

try:
    TELEGRAPH_VIEW = getConfig('TELEGRAPH_VIEW')
    if len(TELEGRAPH_VIEW) == 0:
        TELEGRAPH_VIEW = None
except KeyError:
    TELEGRAPH_VIEW = 'VIEW LINK'

try:
    SEARCH_VIEW_BUTTON = getConfig('SEARCH_VIEW_BUTTON')
    if len(SEARCH_VIEW_BUTTON) == 0:
        SEARCH_VIEW_BUTTON = None
except KeyError:
    SEARCH_VIEW_BUTTON = '🔎'

try:
    IMAGE_URL = getConfig('IMAGE_URL')
    if len(IMAGE_URL) == 0:
        IMAGE_URL = None
except KeyError:
    IMAGE_URL = 'https://telegra.ph/file/2757eec44b96e6be35e26.jpg'

try:
    ZIP_BOT = getConfig('ZIP_BOT')
    if len(ZIP_BOT) == 0:
        ZIP_BOT = None
except KeyError:
    ZIP_BOT = 'zip'

try:
    DOWNLOAD_DIR = getConfig('DOWNLOAD_DIR')
    if len(DOWNLOAD_DIR) == 0:
        DOWNLOAD_DIR = None
except KeyError:
    DOWNLOAD_DIR = '/usr/src/app/downloads/'

updater = tg.Updater(token=BOT_TOKEN)
bot = updater.bot
dispatcher = updater.dispatcher
