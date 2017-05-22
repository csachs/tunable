# tunable

A tiny library to support tunable parameters (think: configuration values) as they often occur in scientific analyses.
A main aspect differing from many other config approaches is, that the tunables are defined as classes where needed
throughout the source, with default value, type, optional documentation etc., which makes later access fast,
IDE-supported (code completion)
and prevents running it with "missing defaults" or misspelled keys leading to runtime errors.

Theoretically, all Python types instantiable from strings are supported, it is however discouraged to use anything but
bool/int/float/str for portability reasons.

There are some more features and concepts, which will hopefully be documented correctly in the future.

## Example

Example test.py:

```python
import argparse
from tunable import Tunable, TunableManager

# tunable values are just defined as classes
# inheriting from Tunable, their documentation
# being normal inline documentation

# their type is derived from their default value

class MyValue(Tunable):
    """An important tunable."""
    default = 42.0


def main():

    # TunableManager provides some argparser-actions
    # to allow users to interact with tunables
    p = argparse.ArgumentParser()
    TunableManager.register_argparser(p)
    p.parse_args()

    # Access to the value is straightforward:
    print(MyValue.value)

    # will be accessed once dynamically with checks,
    # afterwards as a simple lookup

if __name__ == '__main__':
    main()

```

Without arguments:
```bash
> python test.py
42.0
```

Functionality can automatically be registered with argparser.
```bash
> python test.py --help
usage: test.py [-h] [--tunables-show] [-t TUNABLE]
               [--tunables-load TUNABLES_LOAD] [--tunables-save TUNABLES_SAVE]

optional arguments:
  -h, --help            show this help message and exit
  --tunables-show
  -t TUNABLE, --tunable TUNABLE
  --tunables-load TUNABLES_LOAD
  --tunables-save TUNABLES_SAVE
```
Show set tunables:
```bash
> python test.py --tunables-show
### Tunables ###

# An important tunable.
# type: float
MyValue=42.0

```

Changing a tunable via command line:
(See how int(21) was upcasted to float)
```bash
> python test.py -t MyValue=21
21.0
```

Tunables can be saved/loaded from files, currently supported are key=value style config files, JSON and YAML.
XML and DER are planned.

To help reproducibility, a hash of all tunables currently set can be generated:
```python
print(TunableManager.get_hash())
```
```
51869058fca8e234f73fd3a0f010140141d22c6ebf132303f759be14e68075d5dce5476e96c7660b1d43e7bc2ac3b78515ca0738ec0fd54f2774a49ace549495
```
Cryptographic hashing is based upon the SHA-512 hash of a canonicalized DER based serialization of the tunables.

## Stability
Warning, this library is alpha software, whose interface is subject to change without notice!
Especially, no guarantees are made that the hashing is not going to change, which might lead to wrongly changed hashes!

## License

MIT