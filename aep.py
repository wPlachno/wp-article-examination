"""
aep.py
Separated out from articleexamination.py by Will Plachno on 11/30/23

This is the main file of the script, the source point, the executable script.
It relies on articleexamination.py and article.py to do most of the logic.

Summary: This python script checks the markdown files in a directory
for files which have no links  from other files (Floating Articles) as
well as for file_names that are linked to, but do not correspond with
an actual file (Missing Articles).

How to use:
1. py aep.py
    If you run the script with no arguments, it will output the lists
of floating articles and missing articles in the current working
directory to the terminal. It will also create aep-control.pickle, the
data file that represents the scripts cache.
2. py aep.py wikis/wiki1 VERBOSE
    This has 2 arguments - 'wikis/wiki1', a directory to run in, and
"VERBOSE", the first of our 4 command line flags.
    VERBOSE triggers the script to print any log messages to the
console as they are triggered. This is different from the HISTORY flag,
which does not run the main functionality of the script, and instead
simply prints the entire log history to the terminal.
3. py aep.py ALLLINKS wikis/wiki1 NOCACHE wikis/wiki2 NONMD DEBUG
    This final example illustrates three things: that there is no
required order between directories and flags, that you can have multiple
directories and multiple files, and also shows the final supported flags.
Please note that most flags can be combined except for HISTORY, which is
designed to be called simply to check the log, not trigger the rest of
the ArticleExaminer logic.
    ALLLINKS means to print a list of each of the links between articles,
NOCACHE means to skip reading or writing aep-control.pickle, NONMD
means to include non-article links, and DEBUG means to print all the
debug messages and follow the script's main print with a print of
all the article objects.
    What you should experience with this combination of arguments is
that the script will first work on wiki1, printing out debug messages
while checking the links, then printing out a list of all the articles
and all of their links, including links to web urls and images, then
printing the Floating Articles, then the Missing Articles, which will
culminate in the final print of each of the Article objects. It will do
all of this without opening or writing an aep-control.pickle file.
    It will then repeat exactly that for wiki2.
"""
import sys
import pathlib
from articleexamination import ArticleExaminer, flag_list
import wcutil

flags = None
debug = None
dbg = None

def get_target_directories(args):
    """
    Gets the target directory paths, either as a command line argument
    or the working directory. Also deciphers the rest of the command
    line arguments for flags like VERBOSE and HISTORY
    :return: A list of directory paths
    """
    # Decipher the command line arguments
    target_directories = []
    for cl_argument in args[1:]:
        arg_as_flag = cl_argument.upper()
        if flags.has_flag(arg_as_flag):
            flags.activate(arg_as_flag)
            dbg("Flag: " + arg_as_flag)
        else:
            dbg("Found path: " + cl_argument)
            target_directories.append(cl_argument)
    if len(target_directories) < 1:
        dbg("Using working directory")
        target_directories.append(pathlib.Path().resolve())
    return target_directories

def _main (args):
    flags = wcutil.FlagFarm(flag_list)
    debug = wcutil.Debug(active=False)
    dbg = debug.scribe

    # The main functionality of this file:
    # Get the path, instantiate the ArticleExaminer,
    # find all links, and print the links to the console
    directory_paths = get_target_directories(sys.argv)
    for path in directory_paths:
        article_examiner = ArticleExaminer(path, flags=flags, debug=debug)
        if flags["HISTORY"]:
            print("Printing log for: " + str(path))
            article_examiner.print_log()
        if not flags["HISTORY"] or flags.active_count() > 1:
            article_examiner.summarize_md_issues_in()
            article_examiner.print_summary()

if __name__ == "__main__":
    _main(sys.argv)


