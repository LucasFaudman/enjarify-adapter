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

import zipfile, traceback, argparse
from pathlib import Path
from typing import Optional

from .parsedex import DexFile
from .jvm import writeclass
from .jvm.optimization import Options

def translate(data: bytes,
              options: Options, 
              classes: Optional[dict[str, bytes]]=None, 
              errors: Optional[dict[str, str]]=None, 
              raise_translation_errors=False, 
              quiet=True,
              print_every=10
              ) -> tuple[dict[str, bytes], dict[str, str]]:
    dex = DexFile(data)
    classes = {} if classes is None else classes
    errors = {} if errors is None else errors
    classes_processed = len(classes) + len(errors)

    for dex_class in dex.classes:        
        if (unicode_name := dex_class.unicodeName()) in classes:
            if not quiet: print('Warning, duplicate class name', unicode_name)
            continue

        try:
            class_data = writeclass.toClassFile(dex_class, options)
            classes[unicode_name] = class_data
        except Exception:
            if raise_translation_errors:
                raise
            errors[unicode_name] = traceback.format_exc()

        classes_processed += 1
        if not quiet and not (classes_processed) % print_every:
            print(f'\r{classes_processed} classes processed', end='')
    return classes, errors

def write_jar(fname: str|Path, classes: dict[str, bytes]):
    with zipfile.ZipFile(fname, 'w') as out:
        for unicode_name, data in classes.items():
            # Don't bother compressing small files
            compress_type = zipfile.ZIP_DEFLATED if len(data) > 10000 else zipfile.ZIP_STORED
            info = zipfile.ZipInfo(unicode_name)
            info.external_attr = 0o775 << 16 # set Unix file permissions
            out.writestr(info, data, compress_type=compress_type)

def enjarify(input_file: str|Path, 
             output_file: Optional[str|Path]=None, 
             overwrite=False, 
             raise_translation_errors=False, 
             quiet=True,
             inline_consts=True, 
             prune_store_loads=True, 
             copy_propagation=True, 
             remove_unused_regs=True, 
             dup2ize=False,
             sort_registers=False, 
             split_pool=False, 
             delay_consts=False
             ) -> Path:
    input_file = Path(input_file) if isinstance(input_file, str) else input_file
    if not input_file.exists():
        message = f'Error, input file {input_file!s} does not exist.'
        if not quiet: print(message)
        raise FileNotFoundError(message)
    
    # detect existing file error before going to the trouble of translating everything
    if not output_file:
        output_file = input_file.with_suffix('.jar')
    elif isinstance(output_file, str):
        output_file = Path(output_file)
            
    if output_file.exists() and not overwrite:
        if not quiet:
            message = (f'Attempting to write to {output_file!s}\n'
            'Error, output_file file already exists and --overwrite was not specified. '
            'To overwrite the output_file file, pass -f or --overwrite.')
        raise FileExistsError(message)

    # unzip the input file and get the dex files if it's an .apk or just read the bytes if it's a .dex
    if input_file.suffix.lower() == '.apk':
        with zipfile.ZipFile(input_file, 'r') as z:
            dexs = [z.read(name) for name in z.namelist() if name.startswith('class') and name.endswith('.dex')]            
    else:
        dexs = [input_file.read_bytes()]

    # translate the dex files to java bytecode
    options = Options(inline_consts=inline_consts, 
                          prune_store_loads=prune_store_loads, 
                          copy_propagation=copy_propagation, 
                          remove_unused_regs=remove_unused_regs, 
                          dup2ize=dup2ize,
                          sort_registers=sort_registers, 
                          split_pool=split_pool, 
                          delay_consts=delay_consts
                          )
        

    classes: dict[str, bytes] = {}
    errors: dict[str, str] = {}
    for data in dexs:
        translate(data, options=options, classes=classes, errors=errors, raise_translation_errors=raise_translation_errors, quiet=quiet)

    # write the java bytecode to a .jar file
    write_jar(output_file, classes)

    # print out any errors that occurred
    if not quiet: 
        print(f'Output written to {output_file!s}')
        for name, error in sorted(errors.items()):
            print(name, error)
        print(f'{len(classes)} classes translated successfully, {len(errors)} classes had errors')
    
    return output_file


def main():
    parser = argparse.ArgumentParser(prog='enjarify', description='Translates Dalvik bytecode (.dex or .apk) to Java bytecode (.jar)')
    parser.add_argument('INPUT_FILE', type=Path, help='Input .dex or .apk file')
    parser.add_argument('-o', '--output', type=Path, default=None, help='Output .jar file. Default is [input-filename]-enjarify.jar.')
    parser.add_argument('-f', '--overwrite', action='store_true', default=False, help='Force overwrite. If output file already exists, this option is required to overwrite.')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='Suppress output messages.')
    parser.add_argument('--inline-consts', action=argparse.BooleanOptionalAction, default=True, help='Inline constants. Default is True.')
    parser.add_argument('--prune-store-loads', action=argparse.BooleanOptionalAction, default=True, help='Prune store and load instructions. Default is True.')
    parser.add_argument('--copy-propagation', action=argparse.BooleanOptionalAction, default=True, help='Enable copy propagation optimization. Default is True.')
    parser.add_argument('--remove-unused-regs', action=argparse.BooleanOptionalAction, default=True, help='Remove unused registers. Default is True.')
    parser.add_argument('--dup2ize', action=argparse.BooleanOptionalAction, default=False, help='Enable dup2ize optimization. Default is False.')
    parser.add_argument('--sort-registers', action=argparse.BooleanOptionalAction, default=False, help='Sort registers. Default is False.')
    parser.add_argument('--split-pool', action=argparse.BooleanOptionalAction, default=False, help='Split constant pool. Default is False.')
    parser.add_argument('--delay-consts', action=argparse.BooleanOptionalAction, default=False, help='Delay constants. Default is False.')

    args = parser.parse_args()
    print(vars(args))

    # Convert argparse Namespace to function arguments
    output_file = enjarify(
        input_file=args.INPUT_FILE,
        output_file=args.output,
        overwrite=args.overwrite,
        raise_translation_errors=False,
        quiet=args.quiet,
        inline_consts=args.inline_consts,
        prune_store_loads=args.prune_store_loads,
        copy_propagation=args.copy_propagation,
        remove_unused_regs=args.remove_unused_regs,
        dup2ize=args.dup2ize,
        sort_registers=args.sort_registers,
        split_pool=args.split_pool,
        delay_consts=args.delay_consts
    )
    args = parser.parse_args()
    
    print(f'Output written to {output_file!s}')

    
if __name__ == "__main__":
    main()
