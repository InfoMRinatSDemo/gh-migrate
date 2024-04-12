import click

@click.command()
@click.argument("source-csv", type=click.STRING)
@click.argument("target-csv", type=click.STRING)
def diff(source_csv, target_csv):
    print("Diffing {} and {}".format(source_csv, target_csv))