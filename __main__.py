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
import queue

import yaml
import xmltodict

import psutil
from requests import Session
from telegram import ReplyKeyboardRemove, Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, error
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
    def __init__(self, id, name="?", surname="?", auth="GUEST", tryn=0, notify="True", warnings="True", errors="True"):
        self.id = id
        self.name = name
        self.surname = surname
        self.auth = auth
        self.tryn = tryn
        self.notify = notify
        self.warnings = warnings
        self.errors = errors

    def save_to_db(self, params=[]):
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()
        user = (self.id, self.name, self.surname, self.auth, self.tryn, self.notify, self.warnings, self.errors)
        if not params:
            try:
                cursor.execute('''SELECT id FROM users WHERE id = ?''', (self.id,))
                if not cursor.fetchall():
                    cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                else:
                    cursor.execute('''UPDATE users 
                                        SET name = ?,
                                        surname = ?,
                                        auth = ?,
                                        tryn = ? ,
                                        notify = ?,
                                        warnings = ?,
                                        errors = ?
                                            where id = ?''',
                                   (self.name, self.surname, self.auth, self.tryn, self.notify, self.warnings,
                                    self.errors, self.id))
                sqlite_connection.commit()
                sqlite_connection.close()
                return True
            except Exception as e:
                logger.error("Exception: " + str(e) + " in save to DB users without params")
                logger.info(
                    (self.name, self.surname, self.auth, self.tryn, self.notify, self.warnings, self.errors, self.id))
                return False
        else:
            try:
                new_user = False
                cursor.execute('''SELECT id FROM users WHERE id = ?''', (self.id,))
                if not cursor.fetchall(): new_user = True
                if "name" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET name = ? where id = ?''', (self.name, self.id))
                if "surname" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET surname = ? where id = ?''', (self.surname, self.id))
                if "auth" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET auth = ? where id = ?''', (self.auth, self.id))
                if "tryn" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET tryn = ? where id = ?''', (self.tryn, self.id))
                if "notify" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET notify = ? where id = ?''', (self.notify, self.id))
                if "warnings" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET warnings = ? where id = ?''', (self.warnings, self.id))
                if "errors" in params:
                    if new_user:
                        cursor.execute('''INSERT INTO users VALUES(?,?,?,?,?,?,?,?)''', user)
                        new_user = False
                    else:
                        cursor.execute('''UPDATE users SET errors = ? where id = ?''', (self.errors, self.id))
                sqlite_connection.commit()
                sqlite_connection.close()
                return True
            except Exception as e:
                logger.error("Exception: " + str(e) + " in save to DB users with params:")
                logger.info(
                    (self.name, self.surname, self.auth, self.tryn, self.notify, self.warnings, self.errors, self.id))
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
                self.warnings = user[6]
                self.errors = user[7]
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
            if param == "warnings": self.warnings = user[0]
            if param == "errors": self.errors = user[0]
            sqlite_connection.close()
            return user[0]
        else:
            sqlite_connection.close()
            return False


    @staticmethod
    def delete_from_db(id):
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
                user = User(id=us[0], name=us[1], surname=us[2], auth=us[3], tryn=us[4], notify=us[5], warnings=us[6],
                            errors=us[7])
                self.users.append(user)


AUTH, ROOT, SETTINGS, GET_SETTINGS = range(4)


async def tcp_server(reader, writer, context):
    addr = writer.get_extra_info('peername')
    if addr[0] not in CONFIG["NODES"]:
        logger.warning(f"Get data from unknown address {addr}. Closing connection")
        writer.close()
        await writer.wait_closed()

    else:
        try:
            recieved_data = await reader.read(1 * 1000000)
            recieved_message = pickle.loads(recieved_data)
            update = Update(0)
            send_message = {"code": 400, "data": "Can't handle this request"}
            if recieved_message["code"] == 200:
                if recieved_message["data"] == "miner_status":
                    send_message = {"code": 200, "data": await miner_status(update=update, context=context, slave=True)}
                elif recieved_message["data"] == "sys_info":
                    send_message = {"code": 200, "data": await sys_info(update=update, context=context, slave=True)}
                elif recieved_message["data"] == "farm_status":
                    send_message = {"code": 200, "data": await farm_status(update=update, context=context, slave=True)}
                elif recieved_message["data"] == "/run":
                    send_message = {"code": 200,
                                    "data": await miner_control(update=update, context=context, slave="/run")}
                elif recieved_message["data"] == "/stop":
                    send_message = {"code": 200,
                                    "data": await miner_control(update=update, context=context, slave="/stop")}
                elif recieved_message["data"] == "/kill":
                    send_message = {"code": 200,
                                    "data": await miner_control(update=update, context=context, slave="/kill")}
                elif type(recieved_message["data"]) is dict:
                    send_message = {"code": 200,
                                    "data": await remote_settings(request=recieved_message["data"]["request"],
                                                                  params=recieved_message["data"]["params"])}
                else:
                    warning_message = recieved_message["data"]
                    node = CONFIG["NODES"].index(addr[0]) + 1
                    await send_message_all(context, f"NODE {node} {warning_message}")
                    send_message = {"code": 200, "data": "OK"}

                send_data = pickle.dumps(send_message)
                writer.write(send_data)
                await writer.drain()
                writer.close()
                await writer.wait_closed()
        except Exception as e:
            logger.error(f"can't process the received request. {e}")
            writer.close()
            await writer.wait_closed()


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


async def tcp_client(host, port, message, comand=False, timeout=20) -> any:
    try:
        reader, writer = await asyncio.open_connection(
            host, port)
    except(ConnectionRefusedError):
        logger.error(f"ConnectionRefusedError {host}")
        return f"ConnectionRefusedError {host}"
    writer.write(pickle.dumps(message))
    await writer.drain()

    fut = reader.read()
    try:
        data = await asyncio.wait_for(fut, timeout)
    except Exception as e:
        logger.error(f"{e} {host}")
        return f"TimeoutError {host}"

    try:
        answer = pickle.loads(data)
    except Exception as e:
        return str(e)
    if comand:
        if answer["code"] == 200:
            return answer["data"]
        else:
            return "No response from slave PC"
    else:
        if answer["code"] != 200 or answer["data"] != "OK":
            logger.error("Error sending message to master PC")
            return "Error sending message to master PC"

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


def num_to_scale(percent_value, numsimb=15, add_percent=True, prefix="", value="", si=""):
    output_text = ""
    if percent_value > 100:
        percent_value_scale = 100
    else:
        percent_value_scale = percent_value
    scale = "<s>"
    blocks = ["⠀", "▏", "▎", "▍", "▌", "▋", "▊", "█"]
    discretization = numsimb * 7
    simbols = (percent_value_scale / 100) * discretization
    full_simbols = int(simbols // 7)
    half_simbol = int(simbols % 7)
    for i in range(full_simbols):
        scale += blocks[7]
    if percent_value_scale != 100:
        scale += blocks[half_simbol]
    for i in range(numsimb - full_simbols - 1):
        if i == 0 and full_simbols == 0 and half_simbol == 0:
            scale = "<s>▏⠀"
            continue
        scale += blocks[0]

    if prefix:
        scale = prefix + scale

    scale += "</s>▏"
    if len(value) > 0:
        k_letter = 180 / 267
        k_point = 112 / 267
        k_space = 104 / 267
        text = str(value) + " " + si
        start_pos = ((len(scale))
                     - (((len(text) - text.count('.') + text.count(' ')) * k_letter)
                        + text.count('.') * k_point + text.count(' ') * k_space)) / 2
        for i in range(int(round(start_pos))):
            output_text += "⠀"
        output_text += text + "\n"
    if add_percent:
        scale += " " + str(round(percent_value)) + '%'

    output_text += scale
    return (output_text)


async def update_message(update, context, text, keyboard):
    try:
        if update.message:
            if len(text) > 4096:
                with open(dir_script + '/bot_send.txt', 'w') as f:
                    f.write(text)
                context.chat_data["last_message"] = await update.message.reply_document(
                    document=open(dir_script + '/bot_send.txt', 'rb')
                )
                context.chat_data["last_message"] = await update.message.reply_text(
                    "Message too long for TG", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
                )
                if os.path.exists(dir_script + '/bot_send.txt'):
                    os.remove(dir_script + '/bot_send.txt')
            else:
                context.chat_data["last_message"] = await update.message.reply_text(
                    text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
                )
        else:
            if len(text) > 4096:
                text = text[:4096]
            if update.callback_query.message.text != text or update.callback_query.message.reply_markup != InlineKeyboardMarkup(
                    keyboard):
                await update.callback_query.answer()
                context.chat_data["last_message"] = await update.callback_query.edit_message_text(text,
                                                                                                  reply_markup=InlineKeyboardMarkup(
                                                                                                      keyboard),
                                                                                                  parse_mode="HTML")
            else:
                await update.callback_query.answer()
    except error.BadRequest as e:
        logger.warning(str(e))


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
                context.user_data["user"].auth = "ADMIN"
            context.user_data["user"].name = user.first_name
            context.user_data["user"].surname = user.last_name
            context.user_data["user"].notify = "True"
            context.user_data["user"].tryn = 0
            context.user_data["user"].save_to_db()

            logger.info("User " + str(user.first_name) + " " + str(user.last_name) + ": " + str(
                user.id) + " successfully logged in")

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
    if "NODES" in CONFIG and CONFIG["NODES"]:
        reply_keyboard = [[]]
        input_field_placeholder = ""
        text = "Welcome to NoSSD bot"
        for index, ip in enumerate(CONFIG["NODES"]):
            reply_keyboard[0].append(f"{index + 1}")
            input_field_placeholder += f"{index + 1}:{ip[-3:]}; "
        input_field_placeholder = input_field_placeholder[:-2]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True,
                                           input_field_placeholder=input_field_placeholder[:64])

        if update.message:
            context.chat_data["last_message"] = await update.message.reply_text(text, reply_markup=reply_markup)
            await miner_status(update, context)

    else:
        await miner_status(update, context)

    if update.callback_query:
        if update.callback_query.data == "miner_status" or update.callback_query.data == "root":
            await miner_status(update, context)

        elif update.callback_query.data == "sys_info":
            await sys_info(update, context)
        elif update.callback_query.data == "farm_status":
            await farm_status(update, context)
        else:
            pass  # put new functions

    if "farm" not in context.user_data:
        context.user_data["farm"] = "1"
    return ROOT


async def miner_status(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=False):
    if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
        stat = ["STOP", "START", "MINING ⛏", "RESTART", "IDLE 💤", "STOPPING ⏱", "KILL"]
        text = "Miner state: " + stat[RUN_STATE] + "\n\n"
        text += f"Worker: {INFO_DICT['worker']}\n"
        text += f"Mineable plots: {INFO_DICT['mineable_plots']}\n"
        text += f"Last plot time: {INFO_DICT['last_time_plot']}"
        text += f'''\n{num_to_scale(percent_value=(INFO_DICT['shares1'] / INFO_DICT['max_shares1'] * 100),
                                    add_percent=False,
                                    prefix="Shares 1h   ",
                                    value=str(INFO_DICT['shares1']))}\n'''
        text += f'''{num_to_scale(percent_value=(INFO_DICT['shares24'] / INFO_DICT['max_shares24'] * 100),
                                  add_percent=False,
                                  prefix="Shares 24h ",
                                  value=str(INFO_DICT['shares24']))}\n\n'''
        if NoSSD_work_queue.empty():
            text += "No new messages in the log"
        else:
            text += "Last messages:"
            while not NoSSD_work_queue.empty():
                text += "\n" + await NoSSD_work_queue.get()
        if slave:
            return text
        else:
            text = f"NODE 1\n\n" + text

    else:
        text = f"NODE {context.user_data['farm']}\n\n"
        text += await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                 {"code": 200, "data": "miner_status"},
                                 True)
    await update_message(update, context, text, standart_keyboard)
    return ROOT


async def farm_status(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=False):
    stat = ["STOP", "START", "MINING ⛏", "RESTART", "IDLE 💤", "STOPPING ⏱", "KILL"]
    status = stat[RUN_STATE]

    if not slave:
        text = f"Node 1 status: {stat[RUN_STATE]}\n"
        text += f"Mineable plots: {INFO_DICT['mineable_plots']}"
        text += f'''\n{num_to_scale(percent_value=(INFO_DICT['shares1'] / INFO_DICT['max_shares1'] * 100),
                                    add_percent=False,
                                    prefix="Shares 1h   ",
                                    value=str(INFO_DICT['shares1']))}\n'''
        text += f'''{num_to_scale(percent_value=(INFO_DICT['shares24'] / INFO_DICT['max_shares24'] * 100),
                                  add_percent=False,
                                  prefix="Shares 24h ",
                                  value=str(INFO_DICT['shares24']))}'''

        summary = {"shares1": INFO_DICT['shares1'], "shares24": INFO_DICT['shares24'],
                   "mineable_plots": INFO_DICT['mineable_plots']}

        for i in range(1, len(CONFIG["NODES"])):
            node = i + 1
            answer = await tcp_client(host=CONFIG["NODES"][i],
                                      port=2605,
                                      message={"code": 200, "data": "farm_status"},
                                      comand=True,
                                      timeout=3)
            if type(answer) == str:
                text += f"\n\nNode {node} status: {answer}\n"
            else:
                text += f"\n\nNode {node} status: {answer['status']}\n"
                text += f"Mineable plots: {answer['info']['mineable_plots']}"
                text += f'''\n{num_to_scale(percent_value=(answer['info']['shares1'] / answer['info']['max_shares1'] * 100),
                                            add_percent=False,
                                            prefix="Shares 1h   ",
                                            value=str(answer['info']['shares1']))}\n'''
                text += f'''{num_to_scale(percent_value=(answer['info']['shares24'] / answer['info']['max_shares24'] * 100),
                                          add_percent=False,
                                          prefix="Shares 24h ",
                                          value=str(answer['info']['shares24']))}'''

                summary["shares1"] += answer['info']['shares1']
                summary["shares24"] += answer['info']['shares24']
                summary["mineable_plots"] += answer['info']['mineable_plots']

        text += (f"\n\nTotal:\n"
                 f"Mineable plots: {summary['mineable_plots']}\n"
                 f"Shares 1h: {summary['shares1']}\n"
                 f"Shares 24h: {summary['shares24']}")
    else:
        return {"status": status, "info": INFO_DICT}

    #try to get netspace, price and balance
    try:
        address = re.findall(r"-a (xch\w+)", CONFIG["NoSSD_PARAMS"])
        url = f'https://xchscan.com/api/account/balance?address={address[0]}'
        session = Session()
        response = session.get(url, timeout=2)
        data = json.loads(response.text)
        balance = round(float(data["xch"]), 5)

        url = f'https://xchscan.com/api/chia-price'
        session = Session()
        response = session.get(url, timeout=2)
        data = json.loads(response.text)
        price = float(data["usd"])

        url = 'https://xchscan.com/api/netspace'
        session = Session()
        response = session.get(url, timeout=2)
        data = json.loads(response.text)
        convert = 1024 ** 6
        net_space = round(int(data["netspace"]) / convert, 2)

        k = 9467476972000000
        if time.time() > 1994846400:
            k /= 16
        elif time.time() > 1900152000:
            k /= 8
        elif time.time() > 1805457600:
            k /= 4
        elif time.time() > 1710849600:
            k /= 2
        else: pass
        daily = round(((summary['shares24'] / int(data["netspace"]) * k) / 0.965), 4)
        fee = round((daily * 0.035), 4)
        text += (f'\n\nYour balance: {balance} XCH\n'
                 f'Net space: {net_space} EiB\n'
                 f'Chia price: {price} $\n'
                 f'XCH per day: <b>{daily}</b> (-fee:{fee})\n'
                 f'USD per day: {round(((daily - fee)*price), 2)} $')

    except Exception as e:
        logger.warning(str(e))

    await update_message(update, context, text, standart_keyboard)
    return ROOT


# get all hdd in system
def get_disk_list(min_size):
    disk_part = psutil.disk_partitions(all=True)
    disk_list = {}
    for partitions in disk_part:
        if (partitions.device.startswith("/dev/s") or partitions.device.startswith(
                "/dev/nvm") or partitions.device == '/'):
            d = psutil.disk_usage(partitions.mountpoint)
            if d.total > min_size:
                disk_list[partitions.device] = [d.total, d.used, d.free, d.percent, partitions.mountpoint]
    return disk_list


def disk_info(disk_info_queue: queue, context: ContextTypes.DEFAULT_TYPE):
    if 'disk_info' in context.bot_data and time.time() - context.bot_data['disk_info']['time'] < 30:
        disk_info_queue.put(context.bot_data['disk_info']['data'])
        return

    disk_list = get_disk_list(10 * 1000000000)
    disk_list_keys = list(disk_list.keys())
    disk_list_keys.sort()
    text = ""
    prev_disks = {}
    sudo_password = CONFIG["SUDO_PASS"]
    if not disk_list_keys: return "No available disks\n"
    for dev in disk_list_keys:
        temperature = "? "
        if not dev in prev_disks:
            p = subprocess.Popen(['sudo', '-S', 'smartctl', '-A', '-j', dev], stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            cli = p.communicate(sudo_password + '\n')[0]
            try:
                data = json.loads(cli)
                temperature = data["temperature"]["current"]
            except(json.decoder.JSONDecodeError, IndexError, KeyError):
                temperature = "? "
            prev_disks[dev] = temperature
        else:
            temperature = prev_disks[dev]

        attention = " "
        if temperature and temperature != "? " and temperature > 50: attention = "🌡"
        text += f'''<b>    {dev}</b>   {round((disk_list[dev][0] / 1000000000), 2)} / {round((disk_list[dev][2] / 1000000000), 2)} GB
{num_to_scale(
            percent_value=disk_list[dev][3],
            numsimb=20)}
    {disk_list[dev][4][:20]} ({temperature} ℃{attention})\n'''

    context.bot_data['disk_info'] = {}
    context.bot_data['disk_info']['data'] = text
    context.bot_data['disk_info']['time'] = time.time()
    disk_info_queue.put(text)


async def sys_info(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=False):
    for n in range(6):
        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            psutil.cpu_percent(percpu=False)

            disk_info_queue = queue.Queue()
            disk_info_thread = threading.Thread(target=disk_info, args=[disk_info_queue, context])
            disk_info_thread.start()

            used_RAM = psutil.virtual_memory()[2]
            used_SWAP = psutil.swap_memory()[3]


            CPU_freq = round(psutil.cpu_freq(percpu=False)[0])

            try:
                CPU_temp = psutil.sensors_temperatures(fahrenheit=False)["coretemp"][0][1]
            except:
                CPU_temp = "No CPU temp"

            try:
                fan_list = psutil.sensors_fans()
                FAN = "no fan"
                for key, value in fan_list.items():
                    for i in value:
                        if i[1] > 0:
                            FAN = i[1]
            except:
                FAN = "no fan"

            used_CPU = psutil.cpu_percent(percpu=False)

            text = "<b>System info:</b>\n"
            text += ("<b>RAM:</b>\nUsed_RAM: {0}%. Used_SWAP: {1} %\n<b>CPU:</b>\nUsed_CPU: {2} %. CPU_freq: {3} "
                     "MHz.\nCPU_Temp: {4} C. FAN: {5} RPM\n\n").format(
                used_RAM, used_SWAP, used_CPU, CPU_freq, CPU_temp, FAN)

            # GPU info
            text += "<b>GPU:</b>\n"
            try:
                cli = os.popen('nvidia-smi -q -x').read()
                gpu_dict = xmltodict.parse(cli)
                if int(gpu_dict['nvidia_smi_log']['attached_gpus']) > 1:
                    for gpu in gpu_dict['nvidia_smi_log']['gpu']:
                        text += f"{gpu['product_name']}\n"
                        for args in ((f"FAN: {gpu['fan_speed']}", f"Mem used: {gpu['fb_memory_usage']['used']}"),
                                     (f"GPU util: {gpu['utilization']['gpu_util']}",
                                      f"Mem util: {gpu['utilization']['memory_util']}"),
                                     (f"GPU temp: {gpu['temperature']['gpu_temp']}",
                                      f"Mem temp: {gpu['temperature']['memory_temp']}"),
                                     (f"Power: {gpu['power_readings']['power_draw']}",
                                      f"{gpu['power_readings']['power_limit']}"),
                                     (f"GPU: {gpu['clocks']['graphics_clock']}",
                                      f"Mem: {gpu['clocks']['mem_clock']}\n")):
                            text += '{0:<20} {1:<20}'.format(*args) + "\n"
                else:
                    gpu = gpu_dict['nvidia_smi_log']['gpu']
                    text += f"{gpu['product_name']}\n"
                    for args in ((f"FAN: {gpu['fan_speed']}", f"Mem used: {gpu['fb_memory_usage']['used']}"),
                                 (f"GPU util: {gpu['utilization']['gpu_util']}",
                                  f"Mem util: {gpu['utilization']['memory_util']}"),
                                 (f"GPU temp: {gpu['temperature']['gpu_temp']}",
                                  f"Mem temp: {gpu['temperature']['memory_temp']}"),
                                 (f"Power: {gpu['power_readings']['power_draw']}",
                                  f"{gpu['power_readings']['power_limit']}"),
                                 (f"GPU: {gpu['clocks']['graphics_clock']}", f"Mem: {gpu['clocks']['mem_clock']}\n")):
                        text += '{0:<20} {1:<20}'.format(*args) + "\n"
            except Exception as e:
                logging.error(f" No GPU info {e}")
                text += "No GPU info\n"

            text += "\n<b>HDD/NVME</b>\n"

            disk_info_thread.join(10)
            if not disk_info_thread.is_alive():
                try:
                    text += disk_info_queue.get_nowait()
                except:
                    text += "Error get disk info\n"

            Sys_start_at = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            text += "System start at: {0}".format(Sys_start_at)
            if n % 2 == 0 and not slave:
                text += " ⌛"
            if slave:
                return text
            else:
                text = f"NODE 1\n\n" + text
        else:
            text = f"NODE {context.user_data['farm']}\n\n"
            text += await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                     {"code": 200, "data": "sys_info"},
                                     True)
            if n % 2 == 0:
                text += " ⌛"
        await update_message(update, context, text, standart_keyboard)
        await asyncio.sleep(1)
    return ROOT


async def miner_control(update: Update, context: ContextTypes.DEFAULT_TYPE, slave=""):
    # refresh config
    with open(dir_script + "/config.yaml") as f:
        new_config = yaml.load(f.read(), Loader=yaml.FullLoader)
        if "NoSSD_PATCH" in new_config: globals()["CONFIG"]["NoSSD_PATCH"] = new_config["NoSSD_PATCH"]
        if "NoSSD_PARAMS" in new_config: globals()["CONFIG"]["NoSSD_PARAMS"] = new_config["NoSSD_PARAMS"]

    if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
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
        text += await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                 {"code": 200, "data": update.message.text},
                                 True)

    await update_message(update, context, text, standart_keyboard)
    return ROOT


async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ''
    if 'log' in context.bot_data:
        for line in context.bot_data['log']:
            text += f'{line}\n'
    else:
        text = "Log is empty now"

    await update_message(update, context, text, standart_keyboard)
    return ROOT


async def set_farm(update: Update, context: CallbackContext):
    if not "NODES" in CONFIG or int(update.message.text) > len(CONFIG["NODES"]):
        context.chat_data["last_message"] = await update.message.reply_text(
            "Error node number", reply_markup=InlineKeyboardMarkup(standart_keyboard), parse_mode="HTML"
        )
        return ROOT

    context.user_data["farm"] = update.message.text
    if int(update.message.text) == 1:
        await miner_status(update=update, context=context, slave=False)
    else:
        text = f"NODE {context.user_data['farm']}\n\n"
        text += await tcp_client(CONFIG["NODES"][int(update.message.text) - 1], 2605,
                                 {"code": 200, "data": "miner_status"}, True)
        context.chat_data["last_message"] = await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(standart_keyboard), parse_mode="HTML"
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye!", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        u = update.message.from_user
    else:
        u = update.callback_query.from_user
    text = ""

    notify = context.user_data["user"].notify
    if notify == "True": notify = "ON"
    if notify == "False": notify = "OFF"
    text += f"Sound notifications: {notify}\n"

    warnings = context.user_data["user"].warnings
    if warnings == "True": warnings = "ON"
    if warnings == "False": warnings = "OFF"
    text += f"Send warnings: {warnings}\n"

    errors = context.user_data["user"].errors
    if errors == "True": errors = "ON"
    if errors == "False": errors = "OFF"
    text += f"Send errors: {errors}"

    keyboard = [
        [
            InlineKeyboardButton(f"Warnings", callback_data=f"settings_warnings"),
            InlineKeyboardButton(f"Errors", callback_data=f"settings_errors")
        ],
        [
            InlineKeyboardButton(f"Sound", callback_data=f"settings_notify"),
            InlineKeyboardButton("🏠", callback_data="root"),
        ],
    ]

    if context.user_data["user"].auth == "ADMIN":
        if len(CONFIG["ADMIN_PASSWORD"]) < 3:
            adm_pass = '*' * len(CONFIG["ADMIN_PASSWORD"])
        else:
            adm_pass = f'''{CONFIG["ADMIN_PASSWORD"][0] + ('*' * (len(CONFIG["ADMIN_PASSWORD"]) - 2)) + CONFIG["ADMIN_PASSWORD"][-1]}'''

        if len(CONFIG["PASSWORD"]) < 3:
            usr_pass = '*' * len(CONFIG["PASSWORD"])
        else:
            usr_pass = f'''{CONFIG["PASSWORD"][0] + ('*' * (len(CONFIG["PASSWORD"]) - 2)) + CONFIG["PASSWORD"][-1]}'''

        adm_keyboard = [
            [
                InlineKeyboardButton(f"User list", callback_data=f"settings_adm_user_list"),
            ],
            [
                InlineKeyboardButton(f"Adm pass", callback_data=f"settings_adm_adm_pass"),
                InlineKeyboardButton(f"User pass", callback_data=f"settings_adm_user_pass"),
            ],
            [
                InlineKeyboardButton(f"Run at start", callback_data=f"settings_adm_run"),
                InlineKeyboardButton(f"USB not sleep", callback_data=f"settings_adm_notsleep"),
            ],
            [
                InlineKeyboardButton(f"NoSSD params", callback_data=f"settings_adm_params"),
                InlineKeyboardButton(f"SmartDog", callback_data=f"settings_adm_smartdog"),
            ]
        ]

        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            adm_text = (f'Admin password: {adm_pass}\n'
                        f'User password {usr_pass}\n'
                        f'Run at startup: {str(CONFIG["RUN_AT_STARTUP"])}\n'
                        f'NoSSD parameters: {CONFIG["NoSSD_PARAMS"]}\n'
                        f'USB always work: {str(CONFIG["NOT_SLEEP"])}\n'
                        f'SmartDog: {str(CONFIG["SMARTDOG"])}\n')

        else:
            answer = await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                      {"code": 200, "data": {"request": "GET", "params": {}}},
                                      True)

            adm_text = (f'Admin password: {adm_pass}\n'
                        f'User password {usr_pass}\n'
                        f'Run at startup: {answer["Run at startup"]}\n'
                        f'NoSSD parameters: {answer["NoSSD parameters"]}\n'
                        f'USB always work: {answer["Not sleep"]}\n'
                        f'SmartDog: {answer["Smartdog"]}\n')
    else:
        adm_text = ""
        adm_keyboard = [[]]
    text = f"{u.first_name} {u.last_name} ({u.id}) ⚙\n\n" + adm_text + text
    keyboard = adm_keyboard + keyboard
    await update_message(update, context, text, keyboard)
    return SETTINGS


async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    u = update.callback_query.from_user
    if update.callback_query.data == "settings_notify":
        if context.user_data["user"].notify == "True":
            context.user_data["user"].notify = "False"
        else:
            context.user_data["user"].notify = "True"
        context.user_data["user"].save_to_db("notify")
    elif update.callback_query.data == "settings_warnings":
        if context.user_data["user"].warnings == "True":
            context.user_data["user"].warnings = "False"
        else:
            context.user_data["user"].warnings = "True"
        context.user_data["user"].save_to_db("warnings")
    elif update.callback_query.data == "settings_errors":
        if context.user_data["user"].errors == "True":
            context.user_data["user"].errors = "False"
        else:
            context.user_data["user"].errors = "True"
        context.user_data["user"].save_to_db("errors")
    elif update.callback_query.data == "settings_adm_run":
        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            CONFIG["RUN_AT_STARTUP"] = not CONFIG["RUN_AT_STARTUP"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
        else:
            answer = await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                      {"code": 200, "data": {"request": "POST", "params": {'settings_adm_run': ""}}},
                                      True)
            if type(answer) is str:
                logging.error(answer)
    elif update.callback_query.data == "settings_adm_notsleep":
        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            CONFIG["NOT_SLEEP"] = not CONFIG["NOT_SLEEP"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
        else:
            answer = await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                      {"code": 200, "data": {"request": "POST", "params": {'settings_adm_notsleep': ""}}},
                                      True)
            if type(answer) is str:
                logging.error(answer)
    elif update.callback_query.data == "settings_adm_smartdog":
        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            CONFIG["SMARTDOG"] = not CONFIG["SMARTDOG"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
        else:
            answer = await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                      {"code": 200, "data": {"request": "POST", "params": {'settings_adm_smartdog': ""}}},
                                      True)
            if type(answer) is str:
                logging.error(answer)
    elif update.callback_query.data == "settings_adm_adm_pass":
        await update_message(update, context, "Type new admin password",
                             [[InlineKeyboardButton("⬅", callback_data="back_to_settings")]])
        context.chat_data["adm_settings"] = "settings_adm_adm_pass"
        return GET_SETTINGS
    elif update.callback_query.data == "settings_adm_user_pass":
        await update_message(update, context, "Type new user password",
                             [[InlineKeyboardButton("⬅", callback_data="back_to_settings")]])
        context.chat_data["adm_settings"] = "settings_adm_user_pass"
        return GET_SETTINGS
    elif update.callback_query.data == "settings_adm_params":
        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            text = CONFIG['NoSSD_PARAMS']
        else:
            answer = await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                      {"code": 200, "data": {"request": "GET", "params": {}}},
                                      True)
            text = answer["NoSSD parameters"]

        await update_message(update, context, f"{text}\n\nType new parameters for miner",
                             [[InlineKeyboardButton("⬅", callback_data="back_to_settings")]])
        context.chat_data["adm_settings"] = "settings_adm_params"
        return GET_SETTINGS
    elif update.callback_query.data == "settings_adm_user_list":
        users = Users()
        text = ""
        for user in users.users:
            text += f'{user.id} {user.name} {user.surname}:\n{user.auth}\n'
        await update_message(update, context, f"{text}\nType id for delete",
                             [[InlineKeyboardButton("⬅", callback_data="back_to_settings")]])
        context.chat_data["adm_settings"] = "settings_adm_user_list"
        return GET_SETTINGS
    else:
        pass

    await settings(update, context)
    return SETTINGS


async def set_adm_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.chat_data["adm_settings"] == "settings_adm_adm_pass":
        CONFIG["ADMIN_PASSWORD"] = update.message.text
        with open(dir_script + "/config.yaml", "w") as f:
            f.write(yaml.dump(CONFIG, sort_keys=False))
        users = Users()
        for user in users.users:
            if user.auth == "ADMIN":
                user.auth = "GUEST"
                user.save_to_db(params=["auth"])

    elif context.chat_data["adm_settings"] == "settings_adm_user_pass":
        CONFIG["PASSWORD"] = update.message.text
        with open(dir_script + "/config.yaml", "w") as f:
            f.write(yaml.dump(CONFIG, sort_keys=False))
        users = Users()
        for user in users.users:
            if user.auth == "USER":
                user.auth = "GUEST"
                user.save_to_db(params=["auth"])

    elif context.chat_data["adm_settings"] == "settings_adm_user_list":
        try:
            id = int(update.message.text)
            User.delete_from_db(id)
        except:
            pass


    elif context.chat_data["adm_settings"] == "settings_adm_params":
        if not context.user_data or "farm" not in context.user_data or context.user_data["farm"] == "1":
            CONFIG["NoSSD_PARAMS"] = update.message.text
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
        else:
            answer = await tcp_client(CONFIG["NODES"][int(context.user_data["farm"]) - 1], 2605,
                                      {"code": 200, "data": {"request": "POST",
                                                             "params": {'settings_adm_params': update.message.text}}},
                                      True)
            if type(answer) is str:
                logging.error(answer)
    else:
        pass

    await settings(update, context)
    return SETTINGS


async def remote_settings(request, params):  # only for slave pc
    if request == "GET":
        return {'Run at startup': str(CONFIG["RUN_AT_STARTUP"]), 'NoSSD parameters': CONFIG["NoSSD_PARAMS"], 'Not sleep': CONFIG["NOT_SLEEP"], 'Smartdog': CONFIG["SMARTDOG"]}
    elif request == "POST":
        if "settings_adm_run" in params:
            CONFIG["RUN_AT_STARTUP"] = not CONFIG["RUN_AT_STARTUP"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
            return "True"
        if "settings_adm_params" in params:
            CONFIG["NoSSD_PARAMS"] = params["settings_adm_params"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
            return "True"
        if "settings_adm_notsleep" in params:
            CONFIG["NOT_SLEEP"] = not CONFIG["NOT_SLEEP"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
            return "True"
        if "settings_adm_smartdog" in params:
            CONFIG["SMARTDOG"] = not CONFIG["SMARTDOG"]
            with open(dir_script + "/config.yaml", "w") as f:
                f.write(yaml.dump(CONFIG, sort_keys=False))
            return "True"

    else:
        return "unknown request"


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
    users = Users()
    if "WARNING" in text:
        type = "w"
    elif "ERROR" in text:
        type = "e"
    else:
        type = "o"
    for user in users.users:
        if user.auth == "GUEST" or user.auth == "BLACK": continue
        if type == "w" and not eval(user.warnings): continue
        if type == "e" and not eval(user.errors): continue
        try:
            await context.bot.send_message(
                chat_id=user.id, text=text, reply_markup=InlineKeyboardMarkup(standart_keyboard), parse_mode="HTML",
                disable_notification=not eval(user.notify)
            )
        except error.BadRequest as e:
            logger.warning(str(e))
    # save log
    if 'log' not in context.bot_data:
        context.bot_data['log'] = []
    context.bot_data['log'].append(text)
    if len(context.bot_data['log']) > 100:
        context.bot_data['log'].pop(0)


async def error_log_handler(context: CallbackContext):
    while True:
        text = await NoSSD_err_queue.get()
        NoSSD_err_queue.task_done()
        if not CONFIG["SLAVE_PC"]:
            await send_message_all(context, "NODE 1 \n\n" + text)
        else:
            await tcp_client(CONFIG["NODES"][0], 2605, {"code": 200, "data": text}, False)


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(CONFIG["BOT_TOKEN"]).concurrent_updates(10).build()

    # Add my handler for NoSSd log events
    jobs = application.job_queue
    jobs.run_once(callback=error_log_handler, when=1)
    # Start tcp server
    if "NODES" in CONFIG:
        jobs.run_once(callback=start_tcp_server, when=2)

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
                   CommandHandler("log", get_log),
                   CallbackQueryHandler(miner_status, pattern='miner_status'),
                   CallbackQueryHandler(farm_status, pattern='farm_status'),
                   CallbackQueryHandler(sys_info, pattern='sys_info'),
                   CallbackQueryHandler(root, pattern='root'),
                   MessageHandler(filters.Regex('^(\d{,2})$'), set_farm)
                   ],
            SETTINGS: [CommandHandler("start", start),
                       CommandHandler("cancel", cancel),
                       CommandHandler("logout", logout),
                       CommandHandler("settings", go_to_settings),
                       CallbackQueryHandler(miner_status, pattern='miner_status'),
                       CallbackQueryHandler(farm_status, pattern='farm_status'),
                       CallbackQueryHandler(sys_info, pattern='sys_info'),
                       CallbackQueryHandler(root, pattern='root'),
                       MessageHandler(filters.Regex('^(\d{,2})$'), set_farm),
                       CallbackQueryHandler(set_settings, pattern='settings_notify'),
                       CallbackQueryHandler(set_settings, pattern='settings_warnings'),
                       CallbackQueryHandler(set_settings, pattern='settings_errors'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_adm_pass'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_user_pass'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_run'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_params'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_user_list'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_notsleep'),
                       CallbackQueryHandler(set_settings, pattern='settings_adm_smartdog')],
            GET_SETTINGS: [CommandHandler("start", start),
                           CommandHandler("cancel", cancel),
                           CommandHandler("logout", logout),
                           CommandHandler("settings", go_to_settings),
                           CallbackQueryHandler(miner_status, pattern='miner_status'),
                           CallbackQueryHandler(farm_status, pattern='farm_status'),
                           CallbackQueryHandler(sys_info, pattern='sys_info'),
                           CallbackQueryHandler(root, pattern='root'),
                           CallbackQueryHandler(go_to_settings, pattern='back_to_settings'),
                           MessageHandler(filters.ALL, set_adm_settings)],
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


def main_slave():
    application = Application.builder().token(CONFIG["BOT_TOKEN"]).concurrent_updates(10).build()
    context = CallbackContext(application)
    loop.run_until_complete(asyncio.gather(error_log_handler(context), start_tcp_server(context)))


# For MINER
STOP, START, RUNNING, RESTART, IDLE, STOPPING, KILL = range(7)


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)


def run(std_type):
    while True:
        if RUN_STATE == IDLE:
            time.sleep(3)
            if "process" in locals() and process.poll() is None:
                yield (f"Miner runing yet {process.pid}")
                globals()["RUN_STATE"] = RUNNING

        if RUN_STATE == STOPPING:
            try:
                if std_type == "err":
                    line = process.stderr.readline().rstrip()
                elif std_type == "out":
                    line = process.stdout.readline().rstrip()
                else:
                    break
            except(UnicodeDecodeError) as e:
                logger.error(str(e))
                continue
            if not line and process.poll() != None:
                globals()["RUN_STATE"] = IDLE
                yield f"{datetime.datetime.now().strftime('%H:%M:%S')} WARNING: Miner stopped"
            yield line

        if RUN_STATE == START:
            if not "process" in locals() or ("process" in locals() and process.poll() != None):
                command = str(CONFIG["NoSSD_PATCH"]) + "/client "
                command += str(CONFIG["NoSSD_PARAMS"])
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True, encoding="utf-8", bufsize=1, universal_newlines=True)
                globals()["RUN_STATE"] = RUNNING
                time.sleep(2)
                yield (f"Start process: {process.pid}")

        if RUN_STATE == STOP:
            if ("process" in locals() and process.poll() == None):
                kill_child_processes(process.pid, signal.SIGINT)
                globals()["RUN_STATE"] = STOPPING
                yield "Stopping miner"
            else:
                globals()["RUN_STATE"] = IDLE
                yield "Miner not running now"

        if RUN_STATE == KILL:
            if ("process" in locals() and process.poll() == None):
                kill_child_processes(process.pid, signal.SIGKILL)
                globals()["RUN_STATE"] = STOPPING
                yield "Killing miner"
                time.sleep(1)
            else:
                globals()["RUN_STATE"] = IDLE
                yield "Miner not running now"

        if RUN_STATE == RUNNING:
            try:
                if std_type == "err":
                    line = process.stderr.readline().rstrip()
                elif std_type == "out":
                    line = process.stdout.readline().rstrip()
                else:
                    continue
            except(UnicodeDecodeError) as e:
                continue
            if not line and process.poll() != None:
                globals()["RUN_STATE"] = IDLE
                yield f"{datetime.datetime.now().strftime('%H:%M:%S')} ERROR: Miner process was unexpectedly closed"
            yield line


def read_nossd_log(std_type):
    class Shares:
        def __init__(self):
            self.shares = []
            self.shares1 = 0
            self.shares24 = 0

        def new_share(self):
            self.shares.append(time.time())

        def check_shares(self):
            for i in range(len(self.shares)):
                if time.time() - self.shares[i] > 86400:
                    self.shares.pop(i)
                else:
                    break
            self.shares24 = len(self.shares)
            self.shares1 = 0
            for i in range(len(self.shares) - 1, -1, -1):
                if time.time() - self.shares[i] > 3600: break
                self.shares1 += 1

    shares = Shares()
    for log in run(std_type):
        print(colored(log, 'green'))
        error_log = re.findall(r"(\d{2}:\d{2}:\d{2} ERROR:.+$)", log)
        warning_log = re.findall(r"(\d{2}:\d{2}:\d{2} WARNING:.+$)", log)
        mineable_plots = re.findall(r"Mineable plots: (\d+)$", log)
        removed_plot = re.findall(r"(\d{2}:\d{2}:\d{2} Plot.+ has been removed.+)", log)
        share_gen = re.findall(r"(\d{2}:\d{2}:\d{2} Share generated.+)", log)
        worker = re.findall(r"^Worker: (.+)$", log)
        last_time_plot = re.findall(r"\d{2}:\d{2}:\d{2} Plotting, 99%, (.+) elapsed, [012345]s remaining$", log)
        plot_done = re.findall(r"\d{2}:\d{2}:\d{2} Plot done (.+)$", log)

        if error_log:
            asyncio.run_coroutine_threadsafe(NoSSD_err_queue.put(error_log[0]), loop)
        elif warning_log:
            asyncio.run_coroutine_threadsafe(NoSSD_err_queue.put(warning_log[0]), loop)
        elif mineable_plots:
            if int(mineable_plots[0]) < INFO_DICT["mineable_plots"]:
                asyncio.run_coroutine_threadsafe(NoSSD_err_queue.put(
                    f"Mineable plots: {mineable_plots[0]}. Prev number: {INFO_DICT['mineable_plots']}"), loop)
            INFO_DICT["mineable_plots"] = int(mineable_plots[0])
        elif removed_plot:
            asyncio.run_coroutine_threadsafe(NoSSD_err_queue.put(removed_plot[0]), loop)
        elif share_gen:
            shares.new_share()
            shares.check_shares()
            INFO_DICT["shares1"] = shares.shares1
            INFO_DICT["shares24"] = shares.shares24
            if shares.shares1 > INFO_DICT["max_shares1"]: INFO_DICT["max_shares1"] = shares.shares1
            if shares.shares24 > INFO_DICT["max_shares24"]: INFO_DICT["max_shares24"] = shares.shares24
        elif worker:
            INFO_DICT["worker"] = worker[0]
        elif last_time_plot:
            INFO_DICT["last_time_plot"] = last_time_plot[0]
        elif plot_done:
            INFO_DICT["mineable_plots"] += 1
        else:
            pass

        asyncio.run_coroutine_threadsafe(NoSSD_work_queue.put(log), loop)
        while NoSSD_work_queue.qsize() > 7:
            NoSSD_work_queue.get_nowait()

def not_sleep():
    disk_smart_dict = {}
    famous_smart_attr = ["Raw_Read_Error_Rate",
                        "Power_Cycle_Count",
                        "Reallocated_Sector_Ct",
                        "Seek_Error_Rate",
                        "Spin_Retry_Count",
                        "Helium_Condition_Lower",
                        "Helium_Condition_Upper",
                        "G-Sense_Error_Rate",
                        "Power-Off_Retract_Count",
                        "Load_Cycle_Count",
                        "Reallocated_Event_Count",
                        "Current_Pending_Sector",
                        "Offline_Uncorrectable",
                        "UDMA_CRC_Error_Count"]
    while True:
        if CONFIG["NOT_SLEEP"]:
            disk_list = get_disk_list(10 * 1000000000)
            for dev, disk in disk_list.items():
                if "usb" in disk[4]:
                    f = open(disk[4] + "/sleep.txt", 'w')
                    f.write(str(datetime.datetime.now()))
                    f.close()

        #smartdog)
        now = datetime.datetime.now()
        if (CONFIG["SMARTDOG"] and now.hour == 12 and now.minute == 0) or (CONFIG["SMARTDOG"] and not disk_smart_dict):
            logger.info("Updating SMART info")
            text = ""
            if not CONFIG["NOT_SLEEP"]: disk_list = get_disk_list(10 * 1000000000)
            for dev, disk in disk_list.items():
                p = subprocess.Popen(['sudo', '-S', 'smartctl', '-A', '-j', dev], stdout=subprocess.PIPE,
                                     stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                cli = p.communicate(CONFIG["SUDO_PASS"] + '\n')[0]
                try:
                    data = json.loads(cli)
                except json.decoder.JSONDecodeError:
                    continue
                if not dev in disk_smart_dict:
                    disk_smart_dict[dev] = {}
                if "ata_smart_attributes" in data:
                    for attr in data["ata_smart_attributes"]["table"]:
                        if attr["name"] in famous_smart_attr:
                            if attr["name"] in disk_smart_dict[dev]:
                                if disk_smart_dict[dev][attr["name"]]["value"] != attr["value"]:
                                    text += f'''WARNING. S.M.A.R.T: {dev} ({disk[4]}) value {attr["name"]} 
                                    changed from {disk_smart_dict[dev][attr["name"]]["value"]} 
                                    to {attr["value"]}. Tresh: {attr["thresh"]}\n\n'''
                                    disk_smart_dict[dev][attr["name"]]["value"] = attr["value"]
                            else:
                                disk_smart_dict[dev][attr["name"]] = {"value": attr["value"],
                                                                      "raw": attr["raw"]["value"]}
            if text:
                asyncio.run_coroutine_threadsafe(NoSSD_err_queue.put(text), loop)
        time.sleep(60)

if __name__ == "__main__":
    dir_script = get_script_dir()

    # Config load
    with open(dir_script + "/config.yaml") as f:
        CONFIG = yaml.load(f.read(), Loader=yaml.FullLoader)
    if not "CONFIG" in locals():
        CONFIG = {}
    if "PASSWORD" not in CONFIG:
        CONFIG["PASSWORD"] = "12345"
    if "ADMIN_PASSWORD" not in CONFIG:
        CONFIG["ADMIN_PASSWORD"] = CONFIG["PASSWORD"]
    if "RUN_AT_STARTUP" not in CONFIG:
        CONFIG["RUN_AT_STARTUP"] = True
    if "SLAVE_PC" not in CONFIG:
        CONFIG["SLAVE_PC"] = False
    if "NOT_SLEEP" not in CONFIG:
        CONFIG["NOT_SLEEP"] = False
    if "SUDO_PASS" not in CONFIG:
        CONFIG["SUDO_PASS"] = "0"
    if "SMARTDOG" not in CONFIG:
        CONFIG["SMARTDOG"] = False

    if "NODES" in CONFIG:
        standart_keyboard = [
            [
                InlineKeyboardButton("Farm status", callback_data="farm_status"),
            ],
            [
                InlineKeyboardButton("Node status", callback_data="miner_status"),
                InlineKeyboardButton("System info", callback_data="sys_info"),
            ],
        ]
    else:
        standart_keyboard = [
            [
                InlineKeyboardButton("Farm status", callback_data="miner_status"),
                InlineKeyboardButton("System info", callback_data="sys_info"),
            ],
        ]

    # Create async QUEUEs
    NoSSD_err_queue = asyncio.Queue()
    NoSSD_work_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    if not CONFIG["SLAVE_PC"]:
        # DB CONNECT
        DB_PATCH = dir_script + '/users.db'
        sqlite_connection = sqlite3.connect(DB_PATCH)
        cursor = sqlite_connection.cursor()
        try:
            cursor.execute("""CREATE TABLE if not exists users (id integer NOT NULL UNIQUE, name text, surname text, 
            auth text, tryn integer, notify text, warnings text, errors text)""")
            sqlite_connection.commit()
        except Exception as e:
            logger.error("Exception: %s at DB connect.", e)
        sqlite_connection.close()

    # Run miner thread
    if "NoSSD_PATCH" in CONFIG:
        if CONFIG["RUN_AT_STARTUP"]:
            RUN_STATE = START
        else:
            RUN_STATE = IDLE
        NoSSD_thread = threading.Thread(target=read_nossd_log, args=("out",))
        NoSSD_thread.start()

    # Run not sleep thread
    NoSleep_thread = threading.Thread(target=not_sleep)
    NoSleep_thread.start()


    INFO_DICT = {"worker": "unknown", "mineable_plots": 0, "shares24": 0, "shares1": 0, "max_shares24": 1,
                 "max_shares1": 1, "last_time_plot": "unknown"}

    #Turn off powersave
    disk_list = get_disk_list(10 * 1000000000)
    for dev in disk_list.keys():
        command = ("sudo -S hdparm -B 254 -S 0 " + dev).split()
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
        cli = p.communicate(CONFIG["SUDO_PASS"] + '\n')[0]


    if CONFIG["SLAVE_PC"]:
        main_slave()
    else:
        main()
