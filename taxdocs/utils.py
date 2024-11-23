import csv
import re
from io import StringIO

import funcy_pipe as fp
import requests
from cachetools import cached
from jinja2 import Environment, FileSystemLoader, select_autoescape

import taxdocs
import taxdocs.utils as utils
from taxdocs import constants


def render_template(template_path: str, context: dict):
    env = Environment(
        loader=FileSystemLoader(taxdocs.root / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template(template_path)
    return template.render(context)


# TODO formatting here is so ugly, simplify, maybe to a jinga template
def format_user_data(user_data) -> str:
    output = """
Below are a list of possible recipients for this tax document.

"""

    for recipient in user_data:
        output += f"""
## Name: {recipient["name"]}

SSN: {recipient["ssn"]}
Address: {recipient["addresses"][0]}
"""

    return output


def format_field(duplicate_headers: list[str], row: dict) -> str:
    header_formatted = row["header"]

    # include header if category is a duplicate entry
    if row["header"] in duplicate_headers:
        header_formatted = f"{row['category']} {header_formatted}"

    return (
        [
            header_formatted,
            row["description"],
            f"`{row['field_name']}`",
        ]
        | fp.compact
        | fp.join_str(". ")
    )


def duplicates_on(fields, key):
    "return a list of duplicates based on the key provided"

    return (
        fields
        | fp.pluck(key)
        | fp.count_reps
        | fp.select_values(lambda x: x > 1)
        | fp.to_list
    )


def get_field_descriptions(
    sheet_url: str, snapshot_name: str, *, condition=None
) -> list[dict]:
    """
    Get CSV version of a google sheet, add field name, exclude certain fields
    """

    field_descriptions_csv_raw = utils.get_google_sheet(sheet_url, snapshot_name)

    field_descriptions_csv = utils.read_csv(field_descriptions_csv_raw)

    if not condition:
        condition = fp.where_not(exclude="Y")

    field_descriptions = (
        field_descriptions_csv
        | condition
        # remove field we don't need to have around for debugging
        | fp.pmap(fp.omit(["exclude", "notes"]))
        # construct field_name from category and header
        | fp.map(fp.rpartial(utils.add_field_name, ["category", "header"]))
        | fp.to_list
    )

    return field_descriptions


def add_field_name(input: dict, keys: list[str]) -> dict:
    """
    gsheet doesn't have a field name, let's generate the field name dynamically from specific keys
    """

    return input | {
        "field_name": (
            keys
            # neat trick: referencing the method includes the object context in the call
            | fp.map(input.get)
            | fp.compact
            | fp.join_str("_")
            | fp.pipe(utils.to_json_field_name)
        )
    }


def read_csv(csv_data: str) -> list[dict]:
    csv_file = StringIO(csv_data)
    reader = csv.DictReader(csv_file)
    return list(reader)


@cached(cache={})
def get_google_sheet(sheet_url: str, snapshot_name: str) -> str:
    snapshot_path = taxdocs.root / f"data/snapshot/{snapshot_name}.csv"

    if constants.USE_LIVE_SHEET:
        # required for the sheet to download as csv properly
        assert (
            "single=true&output=csv" in sheet_url
        ), "Please add single=true&output=csv to the sheet url."

        published_google_sheet_csv = sheet_url
        field_descriptions_csv = requests.get(published_google_sheet_csv).text

        snapshot_path.write_text(field_descriptions_csv)
    else:
        field_descriptions_csv = snapshot_path.read_text()

    return field_descriptions_csv


def to_json_field_name(input_string):
    input_string = (
        input_string.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace('"', "")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
        .replace("'", "")
        .replace("__", "_")
    )

    input_string = re.sub("_+", "_", input_string)
    return input_string
