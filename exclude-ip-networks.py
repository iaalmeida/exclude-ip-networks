#!/usr/bin/env python3
# -*- coding: latin-1 -*-
'''
Exclude IP network addresses presented in a file from Internet global address space
'''

import os, sys
import re, logging
import argparse
import ipaddress

# Versioning
__author__ = 'Ivo Almeida'
__copyright__ = 'Copyright 2019, Millennium bcp'
__version__ = '0.1.0'
__maintainer__ = 'Ivo Almeida'
__email__ = 'ivo.almeida@millenniumbcp.pt'


# Parsing options
parser = argparse.ArgumentParser(description='Exclude network addresses from Internet global address space')
parser.add_argument('-m', '--mask', action='store_true', help='show networks with complete netmasks')
parser.add_argument('-d', '--debug', action='store_true', help='debug')
parser.add_argument('-f', '--file', default='networks-to-exclude.txt', help='file of network addresses to exclude')
parser.add_argument('-s', '--source', metavar='NET/MASK', help='source network to be processed')
parser.add_argument('-x', '--exclude', metavar='NET/MASK', help='network to be excluded')
args = parser.parse_args()


def setupLog():
    log = logging.getLogger(__name__)

    # define logging level
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)

    # define file handler and set formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    return log
#---


def stripComments(line):
    m = re.match(r'^([^#]*)#(.*)$', line)
    if m:  #line contains a comment
        line = m.group(1)
    return line
#---


def readfile(file):
    if not os.path.isfile(file):
        print(f"'{file}' does not exist", file=sys.stderr)
        sys.exit(-1)

    lines = [ ]
    for line in open(file):
        line = stripComments(line)
        if line.strip():
            lines.append(ipaddress.ip_network(line.rstrip('\n')))
    return lines
#---


if __name__ == '__main__':
    log = setupLog()

    if args.source:
        allowed = [ ipaddress.ip_network(args.source) ]
    else:
        log.info(f"using full Internet address space as a source")
        #start with the global address space, /8 bits
        allowed = [ ipaddress.ip_network(str(n)+".0.0.0/2") for n in range(0, 255, 64) ]  #range(0, 256)
    
    if args.exclude:
        denied = [ ipaddress.ip_network(args.exclude) ] 
    else:
        log.info(f"excluding addresses from file '{args.file}'")
        denied = sorted(readfile(args.file))

    log.debug(f'initial address space: {allowed}')
    log.debug(f'  networks to exclude: {denied}')

    a = d = 0
    while a < len(allowed) and d < len(denied):
        #* I can't use a for in range here because these arrays are variable
        if allowed[a] == denied[d]:
            log.debug(f'{allowed[a]} will be excluded')
            del(allowed[a])
            d += 1
        elif allowed[a].supernet_of(denied[d]):
            log.debug(f'{allowed[a]} is a supernet of {denied[d]}')
            excluded = list(allowed[a].address_exclude(denied[d]))
            del(allowed[a])
            allowed[a:a] = sorted(excluded)
            log.debug(f'  exploding to {excluded}')
            d += 1
        else:
            a += 1
    #---

    print('Allowed networks:')
    for net in allowed:
        #pass
        if args.mask:
            print(f' {net.network_address}/{net.netmask}')
        else:
            print(f' {net}')
    log.info(f'{len(allowed)} networks allowed')
#---

sys.exit(0)