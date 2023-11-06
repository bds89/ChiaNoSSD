import asyncio
import datetime
import inspect
import json
import logging
import os
import pickle
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import yaml

import psutil
from telegram import ReplyKeyboardRemove, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext
)
from termcolor import colored

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class User:
    def __init__(self, id, name="?", surname="?", auth="GUEST", tryn=0, notify="True"):
        self.id = id
        self.name = name
        self.surname = surname
        self.auth = auth
        self.tryn = tryn
        self.notify = notify

    def save_to_db(self, params=[]):
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()
        user = (self.id, self.name, self.surname, self.auth, self.tryn, self.notify)
        if not params:
            try:
                cursor.execute('''SELECT id FROM users WHERE id = ?''', (self.id,))
                if not cursor.fetchall():
                    cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?)''', user)
                else:
                    cursor.execute('''UPDATE users 
                                        SET name = ?,
                                        surname = ?,
                                        auth = ?,
                                        tryn = ? ,
                                        notify = ?
                                            where id = ?''',
                                   (self.name, self.surname, self.auth, self.tryn, self.notify, self.id))
                sqlite_connection.commit()
                sqlite_connection.close()
                return True
            except Exception as e:
                logger.error("Exception: " + str(e) + " in save to DB users without params")
                logger.info((self.name, self.surname, self.auth, self.tryn, self.notify, self.id))
                return False
        else:
            try:
                new_user = False
                cursor.execute('''SELECT id FROM users WHERE id = ?''', (self.id,))
                if not cursor.fetchall(): new_user = True
                if "name" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET name = ? where id = ?''', (self.name, self.id))
                if "surname" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET surname = ? where id = ?''', (self.surname, self.id))
                if "auth" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET auth = ? where id = ?''', (self.auth, self.id))
                if "tryn" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET tryn = ? where id = ?''', (self.tryn, self.id))
                if "notify" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET notify = ? where id = ?''', (self.notify, self.id))
                sqlite_connection.commit()
                sqlite_connection.close()
                return True
            except Exception as e:
                logger.error("Exception: " + str(e) + " in save to DB users with params:")
                logger.info((self.name, self.surname, self.auth, self.tryn, self.notify, self.id))
                return False

    def load_from_db(self, param=""):
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()

        if not param:
            try:
                cursor.execute('''SELECT * FROM users WHERE id = ? ''', (self.id,))
                user = cursor.fetchone()
                sqlite_connection.close()
            except Exception as e:
                logger.error("Exception: " + str(e) + " in load from DB without params")
                return False
            if user:
                self.id = user[0]
                self.name = user[1]
                self.surname = user[2]
                self.auth = user[3]
                self.tryn = user[4]
                self.notify = user[5]
                sqlite_connection.close()
                return True
            else:
                sqlite_connection.close()
                return False

        try:
            cursor.execute('''SELECT ? FROM users WHERE id = ? ''', (param, self.id))
            user = cursor.fetchone()
            sqlite_connection.close()
        except Exception as e:
            logger.error("Exception: " + str(e) + " in load from DB users with param:" + param)
            return False
        if user:
            if param == "name": self.name = user[0]
            if param == "surname": self.surname = user[0]
            if param == "auth": self.auth = user[0]
            if param == "tryn": self.tryn = user[0]
            if param == "notify": self.notify = user[0]
            sqlite_connection.close()
            return user[0]
        else:
            sqlite_connection.close()
            return False

    def delete_from_db(self, id):
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()

        try:
            cursor.execute('''DELETE FROM users WHERE id = ? ''', (id,))
            sqlite_connection.commit()
        except Exception as e:
            logger.error("Exception: " + str(e) + " in delete from DB users")
            sqlite_connection.close()
            return False
        sqlite_connection.close()
        return True


class Users:
    def __init__(self):
        self.users = []
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()
        try:
            cursor.execute('''SELECT * FROM users ''')
            all_users = cursor.fetchall()
            sqlite_connection.close()
        except Exception as e:
            logger.error("Exception: " + str(e) + " in load from DB all users")
            sqlite_connection.close()
            return
        if all_users:
            for us in all_users:
                user = User(id=us[0], name=us[1], surname=us[2], auth=us[3], tryn=us[4], notify=us[5])
                self.users.append(user)


AUTH, ROOT, SETTINGS, SET_SETTINGS = range(4)

standart_keyboard = [
    [
        InlineKeyboardButton("Status", callback_data="miner_status"),
        InlineKeyboardButton("System info", callback_data="sys_info"),
    ],
]


async def tcp_server(reader, writer, context):
    addr = writer.get_extra_info('peername')
    if addr[0] not in CONFIG["NODES"]:
        logger.warning(f"Get data from unknown address {addr}. Closing connection")
        writer.close()
        await writer.wait_closed()

    else:
        # try:
            recieved_data = await reader.read(1*1000000)
            recieved_message = pickle.loads(recieved_data)
            update = Update(0)
            send_message = {"code": 400, "data": "Can't handle this request"}
            if recieved_message["code"] == 200:
                if recieved_message["data"] == "miner_status":
                    send_message = await miner_status(update=update, context=context, slave=True)
                    print(send_message)
                elif recieved_message["data"] == "sys_info":
                    send_message = await sys_info(update=update, context=context, slave=True)
                elif recieved_message["data"] == "/run":
                    send_message = await miner_control(update=update, context=context, slave="/run")
                elif recieved_message["data"] == "/stop":
                    send_message = await miner_control(update=update, context=context, slave="/stop")
                elif recieved_message["data"] == "/kill":
                    send_message = await miner_control(update=update, context=context, slave="/kill")
                else:
                    warning_message = recieved_message["data"]
                    node = CONFIG["NODES"].index(addr[0])
                    await send_message_all(context, f"NODE {node} {warning_message}")
                    send_message = {"code": 200, "data": "OK"}

            send_data = pickle.dumps(send_message)
            writer.write(send_data)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        # except Exception as e:
        #     logger.error(f"can't process the received request. {e}")
        #     writer.close()
        #     await writer.wait_closed()



async def start_tcp_server(context: CallbackContext = None):
    if not "IP" in CONFIG:
        net_info = psutil.net_if_addrs()
        address = "127.0.0.1"
        for value in net_info.values():
            if re.findall(r"\d+\.\d+\.\d+\.\d+", value[0].address) and value[0].address != '127.0.0.1':
                address = value[0].address
            if len(value) > 1:
                if re.findall(r"\d+\.\d+\.\d+\.\d+", value[1].address) and value[1].address != '127.0.0.1':
                    address = value[1].address
    else:
        address = CONFIG["IP"]
    # if not "PORT" in CONFIG:
    #     port = 2605
    # else: port = CONFIG["PORT"]
    server = await asyncio.start_server(lambda r, w: tcp_server(r, w, context), address, 2605)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.info(f'Serving on {addrs}')
    async with server:
        await server.serve_forever()


async def tcp_client(host, port, message, comand=False):
    try:
        reader, writer = await asyncio.open_connection(
            host, port)
    except(ConnectionRefusedError):
        logger.error("ConnectionRefusedError")
        return

    writer.write(pickle.dumps(message))
    await writer.drain()

    fut = reader.read()
    try:
        data = await asyncio.wait_for(fut, 5)
    except asyncio.exceptions.TimeoutError:
        logger.error("TimeoutError")
        return

    answer = pickle.loads(data)
    if comand:
        if answer["code"] == 200:
            return answer["data"]
        else:
            return "No response from slave PC"
    else:
        if answer["code"] != 200 or answer["data"] != "OK": logger.error("Error sending message to master PC")

    writer.close()
    await writer.wait_closed()


def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False):  # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


def num_to_scale(value, numsimb):
    # Type 1: ▓▓▓▓▓▓▓▓░░░░░░░░
    simbols = round((value / 100) * numsimb)
    hole = round(numsimb - simbols)
    if simbols > numsimb:
        simbols = numsimb
    i = 0
    text = ""
    while i < simbols:
        text += "▓"
        i += 1
    while i < numsimb:
        text += "░"
        i += 1
    text += ""
    return (text)


async def update_message(update, context, text, keyboard):
    if update.message:
        context.chat_data["last_message"] = await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        if update.callback_query.message.text != text or update.callback_query.message.reply_markup != InlineKeyboardMarkup(
                keyboard):
            await update.callback_query.answer()
            context.chat_data["last_message"] = await update.callback_query.edit_message_text(text,
                                                                                              reply_markup=InlineKeyboardMarkup(
                                                                                                  keyboard),
                                                                                              parse_mode="HTML")
        else:
            await update.callback_query.answer()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        u = update.message.from_user
    else:
        u = update.callback_query.from_user
    user = User(id=u.id)
    if user.load_from_db():
        context.user_data["user"] = user
    else:
        user.auth = "GUEST"
        user.name = u.first_name
        user.surname = u.last_name

    if user.auth == "BLACK": return ConversationHandler.END

    if user.auth == "USER" or user.auth == "ADMIN":
        await root(update, context)
        return ROOT

    context.user_data["user"] = user
    if update.message:
        context.chat_data["last_message"] = await update.message.reply_text(
            "🔐 Please enter your password",
        )
    else:
        await update.callback_query.answer()
        context.chat_data["last_message"] = await update.callback_query.message.reply_text(
            "🔐 Please enter your password",
        )
    return AUTH


async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        user = update.message.from_user
        user_pass = update.message.text
        if user_pass == str(CONFIG["PASSWORD"]) or (
                "ADMIN_PASSWORD" in CONFIG and user_pass == str(CONFIG["ADMIN_PASSWORD"])):
            if user_pass == str(CONFIG["PASSWORD"]):
                context.user_data["user"].auth = "USER"
            if "ADMIN_PASSWORD" in CONFIG and user_pass == str(CONFIG["ADMIN_PASSWORD"]):
                context.user_data.auth = "ADMIN"
            context.user_data["user"].name = user.first_name
            context.user_data["user"].surname = user.last_name
            context.user_data["user"].notify = "True"
            context.user_data["user"].tryn = 0
            context.user_data["user"].save_to_db()

            logger.info("User " + str(user.first_name) + " " + str(user.last_name) + ": " + str(
                user.id) + " successfully logged in")
            if "users" in context.bot_data:
                context.bot_data["users"].append(context.user_data["user"])
            else:
                context.bot_data["users"] = [context.user_data["user"], ]

            await root(update, context)
            return ROOT

        else:
            logger.warning("User " + str(user.first_name) + " " + str(user.last_name) + ": " + str(
                user.id) + " type wrong password")
            context.user_data["user"].tryn += 1

            if context.user_data["user"].tryn > 4:
                context.user_data["user"].auth = "BLACK"
                # context.user_data["user"].name = user.first_name
                # context.user_data["user"].surname = user.last_name
                # context.user_data["user"].notify = True
                context.user_data["user"].save_to_db()
                logger.warning(
                    "User " + str(user.first_name) + " " + str(user.last_name) + ": " + str(user.id) + " was banned")
                return ConversationHandler.END

            else:
                context.user_data["user"].save_to_db()

            context.chat_data["last_message"] = await update.message.reply_text(
                "⛔ Password is incorrect, please try again"
            )
            return AUTH
    else:
        return AUTH


async def root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Welcome to NoSSD bot"
    await update_message(update, context, text, standart_keyboard)
    return ROOT


async def miner_status(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=False):
    if not context.user_data or "farm" not in context.user_data or int(context.user_data["farm"]) == 1:
        stat = ["STOP", "START", "RUNNING", "RESTART", "IDLE", "STOPPING", "KILL"]
        text = f"NODE 1\n\n"
        text += "Miner state: " + stat[RUN_STATE] + "\n"
        if NoSSD_work_queue.empty():
            text += "\nNo new messages in the log"
        else:
            text += "\nLast messages:"
            while not NoSSD_work_queue.empty():
                text += "\n" + await NoSSD_work_queue.get()
        if slave: return text

    else:
        text = f"NODE {context.user_data['farm']}\n\n"
        text += tcp_client(CONFIG["NODES"][int(context.user_data["farm"])], 2605, {"code": 200, "data": "miner_status"},
                           True)
    await update_message(update, context, text, standart_keyboard)
    return ROOT


# get all hdd in system
def get_disk_list(min_size):
    disk_part = psutil.disk_partitions(all=False)
    disk_list = {}
    for partitions in disk_part:
        if (partitions.device.startswith("/dev/s") or partitions.device.startswith(
                "/dev/nvm") or partitions.device == '/'):
            d = psutil.disk_usage(partitions.mountpoint)
            if d.total > min_size:
                disk_list[partitions.device] = [d.total, d.used, d.free, d.percent, partitions.mountpoint]
    return disk_list


def disk_info():
    if not "SUDO_PASS" in CONFIG:
        return "Can't get disk info without sudo\n"

    disk_list = get_disk_list(10 * 1000000000)
    disk_list_keys = list(disk_list.keys())
    disk_list_keys.sort()
    text = ""
    prev_disks = {}
    sudo_password = CONFIG["SUDO_PASS"]
    if not disk_list_keys: return "No available disks\n"
    for key in disk_list_keys:
        temperature = ""
        dev = re.findall(r"\D+", key)[0]
        if not dev in prev_disks:
            p = subprocess.Popen(['sudo', '-S', 'smartctl', '-A', '-j', dev], stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            cli = p.communicate(sudo_password + '\n')[0]
            try:
                data = json.loads(cli)
                temperature = data["temperature"]["current"]
            except(json.decoder.JSONDecodeError, IndexError, KeyError):
                return "Can't get disk info\n"
            prev_disks[dev] = temperature
        else:
            temperature = prev_disks[dev]

        attention = " "
        if temperature and temperature > 50: attention = "❗"
        text = text + "{0} ({1})({4}℃){7}:\nTotal: {2} GB. Free: {3} GB\nUsed: {5} {6}%".format(key, disk_list[key][4],
                                                                                                round((disk_list[key][
                                                                                                           0] / 1000000000),
                                                                                                      2),
                                                                                                round((disk_list[key][
                                                                                                           2] / 1000000000),
                                                                                                      2), temperature,
                                                                                                num_to_scale(
                                                                                                    disk_list[key][3],
                                                                                                    19),
                                                                                                disk_list[key][3],
                                                                                                attention) + "\n"
        return text


async def sys_info(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=False):
    if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == 1:
        psutil.cpu_percent(percpu=False)

        disk_info_result = disk_info()

        used_RAM = psutil.virtual_memory()[2]
        used_SWAP = psutil.swap_memory()[3]

        CPU_freq = round(psutil.cpu_freq(percpu=False)[0])
        CPU_temp = psutil.sensors_temperatures(fahrenheit=False)["coretemp"][0][1]

        fan_list = psutil.sensors_fans()
        FAN = "no fan"
        for key, value in fan_list.items():
            for i in value:
                if i[1] > 0:
                    FAN = i[1]

        Sys_start_at = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

        used_CPU = psutil.cpu_percent(percpu=False)

        text = f"NODE 1\n\n"
        text += "<b>System info:</b>\n"
        text += ("<b>RAM:</b>\nUsed_RAM: {0}%. Used_SWAP: {1} %\n<b>CPU:</b>\nUsed_CPU: {2} %. CPU_freq: {3} "
                 "MHz.\nCPU_Temp: {4} C. FAN: {5} RPM\n<b>HDD/NVME:</b>\n").format(
            used_RAM, used_SWAP, used_CPU, CPU_freq, CPU_temp, FAN)

        text += disk_info_result

        text += "System start at: {0}".format(Sys_start_at) + "\n"
        if slave: return text
    else:
        text = f"NODE {context.user_data['farm']}\n\n"
        text += tcp_client(CONFIG["NODE_LIST"][context.user_data["farm"]], 2605, {"code": 200, "data": "sys_info"},
                           True)
    await update_message(update, context, text, standart_keyboard)
    return ROOT


async def miner_control(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=""):
    if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == 1:
        if slave == "/run":
            globals()["RUN_STATE"] = START
            text = "Starting miner"
            return text
        elif slave == "/stop":
            globals()["RUN_STATE"] = STOP
            text = "Stopping miner"
            return text
        elif slave == "/kill":
            globals()["RUN_STATE"] = KILL
            text = "Killing miner"
            return text
        elif slave:
            text = "Unknown command for miner"
            return text
        elif update.message.text == "/run":
            globals()["RUN_STATE"] = START
            text = "Starting miner"
        elif update.message.text == "/stop":
            globals()["RUN_STATE"] = STOP
            text = "Stopping miner"
        elif update.message.text == "/kill":
            globals()["RUN_STATE"] = KILL
            text = "Killing miner"
        else:
            text = "Unknown command for miner"
            if slave: return text
    else:
        text = f"NODE {context.user_data['farm']}\n\n"
        text += tcp_client(CONFIG["NODE_LIST"][context.user_data["farm"]], 2605, {"code": 200, "data": update.message.text},
                           True)

    await update_message(update, context, text, standart_keyboard)
    return ROOT


async def set_farm(update: Update, context: CallbackContext) -> None:
    if int(update.message.text) > len(CONFIG["NODES"]):
        context.chat_data["last_message"]  = await update.message.reply_text(
            "Error node number", reply_markup=InlineKeyboardMarkup(standart_keyboard), parse_mode="HTML"
        )
        return
    context.user_data["farm"] = update.message.text
    if int(update.message.text) == 1:
        await miner_status(update=update, context=context, slave=False)
    else:
        text = await tcp_client(CONFIG["NODES"][int(update.message.text) - 1], 2605, "miner_status", True)
        context.chat_data["last_message"] = await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(standart_keyboard), parse_mode="HTML"
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("no settings yet")
    return SETTINGS


async def go_to_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        u = update.message.from_user
    else:
        u = update.callback_query.from_user
    user = User(id=u.id)
    if user.load_from_db():
        context.user_data["user"] = user
    else:
        user.auth = "GUEST"

    if user.auth == "BLACK": return ConversationHandler.END
    if user.auth == "USER" or user.auth == "ADMIN":
        await settings(update, context)
        return SETTINGS

    context.user_data["user"] = user
    if update.message:
        context.chat_data["last_message"] = await update.message.reply_text(
            "First you need to login",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👤 Authorization", callback_data="auth")]])
        )
    else:
        await update.callback_query.answer()
        context.chat_data["last_message"] = await update.callback_query.message.reply_text(
            "First you need to login",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👤 Authorization", callback_data="auth")]])
        )
    return ConversationHandler.END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cancel(update, context)


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message: return ConversationHandler.END
    u = update.message.from_user
    if "user" in context.user_data:
        context.user_data["user"].auth = "GUEST"
        context.user_data["user"].save_to_db(params=["auth"])
        context.user_data.clear()
    else:
        user = User(id=u.id)
        user.save_to_db(params=["auth"])
    context.chat_data["last_message"] = await update.message.reply_text(
        "🏁 Bye!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏳 Start", callback_data="root")]])
    )
    return ConversationHandler.END


async def send_message_all(context: CallbackContext, text):
    if "users" not in context.bot_data:
        users = Users()
        context.bot_data["users"] = users
    for user in context.bot_data["users"]:
        await context.bot.send_message(
            chat_id=user.id, text=text, reply_markup=InlineKeyboardMarkup(standart_keyboard), parse_mode="HTML",
            disable_notification=not eval(user.notify)
        )


async def error_log_handler(context: CallbackContext):
    while True:
        text = await NoSSD_err_queue.get()
        NoSSD_err_queue.task_done()
        if not CONFIG["SLAVE_PC"]:
            await send_message_all(context, "NODE 1 \n\n" + text)
        else:
            await tcp_client(CONFIG["NODES"][0], 2605, text, False)


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(CONFIG["BOT_TOKEN"]).concurrent_updates(10).build()

    # Add my handler for NoSSd log events
    jobs = application.job_queue
    jobs.run_once(callback=error_log_handler, when=1)
    # Start tcp server
    jobs.run_once(callback=start_tcp_server, when=2)

    if not CONFIG["SLAVE_PC"]:
        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start),
                          CommandHandler("cancel", start),
                          CommandHandler("logout", start),
                          CommandHandler("settings", go_to_settings),
                          CallbackQueryHandler(start, pattern='^')],
            states={
                AUTH: [CommandHandler("start", start),
                       CommandHandler("settings", go_to_settings),
                       CommandHandler("cancel", cancel),
                       MessageHandler(filters.TEXT, auth)],
                ROOT: [CommandHandler("start", start),
                       CommandHandler("cancel", cancel),
                       CommandHandler("logout", logout),
                       CommandHandler("settings", go_to_settings),
                       CommandHandler("run", miner_control),
                       CommandHandler("stop", miner_control),
                       CommandHandler("kill", miner_control),
                       CallbackQueryHandler(miner_status, pattern='^miner_status'),
                       CallbackQueryHandler(sys_info, pattern='^sys_info'),
                       CallbackQueryHandler(root, pattern='^root'),
                       MessageHandler(filters.Regex('^(\d{,2})$'), set_farm)
                       ],
                SETTINGS: [CommandHandler("stop", cancel),
                           CommandHandler("cancel", cancel),
                           CommandHandler("logout", logout),
                           CommandHandler("settings", go_to_settings),
                           CallbackQueryHandler(root, pattern='^root$'), ],
                # ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, timeout),
                #                               CallbackQueryHandler(timeout, pattern='^'), ],
            },
            # conversation_timeout=300,
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        application.add_handler(conv_handler)

        # Run the bot until the user presses Ctrl-C
        application.run_polling(connect_timeout=10, pool_timeout=10, read_timeout=5, write_timeout=5,
                                allowed_updates=Update.ALL_TYPES)




async def main_slave():
    application = Application.builder().token(CONFIG["BOT_TOKEN"]).concurrent_updates(10).build()

    # Add my handler for NoSSd log events
    jobs = application.job_queue
    jobs.run_once(callback=error_log_handler, when=1)
    # Start tcp server
    jobs.run_once(callback=start_tcp_server, when=2)
    print("Slave")
    await application.initialize()
    await application.start()

# For MINER
STOP, START, RUNNING, RESTART, IDLE, STOPPING, KILL = range(7)


def run(command, std_type):
    while True:
        if RUN_STATE == IDLE:
            time.sleep(3)
            if "process" in locals() and process.poll() is None:
                yield (f"process runing yet {process.pid}")
                globals()["RUN_STATE"] = RUNNING

        if RUN_STATE == STOPPING:
            if "process" in locals() and process.poll() is None:
                time.sleep(2)
                continue
            globals()["RUN_STATE"] = IDLE
            yield "Miner stopped"

        if RUN_STATE == START:
            if not "process" in locals() or ("process" in locals() and process.poll() != None):
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True, encoding="utf-8", bufsize=1, universal_newlines=True)
                globals()["RUN_STATE"] = RUNNING
                time.sleep(2)
                yield (f"Start process: {process.pid}")

        if RUN_STATE == STOP:
            if ("process" in locals() and process.poll() == None):
                process.send_signal(signal.SIGTERM)
                globals()["RUN_STATE"] = STOPPING
                yield "Stopping miner"
            else:
                yield "Miner not running now"

        if RUN_STATE == KILL:
            if ("process" in locals() and process.poll() == None):
                process.send_signal(signal.SIGKILL)
                globals()["RUN_STATE"] = STOPPING
                yield "Killing miner"
                time.sleep(1)
            else:
                yield "Miner not running now"

        if RUN_STATE == RUNNING:
            try:
                if std_type == "err":
                    line = process.stderr.readline().rstrip()
                elif std_type == "out":
                    line = process.stdout.readline().rstrip()
                else:
                    break
            except(UnicodeDecodeError) as e:
                print(e)
                continue
            if not line and process.poll() != None:
                globals()["RUN_STATE"] = IDLE
                yield f"{datetime.datetime.now().strftime('%H:%M:%S')} ERROR: Miner process was unexpectedly closed"
            yield line


def create_shortcut():
    try:
        from pyshortcuts import make_shortcut
        patch = get_script_dir()
        icon = '/res/icon.png'
        make_shortcut(script=patch, name='Chia NoSSD',
                                icon=patch+icon,
                                terminal=False)
    except ImportError:
        print("Can't create desktop shortcut, without package pyshortcuts")

def read_nossd_log(command, std_type):
    for log in run(command, std_type):
        print(colored(log, 'green'))
        error_log = re.findall(r"(\d{2}:\d{2}:\d{2} ERROR:.+$)", log)
        warning_log = re.findall(r"(\d{2}:\d{2}:\d{2} WARNING:.+$)", log)
        if error_log:
            NoSSD_err_queue.put_nowait(error_log[0])
        elif warning_log:
            NoSSD_err_queue.put_nowait(warning_log[0])
        else:
            NoSSD_work_queue.put_nowait(log)
            while NoSSD_work_queue.qsize() > 5:
                NoSSD_work_queue.get_nowait()


if __name__ == "__main__":
    dir_script = get_script_dir()

    # Config load
    with open(dir_script + "/config.yaml") as f:
        CONFIG = yaml.load(f.read(), Loader=yaml.FullLoader)
    if not "CONFIG" in locals():
        CONFIG = {}
    if "PASSWORD" not in CONFIG:
        CONFIG["PASSWORD"] = "12345"
    if "RUN_AT_STARTUP" not in CONFIG:
        CONFIG["RUN_AT_STARTUP"] = True
    if "SLAVE_PC" not in CONFIG:
        CONFIG["SLAVE_PC"] = False

    # Create async QUEUEs
    NoSSD_err_queue = asyncio.Queue()
    NoSSD_work_queue = asyncio.Queue()

    if not CONFIG["SLAVE_PC"]:
        # DB CONNECT
        DB_PATCH = dir_script + '/users.db'
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()
        try:
            cursor.execute("""CREATE TABLE if not exists users
                            (id integer NOT NULL UNIQUE, name text, surname text, auth text, tryn integer, notify text)
                        """)
            sqlite_connection.commit()
        except Exception as e:
            logger.error("Exception: %s at DB connect.", e)
        sqlite_connection.close()

    # Run miner thread
    if "NoSSD_PATCH" in CONFIG:
        command = str(CONFIG["NoSSD_PATCH"]) + "/client "
        command += str(CONFIG["NoSSD_PARAMS"])
        if CONFIG["RUN_AT_STARTUP"]:
            RUN_STATE = START
        else:
            RUN_STATE = IDLE
        NoSSD_thread = threading.Thread(target=read_nossd_log, args=(command, "out",))
        NoSSD_thread.start()

    if CONFIG["SLAVE_PC"]:
        asyncio.run(main_slave())
    else:
        main()
