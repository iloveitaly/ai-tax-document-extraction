import funcy_pipe as fp
import xlrd
from xlutils.copy import copy

import taxdocs.docs.personal_1099_b
import taxdocs.docs.personal_1099_div
import taxdocs.docs.personal_1099_int
import taxdocs.docs.personal_w2
from taxdocs import log, logger
from taxdocs.types import TaxDocumentType

TEMPLATES: dict[TaxDocumentType, dict] = {
    "1099_int": {
        "file": "data/wulters/2023 I 2017-Interest (1099-INT)-Interest (IRS 1099-INT)_Interest.xls",
        "columns": 83,
        "start": 7,
        "field_index": taxdocs.docs.personal_1099_int.field_index_lookup,
        "sort_key": "payers_information_payer",
    },
    "1099_div": {
        "file": "data/wulters/2023 I 2017-Dividends (1099-DIV)-Dividends (IRS 1099-DIV)_Dividends.xls",
        "start": 6,
        "columns": 75,
        "field_index": taxdocs.docs.personal_1099_div.field_index_lookup,
        "sort_key": "payers_information_payer_name",
    },
    "w2": {
        "file": "/data/wulters/2023 I 2017-Wages, Salaries and Tips (W-2)-Wages and Salaries (IRS W-2)_Wages and Salaries.xls",
        "start": 6,
        "columns": 82,
        "field_index": taxdocs.docs.personal_w2.field_index_lookup,
        "sort_key": "electronic_filing_use_only_employer_name",
    },
    "1099_b": {
        "file": "/data/wulters/2023 I-Sch D _ 4797 _ 4684 - Gains and Losses (1099-B, 1099-S, 2439)-Capital Gains and Losses_Capital Gains and Losses.xls",
        "start": 6,
        "columns": 53,
        "field_index": taxdocs.docs.personal_1099_b.field_index_lookup,
        "sort_key": "payers_information_payer_name",
    },
}


def write(
    extracted_data_list: list[dict], doc_type: TaxDocumentType, output_name: str
) -> str:
    logger.info("writing to xls", output_name=output_name, doc_type=doc_type)

    template = TEMPLATES[doc_type]

    # Open the workbook and select the sheet
    rb = xlrd.open_workbook(template["file"])
    rs = rb.sheet_by_index(0)

    # Create a new workbook and copy the existing data to it
    wb = copy(rb)
    ws = wb.get_sheet(0)

    starting_index = template["start"]
    field_layout = template["field_index"]()

    def insertion_tuple(row):
        "determine column insertion index in the excel template for a each provided field"

        key, value = row
        index = field_layout[key]
        return index, value

    sort_key = template["sort_key"]
    if sort_key not in field_layout:
        raise ValueError(f"sort key {sort_key} not found in field layout")

    # accountants like the inputs to be alpha sorted
    extracted_data_list = extracted_data_list | fp.sort(key=sort_key)

    for row_index, row in enumerate(extracted_data_list):
        # notes are not supported in the template
        columns = row | fp.omit(["notes"]) | fp.compact() | fp.walk(insertion_tuple)

        for column_index, column_value in columns.items():
            # Row and column indexes are zero-based
            ws.write(starting_index + row_index, column_index, column_value)

    # TODO does not seem like the right place for this
    output_path = f"{output_name}.xls"

    log.info("exporting", output_path=output_path)

    # TODO should save to bytes instead of file, cli can handle the file writing
    wb.save(output_path)
    return output_path
