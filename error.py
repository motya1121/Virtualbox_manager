#!/usr/bin/python
# coding: utf-8

import sys

error_code = {101: "設定ファイルが見つかりません", 102: "ArchiveDirが入力されていない or 不正な値", 103: "VBoxSettingPATHが入力されていない or 不正な値"}


def err_print(errnum: int, errmsg: str = ""):
    print_str = '[{0}] {1}'.format(errnum, error_code[errnum])
    if (errmsg != ""):
        print_str += '({0})'.format(errmsg)
    print(print_str, file=sys.stderr)
