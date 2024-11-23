import time
from pathlib import Path


def versioned_name(suffix, extensions: list[str]) -> str:
    """
    Only for testing + tinkering right now
    """

    date_str = time.strftime("%m-%d-%y")
    version = 1

    output_name = f"{date_str}-v{version}-{suffix}"

    while any(Path(f"{output_name}.{ext}").exists() for ext in extensions):
        version += 1
        output_name = f"{date_str}-v{version}-{suffix}"

    return output_name
