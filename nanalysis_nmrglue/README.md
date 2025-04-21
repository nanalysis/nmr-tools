# Using nmrglue with Nanalysis .dx files

Note: nmrglue does not currently work with 2D Jcamp-DX files.
By manually creating the nmrglue dictionary, limited support for processing has
been achieved.

## pseudo2d.py

```
usage: pseudo2d.py [-h] [--debug] [--plot] [--save-fd-csv] filename

Load a pseudo-2D .dx file

positional arguments:
  filename       The pseudo-2D .dx file to load

options:
  -h, --help     show this help message and exit
  --debug        Print debug information (default: False)
  --plot         Plot pseudo-2D data (default: False)
  --save-fd-csv  Save frequency domain .csv files (default: False)
```

When exporting .csv files (one per row,) the filenames are the same as the given filename,
but with the extension changed from `.dx` to `{row}.csv`

The .csv files contain three columns: X (ppm), real, imaginary
