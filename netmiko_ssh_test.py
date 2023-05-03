from datetime import date
from datetime import datetime
import getpass
import grp
import json
import logging
from netmiko import *
import os
import pwd
from shutil import make_archive
import sys
import time
import traceback

date = date.today()
timestr = time.strftime("%Y-%m-%d-%H%M%S")
interactive_mode = False
json_data = ''

logging.basicConfig(filename=f'{date}-run.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s-%(levelname)s:%(message)s')

try:
    device_file = sys.argv[1]
except IndexError as err:
    logging.error('No device file specified')
    logging.exception(err)
    sys.exit()

try:
    config_file = open('config.json')
    json_data = json.load(config_file)
    config_file.close()
except Exception as err:
    logging.info('No config file, running in interactive mode')
    print('Error loading config, running in interactive mode')

switch={
        'device_type':'',
        'ip':'',
        'username':'',
        'password':'',
        'port':22,
        'secret':'',
        'conn_timeout':20,
        'banner_timeout':20,
        'auth_timeout':20
        }

if interactive_mode:
    #get creds and TFTP server destination
    switch['username']=input("User name: ")
    switch['password']=getpass.getpass(prompt='Enter user password: ')
    switch['secret']=getpass.getpass(prompt='Enter enable password: ')
    tftp_server = input("Enter TFTP server ip: ")
else:
    switch['username']=json_data['config']['username']
    switch['password']=json_data['config']['password']
    switch['secret']=json_data['config']['enable_password']
    tftp_server = json_data['config']['tftp_server']

try:
    with open(device_file) as f:
            for line in f:
                l = line.split(',')

                start_time = datetime.now()
                switch_ip=l[1].strip()
                switch_device_type = l[0].strip()
                output = ''

                switch['device_type'] = switch_device_type
                switch['ip']=switch_ip

                #ssh connect
                try:
                    print(f"Connecting to {switch_ip}...")
                    logging.info(f"Connecting to {switch_ip}...")
                    ssh_connect = ConnectHandler(**switch)
                except NetmikoAuthenticationException as err:
                    logging.error("SSH-CONNECT: Authentication Failed")
                    logging.exception(err)
                except NetmikoTimeoutException as err:
                    logging.error("SSH-CONNECT: Timeout Exception")
                    logging.exception(err)
                except err:
                    logging.error(f"Connection to {switch_ip} failed ...")
                    logging.exception(err)

                #perform switch management
                try:
                    with ConnectHandler(**switch) as net_connect:
                        try:
                            print(f"Connected to {switch_ip}, copying config ...")

                            if switch_device_type == "cisco_ios":
                                net_connect.enable()
                                cmd_list = [
                                        f"copy running-config tftp://{tftp_server}/{switch_ip}-run-backup.txt",
                                        "\n",
                                        "\n"
                                        ]
                                output += net_connect.send_multiline_timing(cmd_list)
                            elif switch_device_type == "dell_os6":
                                net_connect.enable()
                                command_string=f"copy running-config tftp://{tftp_server}/{switch_ip}-run-backup.txt"
                                output += net_connect.send_command_timing(command_string, strip_prompt=False, strip_command=False)
                                output += net_connect.send_command_timing("y", strip_prompt=False, strip_command=False, read_timeout=90)
                            elif switch_device_type == "juniper_junos":
                                cmd_list = [
                                        "start shell",
                                        "cd /config",
                                        "tftp",
                                        f"connect {tftp_server}",
                                        f"put juniper.conf.gz {switch_ip}-conf-backup.gz",
                                        "\x04",
                                        "exit"
                                        ]
                                output += net_connect.send_multiline_timing(cmd_list)
                            print(f"Copy complete for {switch_ip}")
                            logging.info(f"Copy complete for {switch_ip}")
                        except NetMikoTimeoutException as e:
                            logging.error(f"TFTP copy failed for {switch_ip}.")
                            logging.exception(err)
                        except err:
                            logging.error("Unknown error: " + str(err))
                            logging.exception(err)

                        ssh_connect.disconnect()
                        print("Disconnected")
                        logging.info("Disconnected")
                except NetmikoAuthenticationException as err:
                    logging.error(f"Authentication failure for {switch_ip}")
                    logging.exception(err)
                except NetmikoTimeoutException as err:
                    logging.error(f"Timeout connencting to {switch_ip}")
                    logging.exception(err)
                finally:
                    end_time = datetime.now()
                    print(f"Exec time for {switch_ip}: {end_time - start_time}")
                    logging.info(f"Exec time for {switch_ip}: {end_time - start_time}")
                    print()
except FileNotFoundError as e:
    logging.error(f"{device_file} does not exist")
    logging.exception(e)

make_archive(f'{timestr}-archive','zip',root_dir=None, base_dir=f"/tftp/")