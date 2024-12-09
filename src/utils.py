import hashlib
import pathlib
from typing import Optional

import yaml


async def write_yaml(path: pathlib.Path, data: any) -> Optional[pathlib.Path]:
    path = pathlib.Path(path)
    try:
        with path.open('w') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print('Error Writing YAML: ', e)
        return

    return path


async def read_yaml(path: pathlib.Path) -> any:
    path = pathlib.Path(path)
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print("Failed to load YAML from %s: %s", path, e)
    except Exception as e:
        print("Unexpected error reading %s: %s", path, e)

    return data

async def get_md5(data: str, salt: str) -> str:
    # Combine the data with the salt
    salted_data = data.encode() + salt.encode()

    # Create MD5 hash object
    md5_hash = hashlib.md5()

    # Update the hash object with the salted data
    md5_hash.update(salted_data)

    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest()
