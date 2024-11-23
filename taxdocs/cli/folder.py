import json
import os
import time
from pathlib import Path

import funcy_pipe as fp
from whatever import _

import taxdocs
from taxdocs import logger
from taxdocs.docs.personal_1099_int import extract_image
from taxdocs.outputs import wulters

from .utils import versioned_name


# TODO assume 1099 type for now
def process_folder(folder_path, output_name):
    files = (
        # make paths abs first
        os.listdir(folder_path)
        | fp.map(fp.partial(os.path.join, folder_path))
        | fp.map(os.path.abspath)
        # TODO support images, not just PDFs
        # `None`s for optional arguments
        | fp.filter(fp.rpartial(str.endswith, ".pdf", None, None))
        | fp.to_list()
    )

    # TODO need structured logging, loguru doesn't do this :/
    logger.info("processing files", files=files)

    user_data = json.loads((taxdocs.root / "user_data.json").read_text())
    extracted_data = files | fp.map(fp.partial(extract_image, user_data)) | fp.to_list()

    # TODO for debugging, disable later!
    (taxdocs.root / f"output/{output_name}.json").write_text(json.dumps(extracted_data))

    return wulters.write(extracted_data, output_name)


if __name__ == "__main__":
    output_name = versioned_name("1099_int_wulters", ["json", "xls"])
    folder_path = "./1099-int-files"

    output = process_folder(folder_path, output_name)
    os.system(f"open {output}")
