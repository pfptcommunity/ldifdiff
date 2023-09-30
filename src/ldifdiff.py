#!/usr/bin/env python3
import json
from enum import Enum
import sys
import argparse
from typing import Dict, TextIO
from ldif import LDIFParser
from colorama import Fore


class DiffType(Enum):
    RIGHT = '[-->] '
    LEFT = '[<--] '
    COMMON = '[<->] '

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


def write_to_stream(message: str = '', diff_type: DiffType = DiffType.COMMON, stream: TextIO = None):
    format = ''
    message.strip()

    if message:
        format = diff_type.value

    if stream is None:
        stream = sys.stdout
        if diff_type == DiffType.RIGHT:
            format = Fore.GREEN + format
        elif diff_type == DiffType.LEFT:
            format = Fore.RED + format
        elif diff_type == DiffType.COMMON:
            format = Fore.WHITE + format

    try:
        stream.write("{}{}\n".format(format, message))
    except AttributeError:
        print("Error: 'stream' object does not support writing.")


def generate_text_output(el_diff: Dict, left: bool, right: bool, common: bool, stream: TextIO = None):
    if right:
        for dn, data in el_diff['right_dns'].items():
            write_to_stream('dn: {}'.format(dn), DiffType.RIGHT, stream)
            for k, v in data.items():
                for e in v:
                    write_to_stream('{}: {}'.format(k, e), DiffType.RIGHT, stream)
            write_to_stream()

    if left:
        for dn, data in el_diff['left_dns'].items():
            write_to_stream('dn: {}'.format(dn), DiffType.LEFT, stream)
            for k, v in data.items():
                for e in v:
                    write_to_stream('{}: {}'.format(k, e), DiffType.LEFT, stream)
            write_to_stream()


    # If common DN doesn't contain any items.

    for dn, data in el_diff['common_dns'].items():
        write_dn = False
        if right:
            for k, v in el_diff['common_dns'][dn]['added_keys'].items():
                if not write_dn:
                    write_to_stream('dn: {}'.format(dn), DiffType.COMMON, stream)
                    write_dn = True
                for e in v:
                    write_to_stream('{}: {}'.format(k, e), DiffType.RIGHT, stream)

        if left:
            for k, v in el_diff['common_dns'][dn]['removed_keys'].items():
                if not write_dn:
                    write_to_stream('dn: {}'.format(dn), DiffType.COMMON, stream)
                    write_dn = True
                for e in v:
                    write_to_stream('{}: {}'.format(k, e), DiffType.LEFT, stream)

        if common:
            if not write_dn:
                write_to_stream('dn: {}'.format(dn), DiffType.COMMON, stream)
                write_dn = True

        for k, v in el_diff['common_dns'][dn]['common_keys'].items():
            if right:
                for e in el_diff['common_dns'][dn]['common_keys'][k]['added_values']:
                    if not write_dn:
                        write_to_stream('dn: {}'.format(dn), DiffType.COMMON, stream)
                        write_dn = True
                    write_to_stream('{}: {}'.format(k, e), DiffType.RIGHT, stream)
            if left:
                for e in el_diff['common_dns'][dn]['common_keys'][k]['removed_values']:
                    if not write_dn:
                        write_to_stream('dn: {}'.format(dn), DiffType.COMMON, stream)
                        write_dn = True
                    write_to_stream('{}: {}'.format(k, e), DiffType.LEFT, stream)
            if common:
                for e in el_diff['common_dns'][dn]['common_keys'][k]['common_values']:
                    if not write_dn:
                        write_to_stream('dn: {}'.format(dn), DiffType.COMMON, stream)
                        write_dn = True
                    write_to_stream('{}: {}'.format(k, e), DiffType.COMMON, stream)
        if write_dn:
            write_to_stream()


def generate_diff_data(ldif_left: Dict, ldif_right: Dict) -> Dict:
    ldif_result = {'left_dns': {}, 'right_dns': {}, 'common_dns': {}}

    left_dns = set(list(ldif_left.keys()))
    right_dns = set(list(ldif_right.keys()))

    removed_dns = left_dns - right_dns
    added_dns = right_dns - left_dns
    common_dns = left_dns.intersection(right_dns)

    # Added DNs (right only)
    for dn in sorted(added_dns):
        ldif_result['right_dns'][dn] = ldif_right[dn]

    # Removed DNs (left only)
    for dn in sorted(removed_dns):
        ldif_result['left_dns'][dn] = ldif_left[dn]

    # DNs on both lists
    for dn in sorted(common_dns):
        left_keys = set(ldif_left[dn].keys())
        right_keys = set(ldif_right[dn].keys())
        removed_keys = left_keys - right_keys
        added_keys = right_keys - left_keys
        common_keys = left_keys.intersection(right_keys)

        ldif_result['common_dns'][dn] = {'added_keys': {}, 'removed_keys': {}, 'common_keys': {}}
        for k in sorted(added_keys):
            ldif_result['common_dns'][dn]['added_keys'][k] = ldif_right[dn][k]

        for k in sorted(removed_keys):
            ldif_result['common_dns'][dn]['removed_keys'][k] = ldif_left[dn][k]

        for k in sorted(common_keys):
            ldif_result['common_dns'][dn]['common_keys'][k] = {'added_values': [], 'removed_values': [],
                                                               'common_values': []}
            left_values = set(ldif_left[dn][k])
            right_values = set(ldif_right[dn][k])
            common_values = right_values.intersection(left_values)
            removed_values = left_values - right_values
            added_values = right_values - left_values
            ldif_result['common_dns'][dn]['common_keys'][k]['added_values'] = sorted(added_values)
            ldif_result['common_dns'][dn]['common_keys'][k]['removed_values'] = sorted(removed_values)
            ldif_result['common_dns'][dn]['common_keys'][k]['common_values'] = sorted(common_values)
    return ldif_result

def main():
    if len(sys.argv) == 1:
        print('ldifdiff [-h] file1 file2')
        exit(1)

    parser = argparse.ArgumentParser(prog="ldifdiff",
                                     description="""Tool for comparing LDIF files""",
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80))

    parser.add_argument('-o', '--output', dest="output")
    parser.add_argument('-l', '--left', dest="left", action='store_true')
    parser.add_argument('-r', '--right', dest="right", action='store_true')
    parser.add_argument('-c', '--common', dest="common", action='store_true')
    parser.add_argument('--color', dest="color", action='store_true')

    parser.add_argument('files', nargs=2)

    args = parser.parse_args()

    ldif_left = get_ldif_dict(args.files[0])
    ldif_right = get_ldif_dict(args.files[1])

    el_diff = generate_diff_data(ldif_left, ldif_right)

    if args.output:
        with open(args.output, 'w', encoding='utf_8_sig') as file:
            generate_text_output(el_diff, args.left, args.right, args.common, file)
    else:
        generate_text_output(el_diff, args.left, args.right, args.common)


# Main entry point of program
if __name__ == '__main__':
    main()
