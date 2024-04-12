import click
from .diff import diff_csv

@click.command()
@click.argument("source-csv", type=click.STRING)
@click.argument("target-csv", type=click.STRING)
@click.argument("output", type=click.STRING)
def diff(source_csv, target_csv, output=None):
    print("Diffing {} and {}".format(source_csv, target_csv))
    diff_csv(source_csv, target_csv, output)