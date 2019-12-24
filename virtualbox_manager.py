#!/usr/local/var/pyenv/shims/python
# coding: utf-8

import argparse
import os
import classes
import xml.etree.ElementTree as ET
import glob
import subprocess
import sqlite3
import time
import uuid
import datetime

NameSpace = "http://www.virtualbox.org/"


def status(args, vbox):
    vbox_info = "[定義済みVM]\n"
    for vm in vbox.vms:
        vbox_info += "  - uuid:{0}\tname:{1}\n".format(vm.uuid, vm.vm_name)
        if args.more is True:
            vbox_info += "    vbox_path:{0}\n".format(vm.vm_path,)
    print(vbox_info)


def define_from_file(args, vbox):
    for vm_name in args.vm_names:
        if os.path.isfile(vm_name) is False:
            print("[error] 指定したファイルが見つかりませんでした．")
            return -1
        elif vm_name.split(".")[-1] != "vbox":
            print("[error] 指定したファイルはvbox形式ではありません．")
            return -1
        else:
            print("[info] {0}のファイルを読み込みました．".format(vm_name))

        # GET directory DATA
        vbox_xml = ET.parse(vm_name)
        for node in vbox_xml.findall(".//{{{0}}}Machine".format(NameSpace)):
            uuid = node.attrib["uuid"][1:-1]

        # uuid check
        for vm in vbox.vms:
            if vm.uuid == uuid:
                print("その仮想マシンはすでに定義されています．")
                return -1

        tree = ET.parse(config.VBoxSettingPATH)
        root = tree.getroot()
        ET.register_namespace('', NameSpace)

        # ADD to MachineRegistry
        registry = tree.find(".//{{{0}}}MachineRegistry".format(NameSpace))
        new_entry = ET.SubElement(registry, '{{{0}}}MachineEntry'.format(NameSpace))
        new_entry.set('uuid', '{{{0}}}'.format(uuid))
        new_entry.set('src', '{0}'.format(vm_name))

        # ADD to GroupDefinitions
        definitions = tree.find(".//{{{0}}}ExtraDataItem[@name='GUI/GroupDefinitions/']".format(NameSpace))
        new_value = "{old_definitions},m={uuid}".format(old_definitions=definitions.attrib["value"], uuid=uuid)
        definitions.set('value', new_value)

        # ツリー反映
        tree = ET.ElementTree(root)
        print("[info] {0}のファイルを追加しました．".format(vm_name))

    # XML保存
    tree.write(config.VBoxSettingPATH, encoding="UTF-8", xml_declaration=True)


def define_from_backup(args, vbox):
    print("準備中")
    pass


def define(args, vbox):
    if args.vm_names != "":
        define_from_file(args, vbox)
    if args.backup is True:
        define_from_backup(args, vbox)


def undefine(args, vbox):
    for vm_name in args.vm_names:
        if os.path.isfile(vm_name) is False:
            print("[error] 指定したファイルが見つかりませんでした．")
            return -1
        elif vm_name.split(".")[-1] != "vbox":
            print("[error] 指定したファイルはvbox形式ではありません．")
            return -1
        else:
            print("[info] {0}のファイルを読み込みました．".format(vm_name))

        # GET directory DATA
        vbox_xml = ET.parse(vm_name)
        for node in vbox_xml.findall(".//{{{0}}}Machine".format(NameSpace)):
            uuid = node.attrib["uuid"][1:-1]

        tree = ET.parse(config.VBoxSettingPATH)
        root = tree.getroot()
        ET.register_namespace('', NameSpace)

        # get MachineEntry
        error_flag = True
        for node in tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
            if node.attrib["src"] == vm_name:
                error_flag = False
        if error_flag is True:
            print("[error] 指定したファイルは定義されていません")
            return -1

        # ADD to MachineRegistry
        registry = tree.find(".//{{{0}}}MachineRegistry".format(NameSpace))
        for entry in tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
            if entry.attrib['src'] == vm_name:
                registry.remove(entry)

        # ADD to GroupDefinitions
        definitions = tree.find(".//{{{0}}}ExtraDataItem[@name='GUI/GroupDefinitions/']".format(NameSpace))
        new_values = []
        for m in definitions.attrib["value"].split(","):
            if m.find(uuid) == -1:
                new_values.append(m)
        new_value = ','.join(new_values)
        definitions.set('value', new_value)

        # ツリー反映
        tree = ET.ElementTree(root)

        print("[info] {0}のファイルを未定義にしました．".format(vm_name))
        print("cd {0} && open .".format(os.path.dirname(os.path.abspath(vm_name))))

    # XML保存
    tree.write(config.VBoxSettingPATH, encoding="UTF-8", xml_declaration=True)


def backup(args, vbox):
    if os.path.isfile(config.BackupFolder + "virtualbox_manage.db") is False:
        exec_sql("CREATE TABLE backup_vms(uuid TEXT, file_name TEXT, backup_date TEXT, machine TEXT, memo TEXT)")

    for vm in vbox.vms:
        if args.all is True or vm.vm_name in args.vm_names:
            results = exec_sql(
                "SELECT * FROM backup_vms WHERE uuid = '{0}' AND machine = '{1}' ORDER BY backup_date DESC".format(
                    vm.uuid, config.MachineName))
            is_backup = False
            if len(results) == 0:
                is_backup = True
            else:
                num = input("[{0}]{1}にバックアップしたファイルを上書きしてもいいですか?[Y/n] >>".format(
                    vm.vm_name, datetime.datetime.fromtimestamp(float(results[0][2]))))
                if num in ["Y", "y", "n"]:
                    if num in ["Y", "y"]:
                        is_backup = True

            if is_backup is True:
                file_name = str(uuid.uuid4())
                memo = input("メモを入力してください>>")
                cmd = "tar zcvf {dest}{file_name}.tar.gz {src}".format(
                    dest=config.BackupFolder, file_name=file_name, src=os.path.dirname(vm.vm_path))
                subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                exec_sql("INSERT INTO backup_vms values (?,?,?,?,?)",
                         (vm.uuid, file_name, time.time(), config.MachineName, memo))


def exec_sql(sql: str or list, purchases: tuple = ()):
    return_result = []
    conn = sqlite3.connect(config.BackupFolder + 'virtualbox_manage.db')
    c = conn.cursor()
    if type(sql) is str:
        if len(purchases) == 0:
            for row in c.execute(sql):
                return_result.append(row)
        else:
            for row in c.execute(sql, purchases):
                return_result.append(row)
    elif type(sql) is list:
        for s in sql:
            temp_result_list = []
            if len(purchases) == 0:
                for row in c.execute(sql):
                    temp_result_list.append(row)
            else:
                for row in c.execute(sql, purchases):
                    temp_result_list.append(row)
            return_result.append(temp_result_list)
    conn.commit()
    conn.close()
    return return_result


def main():
    # コマンドラインパーサーを作成
    parser = argparse.ArgumentParser(description='Virtual Box Manager')
    parser.add_argument('-cf', '--config_file', help='使用する設定ファイル')
    subparsers = parser.add_subparsers()

    parser_add = subparsers.add_parser('status', description='登録さてている全てのVMの状態を表示', help='see `status -h`')
    parser_add.add_argument('-a', '--added', action='store_true', help='定義されているVMのみ', default=False)
    parser_add.add_argument('-d', '--deled', action='store_true', help='定義されていないVMのみ', default=False)
    parser_add.add_argument('-m', '--more', action='store_true', help='詳細な情報を出力する', default=False)
    parser_add.set_defaults(handler=status)

    parser_commit = subparsers.add_parser('define', description='VMを定義する', help='see `define -h`')
    parser_commit.add_argument('-vn', '--vm_names', help='定義するVMのvboxのパス(複数指定可)', nargs='+')
    parser_commit.add_argument('-b', '--backup', action='store_true', help='バックアップから選ぶ')
    parser_commit.set_defaults(handler=define)

    parser_commit = subparsers.add_parser('undefine', description='VMを定義から外す', help='see `undefine -h`')
    parser_commit.add_argument('-vn', '--vm_names', help='定義から外すVMのvboxのパス(複数指定可)', nargs='+')
    parser_commit.add_argument('-b', '--backup', action='store_true', help='バックアップする')
    parser_commit.set_defaults(handler=undefine)

    parser_commit = subparsers.add_parser('backup', description='VMをバックアップする', help='see `backup -h`')
    parser_commit.add_argument('-vn', '--vm_names', help='バックアップするVM名(複数指定可)', nargs='+')
    parser_commit.add_argument('-a', '--all', action='store_true', help='全てバックアップ')
    parser_commit.set_defaults(handler=backup)

    args = parser.parse_args()

    # get manager config file
    if type(args.config_file) is not str:
        config_file = os.path.dirname(__file__) + "virtualbox_manager.conf"
    else:
        config_file = args.config_file
    if config.read_file(config_file_path=config_file) == -1:
        return -1

    # make virtual box instance
    vbox = classes.VirtualBox(config.VBoxSettingPATH)

    if hasattr(args, 'handler'):
        args.handler(args, vbox)
    else:
        # 未知のサブコマンドの場合はヘルプを表示
        parser.print_help()


if __name__ == "__main__":
    config = classes.CONFIG()
    main()