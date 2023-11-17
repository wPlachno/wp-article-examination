import pathlib
import sys
import re

DEBUG = False


# dbg: If debug mode is active, print all statements on the same line
def dbg(*statements):
    """
    Prints the parameters only if debug mode is active.
    Debug mode can be turned on or off by setting the DEBUG variable.
    :param statements: Strings to be printed to the console
    :return: None
    """
    if DEBUG:
        for s in statements:
            print(s, end="")
        print("")


#
class Article:
    """
    The Article class is designed to hold the info regarding a single markdown
    file in the directory, including its name, whether it actually exists, the
    links to other files, and what files link to it. Note that most logic should
    be done outside the class, including finding which links exist in this file,
    finding what other files link to this, and whether this file actually exists,
    which should be passed in the constructor. All of this logic is done in the
    ArticleExaminer class.
    """
    def __init__(self, file_name, parent_path, exists=False):
        self.name = file_name
        self.path = pathlib.Path.joinpath(parent_path, self.name)
        self.exists = exists
        self.md_links = []
        self.linked_from = []

    def add_md_link_to(self, md_file_name):
        """
        Notifies the article that it has a link inside the article's markdown
        file to a separate markdown file whose file name is md_file_name
        :param md_file_name: The file_name, not path, of the file that this
        article's markdown file links to,
        :return: None
        """
        self.md_links.append(md_file_name)

    def add_md_link_from(self, md_file_name):
        """
        Notifies the article that a different markdown file contains a link
        to the article's markdown file.
        :param md_file_name: The file_name, not path, of the file that links
        to this article.
        :return: None
        """
        self.linked_from.append(md_file_name)

    def is_not_linked_to(self):
        """
        Checks whether this article has been notified of any other articles
        which link to it.
        :return: True if no other link lands at this article, False if it's linked.
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
        article_string += "):"
        article_string += str(self.md_links) + str(self.linked_from)
        return article_string


# The ArticleExaminer class is the meat of this program. It tracks what the
# current working directory is and automatically loads the file lists when
# the directory changes. It also keeps a dictionary of filenames to Articles
class ArticleExaminer:
    def __init__(self, parent_path=None):
        self.directory_path = parent_path
        self.full_file_list = []
        self.md_file_list = []
        self.articles = {}
        self.set_directory_path(self.directory_path)
        self.md_link_regular_expression = re.compile(r"\]\s?\([^\)]*\)")
        self.inside_of_code_block = False
        self.floating_articles = []
        self.missing_articles = []

    def check_valid_directory_at(self, path):
        """
        Determines whether the path points to an actual directory
        :param path: A path, hopefully a directory
        :return: Whether path actually leads to a directory.
        """
        try:
            if path and pathlib.Path(path).is_dir():
                return True
        except:
            return False
        return False

    def set_directory_path(self, path):
        """
        If the path is valid, reinitialize this article_examiner
        with a full file list, a list of markdown files, and a
        fresh article dictionary, already initialized with the
        correct articles, but no link information.
        :param path: A directory path with markdown files inside
        :return: None
        """
        if self.check_valid_directory_at(path):
            # Note that the directory_path is saved not as a string,
            # but as an actual Path object.
            self.directory_path = pathlib.Path(path)
            # Get a list of every file in the directory
            self.full_file_list = []
            for file in self.directory_path.iterdir():
                self.full_file_list.append(file.name)
            # Narrow down from all files to just markdown files
            self.md_file_list = list(filter(check_text_is_md_file_name, self.full_file_list))
            if len(self.md_file_list) == 0:
                print("WARNING: No markdown files were found in "+str(self.directory_path))
            # Finally, prepare our articles for the files which exist
            self.articles = {}
            for md_file in self.md_file_list:
                self.articles[md_file] = Article(md_file, self.directory_path, exists=True)

    def add_link_between_articles(self, source_name, destination_name):
        """
        Affects ArticleExaminer.articles by adding links between the articles corresponding
        to the filenames passed in. These links represent that the file at source_name
        contains a Markdown link that points to a file at destination_name, which may or
        may not exist.
        :param source_name: The name of the file the link was found in
        :param destination_name: The name of the file the link targets
        :return: None
        """
        if destination_name not in self.articles:
            self.articles[destination_name] = Article(destination_name, self.directory_path)
        self.articles[source_name].add_md_link_to(destination_name)
        self.articles[destination_name].add_md_link_from(source_name)

    def run_on_each_md_file_line(self, function_given_text_line_and_file_name):
        """
        Runs the passed function on each line of text in each markdown file in
        the directory.
        :param function_given_text_line_and_file_name: function(text_line: str, file_name: str)
        :return: None
        """
        for file_name in self.md_file_list:
            article = self.articles[file_name]
            with open(article.path, "r", encoding="utf-8") as text_file:
                for text_line in text_file:
                    function_given_text_line_and_file_name(text_line, article.name)

    # get_markdown_links(line_of_text, file_name)
    def get_md_links_in_text(self, line_of_text, file_name):
        """
        Finds all Markdown links in the line of text which are not part of a code
        block, then incorporates them into our Articles.
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
            matches = self.md_link_regular_expression.findall(line_of_text)
            for match in matches:
                # Focus down to just "LINKED_PATH"
                link = match.split("(")[1][:-1]
                # We still have to check whether the link is to a local Markdown
                # file, or something else (could be image or web url)
                if check_text_is_local_md_file_name(link):
                    dbg(file_name + ": " + link)
                    self.add_link_between_articles(file_name, link)

    def summarize_md_issues_in(self):
        """
        This function triggers the link retrieval, then walks through the
        articles, making lists of articles that are not linked to and
        articles whose file does not exist.
        :return:
        """
        self.run_on_each_md_file_line(self.get_md_links_in_text)
        self.missing_articles = []
        self.floating_articles = []
        for article in self.articles:
            if self.articles[article].is_not_linked_to():
                self.floating_articles.append(article)
            if self.articles[article].is_not_written():
                self.missing_articles.append(article)

    def print_summary(self):
        print("Floating Articles: ")
        for article_name in self.floating_articles:
            print("- " + article_name)
        print("Missing Articles: ")
        for article_name in self.missing_articles:
            print("- " + article_name + " (linked from: " + str(self.articles[article_name].linked_from) + ")")

    def print_articles(self):
        for article in self.articles:
            print(self.articles[article])


# getTargetDirectoryPath: interprets the command line arguments to find the directory path
def get_target_directory_path():
    # if given a cl arg, use it
    if len(sys.argv) > 1:
        return sys.argv[1]
    # We default to the current working directory, allowing better /bin support
    return pathlib.Path().resolve()



def check_text_has_paths(text):
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


# named_as_markdown_file(name): Checks that name ends in .md
def check_text_is_local_md_file_name(text):
    if check_text_has_paths(text):
        return False
    return check_text_is_md_file_name(text)


def check_text_is_md_file_name(text):
    extension = text[-3:]
    return extension == ".md"


directory_path = get_target_directory_path()
article_examiner = ArticleExaminer(directory_path)
article_examiner.summarize_md_issues_in()
article_examiner.print_summary()
if DEBUG:
    article_examiner.print_articles()
