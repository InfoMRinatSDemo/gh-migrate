import click
import pandas as pd


@click.command()
@click.argument("before-source", type=click.STRING)
@click.argument("after-target", type=click.STRING)
@click.argument("after-source", type=click.STRING)
@click.argument("output", type=click.STRING)
def check(before_source, after_target, after_source, output=None):
    print("Diffing {} and {}".format(before_source, after_target))

    before_source_stats = pd.read_csv(before_source, dtype=str)
    after_target_stats = pd.read_csv(after_target, dtype=str)
    after_source_stats = pd.read_csv(after_source, dtype=str)

    ignore_cols = [
        "createdAt",
        "pushedAt",
        "updatedAt",
        "url",
        "issues.comments.totalCount",
        "issues.timelineItems.totalCount",
    ]
    before_source_stats = before_source_stats.drop(columns=ignore_cols)
    after_target_stats = after_target_stats.drop(columns=ignore_cols)
    after_source_stats = after_source_stats.drop(columns=ignore_cols)

    compare_dfs(
        "name", before_source_stats, after_target_stats, after_source_stats, output
    )


def compare_dfs(key, source_df, target_df, context_df, output):
    """
    Compare the before_source and after_target dataframes and write the differences to file
    """

    def not_equal(val1, val2):
        val1 = val1.lower() if isinstance(val1, str) else val1
        val2 = val2.lower() if isinstance(val2, str) else val2

        if pd.isna(val1) and pd.isna(val2):
            return False
        if pd.isna(val1) or pd.isna(val2):
            return True
        elif val1 != val2:
            return True
        else:
            return False

    def get_row(key, df, name):
        return df[df[key] == name]

    diffs = []

    for row in source_df.itertuples():
        source_row = get_row(key, source_df, row.name)
        target_row = get_row(key, target_df, row.name)
        context_row = get_row(key, context_df, row.name)

        if source_row.equals(target_row):
            continue
        elif source_row.empty or target_row.empty:
            continue
        else:
            for col in source_row.columns:
                if not_equal(source_row[col].values[0], target_row[col].values[0]):
                    diffs.append(
                        {
                            "source_name": f"{source_row['owner.login'].values[0]}/{source_row['name'].values[0]}",
                            "target_name": f"{target_row['owner.login'].values[0]}/{target_row['name'].values[0]}",
                            "column": col,
                            "source_value": source_row[col].values[0],
                            "target_value": target_row[col].values[0],
                            "context_value": context_row[col].values[0],
                            "source_date": source_row["Inventoried"].values[0],
                            "target_date": target_row["Inventoried"].values[0],
                            "context_date": context_row["Inventoried"].values[0],
                        }
                    )

    # Write the differences to a file
    pd.DataFrame(diffs).to_csv(output, index=False)
