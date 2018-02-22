import os, sys, subprocess
import re


class LinuxCollector:
    def __init__(self):
        self.data = self.collect()

    def collect(self):
        raw_data = {}
        data = {}
        filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
        for key in filter_keys:
            try:
                cmd_result = subprocess.Popen("sudo dmidecode -t system|grep '%s'" % key, stdout=subprocess.PIPE,
                                              shell=True).stdout.read()
                cmd_result = cmd_result.decode().strip()
                raw_data[key] = cmd_result.split(':')[1].strip() if cmd_result.split(':')[1] else -1
            except Exception as e:
                print(e)
                raw_data[key] = -2
        data['asset_type'] = 'server'
        data['manufactory'] = raw_data['Manufacturer']
        data['sn'] = raw_data['Serial Number']
        data['model'] = raw_data['Product Name']
        data['uuid'] = raw_data['UUID']
        data['wake_up_type'] = raw_data['Wake-up Type']
        data.update(self.cpuinfo())
        data.update(self.diskinfo())
        data.update(self.osinfo())
        data.update(self.raminfo())
        data.update(self.nicinfo())
        return data

    def cpuinfo(self):
        base_cmd = "cat /proc/cpuinfo"
        raw_cmd = {
            'cpu_model': "%s | grep 'model name' | head -1 | awk -F: '{print $2}'" % base_cmd,
            'cpu_count': "%s | grep 'processor' | wc -l" % base_cmd,
            'cpu_core_count': "%s | grep 'cpu cores' | awk -F: '{SUM+=$2} END {print SUM}'" % base_cmd,
        }
        raw_data = {}
        for k, v in raw_cmd.items():
            try:
                cmd_result = subprocess.Popen(v, stdout=subprocess.PIPE, shell=True).stdout.read().decode().strip()
                raw_data[k] = cmd_result
            except ValueError as e:
                print(e)
                raw_data[k] = -1

        data = {
            "cpu_model": raw_data["cpu_model"].strip(),
            "cpu_count": raw_data["cpu_count"],
            "cpu_core_count": raw_data["cpu_core_count"],
        }
        return data

    def osinfo(self):
        # 目前支持CentOS和Ubuntu，考虑部分系统没有安装lsb_release，通过查看系统文件获取信息
        if os.path.exists("/etc/centos-release"):
            cmd = "cat /etc/centos-release"
            cmd_result = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode().strip()
            distributor = cmd_result.split()[0]
            release = cmd_result.split()[3] + cmd_result.split()[4]
        elif os.path.exists("/etc/os-release"):  # ubuntu系统查看/etc/os-release
            cmd = "cat /etc/os-release"
            cmd_result = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.readlines()
            distributor = cmd_result[0].decode().strip().split('"')[1]
            # if distributor != 'Ubuntu':
            #     sys.exit("ERROR! Collectiong OSinfo of [%s] is not supported!" % distributor)
            release = cmd_result[1].decode().strip().split('"')[1]

        data = {
            "os_distribution": distributor,
            "os_release": release,
            "os_type": "linux",
        }
        return data

    def raminfo(self):
        cmd = "sudo dmidecode -t 17"
        raw_data_list = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode().split("\n")
        raw_data_list = raw_data_list[4:]  # 删除dmidecode开头3行
        raw_ram_list = []
        temp_raw_item = []
        for line in raw_data_list:
            if line.strip().startswith("Memory Device"):
                if temp_raw_item:
                    raw_ram_list.append(temp_raw_item)
                    temp_raw_item = []
            else:
                temp_raw_item.append(line.strip())
        temp_raw_item.append(temp_raw_item)  # 最后一个插槽的信息补上
        ram_list = []
        for ram_item in raw_ram_list:
            ram_item_size = 0
            ram_item_to_dic = {}
            for i in ram_item:
                data_list = i.split(':')
                if len(data_list) == 2:
                    k, v = data_list
                    if k == 'Size':
                        if v.strip() != "No Module Installed":
                            ram_item_to_dic['capacity'] = v.strip().split()[0]
                            ram_item_size = v.strip().split()[0]
                        else:
                            ram_item_to_dic['capacity'] = 0
                    if k == 'Type':
                        ram_item_to_dic['model'] = v.strip()
                    if k == 'Manufacturer':
                        ram_item_to_dic['manufactory'] = v.strip()
                    if k == 'Serial Number':
                        ram_item_to_dic['sn'] = v.strip()
                    if k == 'Asset Tag':
                        ram_item_to_dic['asset_tag'] = v.strip()
                    if k == 'Locator':
                        ram_item_to_dic['slot'] = v.strip()
            if ram_item_size == 0:  # 大小为0， 空插槽，汇报
                pass
            else:
                ram_list.append(ram_item_to_dic)
        ram_size_cmd = "cat /proc/meminfo|grep MemTotal"
        ram_total_size = \
        subprocess.Popen(ram_size_cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode().split(":")[1].strip()
        ram_total_mb_size = int(ram_total_size.split()[0]) / 1024
        ram_data = {'ram': ram_list,
                    'ram_size': ram_total_mb_size}
        return ram_data

    def nicinfo(self):
        cmd = "ifconfig -a"
        raw_data = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode().split("\n")
        os_cmd = "cat /etc/os-release | head -1 | awk -F\\\" '{print $2}'"
        os_data = subprocess.Popen(os_cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode().strip()
        raw_nic_list = []
        temp_nic_list = []
        if os_data == "CentOS Linux":
            for line in raw_data:
                if "flags=" in line:
                    if temp_nic_list:
                        raw_nic_list.append(temp_nic_list)
                        temp_nic_list = []
                    temp_nic_list.append(line.strip())
                else:
                    temp_nic_list.append(line.strip())
            raw_nic_list.append(temp_nic_list)
            nic_list = []
            nic_dic = {}
            for nic_item in raw_nic_list:
                nic_dic = {}
                for info_line in nic_item:
                    if "flags=" in info_line:
                        nic_name = info_line.split(":")[0]
                    if "inet" in info_line and "netmask" in info_line and "broadcast" in info_line:
                        nic_ip = info_line.split()[1]
                        nic_netmask = info_line.split()[3]
                    if info_line.startswith("ether"):
                        nic_mac = info_line.split()[1]
                p = r'eth(\d*)'
                if re.match(p, nic_name):
                    nic_dic["name"] = nic_name
                    nic_dic["macaddress"] = nic_mac
                    nic_dic["netmask"] = nic_netmask
                    nic_dic["ipaddress"] = nic_ip
                    nic_list.append(nic_dic)
            return {"nic": nic_list}

        elif os_data == "Ubuntu":  # ubuntu系统
            for line in raw_data:
                if "HWaddr" in line:
                    if temp_nic_list:
                        raw_nic_list.append(temp_nic_list)
                        temp_nic_list = []
                    temp_nic_list.append(line.strip())
                else:
                    temp_nic_list.append(line.strip())
            raw_nic_list.append(temp_nic_list)
            nic_list = []
            nic_dic = {}
            for nic_item in raw_nic_list:
                nic_dic = {}
                for info_line in nic_item:
                    if "HWaddr" in info_line:
                        nic_name = info_line.split()[0]
                        nic_mac = info_line.split()[4]
                    if "inet addr" in info_line and "Mask" in info_line and "Bcast" in info_line:
                        nic_ip = info_line.split(":")[1].split()[0]
                        nic_netmask = info_line.split(":")[3]
                p = r'eth(\d*)'
                if re.match(p, nic_name):
                    nic_dic["name"] = nic_name
                    nic_dic["macaddress"] = nic_mac
                    nic_dic["netmask"] = nic_netmask
                    nic_dic["ipaddress"] = nic_ip
                    nic_list.append(nic_dic)
            return {"nic": nic_list}

    def diskinfo(self):
        cmd = "lsblk"
        cmd_result = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode().strip().split("\n")
        disk_list = []
        uuid_result = subprocess.Popen("sudo dmidecode -t system|grep 'UUID'|awk -F: '{print $2}'", stdout=subprocess.PIPE,
                                      shell=True).stdout.read().decode().strip()
        for line in cmd_result:
            if re.match(r'sd[a-z]', line):
                diskname = line.split()[0]
                disksize = line.split()[3]
                disk_list.append({
                    'diskname': uuid_result + '-' + diskname,
                    'disksize': disksize,
                })
        return {'disk': disk_list}


