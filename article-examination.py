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
    try:
        name.index('/')
        name.index('\\')
        return False
    except:
        extension = name[-3:]
        dbg(name, " is ", extension)
        return extension == ".md"

def filter_to_markdown_files(file_list):
    return list(filter(named_as_markdown_file, file_list))


# get_list_of_markdown_files_in(path): returns  set of filenames in the directory
def get_list_of_markdown_files_in(path):
    directory_path = pathlib.Path(path)
    file_list = []
    for file in directory_path.iterdir():
        file_list.append(file.name)
    return filter_to_markdown_files(file_list)

# print_files(file_list, directory_path)
def print_files(file_list, directory_path):
    run_on_file_lines(lambda text_line, file_name: print(text_line), file_list, directory_path)

def run_on_files(function_given_file_path_and_file_name, file_list, directory_path):
    for file_name in file_list:
        file_path = pathlib.Path.joinpath(directory_path, file_name)
        function_given_file_path_and_file_name(file_path, file_name)

def run_on_file_lines(function_given_text_line_and_file_name, file_list, directory_path):
    # We have to declare a function here to correctly pass arguments to fgtlafn without using globals
    def file_to_line_socket(file_path, file_name):
        with open(file_path, "r", encoding="utf-8") as text_file:
            for text_line in text_file:
                function_given_text_line_and_file_name(text_line, file_name)

    run_on_files(file_to_line_socket, file_list, directory_path)


# get_markdown_links(line_of_text, file_name)
# def get_markdown_links(line_of_text, file_name):


number_of_command_line_tokens = len(sys.argv)
directory_path = get_target_directory_path()
is_dir = check_valid_directory_at(directory_path)
file_list = get_list_of_markdown_files_in(directory_path)
print_files(file_list, directory_path)
dbg("Hello World! The number of arguments: ", number_of_command_line_tokens)
dbg("Target path: ", directory_path)
dbg("Is it a valid directory? ", is_dir)
dbg("files: ", file_list)

# Use sys.argv to check command line args. If we don't have an argument, assume the local directory.
