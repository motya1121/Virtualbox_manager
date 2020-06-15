#!/usr/bin/python
# coding: utf-8

import os
import error
import json


class CONFIG():
    '''設定ファイルの値を格納する
    '''

    def __init__(self):
        self.ArchiveDir = ""
        self.VBoxSettingPATH = ""
        self.VBoxVMPATH = ''
        self.config_file_path = ""
        self.debug = False

    def read_file(self, config_file_path: str) -> int:
        '''
        設定ファイルの読み込み，ファイルが存在しない場合はerrorを返す．
        相対パスの場合，スクリプトを実行したディレクトリ内と仮定し処理．

        Parameters
        ----------
        config_file_path : str
            設定ファイルのパス(絶対パス))

        Returns
        -------
        int
            * -1: error
            * other: success
        '''

        '''
        check existence of configuration file
        '''
        if type(config_file_path) is not str:
            error.err_print(101)
            return -1
        elif config_file_path == "":
            error.err_print(101)

        if config_file_path[0] == "/":  # Absolute path
            if os.path.isfile(config_file_path):
                self.config_file_path = config_file_path
            else:
                error.err_print(101)
                return -1
        else:
            config_file_path = os.getcwd() + "/" + config_file_path
            if os.path.isfile(config_file_path):
                self.config_file_path = config_file_path
            else:
                error.err_print(101)
                return -1

        # parse config
        with open(config_file_path, 'r') as conf_file:
            json_data = json.load(conf_file)
            self.ArchiveDir = json_data["ArchiveDir"]
            self.VBoxSettingPATH = json_data["VBoxSettingPATH"]
            self.VBoxVMPATH = json_data['VBoxVMPATH']
            if "debug" in json_data.keys():
                self.debug = json_data["debug"]

        #   ArchiveDir
        if self.ArchiveDir is None:
            error.err_print(102)
            return -1
        else:
            if os.path.isdir(self.ArchiveDir) is False:
                error.err_print(102)
                return -1

        #   VBoxSettingPATH
        if self.VBoxSettingPATH is None:
            error.err_print(103)
            return -1
        else:
            if os.path.isfile(self.VBoxSettingPATH) is False:
                error.err_print(103)
                return -1

        if self.debug is True:
            print("[DEBUG]")
            print("MachineFolders:{0}".format(self.ArchiveDir))
            print("VBoxSettingPATH:{0}".format(self.VBoxSettingPATH))
            print("config_file_path:{0}".format(self.config_file_path))
            print("[DEBUG]\n")

        return 0
