# ------------------------------------------------ #
# Plugin Name           : BasicTelegramAirdropBot  #
# Author Name           : Rubiel G. Labarta        #
# File Name             : main.py                  #
# ------------------------------------------------ #

import re
import ssl
from io import BytesIO
from time import gmtime, strftime

import pymysql
import telebot
from aiohttp import web
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import config

WEBHOOK_HOST = config.host
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port needs to be 'open')
WEBHOOK_LISTEN = "0.0.0.0"  # In some VPS you may need to put here the IP addr.

WEBHOOK_SSL_CERT = "./webhook_cert.pem"  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = "./webhook_pkey.pem"  # Path to the ssl private key

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(config.api_token)

bot = telebot.TeleBot(config.api_token)

app = web.Application()


def get_connection():
    connection = pymysql.connect(
        host=config.mysql_host,
        user=config.mysql_user,
        password=config.mysql_pw,
        db=config.mysql_db,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return connection


def create_tables():
    connection = get_connection()
    with connection.cursor() as cursor:
        table_name = "users"
        try:
            cursor.execute(
                "	CREATE TABLE `"
                + table_name
                + "` ( `user_id` int(12) DEFAULT NULL,  `address` varchar(42) DEFAULT NULL,  `address_change_status` tinyint DEFAULT 0,  `captcha` tinyint DEFAULT NULL )"
            )
            print("Database tables created.")
            return create_tables
        except:
            pass


def get_airdrop_wallets():
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "SELECT address FROM users WHERE address IS NOT NULL"
        cursor.execute(sql)
        tmp = []
        for user in cursor.fetchall():
            tmp.append(user["address"])
        return tmp


def get_airdrop_users():
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "SELECT user_id FROM users WHERE address IS NOT NULL"
        cursor.execute(sql)
        tmp = []
        for user in cursor.fetchall():
            tmp.append(user["user_id"])
        return tmp


default_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
default_keyboard.row(types.KeyboardButton("🚀 Join Airdrop"))

airdrop_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
airdrop_keyboard.row(types.KeyboardButton("💼 View Wallet Address"))


def cancel_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Cancel Operation", callback_data="cancel_input"))
    return markup


def update_wallet_address_button(message):
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "SELECT address_change_status FROM users WHERE user_id = %s"
        cursor.execute(sql, message.chat.id)
        address_changes = cursor.fetchone()["address_change_status"]
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                f"Update Address ({address_changes}/{config.wallet_changes})",
                callback_data="edit_wallet_address",
            )
        )
        return markup


@bot.message_handler(
    func=lambda message: message.chat.type == "private", commands=["start"]
)
def handle_text(message):
    connection = get_connection()
    with connection.cursor() as cursor:
        bot.send_chat_action(message.chat.id, "typing")
        sql = "SELECT EXISTS(SELECT user_id FROM users WHERE user_id = %s)"
        cursor.execute(sql, message.chat.id)
        result = cursor.fetchone()
        if not list(result.values())[0]:
            sql = "INSERT INTO users(user_id) VALUES (%s)"
            cursor.execute(sql, message.chat.id)
        if message.chat.id in airdrop_users:
            bot.send_message(
                message.chat.id,
                config.texts["start_2"].format(message.from_user.first_name)
                + "[» Source Code](https://github.com/fabston/Telegram-Airdrop-Bot).",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=airdrop_keyboard,
            )
        elif not config.airdrop_live:
            bot.send_message(
                message.chat.id,
                config.texts["airdrop_start"]
                + "[» Source Code](https://github.com/fabston/Telegram-Airdrop-Bot).",
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        elif len(airdrop_users) >= config.airdrop_cap:
            bot.send_message(
                message.chat.id,
                config.texts["airdrop_max_cap"]
                + "[» Source Code](https://github.com/fabston/Telegram-Airdrop-Bot).",
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        else:
            bot.send_message(
                message.chat.id,
                config.texts["start_1"].format(message.from_user.first_name)
                + "[» Source Code](https://github.com/fabston/Telegram-Airdrop-Bot).",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=default_keyboard,
            )


@bot.message_handler(
    func=lambda message: message.chat.type == "private"
    and message.from_user.id not in airdrop_users
    and message.text == "🚀 Join Airdrop"
)
def handle_text(message):
    bot.send_chat_action(message.chat.id, "typing")
    if not config.airdrop_live:
        bot.send_message(
            message.chat.id,
            config.texts["airdrop_start"],
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    else:
        if len(airdrop_users) >= config.airdrop_cap:
            bot.send_message(
                message.chat.id,
                config.texts["airdrop_max_cap"],
                parse_mode="Markdown",
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
        else:
            bot.send_message(
                message.chat.id,
                config.texts["airdrop_address"],
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
            bot.register_next_step_handler(message, address_check)


@bot.message_handler(
    func=lambda message: message.chat.type == "private"
    and message.from_user.id in airdrop_users
    and message.text == "💼 View Wallet Address"
)
def handle_text(message):
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "SELECT address FROM users WHERE user_id = %s"
        cursor.execute(sql, message.chat.id)
        data = cursor.fetchall()
        bot.send_message(
            message.chat.id,
            text="Your tokens will be sent to:\n\n`{0}`".format(data[0]["address"]),
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=update_wallet_address_button(message),
        )


def address_check(message):
    bot.send_chat_action(message.chat.id, "typing")
    connection = get_connection()
    with connection.cursor() as cursor:
        if len(airdrop_users) >= config.airdrop_cap:
            bot.send_message(
                message.chat.id, config.texts["airdrop_max_cap"], parse_mode="Markdown"
            )
            bot.clear_step_handler(message)
        elif message.text in airdrop_wallets:
            msg = bot.reply_to(
                message,
                config.texts["airdrop_walletused"],
                parse_mode="Markdown",
                reply_markup=cancel_button(),
            )
            bot.register_next_step_handler(msg, address_check)
        elif message.content_type == "text" and re.match(
            r"^(?=.{42}$).*", message.text
        ):
            sql = "UPDATE users SET address = %s WHERE user_id = %s"
            cursor.execute(sql, (message.text, message.chat.id))
            bot.reply_to(
                message,
                config.texts["airdrop_confirmation"],
                parse_mode="Markdown",
                reply_markup=airdrop_keyboard,
            )
            airdrop_wallets.append(message.text)
            airdrop_users.append(message.chat.id)
            try:
                bot.send_message(
                    config.log_channel,
                    "🎈 *#Airdrop_Entry ({0}):*\n"
                    " • User: [{1}](tg://user?id={2}) (#id{2})\n"
                    " • Address: `{3}`\n"
                    " • Time: `{4} UTC`".format(
                        len(airdrop_users),
                        bot.get_chat(message.chat.id).first_name,
                        message.chat.id,
                        message.text,
                        strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    ),
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            except:
                pass
        else:
            msg = bot.reply_to(
                message,
                "❌ Invalid $ETH address. Try again:",
                parse_mode="Markdown",
                reply_markup=cancel_button(),
            )
            bot.register_next_step_handler(msg, address_check)


def address_check_update(message, old_address):
    bot.send_chat_action(message.chat.id, "typing")
    connection = get_connection()
    with connection.cursor() as cursor:
        if message.text in airdrop_wallets:
            msg = bot.reply_to(
                message, config.texts["airdrop_walletused"], parse_mode="Markdown"
            )
            bot.register_next_step_handler(msg, address_check_update, old_address)
        elif message.content_type == "text" and re.match(
            r"^(?=.{42}$).*", message.text
        ):
            sql = "UPDATE users SET address = %s, address_change_status = address_change_status + 1 WHERE user_id = %s"
            cursor.execute(sql, (message.text, message.chat.id))
            bot.reply_to(
                message, config.texts["airdrop_wallet_update"], parse_mode="Markdown"
            )
            airdrop_wallets.append(message.text)
            try:
                bot.send_message(
                    config.log_channel,
                    "📝 *#Address_Updated:*\n"
                    " • User: [{1}](tg://user?id={2}) (#id{2})\n"
                    " • Old Address: `{3}`\n"
                    " • New Address: `{4}`\n"
                    " • Time: `{5} UTC`".format(
                        len(airdrop_wallets),
                        bot.get_chat(message.chat.id).first_name,
                        message.chat.id,
                        old_address,
                        message.text,
                        strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    ),
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            except:
                pass
        else:
            msg = bot.reply_to(
                message,
                "❌ Invalid address. Try again:",
                parse_mode="Markdown",
                reply_markup=cancel_button(),
            )
            bot.register_next_step_handler(msg, address_check_update, old_address)


@bot.message_handler(
    func=lambda message: message.chat.id in config.admins, commands=["airdroplist"]
)
def handle_text(message):
    bot.send_chat_action(message.chat.id, "upload_document")
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "SELECT address FROM users"
        cursor.execute(sql)
        airdrop = "AIRDROP ({}):\n\n".format(len(airdrop_users))
        for user in cursor.fetchall():
            if user["address"] is not None:
                address = user["address"]
                airdrop += "{}\n".format(address)

        with BytesIO(str.encode(airdrop)) as output:
            output.name = "AIRDROP.txt"
            bot.send_document(
                message.chat.id,
                output,
                caption="Here's the list with all airdrop addresses.",
            )
            return


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cancel_input":
        bot.delete_message(
            chat_id=call.message.chat.id, message_id=call.message.message_id
        )
        if len(airdrop_users) >= config.airdrop_cap:
            bot.send_message(
                call.message.chat.id,
                "✅ Operation canceled.\n\nℹ️ The airdrop reached its max cap.",
            )
        elif call.message.chat.id in airdrop_users:
            bot.send_message(
                call.message.chat.id,
                "✅ Operation canceled.",
                reply_markup=airdrop_keyboard,
            )
        else:
            bot.send_message(
                call.message.chat.id,
                "✅ Operation canceled.",
                reply_markup=default_keyboard,
            )
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

    elif call.data == "edit_wallet_address":
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = "SELECT address, address_change_status FROM users WHERE user_id = %s"
            cursor.execute(sql, call.message.chat.id)
            data = cursor.fetchone()
            if data["address_change_status"] != config.wallet_changes:
                address = data["address"]
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="Please send your new address:",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
                bot.register_next_step_handler(
                    call.message, address_check_update, address
                )
            else:
                bot.answer_callback_query(
                    call.id,
                    "⚠️ You can't change your address anymore.",
                    show_alert=True,
                )


create_db_tables = create_tables()
airdrop_users = get_airdrop_users()
airdrop_wallets = get_airdrop_wallets()

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

create_db_tables

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, "r")
)

# Build ssl context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Process webhook calls
async def handle(request):
    if request.match_info.get("token") == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)


app.router.add_post("/{token}/", handle)

# Start aiohttp server
web.run_app(
    app,
    host="0.0.0.0",
    port=WEBHOOK_PORT,
    ssl_context=context,
)
