import pathlib
import sys
import re
import pickle
from datetime import datetime

"""
article-examination.py
Written by Will Plachno on 11/11/23

Summary: This python script checks the markdown files in a directory 
for files which have no links  from other files (Floating Articles) as 
well as for file_names that are linked to, but do not correspond with 
an actual file (Missing Articles).

How to use:
1. py article-examination.py
    If you run the script with no arguments, it will output the lists 
of floating articles and missing articles in the current working 
directory to the terminal. It will also create aep-control.pickle, the 
data file that represents the scripts cache.
2. py article-examination.py wikis/wiki1 VERBOSE
    This has 2 arguments - 'wikis/wiki1', a directory to run in, and 
"VERBOSE", the first of our 4 command line flags.
    VERBOSE triggers the script to print any log messages to the 
console as they are triggered. This is different from the HISTORY flag, 
which does not run the main functionality of the script, and instead 
simply prints the entire log history to the terminal.
3. py article-examination.py ALLLINKS wikis/wiki1 NOCACHE wikis/wiki2 NONMD DEBUG
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

# TODO: make sure of output when no markdown
flag = dict(
    ALLLINKS=False,  # Print a list of all Markdown links in each file
    DEBUG=False,  # Print all debug statements and end with a full print of the articles.
    HISTORY=False,  # Print the existing log to the terminal without running the link check
    NOCACHE=False,  # Run without checking or serializing to "aep-control.pickle"
    NONMD=False,  # Include all links, not just local Markdown links
    VERBOSE=False  # Print any log messages that trigger while executing
)


def number_of_flags():
    """
    Simply returns the number of flags that have been marked. Used
    simply to test whether HISTORY is the only current flag.
    :return: The number of flags set to true
    """
    number_true = 0
    for this_flag in flag:
        if flag[this_flag]:
            number_true += 1
    return number_true


def dbg(*statements):
    """
    Prints the parameters only if debug mode is active.
    Debug mode can be turned on or off by setting the DEBUG variable.
    :param statements: Strings to be printed to the console
    :return: None
    """
    if flag["DEBUG"]:
        for s in statements:
            print(s, end="")
        print("")


#
class Article:
    """
    The Article class is designed to hold the info regarding a single
    markdown file in the directory, including its name, whether it
    0actually exists, the links to other files, and what files link to
    it. Note that most logic should be done outside the class, including
    finding which links exist in this file, finding what other files
    link to this, and whether this file actually exists which should be
    passed in the constructor. All of this logic is done in the
    ArticleExaminer class.
    """

    def __init__(self, file_name, parent_path, exists=False):
        self.name = file_name
        self.path = pathlib.Path.joinpath(parent_path, self.name)
        # self.last_modified: Time of most recent content modification
        # expressed in seconds.
        self.last_modified = 0
        self.exists = exists
        self.md_links = []
        self.linked_from = []
        self.all_links = []

    def get_non_md_links(self):
        """
        Compares the articles all_links list with its md_links list and
        returns the difference
        :return: The links which exist in all_links, but not in md_links
        """
        non_md_links = []
        for link in self.all_links:
            if link not in self.md_links:
                non_md_links.append(link)
        return non_md_links

    def add_link(self, link):
        """
        Adds a link to the articles all_links
        :param link: The link to add
        :return: Whether the link was freshly added
        """
        if not self.all_links:
            self.all_links = []
        if link not in self.all_links:
            self.all_links.append(link)
            return True
        return False

    def remove_link(self, link):
        """
        Removes a link from the article's all_links list
        :param link: The link to remove
        :return: Whether a link was actually removed
        """
        if self.all_links:
            if link in self.all_links:
                self.all_links.remove(link)
                return True
        return False

    def add_md_link_to(self, md_file_name):
        """
        Notifies the article that it has a link inside the article's
        markdown file to a separate markdown file whose file name is
        md_file_name
        :param md_file_name: The file_name, not path, of the file
        that this article's markdown file links to,
        :return: Whether the file was freshly added
        """
        if md_file_name not in self.md_links:
            self.md_links.append(md_file_name)
            return True
        return False

    def add_md_link_from(self, md_file_name):
        """
        Notifies the article that a different markdown file contains a
        link to the article's markdown file.
        :param md_file_name: The file_name, not path, of the file that
        links to this article.
        :return: None
        """
        if md_file_name not in self.linked_from:
            self.linked_from.append(md_file_name)

    def remove_md_link_to(self, md_file_name):
        """
        Notes the removal of the link from the article to another file.
        :param md_file_name: The file that this article has a link to
        :return: None
        """
        if md_file_name in self.md_links:
            self.md_links.remove(md_file_name)

    def remove_md_link_from(self, md_file_name):
        """
        Notes the removal of a link in another file to this article.
        Returns whether the file currently has no reason to still be
        tracked.
        :param md_file_name: The file name that linked to this article
        :return: Whether this article should be removed (True = No
        longer linked to and does not exist)
        """
        if md_file_name in self.linked_from:
            self.linked_from.remove(md_file_name)
            if self.is_not_linked_to() and self.is_not_written():
                return True
        return False

    def is_not_linked_to(self):
        """
        Checks whether this article has been notified of any other
        articles which link to it.
        :return: True if no other link lands at this article, False
        if it's linked.
        """
        return len(self.linked_from) == 0

    def is_not_written(self):
        """
        Checks whether the article's file exists in the directory
        :return:
        """
        return not self.exists

    def __str__(self):
        """
        Compiles the article into a single string
        :return: A single string with no new lines:
            [article_name](article_path):
            [markdown_files_this_article_links_to]
            [markdown_files_that_link_to_this_article]
        """
        article_string = self.name + "("
        if self.exists:
            article_string += str(self.path)
        article_string += ")[" + str(self.last_modified) + "]:"
        article_string += str(self.md_links) + str(self.linked_from)
        return article_string


# The ArticleExaminer class is the meat of this program. It tracks what
# the current working directory is and automatically loads the file
# lists when the directory changes. It also keeps a dictionary of
# filenames to Articles
class ArticleExaminer:
    def __init__(self, parent_path=None):
        self.directory_path = parent_path
        self.control_file_name = "aep-control.pickle"
        self.md_link_regular_expression = re.compile(r"\]\s?\([^\)]*\)")
        self.inside_of_code_block = False
        self.full_file_list = []
        self.md_file_list = []
        self.floating_articles = []
        self.missing_articles = []
        self.log_archive = []
        self.articles = {}
        self.set_directory_path(self.directory_path)

    def log(self, core_message):
        """
        Adds a message to the log, after getting its timestamp
        :param core_message: The message to log
        :return: None
        """
        log_message = get_time_stamp() + ": " + core_message
        self.log_archive.append(log_message)
        if flag["DEBUG"] or flag["VERBOSE"]:
            print("LOG: " + log_message)

    def set_directory_path(self, directory_path):
        """
        If the path is valid, reinitialize this article_examiner
        with a full file list, a list of markdown files, and a
        fresh article dictionary, already initialized with the
        correct articles, but no link information. If a control file
        exists, deserialize it.
        :param directory_path: A directory path with markdown files inside
        :return: None
        """
        if check_valid_directory_at(directory_path):
            # Note that the directory_path is saved not as a string,
            # but as an actual Path object.
            self.directory_path = pathlib.Path(directory_path)
            # Get a list of every file in the directory
            self.full_file_list = []
            for file in self.directory_path.iterdir():
                self.full_file_list.append(file.name)
            # Check for a control file and incorporate it
            if (not flag["NOCACHE"]) and (self.control_file_name in self.full_file_list):
                deserialized = self.deserialize_control_file()
                self.articles = deserialized.articles
                self.floating_articles = deserialized.floating_articles
                self.missing_articles = deserialized.missing_articles
                self.log_archive = deserialized.log_archive
                self.log("Loaded control file. Archives: "
                         + str(len(self.articles)))
            # Narrow down from all files to just markdown files
            self.md_file_list = list(filter(check_text_is_md_file_name,
                                            self.full_file_list))
            if len(self.md_file_list) == 0:
                print("WARNING: No markdown files were found in "
                      + str(self.directory_path))
            # Finally, prepare our articles for the files which exist
            for md_file in self.md_file_list:
                if md_file not in self.articles:
                    self.articles[md_file] = Article(md_file,
                                                     self.directory_path,
                                                     exists=True)
                    dbg("Found new markdown file: " + md_file)

    def add_link_between_articles(self, source_name, destination_name):
        """
        Affects ArticleExaminer articles by adding links between the
        articles corresponding to the filenames passed in. These links
        represent that the file at source_name contains a Markdown link
        that points to a file at destination_name, which may or may not
        exist.
        :param source_name: The name of the file the link was found in
        :param destination_name: The name of the file the link targets
        :return: None
        """
        # If the file does not exist, we should create it
        if destination_name not in self.articles:
            self.articles[destination_name] = Article(destination_name,
                                                      self.directory_path)
            self.log("+ article: " + destination_name)
        # Try to add the link and log if link didn't already exist
        if self.articles[source_name].add_md_link_to(destination_name):
            self.articles[destination_name].add_md_link_from(source_name)
            self.log("+ md_link: " + source_name + " -> " + destination_name)

    def remove_link_between_articles(self, source_name, destination_name):
        """
        Removes a link between two articles and checks if the
        destination should be removed. An article should be
        removed if it is no longer linked to, and it does not exist.
        :param source_name: The file the link was found in
        :param destination_name: The file that the link targets
        :return: Either None or a file name whose article no longer exists
        """
        # Remove the link from the source
        self.articles[source_name].remove_md_link_to(destination_name)
        self.log("- md_link: " + source_name + " -> " + destination_name)
        # Remove the link from the destination and delete if no
        # longer needed
        if (self.articles[destination_name]
                .remove_md_link_from(source_name)):
            del self.articles[destination_name]
            self.log("- article: " + destination_name)
            return destination_name
        return False

    def check_articles(self):
        """
        Updates the link lists for each article if necessary
        :return:
        """
        found_changes = False
        for file_name in self.md_file_list:
            article = self.articles[file_name]
            if not article.exists:
                dbg("Found an article that used to be missing: " + article.name)
                article.exists = True
            # Only update links if file has changed
            file_last_modified = pathlib.Path(article.path).stat().st_mtime
            if file_last_modified > article.last_modified:  # TODO: make article method
                dbg("Found modified file: " + article.name)
                found_changes = True
                old_all_links = article.all_links
                old_md_links = article.md_links
                # get links from each line
                with (open(article.path, "r", encoding="utf-8")
                      as text_file):
                    for text_line in text_file:
                        # get all links instead
                        self.get_all_links_in_text(text_line, article.name)
                # do the md link check here
                for link in article.all_links:
                    if check_text_is_local_md_file_name(link):
                        self.add_link_between_articles(file_name, link)
                article.last_modified = pathlib.Path(article.path).stat().st_mtime

                # We need to compare the old_links to article.md_links to see
                # which links were added and which were removed
                for link in old_md_links:
                    if link not in article.md_links:
                        self.remove_link_between_articles(article.name, link)
                for link in old_all_links:
                    if link not in article.all_links:
                        article.remove_link(link)
                        self.log("- link: " + article.name + " -> " + link)
        if not found_changes:
            dbg("No file changes detected")

    def get_all_links_in_text(self, line_of_text, file_name):
        """
        Finds all links in the line of text which are not part
        of a code block, then incorporates them into our Articles.
        :param line_of_text: The line of text to check for links
        :param file_name: The name of the file line_of_text comes from
        :return: None
        """
        # Check for code blocks
        if "```" in line_of_text:
            self.inside_of_code_block = not self.inside_of_code_block
        if not self.inside_of_code_block:
            # Use our regular expression to find any links
            # Note that they will be in the following format:
            #   "](LINKED_PATH)" with optional space between ']' and '('
            matches = (self.md_link_regular_expression
                       .findall(line_of_text))
            for match in matches:
                # Focus down to just "LINKED_PATH"
                link = match.split("(")[1][:-1]
                # We still have to check whether the link is to a local
                # Markdown file, or something else (could be an image or
                # web url)
                self.articles[file_name].add_link(link)
                self.log("+ link: " + file_name + " -> " + link)

    def summarize_md_issues_in(self):
        """
        This function triggers the link retrieval, then walks through
        the articles, making lists of articles that are not linked to
        and articles whose file does not exist.
        :return:
        """
        # First, update the links
        self.check_articles()
        # Then, compile the lists of missing and floating articles
        self.missing_articles = []
        self.floating_articles = []
        for article in self.articles:
            if self.articles[article].is_not_linked_to():
                self.floating_articles.append(article)
            if self.articles[article].is_not_written():
                self.missing_articles.append(article)
        if not flag["NOCACHE"]:
            # Save our new status
            self.serialize_to_control_file()

    def print_summary(self):
        """
        Prints the floating and missing articles to the console, as well
        as other prints as required by flags
        :return: None
        """
        if flag["ALLLINKS"]:
            self.print_links()
        print("Floating Articles: ")
        run_on_sorted_list(self.floating_articles, lambda article_name: print("- " + article_name))
        print("Missing Articles: ")
        run_on_sorted_list(self.missing_articles, lambda article_name: print(
            "- " + article_name + " (linked from: " + str(self.articles[article_name].linked_from) + ")"))
        if flag["DEBUG"]:
            self.print_articles()

    def print_log(self):
        """
        Prints the logs of the current ArticleExaminer. This is what is
        called when we detect the HISTORY flag - we load up the articles
        and, without editing links, print the logs.
        :return: None
        """
        print("Printing log: ")
        for log_message in self.log_archive:
            print(log_message)

    def print_links(self):
        """
        Prints the links in each article. Only called if ALLLINKS flag
        is included, and the print is expanded if NONMD is also included
        :return: None
        """
        print("Printing All Links: ")
        for article_name in self.articles:
            article = self.articles[article_name]
            run_on_sorted_list(article.md_links, lambda link: print(article.name + " -> " + link))
            if flag["NONMD"]:
                run_on_sorted_list(article.get_non_md_links(), lambda link: print(article.name + " -> " + link))

    def print_articles(self):
        """
        Prints all articles collected, including their
        name, path, links, and last modified
        :return: None
        """
        print("Printing articles: ")
        run_on_sorted_list(self.articles.keys(), lambda article_name: print(self.articles[article_name]))

    def serialize_to_control_file(self):
        """
        Serializes the ArticleExaminer to the file at
        [directory_path]/[control_file_name]
        :return: None
        """
        control_path = pathlib.Path.joinpath(self.directory_path,
                                             self.control_file_name)
        with open(control_path, "wb") as control_file:
            pickle.dump(self, control_file)

    def deserialize_control_file(self):
        """
        Deserializes an ArticleExaminer from the file at
        [directory_path]/[control_file_name]
        :return: The deserialized object.
        """
        control_path = pathlib.Path.joinpath(self.directory_path,
                                             self.control_file_name)
        new_article_examiner = None
        with open(control_path, "rb") as control_file:
            new_article_examiner = pickle.load(control_file)
        return new_article_examiner


def get_target_directories():
    """
    Gets the target directory paths, either as a command line argument
    or the working directory. Also deciphers the rest of the command
    line arguments for flags like VERBOSE and HISTORY
    :return: A list of directory paths
    """
    # Decipher the command line arguments
    target_directories = []
    for cl_argument in sys.argv[1:]:
        if cl_argument in flag:
            dbg("Flag: " + cl_argument)
            flag[cl_argument] = True
        else:
            dbg("Found path: " + cl_argument)
            target_directories.append(cl_argument)
    if len(target_directories) < 1:
        dbg("Using working directory")
        target_directories.append(pathlib.Path().resolve())
    return target_directories


def check_valid_directory_at(directory_path):
    """
    Determines whether the path points to an actual directory
    :param directory_path: A path, hopefully a directory
    :return: Whether path actually leads to a directory.
    """
    try:
        if directory_path and pathlib.Path(directory_path).is_dir():
            return True
    except Exception:
        return False
    return False


def check_text_has_paths(text):
    """
    Checks a string for any path delimiters
    :param text: The string to check for path delimiters
    :return: Whether text contains path delimiters
    """
    has_paths = False
    try:
        text.index('/')
        has_paths = True
    finally:
        try:
            text.index('\\')
            has_paths = True
        finally:
            return has_paths


def check_text_is_local_md_file_name(text):
    """
    Checks both that the string has no paths and has a .md file extension
    :param text: The text to check for paths and correct file extension
    :return: True if the text is a local file name with a .md extension
    """
    if check_text_has_paths(text):
        return False
    return check_text_is_md_file_name(text)


def check_text_is_md_file_name(text):
    """
    Checks the string for a .md file extension
    :param text: The string to check for a file extension
    :return: True if text ends in ".md"
    """
    extension = text[-3:]
    return extension == ".md"


def get_time_stamp():
    """
    Returns the current time in the format I like.
    :return: 12/24/23:7:42:22 = 12/24 of 2023 at 7:42 and 22 seconds,
    but the current time.
    """
    return datetime.now().strftime("%m%d%y:%H:%M:%S")


def run_on_sorted_list(target_list, function_given_string):
    """
    Sorts the list, then runs the function on each item.
    :param target_list: The list to be sorted
    :param function_given_string: The function to run on each item.
    :return: None
    """
    sorted_list = sorted(target_list)
    for list_item in sorted_list:
        function_given_string(list_item)


# The main functionality of this file:
# Get the path, instantiate the ArticleExaminer,
# find all links, and print the links to the console
directory_paths = get_target_directories()
for path in directory_paths:
    article_examiner = ArticleExaminer(path)
    if flag["HISTORY"]:
        print("Printing log for: " + str(path))
        article_examiner.print_log()
    if not flag["HISTORY"] or number_of_flags() > 1:
        article_examiner.summarize_md_issues_in()
        article_examiner.print_summary()
