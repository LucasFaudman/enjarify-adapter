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
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from . import parsedex
from .jvm import writeclass
from .mutf8 import decode
from .jvm.optimization import options


def translate(data, 
              opts: object, 
              classes: Optional[dict[str, bytes]]=None, 
              errors: Optional[dict[str, str]]=None, 
              allowErrors=True, 
              quiet=True) -> tuple[dict[str, bytes], dict[str, str]]:
    dex = parsedex.DexFile(data)
    classes = OrderedDict() if classes is None else classes
    errors = OrderedDict() if errors is None else errors

    for cls in dex.classes:
        unicode_name = decode(cls.name) + '.class'
        if unicode_name in classes or unicode_name in errors:
            if not quiet: print('Warning, duplicate class name', unicode_name)
            continue

        try:
            class_data = writeclass.toClassFile(cls, opts)
            classes[unicode_name] = class_data
        except Exception:
            if not allowErrors:
                raise
            errors[unicode_name] = traceback.format_exc()

        if not quiet and not (len(classes) + len(errors)) % 1000:
            print(len(classes) + len(errors), 'classes processed')
    return classes, errors

def writeToJar(fname: str|Path, classes: dict[str, bytes]):
    with zipfile.ZipFile(fname, 'w') as out:
        for unicode_name, data in classes.items():
            # Don't bother compressing small files
            compress_type = zipfile.ZIP_DEFLATED if len(data) > 10000 else zipfile.ZIP_STORED
            info = zipfile.ZipInfo(unicode_name)
            info.external_attr = 0o775 << 16 # set Unix file permissions
            out.writestr(info, data, compress_type=compress_type)
            
def enjarify(inputfile: str|Path, output: Optional[str|Path]=None, force=False, fast=False, allowErrors=True, quiet=True) -> Path:
    inputfile = Path(inputfile) if isinstance(inputfile, str) else inputfile
    if not inputfile.exists():
        if not quiet: print('Error, input file', str(inputfile), 'does not exist.')
        raise FileNotFoundError(inputfile)
    
    # detect existing file error before going to the trouble of translating everything
    if not output:
        output = inputfile.with_suffix('.jar')
    elif isinstance(output, str):
        output = Path(output)
            
    if output.exists() and not force:
        if not quiet:
            print('Attempting to write to', str(output))
            print('Error, output file already exists and --force was not specified.')
            print('To overwrite the output file, pass -f or --force.')
        raise FileExistsError(output)

    # unzip the input file and get the dex files if it's an .apk or just read the bytes if it's a .dex
    if inputfile.suffix.lower() == '.apk':
        with zipfile.ZipFile(inputfile, 'r') as z:
            dexs = [z.read(name) for name in z.namelist() if name.startswith('class') and name.endswith('.dex')]            
    else:
        dexs = [inputfile.read_bytes()]

    # translate the dex files to java bytecode
    opts = options.NONE if fast else options.PRETTY
    classes: dict[str, bytes] = OrderedDict()
    errors: dict[str, str] = OrderedDict()
    for data in dexs:
        translate(data, opts=opts, classes=classes, errors=errors, allowErrors=allowErrors, quiet=quiet)

    # write the java bytecode to a .jar file
    writeToJar(output, classes)

    # print out any errors that occurred
    if not quiet: 
        print('Output written to', str(output))
        for name, error in sorted(errors.items()):
            print(name, error)
        print('{} classes translated successfully, {} classes had errors'.format(len(classes), len(errors)))
    
    return output


def main():
    parser = argparse.ArgumentParser(prog='enjarify', description='Translates Dalvik bytecode (.dex or .apk) to Java bytecode (.jar)')
    parser.add_argument('inputfile', type=Path, help='Input .dex or .apk file')
    parser.add_argument('-o', '--output', type=Path, default=None, help='Output .jar file. Default is [input-filename]-enjarify.jar.')
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite. If output file already exists, this option is required to overwrite.')
    parser.add_argument('--fast', action='store_true', help='Speed up translation at the expense of generated bytecode being less readable.')
    args = parser.parse_args()
    
    # Call enjarify with the parsed arguments and allowErrors=True and quiet=False to leave CLI behavior unchanged
    enjarify(args.inputfile, args.output, args.force, args.fast, allowErrors=True, quiet=False)

    
if __name__ == "__main__":
    main()
