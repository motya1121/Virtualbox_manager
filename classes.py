#!/usr/bin/python
# coding: utf-8

import os
import configparser
import settings


class CONFIG():
    '''設定ファイルの値を格納する
    '''

    def __init__(self):
        self.MachineFolders = []
        self.VBoxSettingPATH = ""
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

        if settings.DEBUG is True:
            print("[DEBUG]")
            print("MachineFolders:{0}".format(self.MachineFolders))
            print("VBoxSettingPATH:{0}".format(self.VBoxSettingPATH))
            print("config_file_path:{0}".format(self.config_file_path))
            print("[/DEBUG]\n")

        return 0
