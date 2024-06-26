## Introduction

Enjarify is a tool for translating Dalvik bytecode to equivalent Java bytecode. This enjarify-adapter fork exports the `enjarify` method for use in external scripts and is type optimized for building with mypyc.


## Setup
> Install with pip:
```bash
pip install enjarify-adapter
```

## Usage

### Python API
The main entry point is the `enjarify` function. It requires an `.apk` or `.dex` input file path and returns the path the output `.jar` file. If no output arg is provided the output is saved in the same directory as the input file with the name `[INPUT_FILENAME].jar`.


```python
def enjarify(
    input_file: str|Path, # Input .apk or .dex file as a str or pathlib.Path.
    output_file: Optional[str|Path]=None, # Output .jar file as a str or pathlib.Path.
    overwrite=False, # Force overwrite if output file already exists. (Error will raise if not set and output file exists.) 
    raise_translation_errors=False, # Ignore translation errors without raising exceptions.
    quiet=True, # Suppress output to stdout.
    inline_consts=True, # Inline constants.
    prune_store_loads=True, # Remove unnecessary store/load pairs.
    copy_propagation=True, # Perform copy propagation.
    remove_unused_regs=True, # Remove unused registers.
    dup2ize=False, # Replace dup instructions with dup2.
    sort_registers=False, # Sort registers.
    split_pool=False, # Split constant pool.
    delay_consts=False # Delay constant pool entries.
    ) -> Path: # Returns the output .jar file path as a pathlib.Path.
```

The `enjarify` function can be used as follows:

```python
from enjarify import enjarify

inputfile = "yourapp.apk"
outputfile = enjarify(inputfile)
print(f"Output file: {outputfile}")
# Prints: 'Output file: yourapp-enjarify.jar'

inputfile = "classes2.dex"
outputfile = enjarify(inputfile, output="yourapp.jar", force=True)
print(f"Output file: {outputfile}")
# Prints: 'Output file: yourapp.jar'
```

### Command Line Interface
Assuming you set up the script on your path correctly, you can call it from anywhere by just typing enjarify, e.g.

    enjarify yourapp.apk

The most basic form of usage is to just specify an apk file or dex file as input. If you specify a multidex apk, Enjarify will automatically translate all of the dex files and output the results in a single combined jar. If you specify a dex file, only that dex file will be translated. E.g. assuming you manually extracted the dex files you could do

    enjarify classes2.dex

The default output file is [INPUT_FILENAME].jar in the current directory. To specify the filename for the output explicitly, pass the -o or --output option.

    enjarify yourapp.apk -o yourapp.jar

By default, Enjarify will refuse to overwrite the output file if it already exists. To overwrite the output, pass the -f or --force option.

#### CLI options can be found by running `enjarify --help`.
```base
usage: enjarify [-h] [-o OUTPUT] [-f] [-q] [--inline-consts | --no-inline-consts] [--prune-store-loads | --no-prune-store-loads] [--copy-propagation | --no-copy-propagation]
                [--remove-unused-regs | --no-remove-unused-regs] [--dup2ize | --no-dup2ize] [--sort-registers | --no-sort-registers] [--split-pool | --no-split-pool] [--delay-consts | --no-delay-consts]
                INPUT_FILE

Translates Dalvik bytecode (.dex or .apk) to Java bytecode (.jar)

positional arguments:
  INPUT_FILE            Input .dex or .apk file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output .jar file. Default is [input-filename]-enjarify.jar.
  -f, --overwrite       Force overwrite. If output file already exists, this option is required to overwrite.
  -q, --quiet           Suppress output messages.
  --inline-consts, --no-inline-consts
                        Inline constants. Default is True.
  --prune-store-loads, --no-prune-store-loads
                        Prune store and load instructions. Default is True.
  --copy-propagation, --no-copy-propagation
                        Enable copy propagation optimization. Default is True.
  --remove-unused-regs, --no-remove-unused-regs
                        Remove unused registers. Default is True.
  --dup2ize, --no-dup2ize
                        Enable dup2ize optimization. Default is False.
  --sort-registers, --no-sort-registers
                        Sort registers. Default is False.
  --split-pool, --no-split-pool
                        Split constant pool. Default is False.
  --delay-consts, --no-delay-consts
                        Delay constants. Default is False.
  ```


## Why not dex2jar?

Dex2jar is an older tool that also tries to translate Dalvik to Java bytecode. It works reasonably well most of the time, but a lot of obscure features or edge cases will cause it to fail or even silently produce incorrect results. By contrast, Enjarify is designed to work in as many cases as possible, even for code where Dex2jar would fail. Among other things, Enjarify correctly handles unicode class names, constants used as multiple types, implicit casts, exception handlers jumping into normal control flow, classes that reference too many constants, very long methods, exception handlers after a catchall handler, and static initial values of the wrong type.


## Limitations

Currently, only version 35 dex files are supported. This means that the Java 8 related bytecode features introduced in Android N, O, and P are not supported.

Enjarify does not currently translate optional metadata such as sourcefile attributes, line numbers, and annotations.

Enjarify tries hard to successfully translate as many classes as possible, but there are some potential cases where it is simply not possible due to limitations in Android, Java, or both. Luckily, this only happens in contrived circumstances, so it shouldn't be a problem in practice.


## Performance tips

PyPy is much faster than CPython. To install PyPy, see http://pypy.org/. Make sure you get PyPy3 rather than regular PyPy. The Linux wrapper script will automatically use the command pypy3 if available. On Windows, you'll need to edit the wrapper script yourself.

By default, Enjarify runs optimizations on the bytecode which make it more readable for humans (copy propagation, unused value removal, etc.). If you don't need this, you can speed things up by disabling the optimizations with the --fast option. Note that in the very rare case where a class is too big to fit in a classfile without optimization, Enjarify will automatically retry it with all optimizations enabled, so this option does not affect the number of classes that are successfully translated.

### Linux Wrapper Script

For convenience, a wrapper shell script is provided, enjarify.sh. This will try to use Pypy if available, since it is faster than CPython. If you want to be able to call Enjarify from anywhere, you can create a symlink from somewhere on your PATH, such as ~/bin. To do this, assuming you are inside the top level of the repository,

    ln -s "$PWD/enjarify.sh" ~/bin/enjarify

### Windows Wrapper Script

A wrapper batch script, enjarify.bat, is provided. To be able to call it from anywhere, just add the root directory of the repository to your PATH. The batch script will always invoke python3 as interpreter. If you want to use pypy, just edit the script.