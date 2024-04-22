import os
import functools
from git import Repo


def get_branch(branch="engagement"):
    repo = Repo(".")

    if branch in repo.heads:
        repo.heads.engagement.checkout()
    else:
        raise Exception(f"Branch {branch} does not exist")

    return repo


def checkpoint_file(file_path, message):
    repo = get_branch()

    if os.path.exists(file_path):
        repo.index.add([file_path])
        repo.index.commit(message)


def before_and_after_command(message):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            repo = Repo(".")

            # Check if engagement branch already exists
            if "engagement" in repo.heads:
                print("*** Switching to engagement branch")
                repo.heads.engagement.checkout()
            else:
                print("*** Creating engagement branch")
                repo.create_head("engagement")

            # Save existing workbook before re-initializing
            if os.path.exists(message):
                repo.index.add(message)
                repo.index.commit(f"{func.__name__}: Before snapshot")

            result = func(*args, **kwargs)

            repo.index.add(message)
            repo.index.commit(f"{func.__name__}: After snapshot")

            return result

        return wrapper

    return decorator
