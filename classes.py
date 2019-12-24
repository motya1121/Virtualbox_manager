#!/usr/bin/python
# coding: utf-8

import os
import configparser
import settings
import xml.etree.ElementTree as ET
NameSpace = "http://www.virtualbox.org/"


class CONFIG():
    '''設定ファイルの値を格納する
    '''

    def __init__(self):
        self.MachineFolders = []
        self.VBoxSettingPATH = ""
        self.BackupFolder = ""
        self.config_file_path = ""

    def read_file(self, config_file_path: str) -> int:
        '''設定ファイルの読み込み

        Parameters
        ----------
        config_file_path : str, optional
            設定ファイルのパス(絶対パス)), by default os.path.dirname(os.path.abspath(__file__)) + "virtualbox_manager.conf"

        Returns
        -------
        int
            * -1: error
            * other: success
        '''
        error_flag = False

        # check existence of configuration file
        if type(config_file_path) is not str:
            error_flag = True
            return -1
        elif config_file_path == "":
            config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/virtualbox_manager.conf"

        if config_file_path[0] == "/":
            if os.path.isfile(config_file_path):
                self.config_file_path = config_file_path
            else:
                error_flag = True
        else:
            config_file_path = os.getcwd() + "/" + config_file_path
            if os.path.isfile(config_file_path):
                self.config_file_path = config_file_path
            else:
                error_flag = True

        if error_flag is True:
            print("[error] 設定ファイルが見つかりませんでした．")
            return -1

        # parse config
        config = configparser.ConfigParser()
        config.read(self.config_file_path, 'UTF-8')

        #   MachineFolders
        error_dirs = ""
        if config['VBox']['MachineFolders'] is None:
            print("['VBox']['MachineFolders']が存在しません")
            error_flag = True
        else:
            for vm_dir in config['VBox']['MachineFolders'].split(","):
                if os.path.isdir(vm_dir):
                    if vm_dir[-1] != "/":
                        self.MachineFolders.append(vm_dir + "/")
                    else:
                        self.MachineFolders.append(vm_dir)
                else:
                    error_flag = True
                    error_dirs = "{0} '{1}' ".format(error_dirs, vm_dir)

        if error_flag is True:
            print("[error] 設定ファイルで指定されたディレクトリ(MachineFolders)が見つかりませんでした．")
            print("見つからなかったディレクトリ:{0}".format(error_dirs))
            return -1

        #   MachineFolders
        error_dirs = ""
        if config['VBox']['BackupFolder'] is None:
            print("['VBox']['BackupFolder']が存在しません")
            error_flag = True
        else:
            if os.path.isdir(config['VBox']['BackupFolder']):
                if config['VBox']['BackupFolder'][-1] != "/":
                    self.BackupFolder = config['VBox']['BackupFolder'] + "/"
                else:
                    self.BackupFolder = config['VBox']['BackupFolder']
            else:
                error_flag = True
                error_dirs = "{0} '{1}' ".format(error_dirs, config['VBox']['BackupFolder'])

        if error_flag is True:
            print("[error] 設定ファイルで指定されたディレクトリ(BackupFolder)が見つかりませんでした．")
            print("見つからなかったディレクトリ:{0}".format(error_dirs))
            return -1

        #   MachineName
        error_dirs = ""
        if config['VBox']['MachineName'] is None:
            print("['VBox']['MachineName']が存在しません")
            error_flag = True
        else:
            self.MachineName = config['VBox']['MachineName']

        if error_flag is True:
            return -1

        #   VBoxSettingPATH
        if config['VBox']['VBoxSettingPATH'] is None:
            print("['VBox']['VBoxSettingPATH']が存在しません")
        else:
            xml_file = config['VBox']['VBoxSettingPATH']
            if os.path.isfile(xml_file):
                self.VBoxSettingPATH = xml_file
            else:
                error_flag = True

        if error_flag is True:
            print("[error] 設定ファイルで指定されたファイル(VBoxSettingPATH)が見つかりませんでした．")
            print("見つからなかったXMLファイル:{0}".format(xml_file))
            return -1
        return 0

    def __str__(self):
        print("[DEBUG]")
        print("MachineFolders:{0}".format(self.MachineFolders))
        print("VBoxSettingPATH:{0}".format(self.VBoxSettingPATH))
        print("config_file_path:{0}".format(self.config_file_path))
        print("[/DEBUG]\n")


class VirtualMachine():

    def __init__(self, vm_path: str):
        '''init

        Parameters
        ----------
        vbox_file_path : str
            vboxへのpath
        '''
        self.vm_path = vm_path
        self.vm_setting_tree = ET.parse(self.vm_path)
        self.vm_name = ""
        self.uuid = ""
        self.is_define = bool
        # get MachineEntry
        for node in self.vm_setting_tree.findall(".//{{{0}}}Machine".format(NameSpace)):
            self.uuid = node.attrib["uuid"][1:-1]
            self.vm_name = node.attrib["name"]


class VirtualBox():

    def __init__(self, vbox_setting_path: str):
        '''VirtualBox

        Parameters
        ----------
        vbox_setting_path : str
            virtual box の設定ファイル(xml)のパス
        '''
        self.vbox_setting_path = vbox_setting_path
        self.vbox_setting_tree = ET.parse(self.vbox_setting_path)
        self.vms = []
        # get MachineEntry
        for node in self.vbox_setting_tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
            self.vms.append(VirtualMachine(vm_path=node.attrib["src"]))
        # default Machine Folder
        node = self.vbox_setting_tree.find(".//{{{0}}}SystemProperties".format(NameSpace))
        self.defaultMachineFolder = node.attrib["defaultMachineFolder"]

    def is_define(self, uuid):
        for vm in self.vms:
            if vm.uuid == uuid:
                return True
        return False

    def __str__(self):
        vbox_info = "[debug] Virtual box class\n"
        vbox_info += "\tvbox_setting_path:{0}\n".format(self.vbox_setting_path)
        vbox_info += "\tdefaultMachineFolder:{0}\n".format(self.defaultMachineFolder)
        vbox_info += "\tvirtual machines (合計:{0})\n".format(len(self.vms))
        for vm in self.vms:
            vbox_info += "\t  - uuid:{0}\tname:{1}\n".format(vm.uuid, vm.vm_name)
        return vbox_info