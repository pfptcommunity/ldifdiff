#!/usr/bin/env python3
import json
from enum import Enum
import sys
import argparse
from typing import Dict, TextIO, List, Union
from colorama.ansi import AnsiFore
from ldif import LDIFParser
from colorama import Fore


class ElDiffPrinter:
    __stream: TextIO
    __action_symbols: Dict
    __action_colors: Dict
    __action_display: Dict
    __colors: bool

    def __init__(self, stream: TextIO = sys.stdout):
        self.__symbol_colors = None
        self.__stream = stream
        self.__action_symbols = {'+': '<+> ', '-': '<-> ', '=': '<=> '}
        self.__action_colors = {'+': Fore.GREEN, '-': Fore.RED, '=': Fore.WHITE}
        self.__action_display = {'+': True, '-': True, '=': True}
        self.__colors = False

    def set_stream(self, stream: TextIO):
        self.__stream = stream

    @property
    def added_symbol(self) -> str:
        return self.__action_symbols['+']

    @property
    def deleted_symbol(self) -> str:
        return self.__action_symbols['-']

    @property
    def equals_symbol(self) -> str:
        return self.__action_symbols['=']

    @added_symbol.setter
    def added_symbol(self, symbol: str):
        self.__action_symbols['+'] = symbol

    @deleted_symbol.setter
    def deleted_symbol(self, symbol: str):
        self.__action_symbols['-'] = symbol

    @equals_symbol.setter
    def equals_symbol(self, symbol: str):
        self.__action_symbols['='] = symbol

    @property
    def added_color(self) -> str:
        return self.__action_colors['+']

    @property
    def deleted_color(self) -> str:
        return self.__action_colors['-']

    @property
    def equals_color(self) -> str:
        return self.__action_colors['=']

    @added_color.setter
    def added_color(self, color: str):
        self.__action_colors['+'] = color

    @deleted_color.setter
    def deleted_color(self, color: str):
        self.__action_colors['-'] = color

    @equals_color.setter
    def equals_color(self, color: str):
        self.__action_colors['='] = color

    @property
    def added_display(self) -> bool:
        return self.__action_display['+']

    @property
    def deleted_display(self) -> bool:
        return self.__action_display['-']

    @property
    def equals_display(self) -> bool:
        return self.__action_display['=']

    @added_display.setter
    def added_display(self, display: bool):
        self.__action_display['+'] = display

    @deleted_display.setter
    def deleted_display(self, display: bool):
        self.__action_display['-'] = display

    @equals_display.setter
    def equals_display(self, display: bool):
        self.__action_display['='] = display

    @property
    def colors(self) -> bool:
        return self.__colors

    @colors.setter
    def colors(self, colors: bool):
        self.__colors = colors

    def __write(self, action: str = None, message: str = ''):
        message.strip()

        symbol = self.__action_symbols.get(action, '')

        color = ''

        if self.__colors:
            color = self.__action_colors.get(action, Fore.RESET)

        format = color + symbol

        try:
            self.__stream.write("{}{}\n".format(format, message))
        except AttributeError:
            print("Error: 'stream' object does not support writing.")

    def __key_search(self, haystack: Dict, keys_to_find: List):
        for k in keys_to_find:
            if k in haystack:
                return True
        for value in haystack.values():
            if isinstance(value, dict):
                # If a value is itself a dictionary, recursively search within it
                if self.__key_search(value, keys_to_find):
                    return True
        return False

    def __print_attr(self, diff: Dict, attribute: str = ''):
        for action in diff:
            if isinstance(diff[action], dict):
                for entry in diff[action]:
                    if isinstance(diff[action][entry], dict):
                        self.__print_attr(diff[action][entry], entry)
                    else:
                        if self.__action_display[action]:
                            for v in diff[action][entry]:
                                self.__write(action, '{}: {}'.format(entry, v))
            else:
                if self.__action_display[action]:
                    for v in diff[action]:
                        self.__write(action, '{}: {}'.format(attribute, v))

    def print_diff(self, diff: Dict):
        for action in diff:
            for entry, data in diff[action].items():
                special_case = False
                # Special case to show dn value, when show equal is off
                if not self.__action_display['=']:
                    has_added = self.__key_search(data, ['+'])
                    has_removed = self.__key_search(data, ['-'])
                    special_case = (self.__action_display['+'] and has_added or
                                    self.__action_display['-'] and has_removed)

                if self.__action_display[action] or special_case:
                    self.__write(action, '{}: {}'.format('dn', entry))
                    self.__print_attr(data)
                    self.__write()


class LDIFParserNoError(LDIFParser):
    # Remove annoying warnings
    def _error(self, msg):
        if self._strict:
            raise ValueError(msg)


def get_ldif_dict(filename):
    ldif_data = {}
    with open(filename, "rb") as ldif_file:
        parser = LDIFParserNoError(ldif_file, strict=False)
        for dn, record in parser.parse():
            ldif_data[dn] = record
        ldif_file.close()
    return ldif_data


def compare_array(l: List, r: List) -> Dict:
    diff = {}
    lv = set(l)
    rv = set(r)

    av = rv - lv
    dv = lv - rv
    cv = lv.intersection(rv)

    if sorted(av):
        diff['+'] = sorted(av)
    if sorted(dv):
        diff['-'] = sorted(dv)
    if sorted(cv):
        diff['='] = sorted(cv)

    return diff


def compare_dict(l: Dict, r: Dict) -> Dict:
    diff = {}
    lk = set(l.keys())
    rk = set(r.keys())

    ak = rk - lk
    dk = lk - rk
    ck = lk.intersection(rk)

    if sorted(ak):
        diff['+'] = {k: {'+': r[k]} for k in sorted(ak)}
    if sorted(dk):
        diff['-'] = {k: {'-': l[k]} for k in sorted(dk)}
    if sorted(ck):
        diff['='] = {}
        for k in sorted(ck):
            if isinstance(l[k], dict):
                diff['='][k] = compare_dict(l[k], r[k])
            else:
                diff['='][k] = compare_array(l[k], r[k])
    return diff


def main():
    if len(sys.argv) == 1:
        print('ldifdiff [-h] file1 file2')
        exit(1)

    parser = argparse.ArgumentParser(prog="ldifdiff",
                                     description="""Tool for comparing LDIF files""",
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80))

    parser.add_argument('-o', '--output', dest="output", metavar='outfile',
                        help='File for output by default data is written to console')
    parser.add_argument('-a', '--added', dest="added", action='store_true',
                        help='Show items added to right file')
    parser.add_argument('-d', '--deleted', dest="deleted", action='store_true',
                        help='Show items deleted from left file')
    parser.add_argument('-e', '--equal', dest="equal", action='store_true',
                        help='Show items that are the same in both')
    parser.add_argument('-c', '--color', dest="color", action='store_true', help='Colorize the output')
    parser.add_argument('files', nargs=2, help='Two files to compare')

    args = parser.parse_args()

    ldif_left = get_ldif_dict(args.files[0])
    ldif_right = get_ldif_dict(args.files[1])

    diff = compare_dict(ldif_left, ldif_right)

    printer = ElDiffPrinter()
    printer.colors = args.color
    if args.added or args.deleted or args.equal:
        printer.added_display = False
        printer.deleted_display = False
        printer.equals_display = False
        printer.added_display = args.added
        printer.deleted_display = args.deleted
        printer.equals_display = args.equal

    if args.output:
        with open(args.output, 'w', encoding='utf_8_sig') as file:
            printer.set_stream(file)
            printer.print_diff(diff)
    else:
        printer.print_diff(diff)


# Main entry point of program
if __name__ == '__main__':
    main()
