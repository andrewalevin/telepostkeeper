import pathlib

long = '297-document.jpg.aes'

path = pathlib.Path(long)
print('path:', path)
print()

path = path.with_suffix('')
print('🆎 MAKE path: ', path)