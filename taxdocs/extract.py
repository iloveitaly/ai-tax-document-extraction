import json
import tempfile
import time
from pathlib import Path

from griptape.drivers import OpenAiVisionImageQueryDriver
from griptape.engines import ImageQueryEngine
from griptape.loaders import ImageLoader
from griptape.structures import Agent

import taxdocs
import taxdocs.docs.personal_1099_div
import taxdocs.docs.personal_1099_int
import taxdocs.docs.personal_w2
import taxdocs.image
from taxdocs import constants, log
from taxdocs.types import TaxDocumentType

MAX_VISION_TOKENS = 2_000


def execute_prompt_on_image_data(image_data: bytes, prompt: str) -> dict:
    "lightweight wrapper around griptape"

    driver = OpenAiVisionImageQueryDriver(
        model="gpt-4-vision-preview",
        image_quality="high",
        # TODO should determine max_tokens dynamically
        # @iloveitaly unfortunately not -- the Vision driver doesn't yet integrate into our text-based tokenizers, and the default output token value (if unset in the driver) is very low (I believe 16). I've found it helpful to tune the max_token values depending on the use case, e.g. lower values to subjectively describe an image, higher values to parse text, etc., but I understand that's not very dynamic.
        max_tokens=MAX_VISION_TOKENS,
    )

    # NOTE that this cannot be used with the `agent`, which means a `structure` is not created
    engine = ImageQueryEngine(
        image_query_driver=driver,
    )

    image_artifact = ImageLoader().load(image_data)

    result = engine.run(prompt, [image_artifact])

    # TODO really don't want this information headed to the primary logs :/
    log.debug("image extraction result", result=result.value)

    # TODO if json is improperly formatted, this will fail

    return json.loads(result.value)


def persist_prompt_contents(image_data: bytes, prompt: str) -> None:
    "write image + prompt to disk for debugging"

    uid = f"{int(time.time())}"

    image_file = tempfile.NamedTemporaryFile(
        dir=taxdocs.root / "tmp", prefix=uid, suffix=".png", delete=False
    )
    prompt_file = tempfile.NamedTemporaryFile(
        dir=taxdocs.root / "tmp", prefix=uid, suffix=".txt", delete=False
    )

    with open(image_file.name, "wb") as f:
        f.write(image_data)

    Path(prompt_file.name).write_text(prompt)

    log.info(f"Image saved to {image_file.name}")
    log.info(f"Prompt saved to {prompt_file.name}")


def perform(
    *, user_data, extraction_type: TaxDocumentType, full_pdf_bytes: bytes, page: int
):
    log.local(page=page, extraction_type=extraction_type)

    # first, let's extract the page bytes & text on the page
    image_data, image_text = taxdocs.image.perform(full_pdf_bytes, page)

    prompt_generator = {
        "1099_int": taxdocs.docs.personal_1099_int.generate_prompt,
        "1099_div": taxdocs.docs.personal_1099_div.generate_prompt,
        "w2": taxdocs.docs.personal_w2.generate_prompt,
    }[extraction_type]

    prompt = prompt_generator(user_data=user_data, image_text=image_text)

    if constants.DEBUG_EXTRACTION:
        persist_prompt_contents(image_data, prompt)

    extracted_data = execute_prompt_on_image_data(image_data, prompt)

    log.clear()

    return extracted_data
