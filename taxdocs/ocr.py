"""
Distinct from vision models, we need to combine OCR with vision models
"""

import io
import typing as t
from pathlib import Path

import pytesseract
from PIL.Image import Image

OCR_DRIVER: t.Literal["google_vision", "tesseract"] = "tesseract"


def image_to_string(image: Image) -> str:
    """
    Simple entrypoint so we can test with other OCR providers
    """

    if OCR_DRIVER == "google_vision":
        image_bytes_fp = io.BytesIO()
        image.save(image_bytes_fp, format="PNG")
        image_bytes = image_bytes_fp.getvalue()

        return google_vision_ocr(image_bytes)
    elif OCR_DRIVER == "tesseract":
        return tesseract_ocr(image)
    else:
        raise ValueError(f"OCR_DRIVER {OCR_DRIVER} not supported")


def tesseract_ocr(image_bytes: bytes):
    # TODO bytes may not work as an input here
    return pytesseract.image_to_string(image_bytes, lang="eng")


def google_vision_ocr(image_bytes: bytes):
    """
    Google vision does not group data together as cleanly as pytesseract, this is a well-known problem that there
    "Document AI" product solves. It doesn't look much additional work is being put into the google vision product at
    this point.
    """

    from google.cloud import vision

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    # image.source.image_uri = uri

    # response = client.text_detection(image=image)
    response = client.document_text_detection(image=image)
    breakpoint()
    texts = response.text_annotations
    # print("Texts:")

    # for text in texts:
    #     print(f'\n"{text.description}"')

    #     vertices = [
    #         f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
    #     ]

    #     print("bounds: {}".format(",".join(vertices)))

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

    return response.full_text_annotation.text


if __name__ == "__main__":
    image_bytes = Path(
        "tmp/1712094337wo09ucgl.png"
    ).read_bytes()

    google_vision_ocr(image_bytes)
