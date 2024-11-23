"""
Categorize the pages in a PDF file. Use cases:

* Has multiple tax documents in the PDF
* Brokerage form with many pages of transactions
"""

import json

import funcy_pipe as fp
from griptape.drivers import OpenAiChatPromptDriver
from griptape.structures import Agent
from griptape.tasks import PromptTask
from pdf2image import convert_from_path

# TODO reexport should be added to pdf2image
from PIL.Image import Image
from schema import Literal, Optional, Or, Schema

import taxdocs.utils as utils
from taxdocs import logger


def get_prompt(image_text: str) -> str:
    """
    Editable:

    https://docs.google.com/spreadsheets/d/1PLvm-GjQEG30IAVmZIs6BIvQy1byYTn8SG2LoBrpBtI/edit#gid=1752116655
    """

    category_descriptions_raw = utils.get_google_sheet(
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG3yuQxvnj1JaH2pgdsm6oqusMp3MLhzsxpD9Hqsv3WOAuxPwIx8Hn0R49YggBaj-WbWGLKB6oFzxj/pub?gid=1752116655&single=true&output=csv",
        "category_descriptions",
    )

    category_descriptions = utils.read_csv(category_descriptions_raw)

    def add_field_name(r):
        return r | {
            "field_name": (
                [r["category"], r["sub-category"]]
                | fp.compact
                | fp.join_str("_")
                | fp.pipe(utils.to_json_field_name)
            )
        }

    def field_instruction(r):
        return f"* `{r['field_name']}`: {r['description']}"

    category_instructions = (
        category_descriptions
        | fp.where_not(category="")
        | fp.map(add_field_name)
        | fp.map(field_instruction)
        | fp.join_str("\n")
    )

    schema = Schema(
        {
            Literal(
                "category",
                description="Identifier for the tax document based on the document text",
            ): str,
            Literal(
                "reasoning",
                description="One sentence summary of the reasoning for the categorization",
            ): str,
            Optional(
                Literal(
                    "included_documents",
                    description="If 'consolidated_document', list of included documents",
                )
            ): Or("1099_div", "1099_int", "1099_b", "other"),
        }
    ).json_schema("TaxDocumentDescription")

    json_schema = json.dumps(schema, indent=4)

    # NOTE when switching to GPT4-turbo it started to include a ```json, just sometimes
    #      until I capitalized 'WITHOUT'

    return f"""
# Rules

Follow these rules to categorize the included [[Document Text]]:

* The [[Document Text]] represents a US tax document.
* Only return JSON, WITHOUT markdown block.
* Return JSON must follow the JSON Schema below.
* [[Categories]] contains available categories and descriptions.

# Return JSON Schema

{json_schema}

# Categories

{category_instructions}

# Document Text

```
{image_text}
```
"""


def run_prompt(prompt: str) -> dict:

    # TODO we should log to a separate file
    agent = Agent(
        prompt_driver=OpenAiChatPromptDriver(
            model="gpt-4-turbo-preview", response_format="json_object", temperature=0
        )
    )

    agent.add_task(
        PromptTask(
            # TODO note that jinga templates can be used here instead
            prompt,
            # context={"preferred_language": "ENGLISH", "tone": "PLAYFUL"},
        )
    )

    agent.run()

    # TODO document on griptape how to actually get the output, this is crazy
    return json.loads(agent.output_task.output.value)


def perform(pdf_image: Image) -> list[dict]:
    logger.info("categorizing PDF pages", length=len(pdf_image))

    result = []

    for index, page in enumerate(pdf_image):
        # page: <PIL.PpmImagePlugin.PpmImageFile image mode=RGB size=1700x2200 at 0x1059F8420>
        image_text = image_to_string(page)
        prompt = get_prompt(image_text)
        categorization = run_prompt(prompt)

        result.append(categorization | {"page_number": index})

    return result


if __name__ == "__main__":
    image_data = convert_from_path(
        "/path/to/1099/pdf.pdf", dpi=200
    )
    result = perform(image_data)
    breakpoint()
