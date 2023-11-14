import pathlib
import sys
from pathlib import Path
from datetime import datetime, timezone

DEBUG = True


# dbg: If debug mode is active, print all statements on the same line
def dbg(*statements):
    if DEBUG:
        for s in statements:
            print(s, end="")
        print("")


# getTargetDirectoryPath: interprets the command line arguments to find the directory path
def get_target_directory_path():
    # if given a cl arg, use it
    if len(sys.argv) > 1:
        return sys.argv[1]
    # We default to the current working directory, allowing better /bin support
    return pathlib.Path().resolve()


# check_valid_directory_at(path): Verifies a directory at the path; returns boolean
def check_valid_directory_at(path):
    return pathlib.Path(path).is_dir()


# named_as_markdown_file(name): Checks that name ends in .md
def named_as_markdown_file(name):
    extension = name[-3:]
    dbg(name, " is ", extension)
    return extension == ".md"


# get_list_of_files_in(path): returns  set of filenames in the directory
def get_list_of_files_in(path):
    directory_path = pathlib.Path(path)
    file_list = []
    for file in directory_path.iterdir():
        file_list.append(file.name)
    return list(filter(named_as_markdown_file, file_list))


number_of_command_line_tokens = len(sys.argv)
directory_path = get_target_directory_path()
is_dir = check_valid_directory_at(directory_path)
file_list = get_list_of_files_in(directory_path)
dbg("Hello World! The number of arguments: ", number_of_command_line_tokens)
dbg("Target path: ", directory_path)
dbg("Is it a valid directory? ", is_dir)
dbg("files: ", file_list)

# Use sys.argv to check command line args. If we don't have an argument, assume the local directory.
