#!/usr/bin/env python3
'''
Proof of Concept to unpack packed UPX windows binaries using Qiling Framework
Heavily based on the lecture 14 from Ricardo Narvaja Course [0] and blogpost [1]

[0] https://drive.google.com/open?id=1EQn38QrbZdG_bvDyz9CqsxRHNqkC6Hll
[1] https://lopqto.me/posts/automated-malware-unpacking

Author: Nahuel D. Sanchez - 15/02/21
'''
import logging
import sys
sys.path.append("..")
import argparse
import pdb

from qiling import *
from capstone import *

md = Cs(CS_ARCH_X86, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)

'''
We know this due to the fact that we have
the original uncompressed file
'''
ORIGINAL_ENTRY_POINT = 0x401349

'''
# HelloWorldCompressed.exe
...
00408253 6a 00                  PUSH       0x0
00408255 39 c4                  CMP        ESP,EAX
00408257 75 fa                  JNZ        LAB_00408253
00408259 83 ec 80               SUB        ESP,-0x80
0040825c e9 e8 90 ff ff         JMP        LAB_00401349
...
'''
JMP_TO_OEP = 0x0040825c

#[=] [memory.py:139]	[+] 00400000 - 0040a000 - rwx    [PE] (./bin/x86/HelloWorldCompressed.exe)
UPX0_START = 0x400000
DUMP_SIZE = 0xa000

def break_at_oep(ql):
    pdb.set_trace()

def trace_code(ql, address, size):
    try:
        buf = ql.mem.read(address, size)
        for i in md.disasm(buf, address):
            print(":: 0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
    except:
        pass
    

def dump_packed_program(ql):
    logging.info('Dumping program from memory...')
    with open('dump_file_compressed.bin', 'wb') as dump_file:
        dump_file.write(ql.mem.read(UPX0_START, DUMP_SIZE))
    logging.info('File dumped to: dump_file_compressed.bin')


# Our Qiling Sandbox, it will execute the program
def our_sandbox(path, rootfs):
    print('Starting emulation...\n')
    ql = Qiling(path, rootfs,libcache=True)

    # Once we reach the JMP to the OEP we can safely dump
    # the program knowing that it's fully decompressed and
    # that the packer built its own "IAT"
    #ql.hook_address(dump_packed_program, JMP_TO_OEP)
    ql.hook_block(trace_code,begin=0x401000, end=0x00407000)
    ql.run()

# We have to pass the UPX Packed binary
# the required libraries for windows executables
# according to "Important note on Windows DLL and registry" (https://www.qiling.io/install/),
# and the path where the unpacked file will be written.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('WindowsApp',
                    help='Path to UPX Packed Executable')
    parser.add_argument('windows_libs',
                help='Path to the required Windows DLLs')
    #parser.add_argument("output_file", help="path where the dumped file will be written")
    
    args = parser.parse_args()
    our_sandbox([args.WindowsApp], args.windows_libs)
