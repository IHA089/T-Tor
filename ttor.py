import netifaces
from os import system
from re import search
from threading import Thread
from requests  import get
from time import sleep
from stem import Signal, SocketError
from stem.control import Controller
from subprocess import call, check_output
from random import randint
from sys import exit

def get_default_gateway_interface():
    gateways = netifaces.gateways()
    default_gateway = gateways['default']
    return default_gateway[netifaces.AF_INET][1] if netifaces.AF_INET in default_gateway else None

def get_interface_name_by_ip(ip_address):
    for interface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(interface):
            addresses = netifaces.ifaddresses(interface)[netifaces.AF_INET]
            if any(addr['addr'] == ip_address for addr in addresses):
                return interface
    return None

def get_internet_interface():
    default_gateway_interface = get_default_gateway_interface()
    if default_gateway_interface:
        return default_gateway_interface
    else:
        external_ip = '8.8.8.8'
        return get_interface_name_by_ip(external_ip)

def read_file(filename):
    f_read = open(filename, 'r')
    lines = f_read.readlines()
    f_read.close()
    dd = open(filename, 'w')
    for line in lines:
        if "ControlPort 9051" in line:
            line = line.replace("#", "")

        if "HashedControlPassword" in line:
            line = line.replace("#", "")
            hcp = line.replace("HashedControlPassword ", "")

        dd.write(line)
    dd.close()
    return hcp

def generate_random_mac():
    mac = [ 0x00, 0x16, 0x3e,
            randint(0x00, 0x7f),
            randint(0x00, 0xff),
            randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def change_mac(interface, new_mac):
    try:
        call(["sudo", "ifconfig", interface, "down"])
        call(["sudo", "ifconfig", interface, "hw", "ether", new_mac])
        call(["sudo", "ifconfig", interface, "up"])
        print("Current MAC address ::: {}".format(new_mac))
    except Exception as e:
        print("Error:", e)

def get_current_ip():
    try:
        ip = get("https://httpbin.org/ip", proxies={'http':'socks5://127.0.0.1:9050', 'https':'socks5://127.0.0.1:9050'})
        if ip.status_code == 200:
            data = ip.text
            data = data.replace('{\n  "origin": "','')
            data = data.replace('"\n}\n', '')
            print("Current ip ::: {}".format(data))
        else:
            print("Failed to get ip")
    except:
        get_current_ip()


def change_tor_circut(hash_key, internet_interface):
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=hash_key)
            controller.signal(Signal.NEWNYM)
            print("New Tor circuit established.")
            get_current_ip()
            new_mac = generate_random_mac()
            change_mac(internet_interface, new_mac)
    except SocketError as exc:
        print("Unable to connect to Tor control port:", exc)

def start_tor():
    system("service tor start")

def stop_tor():
    system("service tor stop")

def xterm_bind():
    system('''xterm -fa "monospace-10" -title "T-Tor:IHA089" -e "bash -c 'export http_proxy=socks5://127.0.0.1:9050; export https_proxy=socks5://127.0.0.1:9050; exec bash'"''')

def Main():
    try:
        print("you need high speed internet connection")
        ttc = int(input("How much time after you want to change terminal ip(minimum 100 sec) :"))
        if ttc < 100:
            ttc = 100

    except ValueError:
        print("please enter Integer value between 100-1000")
        exit()
    filename = "/etc/tor/torrc"
    hh_key = read_file(filename)
    start_tor()
    internet_interface = get_internet_interface()
    new_mac = generate_random_mac()
    change_mac(internet_interface, new_mac)
    sleep(1)
    xterm_thread = Thread(target=xterm_bind)
    xterm_thread.start()
    sleep(1)
    loop=True
    
    while False:
        try:
            change_tor_circut(hh_key, internet_interface)
            sleep(ttc)
        except KeyboardInterrupt:
            stop_tor()
            loop=False
            print("Exiting by user...")
            exit()
        except Exception as e:
            print("An Exception occur :::  {}".format(e))
            loop=False
            exit()

    exit()
            

if __name__ == "__main__":
    Main()