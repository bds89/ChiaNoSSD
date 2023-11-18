# Chia NoSSD bot

Control and monitoring for NoSSD Chia pool client.

<img src="screenshots/1.gif" width="300">


**Supported OS**

- Linux

**Launching**


1. Unpack the ChiaNoSSD.zip
2. Edit `config.yaml` 
- put your telegram `BOT_TOKEN`, from https://t.me/BotFather
- put patch to NoSSD folder in `NoSSD_PATCH`
- put all arguments, for start NoSSD client in `NoSSD_PARAMS`
- remove `NODES` if you have only one node

3. Run

**Description**
1. Commands:
- `/start` - start conversation with bot
- `/cancel` - stop conversation with bot
- `/logout` - un authorization in bot
- `/settings` - user settings (admin settings in develop)
- `/run` - run NoSSD client
- `/stop` - stop NoSSD client by sending ctrl+c (current plot will be completed)
- `/kill` - kill NoSSD client process immediately
- `/log` - send last 100 messages from miner

2. Config variables:
* - required params
- `BOT_TOKEN`* - Your telegram token, from https://t.me/BotFather
- `NoSSD_PATCH`* - Patch to folder with NoSSD client
- `NoSSD_PARAMS`* - Arguments for start NoSSD client. Example: "-a xch18s44l93zegl3p3awkhfdwy5hhuj74wvkuzndvasjgkx7w37s4dsqpumnje -c 15 -w bds89 -d,p /media/bds89/test"
- `PASSWORD` - Password for you bot
- `ADMIN_PASSWORD` - Admin password for you bot (you can change NoSSD_PARAMS, passwords, and delete users from BD)
- `RUN_AT_STARTUP` - Start mining after bot script start
- `SUDO_PASS` - Your sudo password. Needs for collect hdd's temperatures, or you can run bot with sudo, not necessary.
- `SLAVE_PC` - If your farm consists of several nodes, you can make one node the master by setting the `SLAVE_PC` parameter to `False`, and the remaining nodes as slaves. 
Thus, one telegram bot will be enough to monitor all your nodes. 
Switching between farms by sending a message with the farm address number according to the list in the `NODES`. Can be removed if you only have one node.
- `NODES` - List of IP's yours nodes. First address must be Master node. On slave nodes, the list can be limited only by the IP of the master node. 
I use exactly the same config, only with the `SLAVE_PC` parameter. Can be removed if you only have one node.
- `IP` - Each node deploys a server to receive and send messages. 
The script will try to find its own IP, if this does not happen and the script is deployed on 127.0.0.1, 
this parameter can be specified explicitly.Can be removed if you only have one node.

3. Dependencies
- for collect hdds's temperatures you must install a `smartmontools`, not necessary
```bash
sudo apt-get install smartmontools
```
- for collect gpu's params you must install a `nvidia drivers`, not necessary. For test try:
```bash
nvidia-smi
```
**Changes**
<details>
  <summary>0.9</summary>

    Please delete your users.db file after update
  - add `/log` command. Bot saves in memory last 100 messages from miner
  - add turn of warnings messages and/or errors messages in the settings
  - bug fixes
</details>

<details>
  <summary>1.0</summary>

  - add admin settings.
  - System info refreshing 5 seconds.
  - bug fixes
</details>