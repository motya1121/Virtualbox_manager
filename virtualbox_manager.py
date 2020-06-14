#!/usr/local/var/pyenv/shims/python
# coding: utf-8

import argparse
import os
import classes
import xml.etree.ElementTree as ET
import glob
import error
import subprocess
import json

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

    for uuid, dir_vbox in xml_vbox_dict.items():
        print("{uuid}: 定義済み (file: {f_name})".format(f_name=dir_vbox, uuid=uuid))

    # GET directory DATA
    if args.all is True:
        archive_file_path = os.path.join(config.ArchiveDir, 'archive_info.json')
        if os.path.isfile(archive_file_path):
            with open(archive_file_path, 'r') as conf_file:
                archive_info = json.load(conf_file)
                for info in archive_info['vm_data']:
                    print("{uuid}: 未定義   (name: {name})".format(name=info['name'], uuid=info['uuid']))


def unarchive(args):
    # TODO: 復帰の実装
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


def archive(args):
    # init valiables
    vm_uuid = args.vm_uuid[0]
    vm_path = ''
    vm_memo = ''
    vm_name = ''
    tree = ET.parse(config.VBoxSettingPATH)

    # init xml file
    root = tree.getroot()
    ET.register_namespace('', NameSpace)

    # Confirm the existence of uuid to xml file
    error_flag = True
    for node in tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
        if node.attrib["uuid"] == '{' + vm_uuid + '}':
            error_flag = False
            vm_path = node.attrib['src']
    if error_flag is True:
        print("[error] 指定したファイルは定義されていません")
        return - 1

    # get vm infomation
    vm_info_tree = ET.parse(vm_path)
    Machine = vm_info_tree.find(".//{{{0}}}Machine".format(NameSpace))
    vm_name = Machine.attrib["name"]
    Description = Machine.find(".//{{{0}}}Description".format(NameSpace))
    vm_memo = Description.text

    # remove to MachineRegistry
    registry = tree.find(".//{{{0}}}MachineRegistry".format(NameSpace))
    for entry in tree.findall(".//{{{0}}}MachineEntry".format(NameSpace)):
        if entry.attrib["uuid"] == '{' + vm_uuid + '}':
            registry.remove(entry)

    # remove to GroupDefinitions
    definitions = tree.find(".//{{{0}}}ExtraDataItem[@name='GUI/GroupDefinitions/']".format(NameSpace))
    new_values = []
    for m in definitions.attrib["value"].split(","):
        if m.find(vm_uuid) == -1:
            new_values.append(m)
    new_value = ','.join(new_values)
    definitions.set('value', new_value)

    # Reflect changes in tree
    tree = ET.ElementTree(root)

    # archive
    com = "tar -zcf {0}.tar.gz {1}".format(
        os.path.join(config.ArchiveDir, vm_uuid),
        os.path.basename(os.path.dirname(vm_path)))
    subprocess.check_call(com.split(' '), cwd=os.path.dirname(os.path.dirname(vm_path)))

    # remove vm file
    com = "rm -R {0}".format(os.path.dirname(vm_path))
    subprocess.check_call(com.split(' '))

    # save XML file
    tree.write(config.VBoxSettingPATH, encoding="UTF-8", xml_declaration=True)

    # update archive info
    archive_info = {}
    archive_file_path = os.path.join(config.ArchiveDir, 'archive_info.json')
    if os.path.isfile(archive_file_path):
        with open(archive_file_path, 'r') as conf_file:
            archive_info = json.load(conf_file)
    else:
        archive_info = {'vm_data': []}
    archive_info['vm_data'].append(
        {
            'uuid': vm_uuid,
            'name': vm_name,
            'memo': vm_memo
        }
    )
    with open(archive_file_path, 'w') as conf_file:
        json.dump(archive_info, conf_file, ensure_ascii=False, indent=4)

    print("[info] {0}を未定義にしました．".format(vm_uuid))


def main():
    # コマンドラインパーサーを作成
    parser = argparse.ArgumentParser(description='Virtual Box Manager')
    parser.add_argument('-cf', '--config_file', help='使用する設定ファイル(指定なしでこのpythonファイルと同じディレクトリにある"settings.json"を読み込み)')
    subparsers = parser.add_subparsers()

    parser_add = subparsers.add_parser('status', description='制御可能なVMの状態を表示', help='see `status -h`')
    parser_add.add_argument('-l', '--list', action='store_true', help='Virtual Boxに登録されているVMのみ', default=False)
    parser_add.add_argument('-a', '--all', action='store_true', help='Virtual Boxに登録されているVM + Dropbox上のアーカイブ', default=False)
    parser_add.set_defaults(handler=status)

    parser_commit = subparsers.add_parser('unarchive', description='VMを元に戻す', help='see `unarchive -h`')
    parser_commit.add_argument('-vu', '--vm_uuid', help='元に戻すVMのUUID', nargs=1, required=True)
    parser_commit.set_defaults(handler=unarchive)

    parser_commit = subparsers.add_parser('archive', description='VMをアーカイブする', help='see `archive -h`')
    parser_commit.add_argument('-vu', '--vm_uuid', help='アーカイブするVMのUUID', nargs=1, required=True)
    parser_commit.set_defaults(handler=archive)

    args = parser.parse_args()

    # get config file
    if type(args.config_file) is not str:
        config_file = os.path.dirname(os.path.abspath(__file__)) + '/settings.json'
    else:
        config_file = args.config_file
    config.read_file(config_file_path=config_file)

    # execute
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        # if unknown option, show hint
        parser.print_help()


if __name__ == "__main__":
    config = classes.CONFIG()
    main()