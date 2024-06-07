# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import dalvikformats
from . import util
from typing import Iterator

class DalvikInstruction:
    def __init__(self, type_, pos, newpos, opcode, args):
        self.type = type_
        self.pos = pos
        self.pos2 = newpos
        self.opcode = opcode
        self.args = args

        self.implicit_casts = None
        self.prev_result = None # for move-result/exception
        self.fillarrdata = None
        self.switchdata = None

_it: Iterator[int] = iter(range(999))
Nop: int = next(_it)
Move: int = next(_it)
MoveWide: int = next(_it)
MoveResult: int = next(_it)
Return: int = next(_it)
Const32: int = next(_it)
Const64: int = next(_it)
ConstString: int = next(_it)
ConstClass: int = next(_it)
MonitorEnter: int = next(_it)
MonitorExit: int = next(_it)
CheckCast: int = next(_it)
InstanceOf: int = next(_it)
ArrayLen: int = next(_it)
NewInstance: int = next(_it)
NewArray: int = next(_it)
FilledNewArray: int = next(_it)
FillArrayData: int = next(_it)
Throw: int = next(_it)
Goto: int = next(_it)
Switch: int = next(_it)
Cmp: int = next(_it)
If: int = next(_it)
IfZ: int = next(_it)

ArrayGet: int = next(_it)
ArrayPut: int = next(_it)
InstanceGet: int = next(_it)
InstancePut: int = next(_it)
StaticGet: int = next(_it)
StaticPut: int = next(_it)

# Invoke: int = next(_it)
InvokeVirtual: int = next(_it)
InvokeSuper: int = next(_it)
InvokeDirect: int = next(_it)
InvokeStatic: int = next(_it)
InvokeInterface: int = next(_it)

# actual ops for these are defined in jvm/mathops.py
UnaryOp: int = next(_it)
BinaryOp: int = next(_it)
BinaryOpConst: int = next(_it)

INVOKE_TYPES = InvokeVirtual, InvokeSuper, InvokeDirect, InvokeStatic, InvokeInterface

# instructions which Dalvik considers to throw
THROW_TYPES = INVOKE_TYPES + (ConstString, ConstClass, MonitorEnter, MonitorExit, CheckCast, InstanceOf, ArrayLen, NewArray, NewInstance, FilledNewArray, FillArrayData, Throw, ArrayGet, ArrayPut, InstanceGet, InstancePut, StaticGet, StaticPut, BinaryOp, BinaryOpConst)
# last two only if it is int/long div or rem

# ignore the possiblity of linkage errors (i.e. constants and instanceof can't throw)
# in theory MonitorExit can't throw either due to the structured locking checks, but these are broken and work inconsistently
PRUNED_THROW_TYPES = INVOKE_TYPES + (MonitorEnter, MonitorExit, CheckCast, ArrayLen, NewArray, NewInstance, FilledNewArray, FillArrayData, Throw, ArrayGet, ArrayPut, InstanceGet, InstancePut, StaticGet, StaticPut, BinaryOp, BinaryOpConst)

OPCODES = util.keysToRanges({
    0x00: Nop,
    0x01: Move,
    0x04: MoveWide,
    0x07: Move,
    0x0a: MoveResult,
    0x0e: Return,
    0x12: Const32,
    0x16: Const64,
    0x1a: ConstString,
    0x1c: ConstClass,
    0x1d: MonitorEnter,
    0x1e: MonitorExit,
    0x1f: CheckCast,
    0x20: InstanceOf,
    0x21: ArrayLen,
    0x22: NewInstance,
    0x23: NewArray,
    0x24: FilledNewArray,
    0x26: FillArrayData,
    0x27: Throw,
    0x28: Goto,
    0x2b: Switch,
    0x2d: Cmp,
    0x32: If,
    0x38: IfZ,
    0x3e: Nop, # unused
    0x44: ArrayGet,
    0x4b: ArrayPut,
    0x52: InstanceGet,
    0x59: InstancePut,
    0x60: StaticGet,
    0x67: StaticPut,
    0x6e: InvokeVirtual,
    0x6f: InvokeSuper,
    0x70: InvokeDirect,
    0x71: InvokeStatic,
    0x72: InvokeInterface,
    0x73: Nop, # unused
    0x74: InvokeVirtual,
    0x75: InvokeSuper,
    0x76: InvokeDirect,
    0x77: InvokeStatic,
    0x78: InvokeInterface,
    0x79: Nop, # unused
    0x7b: UnaryOp,
    0x90: BinaryOp,
    0xd0: BinaryOpConst,
    0xe3: Nop, # unused
}, 256)


def parseInstruction(dex, insns_start_pos, shorts, pos):
    word = shorts[pos]
    opcode = word & 0xFF
    newpos, args = dalvikformats.decode(shorts, pos, opcode)

    # parse special data instructions
    switchdata = None
    fillarrdata = None
    if word == 0x100 or word == 0x200: #switch
        size = shorts[pos+1]
        st = dex.stream(insns_start_pos + pos*2 + 4)

        if word == 0x100: #packed
            first_key = st.u32()
            targets = [st.u32() for _ in range(size)]
            newpos = pos + 2 + (1 + size)*2
            switchdata = {(i+first_key):x for i,x in enumerate(targets)}
        else: #sparse
            keys = [st.u32() for _ in range(size)]
            targets = [st.u32() for _ in range(size)]
            newpos = pos + 2 + (size + size)*2
            switchdata = dict(zip(keys, targets))

    if word == 0x300:
        width = shorts[pos+1] % 16
        size = shorts[pos+2] ^ (shorts[pos+3] << 16)
        newpos = pos + ((size * width + 1) // 2 + 4)
        # get array data
        stream = dex.stream(insns_start_pos + pos*2 + 8)
        func = {
            1: stream.u8,
            2: stream.u16,
            4: stream.u32,
            8: stream.u64
        }[width]
        fillarrdata = width, [func() for _ in range(size)]

    # warning, this must go below the special data handling that calculates newpos
    instruction = DalvikInstruction(OPCODES[opcode], pos, newpos, opcode, args)
    instruction.fillarrdata = fillarrdata
    instruction.switchdata = switchdata

    return newpos, instruction

def parseBytecode(dex, insns_start_pos, shorts, catch_addrs):
    ops = []
    pos = 0
    while pos < len(shorts):
        pos, op = parseInstruction(dex, insns_start_pos, shorts, pos)
        ops.append(op)

    # Fill in data for move-result
    for instr, instr2 in zip(ops, ops[1:]):
        if not instr2.type == MoveResult:
            continue
        if instr.type in INVOKE_TYPES:
            called_id = dex.method_id(instr.args[0])
            if called_id.return_type != b'V':
                instr2.prev_result = called_id.return_type
        elif instr.type == FilledNewArray:
            instr2.prev_result = dex.type(instr.args[0])
        elif instr2.pos in catch_addrs:
            instr2.prev_result = b'Ljava/lang/Throwable;'
    assert 0 not in catch_addrs

    # Fill in implicit cast data
    for i, instr in enumerate(ops):
        if instr.opcode in (0x38, 0x39): # if-eqz, if-nez
            if i > 0 and ops[i-1].type == InstanceOf:
                prev = ops[i-1]
                desc_ind = prev.args[2]
                regs = {prev.args[1]}

                if i > 1 and ops[i-2].type == Move:
                    prev2 = ops[i-2]
                    if prev2.args[0] == prev.args[1]:
                        regs.add(prev2.args[1])
                # Don't cast result of instanceof if it overwrites the input
                regs.discard(prev.args[0])
                if regs:
                    instr.implicit_casts = desc_ind, sorted(regs)
    return ops
