#!/usr/bin/env python3

from io import BytesIO

import datetime as dt
import struct
import marshal
import opcode
import dis
import sys

def dud(): pass
CodeType = type(dud.__code__)

def generate_code(code_obj: BytesIO):
    consts = []
    names = []
    varnames = []

    def name(name):
        names.append(name)
        return len(names) - 1

    def const(const):
        consts.append(const)
        return len(consts) - 1

    instructions = [
        ("RESUME", 0),

        ("LOAD_GLOBAL", name("print") + 1),
        ("LOAD_CONST", const("Hello, World!")),
        ("PRECALL", 1),
        ("CALL", 1),
        ("POP_TOP", None),

        ("LOAD_CONST", const(69)),
        ("RETURN_VALUE", None),
    ]

    code = BytesIO()

    cache = bytes([dis.opmap["CACHE"], 0])
    for op, arg in instructions:
        opc = dis.opmap[op]
        if arg is None: arg = 0
        code.write(bytes([opc, arg]))
        code.write(cache * dis._inline_cache_entries[opc])

    code = CodeType(
        0, # argcount
        0, # posonlyargcount
        0, # kwonlyargcount
        0, # nlocals
        1, # stacksize
        2, # flags (newlocals)
        code.getvalue(), # code
        tuple(consts), # consts
        tuple(names), # names
        tuple(varnames), # varnames
        __file__, # filename
        "main", # name
        "main", # qualname
        0, # firstlineno
        b"", # linetable
        b"", # exceptiontable
        (), # freevars
        (), # cellvars
    )
    marshal.dump(code, code_obj)


def main(argv: list[str]):
    filename = "generated.pyc"
    with open(filename, "wb") as f:
        f.write(b"\xa7\x0d") # magic
        f.write(b"\r\n") # crlf (separates magic from the rest of the file)
        f.write(struct.pack("<L", 0)) # flags
        f.write(struct.pack("<L", int(dt.datetime.now().timestamp()))) # timestamp
        
        code_obj = BytesIO()
        generate_code(code_obj)

        code = code_obj.getvalue()
        f.write(struct.pack("<L", len(code))) # size
        f.write(code)

    if len(argv) > 1 and argv[1] == "show":
        import show_pyc
        show_pyc.show_pyc_file(filename)
    else:
        import generated



if __name__ == "__main__":
    main(sys.argv)
