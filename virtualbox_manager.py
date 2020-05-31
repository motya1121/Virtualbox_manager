#!/usr/local/var/pyenv/shims/python
# coding: utf-8

import argparse
import os
import classes
import xml.etree.ElementTree as ET
import glob
import error

NameSpace = "http://www.virtualbox.org/"


def status(args):
    xml_vbox_dict = {}
    tree = ET.parse(config.VBoxSettingPATH)

    # GET XML DATA
    # get GUI/GroupDefinitions (m=uuid, m=uuid,...)     # Not Used
    # for node in tree.findall(".//{{{0}}}ExtraDataItem[@name='GUI/GroupDefinitions/']".format(NameSpace)):
    #    print(node.attrib["value"])

    # get MachineEntry
    for node in tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
        xml_vbox_dict[node.attrib["uuid"][1:-1]] = node.attrib["src"]

    # GET directory DATA
    for dir_path in config.MachineFolders:
        dir_vbox_list = glob.glob('{0}**/*.vbox'.format(dir_path), recursive=True)

    # PRINT DATA
    all_flag = True if args.added is args.deled else False
    for dir_vbox in dir_vbox_list:
        # GET uuid
        vbox_xml = ET.parse(dir_vbox)
        for node in vbox_xml.findall(".//{{{0}}}Machine".format(NameSpace)):
            uuid = node.attrib["uuid"][1:-1]

        # print data
        if dir_vbox in xml_vbox_dict.values() and (all_flag is True or (all_flag is False and args.added is True)):
            print("{uuid}: 定義済み (file: {f_name})".format(f_name=dir_vbox, uuid=uuid))
        elif dir_vbox not in xml_vbox_dict.values() and (all_flag is True or
                                                         (all_flag is False and args.deled is True)):
            print("{uuid}: 未定義   (file: {f_name})".format(f_name=dir_vbox, uuid=uuid))


def define(args):
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
        for node in tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
            if node.attrib["src"] == vm_name:
                print("[error] 指定したファイルはすでに定義されています．")
                return -1

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


def undefine(args):
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


def main():
    # コマンドラインパーサーを作成
    parser = argparse.ArgumentParser(description='Virtual Box Manager')
    parser.add_argument('-cf', '--config_file', help='使用する設定ファイル(指定なしでこのpythonファイルと同じディレクトリにある"settings.json"を読み込み)')
    subparsers = parser.add_subparsers()

    parser_add = subparsers.add_parser('status', description='制御可能なVMの状態を表示', help='see `status -h`')
    parser_add.add_argument('-a', '--added', action='store_true', help='Virtual Boxに登録されているVMのみ', default=False)
    parser_add.add_argument('-d', '--deled', action='store_true', help='Virtual Boxに登録されているVM + Dropbox上のアーカイブ', default=False)
    parser_add.set_defaults(handler=status)

    parser_commit = subparsers.add_parser('define', description='VMを定義する', help='see `define -h`')
    parser_commit.add_argument('-vn', '--vm_names', help='定義するVMのvboxのパス(複数指定可)', nargs='*', required=True)
    #parser_commit.add_argument('-h', '--help', help='help')
    parser_commit.set_defaults(handler=define)

    parser_commit = subparsers.add_parser('undefine', description='VMを定義から外す', help='see `undefine -h`')
    parser_commit.add_argument('-vn', '--vm_names', help='定義から外すVM名(複数指定可)', nargs='*', required=True)
    #parser_commit.add_argument('-h', '--help', help='help')
    parser_commit.set_defaults(handler=undefine)

    args = parser.parse_args()

    # get config file
    if type(args.config_file) is not str:
        config_file = os.path.dirname(os.path.abspath(__file__)) + '/settings.json'
    else:
        config_file = args.config_file
    config.read_file(config_file_path=config_file)

    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        # 未知のサブコマンドの場合はヘルプを表示
        parser.print_help()


if __name__ == "__main__":
    config = classes.CONFIG()
    main()