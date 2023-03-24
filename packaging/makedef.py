#!/usr/bin/env python3
# This file is part of libAudio
#
# SPDX-FileCopyrightText: 2022-2023 amyspark <amy@amyspark.me>
# SPDX-License-Identifier: LGPL-2.1-or-later
#

import argparse
import errno
import pathlib
import os
import re
import subprocess

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Craft a Windows exports or version file')

    arg_parser.add_argument('--format', metavar='FORMAT', default='windows', choices=['msvc', 'darwin', 'gcc'], help='Exports file format')
    arg_parser.add_argument('--prefix', metavar='PREFIX', default='',
                            help='Prefix for extern symbols')
    arg_parser.add_argument('--nm', metavar='NM_PATH', type=pathlib.Path,
                            help='If specified, runs this instead of dumpbin (MinGW)')
    arg_parser.add_argument('--dumpbin', metavar='DUMPBIN_PATH', type=pathlib.Path,
                            help='If specified, runs this instead of nm (MSVC)')
    arg_parser.add_argument('libname', metavar='FILE', type=pathlib.Path,
                            help='Library to parse')

    args = arg_parser.parse_args()

    libname = args.libname

    if not libname.exists():
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), libname)

    started = 0

    def removeprefix(self: str, prefix: str, /) -> str:
        if self.startswith(prefix):
            return self[len(prefix):]
        else:
            return self[:]

    if args.nm is not None:
        # Use eval, since NM="nm -g"
        s = subprocess.run([args.nm, '--defined-only',
                            '-g', libname], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=True)
        dump = s.stdout.splitlines()
        # Exclude lines with ':' (object name)
        dump = [x for x in dump if ":" not in x]
        # Exclude blank lines
        dump = [x for x in dump if len(x) > 0]
        # Take only the third field (split by spaces)
        dump = [x.split()[2] for x in dump]
        # Subst the prefix out
        dump = [removeprefix(x, args.prefix) for x in dump]

    else:
        dump = subprocess.run([args.dumpbin, '-linkermember:1', libname],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).stdout.splitlines()
        # Find the index of the first line with
        # "public symbols", keep the rest
        # Then the line with " Summary",
        # delete it and the rest
        for i, line in enumerate(dump):
            if 'public symbols' in line:
                start = i + 1
            elif re.match(r'\s+Summary', line):
                end = i
        dump = dump[start:end]
        # Substitute prefix out
        dump = [re.sub(f'\s+{args.prefix}', ' ', x) for x in dump]
        # Substitute big chonky spaces out
        dump = [re.sub('\s+', ' ', x) for x in dump]
        # Exclude blank lines
        dump = [x for x in dump if len(x) > 0]
        # Take only the *second* field (split by spaces)
        # Python's split excludes whitespace at the beginning
        dump = [x.split()[1] for x in dump]

    if args.format == 'msvc':
        print("EXPORTS")
        print("\n".join(sorted(set([f'    {i}' for i in dump]))))
    elif args.format == 'darwin':
        print("\n".join(sorted(set(dump))))
    else:
        print(f"{libname.stem.replace('.', '_')} {{")
        print("\tglobal:")
        print(";\n".join(sorted(set([f'\t\t{i}' for i in dump]))))
        print("\tlocal:")
        print("\t\t*;")
        print("};")
