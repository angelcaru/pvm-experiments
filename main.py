#!/usr/bin/env python3

from __future__ import annotations
from io import BytesIO
from dataclasses import dataclass, field

import datetime as dt
import struct
import marshal
import opcode
import dis
import sys

def dud(): pass
CodeType = type(dud.__code__)

@dataclass
class PyCodeBuilder:
    """
    Builder class for code objects.
    """
    fn_name: str
    argcount: int
    stacksize: int
    consts: list[object] = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    varnames: list[str] = field(default_factory=list)
    filename: str = field(default="<assembly>")
    instructions: list[tuple[str, int | None]] = field(default_factory=list)
    
    def name(self, name):
        """Use this method to use a name inside Python ASM"""
        if name in self.names: return self.names.index(name)
        self.names.append(name)
        return len(self.names) - 1

    def const(self, const):
        """Use this method to use a constant (number, string literal, None, etc.) inside Python ASM"""
        if const in self.consts: return self.consts.index(const)
        self.consts.append(const)
        return len(self.consts) - 1

    def local(self, local):
        """Use this method to use a local variable inside Python ASM"""
        if local in self.varnames: return self.varnames.index(local)
        self.varnames.append(local)
        return len(self.varnames) - 1
    
    def global_(self, global_):
        """Use this method to use a global builtin variable (print, input, exec, etc.) inside Python ASM"""
        return self.name(global_) * 2 + 1 # why, Python? Why?

    def assemble(self) -> CodeType:
        """Creates a code object from a PyCodeBuilder"""
        ret = BytesIO()

        code = BytesIO()
    
        cache = bytes([dis.opmap["CACHE"], 0])
        for op, arg in self.instructions:
            opc = dis.opmap[op]
            if arg is None: arg = 0
            code.write(bytes([opc, arg]))
            code.write(cache * dis._inline_cache_entries[opc])
    
        code = CodeType(
            self.argcount, # argcount
            0, # posonlyargcount
            0, # kwonlyargcount
            len(self.varnames), # nlocals
            self.stacksize, # stacksize
            2, # flags (newlocals)
            code.getvalue(), # code
            tuple(self.consts), # consts
            tuple(self.names), # names
            tuple(self.varnames), # varnames
            self.filename, # filename
            self.fn_name, # name
            f"generated({__file__})::{self.name}", # qualname
            0, # firstlineno
            b"", # linetable
            b"", # exceptiontable
            (), # freevars
            (), # cellvars
        )
        return code

def generate_code(code_obj: BytesIO):
    code = PyCodeBuilder(fn_name="foo", stacksize=69, argcount=0)

    # Here is the Python ASM code. If you need examples, there is literally one right here. (They say source code is the best documentation)
    # Or you could use the `dis` module from the standard library:
    # ```python
    # import dis
    # def f():
    #     the_code_you_want_as_asm()
    # dis.dis(f)
    # ```
    code.instructions += [
        ("RESUME", 0),

        ("LOAD_GLOBAL", code.global_("print")),
        ("LOAD_CONST", code.const("Hello, World!")),
        ("PRECALL", 1),
        ("CALL", 1),
        ("POP_TOP", None),

        ("LOAD_CONST", code.const(69)),
        ("RETURN_VALUE", None),
    ]

    # Functions are implemented as separate code objects.
    func_code = code.assemble()

    code = PyCodeBuilder(fn_name="<module>", stacksize=69, argcount=0)

    code.instructions += [
        ("LOAD_CONST", code.const(func_code)),
        ("MAKE_FUNCTION", 0),
        ("STORE_NAME", code.name("foo")),

        ("LOAD_GLOBAL", code.global_("exec")),
        # Too lazy to actually implement the `if` statement, so I had Python do it for me
        ("LOAD_CONST", code.const(compile("if __name__ == '__main__': foo()", code.filename, "exec"))),
        ("PRECALL", 1),
        ("CALL", 1),
        ("POP_TOP", None),

        ("LOAD_CONST", code.const(None)),
        ("RETURN_VALUE", None),
    ]
    module_code = code.assemble()
    print("Disassembly of module code:")
    dis.disassemble(module_code)
    print()
    print("Disassembly of function 'foo' code:")
    dis.disassemble(func_code)
    marshal.dump(module_code, code_obj)

MAGIC = b"\xa7\x0d" # Release version 3.11
#MAGIC = b"\xf1\x0d" # CPython `master` branch

def main(argv: list[str]):  
    filename = "generated.pyc"
    with open(filename, "wb") as f:
        f.write(MAGIC) # magic
        f.write(b"\r\n") # crlf (separates magic from the rest of the file)
        f.write(struct.pack("<L", 0)) # flags
        f.write(struct.pack("<L", int(dt.datetime.now().timestamp()))) # timestamp
        
        code_obj = BytesIO()
        generate_code(code_obj)

        code = code_obj.getvalue()
        f.write(struct.pack("<L", len(code))) # size
        f.write(code)

if __name__ == "__main__":
    main(sys.argv)
