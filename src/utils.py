import pathlib

import yaml


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