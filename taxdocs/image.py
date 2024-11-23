import io

import filetype
import pdf2image

from taxdocs import constants, logger
from taxdocs.ocr import image_to_string


# TODO should research the interactor pattern / command pattern with python
def perform(full_pdf_bytes: bytes, page: int) -> tuple[bytes, str]:
    """
    Convert bytes of pdf and extract text & image data for a single page
    """

    # we can determine the file type via bytes, which is better than file extension
    if filetype.guess(full_pdf_bytes).mime != "application/pdf":
        raise ValueError("File is not a PDF")

    logger.info("converting image to bytes")

    # DPI is very important!
    # TODO maybe use grayscale?
    images = pdf2image.convert_from_bytes(
        full_pdf_bytes, dpi=constants.PDF_TO_IMAGE_DPI
    )

    logger.info("extracting text from image")
    image_text = image_to_string(images[page])

    # Save the first page of the PDF as a PNG in memory
    img_byte_arr = io.BytesIO()
    # TODO is png really the best?
    images[page].save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    return img_bytes, image_text
