# Simple tool to compare LDIF files

This tool is used to compare two LDIF files.

### Requirements:

* Python 3.9+
* ldif
* colorama
 
### Installing the Package

You can install the tool using the following command directly from Github.

```
pip install git+https://github.com/pfptcommunity/ldifdiff.git
```

or can install the tool using pip.

```
pip install ldifdiff
```

### Usage

```
usage: ldifdiff [-h] [-o outfile] [-a] [-d] [-e] [-c] files files

Tool for comparing LDIF files

positional arguments:
  files                         Two files to compare

optional arguments:
  -h, --help                    show this help message and exit
  -o outfile, --output outfile  File for output by default data is written to
                                console
  -a, --added                   Show items added to right file
  -d, --deleted                 Show items deleted from left file
  -e, --equal                   Show items that are the same in both
  -c, --color                   Colorize the output
```
