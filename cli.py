import csv
import json
import os

import click


@click.command()
@click.argument("folder_path", type=click.Path(exists=True))
@click.option("--type", type=click.Choice(["div", "int"]), default="int")
@click.option(
    "--output", type=click.Choice(["json", "wulter", "csv"]), default="wulter"
)
def process(folder_path, type, output):
    # get all the files in the folder
    files = os.listdir(folder_path)


if __name__ == "__main__":
    process()
