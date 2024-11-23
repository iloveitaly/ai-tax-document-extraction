import logging
import os
import sys
from pathlib import Path


def get_log_level():
    """Get the log level from the environment variable and normalize it."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level, logging.INFO)


# Configure logging
log_level = get_log_level()
logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
logger = logging.getLogger("module_detection")


def get_local_module_names(directory="."):
    """Retrieve Python file names in the specified directory."""
    logger.debug("Scanning directory for local modules: %s", Path(directory).resolve())
    return {
        file.stem
        for file in Path(directory).iterdir()
        if file.is_file() and file.suffix == ".py"
    }


def get_external_modules():
    """Retrieve names of all external modules including stdlib and site-packages."""
    external_modules = set(sys.builtin_module_names)
    external_modules.update(
        mod for mod in sys.stdlib_module_names if mod not in external_modules
    )
    site_packages_paths = [
        Path(path)
        for path in sys.path
        if "site-packages" in path or "dist-packages" in path
    ]

    for path in site_packages_paths:
        external_modules.update({file.stem for file in path.glob("*.py")})

        # Iterate through each .dist-info directory
        for dist_info in path.glob("*.dist-info"):
            top_level_path = dist_info / "top_level.txt"

            # Only process if top_level.txt exists
            if top_level_path.exists():
                with top_level_path.open("r") as f:
                    external_modules.update(line.strip() for line in f if line.strip())

    return external_modules


def check_local_modules_for_conflicts():
    """
    Check all local module names for conflicts with external modules.
    """
    local_modules = get_local_module_names()
    external_modules = get_external_modules()
    conflicts = local_modules.intersection(external_modules)

    if conflicts:
        logger.info("Conflicting local modules: %s", conflicts)
    else:
        logger.info("No conflicts found between local and external modules.")


# Perform the conflict check
check_local_modules_for_conflicts()
