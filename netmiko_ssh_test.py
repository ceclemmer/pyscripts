from datetime import date
from datetime import datetime
#from netmiko import ConnectHandler
from netmiko import *
import traceback
import getpass
import sys


date = date.today()

switch={
        'device_type':'dell_os10',
        'ip':'',
        'username':'',
        'password':'',
        'port':22,
        'secret':''
        }


#get creds
switch['username']=input("User name: ")
switch['password']=getpass.getpass(prompt='Enter user password: ')
switch['secret']=getpass.getpass(prompt='Enter enable password: ')


with open('switch-list.txt') as f:
        for line in f:
            start_time = datetime.now()
            switch_ip=line.strip()
            output = ''
            switch['ip']=switch_ip

            #ssh connect
            try:
                print(f"Connecting to {switch_ip}.....", end='')
                ssh_connect = ConnectHandler(**switch)
            except:
                print(f"Connection to {switch_ip} failed ...")

            #perform switch management
            command_string=f"copy running-config tftp://192.168.120.29/{switch_ip}-run-backup.txt"

            try:
                with ConnectHandler(**switch) as net_connect:
                    try:
                        print("Attempting to copy run config to tftp server.....", end='')
                        net_connect.enable()
                        output += net_connect.send_command_timing(command_string, strip_prompt=False, strip_command=False)
                        output += net_connect.send_command_timing("y", strip_prompt=False, strip_command=False, read_timeout=90)
                        print(f"Copy complete for {switch_ip}", end="")
                    except:
                        print("TFTP copy failed.")

                ssh_connect.disconnect()
                print("Disconnected")
            except NetmikoAuthenticationException:
                print(f"Authentication failure for {switch_ip}")
            finally:
                end_time = datetime.now()
                print(f"Exec time for {switch_ip}: {end_time - start_time}")
                print()