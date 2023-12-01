import pathlib
import re
import pickle
import wcutil
from article import Article

"""
articleexamination.py
Written by Will Plachno on 11/11/23

The main class for the aep project. Given a directory, it searches
through the directory for Markdown files, retrieves all the links,
and produces two lists: a list of the floating articles, or files
that are not linked to, and a list of the missing articles, or the
links inside of existing files that point to files that have not
yet been written.
"""

flag_list = list((
    "ALLLINKS",  # Print a list of all Markdown links in each file
    "DEBUG",  # Print all debug statements and end with a full print of the articles.
    "HISTORY",  # Print the existing log to the terminal without running the link check
    "NOCACHE",  # Run without checking or serializing to "aep-control.pickle"
    "NONMD",  # Include all links, not just local Markdown links
    "VERBOSE"  # Print any log messages that trigger while executing
))

# The ArticleExaminer class is the meat of this program. It tracks what
# the current working directory is and automatically loads the file
# lists when the directory changes. It also keeps a dictionary of
# filenames to Articles
class ArticleExaminer:
    def __init__(self, parent_path=None, flags=None, debug=None):
        self.md_link_regular_expression = re.compile(r"\]\s?\([^\)]*\)")
        self.inside_of_code_block = False
        if flags:
            self.flag = flags
        else:
            self.flag = wcutil.FlagFarm(flag_list)
        if debug:
            self.debug = debug
            self.dbg = debug.scribe
        else:
            self.debug = wcutil.Debug()
            self.dbg = debug.scribe
        self.directory_path = parent_path
        self.full_file_list = []
        self.md_file_list = []
        self.articles = {}
        self.floating_articles = []
        self.missing_articles = []

        self.control_file_name = "aep-control.pickle"
        self.log_archive = []
        self.set_directory_path(self.directory_path)

    def log(self, core_message):
        """
        Adds a message to the log, after getting its timestamp
        :param core_message: The message to log
        :return: None
        """
        log_message = wcutil.time_stamp() + ": " + core_message
        self.log_archive.append(log_message)
        if self.flag["DEBUG"] or self.flag["VERBOSE"]:
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
        if wcutil.valid_directory_at(directory_path):
            # Note that the directory_path is saved not as a string,
            # but as an actual Path object.
            self.directory_path = pathlib.Path(directory_path)
            # Get a list of every file in the directory
            self.full_file_list = []
            for file in self.directory_path.iterdir():
                self.full_file_list.append(file.name)
            # Check for a control file and incorporate it
            if (not self.flag["NOCACHE"]) and (self.control_file_name in self.full_file_list):
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
            # Update whether each article exists, so that we can see when files are
            # made or destroyed
            for article_name in self.articles:
                article = self.articles[article_name]
                if article.name in self.md_file_list:
                    if not article.has_existing_file:
                        article.has_existing_file = True
                        self.log("+ existing: "+article.name)
                else:
                    if article.has_existing_file:
                        article.has_existing_file = False
                        self.log("- existing: "+article.name)

            if len(self.md_file_list) == 0:
                print("WARNING: No markdown files were found in "
                      + str(self.directory_path))

            # Finally, prepare our articles for the files which exist
            for md_file in self.md_file_list:
                if md_file not in self.articles:
                    self.articles[md_file] = Article(md_file,
                                                     self.directory_path,
                                                     exists=True)
                    self.dbg("Found new markdown file: " + md_file)

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
        if (self.articles[destination_name].remove_md_link_from(source_name)):
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
            if article.is_not_written():
                self.dbg("Found an article that used to be missing: " + article.name)
                article.has_existing_file = True
            # Only update links if file has changed
            file_last_modified = pathlib.Path(article.path).stat().st_mtime
            if file_last_modified > article.last_modified:
                self.dbg("Found modified file: " + article.name)
                found_changes = True
                old_all_links = article.all_links
                article.all_links = []
                old_md_links = article.md_links
                article.md_links = []
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
            self.dbg("No file changes detected")

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
        if not self.flag["NOCACHE"]:
            # Save our new status
            self.serialize_to_control_file()

    def print_summary(self):
        """
        Prints the floating and missing articles to the console, as well
        as other prints as required by flags
        :return: None
        """
        if len(self.md_file_list) == 0:
            return  # Don't print if no md, the warning message was printed in ArticleExaminer.setDirectoryRoot
        if self.flag["ALLLINKS"]:
            self.print_links()
        print("Floating Articles: ")
        wcutil.run_on_sorted_list(self.floating_articles, lambda article_name: print("- " + article_name))
        print("Missing Articles: ")
        wcutil.run_on_sorted_list(self.missing_articles, lambda article_name: print(
            "- " + article_name + " (linked from: " + str(self.articles[article_name].linked_from) + ")"))
        if self.flag["DEBUG"]:
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
            wcutil.run_on_sorted_list(article.md_links, lambda link: print(article.name + " -> " + link))
            if self.flag["NONMD"]:
                wcutil.run_on_sorted_list(article.get_non_md_links(), lambda link: print(article.name + " -> " + link))

    def print_articles(self):
        """
        Prints all articles collected, including their
        name, path, links, and last modified
        :return: None
        """
        print("Printing articles: ")
        wcutil.run_on_sorted_list(self.articles.keys(), lambda article_name: print(self.articles[article_name]))

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


def check_text_is_local_md_file_name(text):
    """
    Checks both that the string has no paths and has a .md file extension
    :param text: The text to check for paths and correct file extension
    :return: True if the text is a local file name with a .md extension
    """
    if wcutil.text_has_paths(text):
        return False
    return check_text_is_md_file_name(text)


def check_text_is_md_file_name(text):
    return wcutil.tail_matches_token(text, ".md")
