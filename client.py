# -*- coding: utf-8 -*-
from __future__ import print_function
import yaml
import requests
import platform as pf
import base64
import json
import subprocess
import os,sys
import time
import psutil,re
import subprocess
import pywifi
import cv2

my_data = dict(pf.uname()._asdict())
if os.name == 'nt':
    import wmi

"""
system = Windows
node = DESKTOP-N5U9EN8
release = 10
version = 10.0.18362
machine = AMD64
processor = Intel64 Family 6 Model 158 Stepping 10, GenuineIntel
"""
uid_file_name = 'demo_uid.txt'
camera = cv2.VideoCapture(0)
def get_info(wifi):
    tmp = wifi.freq
    tmp = tmp/1000 if tmp>10000 else tmp
    return {'bssid': wifi.bssid[:17],'ssid': wifi.ssid,'f': tmp,'signal': wifi.signal}
while True:
    try:
        with open(r'config.yml') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
    except:
        config = {}
    if config.get('path_open') != False:
        ret, frame = camera.read()
        if ret:
            shape = frame.shape
            weight, height = shape[0]//5, shape[1]//5
            frame = cv2.resize(frame, (height, weight), interpolation=cv2.INTER_CUBIC)
            frame = frame.tolist()
    else:
        frame = None
    frame = json.dumps(frame)
    if config.get('pos_open') != False:
        wifi = pywifi.PyWiFi()
        ifaces = wifi.interfaces()[0]
        print(ifaces.name())
        ifaces.scan()
        bessis = ifaces.scan_results()
        wifi_infos =  json.dumps(list(map(get_info,bessis)))
    else:
        wifi_infos = json.dumps(None)
    cord = json.dumps([-10000,-10000,-10000])#[1220,61,55])
    #print(wifi_infos)
    uid_file_name = 'demo_uid.txt'
    my_data = dict(pf.uname()._asdict())
    time.sleep(0.1)
    if config.get('pic_open') != False:
        cpu_percent = psutil.cpu_percent()
        if os.name=='nt':
            w = wmi.WMI(namespace="root/wmi")
            cpu_temperature = w.MSAcpi_ThermalZoneTemperature ()[0].CurrentTemperature/10.0-273.15
        else:
            try:
                cpu_temperature = psutil.sensors_temperatures()['coretemp'][0].current
            except:
                cpu_temperature = 0
        sensor_data = json.dumps([{'s_type': 'CPU溫度','value':cpu_temperature},{'s_type': 'CPU使用率','value':cpu_percent}]).encode("UTF-8")
    else:
        sensor_data = json.dumps(None)
    if os.path.isfile(uid_file_name):
        f = open(uid_file_name,'r')
        ID = f.read()
        f.close()
        #print(ID)
        new_id = ID
        res = requests.post('http://demo-applejenny.dev.rulingcom.com:5000/client', data = {'data':base64.b64encode(json.dumps(my_data).encode("UTF-8")),'id':ID,'sensor_data':sensor_data,'config':json.dumps(config).encode('UTF-8'),'wifi_infos': wifi_infos,'cord':cord,'frame':frame})
        try:
            get_id = res.json().get('id')
        except:
            get_id = None
        if get_id != None:
            new_id = get_id
            if new_id != ID:
                f = open(uid_file_name,'w+')
                f.write(new_id)
                f.close()
    else:
        res = requests.post('http://demo-applejenny.dev.rulingcom.com:5000/client', data = {'data':base64.b64encode(json.dumps(my_data).encode("UTF-8")),'sensor_data':sensor_data,'config':json.dumps(config).encode('UTF-8'),'wifi_infos': wifi_infos,'cord':cord,'frame':frame})
        f = open(uid_file_name,'w+')
        try:
            new_id = res.json()['id']
        except:
            new_id = None
        f.write(new_id)
        f.close()
    try:
        config_change = res.json().get('config_change')
        if config_change != None:
            tmp = json.loads(config_change)
            config = tmp
            with open('config.yml', 'w') as outfile:
                yaml.dump(tmp, outfile, default_flow_style=False)
    except:
        print('get config from server failed')
    update_flag = True if res.json().get('update_flag') else False
    if update_flag:
        tmp = sys.executable
        tmp1 = sys.argv[1:]
        subprocess.call("git fetch origin")
        subprocess.call("git pull origin")
    if new_id != None:
        if update_flag:
            git_head = re.sub("b'|\\\\n'",'',str(subprocess.check_output(['git','rev-parse','HEAD'])))
            res = requests.post('http://demo-applejenny.dev.rulingcom.com:5000/annc',data = {'id': new_id,'update':'finish','git_head': git_head})
        else:
            res = requests.post('http://demo-applejenny.dev.rulingcom.com:5000/annc',data = {'id': new_id})
        if update_flag:
            os.execv(tmp,[tmp, os.path.join(sys.path[0], __file__)] + tmp1)
        print('Announcement:'+res.content.decode('UTF-8'))
        print('config_txt:',config.get('print_txt'))
        if my_data['system'] == 'Linux':
            f = open(uid_file_name,'r')
            parent_id = f.read()
            f.close()
            uid_file_name = 'demo_uid_sub.txt'
            try:
                output = subprocess.check_output('lsusb -v | grep Arduino | grep Bus', shell=True).decode('utf8')
            except:
                output = ''
            if output != '':
                if os.path.isfile(uid_file_name):
                    f = open(uid_file_name,'r')
                    IDs = f.read().split("\n")
                    f.close()
                    #print(ID)
                    outputs = output.split("\n")
                    outputs.remove('')
                    new_ids = []
                    for idx,o in enumerate(outputs):
                        info = o.split()
                        my_data = {'node':info[6],'version':info[8],'parent_id': parent_id}
                        res = requests.post('http://demo-applejenny.dev.rulingcom.com:5000/client', data = {'data':base64.b64encode(json.dumps(my_data).encode("UTF-8")),'id':IDs[idx]})
                        if res.json().get('id') != None:
                            new_id = res.json().get('id')
                            new_ids.append(new_id)
                        else:
                            new_ids.append(ID)
                    if new_ids != IDs:
                        f = open(uid_file_name,'w+')
                        f.write("\n".join(new_ids))
                        f.close()
                else:
                    outputs = output.split("\n")
                    outputs.remove('')
                    new_ids = []
                    for idx,o in enumerate(outputs):
                        info = o.split()
                        my_data = {'node':info[6],'version':info[8],'parent_id': parent_id}
                        res = requests.post('http://demo-applejenny.dev.rulingcom.com:5000/client', data = {'data':base64.b64encode(json.dumps(my_data).encode("UTF-8"))})
                        if res.json().get('id') != None:
                            new_id = res.json().get('id')
                            new_ids.append(new_id)
                        else:
                            new_ids.append(ID)
                    f = open(uid_file_name,'w+')
                    f.write("\n".join(new_ids))
                    f.close()