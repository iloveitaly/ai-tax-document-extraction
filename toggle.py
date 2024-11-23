import logging
import os
import sys
from pathlib import Path

import tomlkit

logging.basicConfig(level=logging.INFO)


def get_package_name_and_version(local_package_path):
    pyproject_path = Path(local_package_path) / "pyproject.toml"
    if not pyproject_path.exists():
        logging.error(f"{pyproject_path} does not exist.")
        return None, None

    with open(pyproject_path, "r") as file:
        content = file.read()
        config = tomlkit.parse(content)
        package_name = config["tool"]["poetry"]["name"]
        version = config["tool"]["poetry"]["version"]
        return package_name, version


def toggle_dependency(file_path, local_package_path):
    package_name, version = get_package_name_and_version(local_package_path)
    if not package_name or not version:
        logging.error("Package name or version could not be determined.")
        return

    with open(file_path, "r+") as file:
        content = file.read()
        config = tomlkit.parse(content)
        dependencies = config["tool"]["poetry"]["dependencies"]

        # Check if the package is a nested table
        if isinstance(dependencies.get(package_name), tomlkit.items.Table):
            # Convert to inline table format
            inline_table = tomlkit.inline_table()
            inline_table["path"] = str(local_package_path)
            inline_table["develop"] = True
            dependencies[package_name] = inline_table
            logging.info(f"Converted {package_name} to inline table format.")
        elif isinstance(
            dependencies.get(package_name), tomlkit.items.InlineTable
        ) or isinstance(dependencies.get(package_name), dict):
            # Convert to PyPI version
            dependencies[package_name] = version
            logging.info(f"Converted {package_name} to PyPI version.")
        else:
            # Default to inline table if not found or is a string
            inline_table = tomlkit.inline_table()
            inline_table["path"] = str(local_package_path)
            inline_table["develop"] = True
            dependencies[package_name] = inline_table
            logging.info(f"Set {package_name} to inline table format by default.")

        file.seek(0)
        file.write(tomlkit.dumps(config))
        file.truncate()


def main(local_package_path):
    if not os.path.isabs(local_package_path):
        local_package_path = os.path.join(os.getcwd(), local_package_path)
    toggle_dependency("pyproject.toml", local_package_path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        logging.error("No path provided for local package.")
        sys.exit(1)
