import sys

import pandas as pd

from taxdocs.outputs.wulters import TEMPLATES


def get_column_structure_with_names(template):
    input_file = template["file"]
    category_row = template["start"]

    df = pd.read_excel(input_file, header=None)

    if "columns" not in template:
        raise ValueError(
            f"Template {template} does not have a 'columns' key. Number of columns: {len(df.columns)}"
        )

    if len(df.columns) != template["columns"]:
        raise ValueError(
            f"Expected {template['columns']} columns, got {len(df.columns)}"
        )

    categories = df.iloc[category_row - 2]

    # Backfill the first category
    if pd.isna(categories[0]):
        categories[0] = categories.dropna().iloc[0]

    # Forward fill the last category
    if pd.isna(categories.iloc[-1]):
        categories.iloc[-1] = categories.dropna().iloc[-1]

    # Forward fill to group categories
    categories = categories.fillna(method="ffill")

    headers = df.iloc[category_row - 1]

    column_structure = {}
    for index, (category, header) in enumerate(zip(categories, headers)):
        if pd.isna(header):
            continue  # Skip columns without headers
        if category not in column_structure:
            column_structure[category] = {"name": category, "columns": {}}
        column_structure[category]["columns"][index] = header

    return column_structure


def generate_tsv_from_structure(column_structure):
    tsv_content = "category\theader\tindex\n"
    for category, details in column_structure.items():
        for index, header in details["columns"].items():
            tsv_content += f"{category}\t{header}\t{index}\n"
    return tsv_content


if __name__ == "__main__":
    if len(sys.argv) != 2 or (describe_type := sys.argv[1]) not in TEMPLATES:
        print(
            f"Unknown template type, choose from this list: {', '.join(TEMPLATES.keys())}"
        )
        sys.exit(1)

    template = TEMPLATES[describe_type]
    structure = get_column_structure_with_names(template)

    tsv_data = generate_tsv_from_structure(structure)

    print(tsv_data)
