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
usage: ldifdiff [-h] [-o outfile] [-l] [-r] [-c] [--left-symbol <]
                [--right-symbol >] [--common-symbol =] [--color]
                files files

Tool for comparing LDIF files

positional arguments:
  files                         Files to compare FILE1 and FILE2

optional arguments:
  -h, --help                    show this help message and exit
  -o outfile, --output outfile  File for output by default data is written to
                                console
  -l, --left                    Show items only in left file
  -r, --right                   Show items only in right file
  -c, --common                  Show items in both left and right file (equal)
  --left-symbol <               Symbol to the left of the entries only in
                                FILE1
  --right-symbol >              Symbol to the left of the entries only in
                                FILE2
  --common-symbol =             Symbol to the left of the entries in both
                                FILE1 and FILE2
  --color                       Colorize the output
```
