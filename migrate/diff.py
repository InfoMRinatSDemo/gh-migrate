import pandas as pd

def compare_dfs(key, source_df, target_df, output):
    """
    Compare the source and target dataframes and write the differences to a file.
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

    diffs = []

    for row in source_df.itertuples():
        source_row = source_df[source_df[key] == row.name]
        target_row = target_df[target_df[key] == row.name]

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
                        }
                    )

    # Write the differences to a file
    pd.DataFrame(diffs).to_csv(output, index=False)

def diff_csv(source_csv, target_csv, output=None):

    source_stats = pd.read_csv(source_csv, dtype=str)
    target_stats = pd.read_csv(target_csv, dtype=str)

    ignore_cols = [
        "createdAt",
        "pushedAt",
        "updatedAt",
        "url",
        "Inventoried",
        "issues.comments.totalCount",
        "issues.timelineItems.totalCount",
    ]
    source_stats = source_stats.drop(columns=ignore_cols)
    target_stats = target_stats.drop(columns=ignore_cols)

    compare_dfs("name", source_stats, target_stats, output)
