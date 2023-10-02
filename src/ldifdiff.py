#!/usr/bin/env python3
import argparse
import sys
from typing import Dict, TextIO, List
from colorama import Fore
from ldif import LDIFParser

class ElDiffPrinter:
    __stream: TextIO
    __action_symbols: Dict
    __action_colors: Dict
    __action_display: Dict
    __colors: bool

    def __init__(self, stream: TextIO = sys.stdout):
        self.__symbol_colors = None
        self.__stream = stream
        self.__action_symbols = {'>': '> ', '<': '< ', '=': '= '}
        self.__action_colors = {'>': Fore.GREEN, '<': Fore.RED, '=': Fore.WHITE}
        self.__action_display = {'>': True, '<': True, '=': True}
        self.__colors = False

    def set_stream(self, stream: TextIO):
        self.__stream = stream

    @property
    def right_symbol(self) -> str:
        return self.__action_symbols['>']

    @right_symbol.setter
    def right_symbol(self, symbol: str):
        self.__action_symbols['>'] = symbol

    @property
    def left_symbol(self) -> str:
        return self.__action_symbols['<']

    @left_symbol.setter
    def left_symbol(self, symbol: str):
        self.__action_symbols['<'] = symbol

    @property
    def common_symbol(self) -> str:
        return self.__action_symbols['=']

    @common_symbol.setter
    def common_symbol(self, symbol: str):
        self.__action_symbols['='] = symbol

    @property
    def left_color(self) -> str:
        return self.__action_colors['<']

    @left_color.setter
    def left_color(self, color: str):
        self.__action_colors['<'] = color

    @property
    def right_color(self) -> str:
        return self.__action_colors['>']

    @right_color.setter
    def right_color(self, color: str):
        self.__action_colors['>'] = color

    @property
    def common_color(self) -> str:
        return self.__action_colors['=']

    @common_color.setter
    def common_color(self, color: str):
        self.__action_colors['='] = color

    @property
    def left_display(self) -> bool:
        return self.__action_display['<']

    @left_display.setter
    def left_display(self, display: bool):
        self.__action_display['<'] = display

    @property
    def right_display(self) -> bool:
        return self.__action_display['>']

    @right_display.setter
    def right_display(self, display: bool):
        self.__action_display['>'] = display

    @property
    def common_display(self) -> bool:
        return self.__action_display['=']

    @common_display.setter
    def common_display(self, display: bool):
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
                    has_added = self.__key_search(data, ['>'])
                    has_removed = self.__key_search(data, ['<'])
                    special_case = (self.__action_display['>'] and has_added or
                                    self.__action_display['<'] and has_removed)

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

    left_only = lv - rv
    right_only = rv - lv
    common = lv.intersection(rv)

    if sorted(left_only):
        diff['<'] = sorted(left_only)
    if sorted(right_only):
        diff['>'] = sorted(right_only)
    if sorted(common):
        diff['='] = sorted(common)

    return diff


def compare_dict(l: Dict, r: Dict) -> Dict:
    diff = {}
    lk = set(l.keys())
    rk = set(r.keys())

    left_only = lk - rk
    right_only = rk - lk
    common = lk.intersection(rk)

    if sorted(left_only):
        diff['<'] = {k: {'<': l[k]} for k in sorted(left_only)}
    if sorted(right_only):
        diff['>'] = {k: {'>': r[k]} for k in sorted(right_only)}
    if sorted(common):
        diff['='] = {}
        for k in sorted(common):
            if isinstance(l[k], dict):
                diff['='][k] = compare_dict(l[k], r[k])
            else:
                diff['='][k] = compare_array(l[k], r[k])
    return diff


def main():
    if len(sys.argv) == 1:
        print("""usage: ldifdiff [-h] [-o outfile] [-l] [-r] [-c] [--left-symbol <] [--right-symbol >] [--common-symbol =] [--color] files files""")
        exit(1)

    parser = argparse.ArgumentParser(prog="ldifdiff",
                                     description="""Tool for comparing LDIF files""",
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80))

    parser.add_argument('-o', '--output', dest="output", metavar='outfile',
                        help='File for output by default data is written to console')
    parser.add_argument('-l', '--left', dest="left", action='store_true',
                        help='Show items only in left file')
    parser.add_argument('-r', '--right', dest="right", action='store_true',
                        help='Show items only in right file')
    parser.add_argument('-c', '--common', dest="common", action='store_true',
                        help='Show items in both left and right file (equal)')
    parser.add_argument('--left-symbol', dest="left_symbol", type=str, metavar='<', default="< ",
                        help='Symbol to the left of the entries only in FILE1')
    parser.add_argument('--right-symbol', dest="right_symbol", type=str, metavar='>', default="> ",
                        help='Symbol to the left of the entries only in FILE2')
    parser.add_argument('--common-symbol', dest="common_symbol", type=str, metavar='=', default="= ",
                        help='Symbol to the left of the entries in both FILE1 and FILE2')

    parser.add_argument('--color', dest="color", action='store_true', help='Colorize the output')
    parser.add_argument('files', nargs=2, help='Files to compare FILE1 and FILE2')

    args = parser.parse_args()

    ldif_left = get_ldif_dict(args.files[0])
    ldif_right = get_ldif_dict(args.files[1])

    diff = compare_dict(ldif_left, ldif_right)

    printer = ElDiffPrinter()
    printer.colors = args.color

    printer.left_symbol = args.left_symbol
    printer.right_symbol = args.right_symbol
    printer.common_symbol = args.common_symbol

    if args.left or args.right or args.common:
        printer.left_display = False
        printer.right_display = False
        printer.common_display = False
        printer.left_display = args.left
        printer.right_display = args.right
        printer.common_display = args.common

    if args.output:
        with open(args.output, 'w', encoding='utf_8_sig') as file:
            printer.set_stream(file)
            printer.print_diff(diff)
    else:
        printer.print_diff(diff)


# Main entry point of program
if __name__ == '__main__':
    main()
