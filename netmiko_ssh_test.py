from datetime import date
from datetime import datetime
#from netmiko import ConnectHandler
from netmiko import *
import traceback
import getpass
import sys


date = date.today()

switch={
        'device_type':'',
        'ip':'',
        'username':'',
        'password':'',
        'port':22,
        'secret':''
        }


#get creds and other stuff
switch['username']=input("User name: ")
switch['password']=getpass.getpass(prompt='Enter user password: ')
switch['secret']=getpass.getpass(prompt='Enter enable password: ')
tftp_server = input("Enter TFTP server ip: ")


with open('switch-list.txt') as f:
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
                ssh_connect = ConnectHandler(**switch)
            except NetmikoAuthenticationException as err:
                print("SSH-CONNECT: Authentication Failed")
            except NetmikoTimeoutException as err:
                print("SSH-CONNECT: Timeout Exception")
            except err:
                print(f"Connection to {switch_ip} failed ...")
                print("Uknown error: " + str(err))

            #perform switch management
            command_string=f"copy running-config tftp://{tftp_server}/{switch_ip}-run-backup.txt"

            if switch_device_type == "cisco_ios":
                print("TO DO: HANDLE CISCO")
            else:
                try:
                    with ConnectHandler(**switch) as net_connect:
                        try:
                            print(f"Connected to {switch_ip}, copying config ...")
                            net_connect.enable()
                            output += net_connect.send_command_timing(command_string, strip_prompt=False, strip_command=False)
                            output += net_connect.send_command_timing("y", strip_prompt=False, strip_command=False, read_timeout=90)
                            print(f"Copy complete for {switch_ip}")
                        except NetMikoTimeoutException as e:
                            print(f"TFTP copy failed for {switch_ip}.")
                        except err:
                            print("Unknown error: " + str(err))

                    ssh_connect.disconnect()
                    print("Disconnected")
                except NetmikoAuthenticationException as err:
                    print(f"Authentication failure for {switch_ip}")
                except NetmikoTimeoutException as err:
                    print(f"Timeout connencting to {switch_ip}")
                finally:
                    end_time = datetime.now()
                    print(f"Exec time for {switch_ip}: {end_time - start_time}")
                    print()
                                                                                             