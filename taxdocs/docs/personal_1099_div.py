import funcy_pipe as fp

import taxdocs.utils as utils

get_field_descriptions = fp.partial(
    utils.get_field_descriptions,
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG3yuQxvnj1JaH2pgdsm6oqusMp3MLhzsxpD9Hqsv3WOAuxPwIx8Hn0R49YggBaj-WbWGLKB6oFzxj/pub?gid=1208092835&single=true&output=csv",
    "1099_div_field_descriptions",
)


def field_index_lookup() -> dict[str, int]:
    fields = get_field_descriptions()
    return {field["field_name"]: int(field["index"]) for field in fields}


def generate_prompt(user_data: dict, image_text: str) -> str:
    fields = get_field_descriptions()

    if duplicate_field_names := utils.duplicates_on(fields, "field_name"):
        raise ValueError(f"Duplicate field names found: {duplicate_field_names}")

    duplicate_headers = utils.duplicates_on(fields, "header")
    format_field = fp.partial(utils.format_field, duplicate_headers)
    formatted_fields = fields | fp.map(format_field)
    rules = ["This image and document text represents a 1099-DIV US tax document."]

    prompt = utils.render_template(
        "prompts/1099.j2",
        {
            "rules": rules,
            "image_text": image_text,
            "fields": formatted_fields,
            "recipient_data": utils.format_user_data(user_data),
        },
    )

    return prompt
