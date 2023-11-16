import pathlib
import sys
import re

DEBUG = False


# dbg: If debug mode is active, print all statements on the same line
def dbg(*statements):
    if DEBUG:
        for s in statements:
            print(s, end="")
        print("")


# The Article class is designed to hold the info regarding a single markdown
# file in the directory, including its name, whether it actually exists, the
# links to other files, and what files link to it
class Article:
    def __init__(self, file_name, parent_path, exists=False):
        self.name = file_name
        self.path = pathlib.Path.joinpath(parent_path, self.name)
        self.exists = exists
        self.md_links = []
        self.linked_from = []

    def add_md_link_to(self, md_file_name):
        self.md_links.append(md_file_name)

    def add_md_link_from(self, md_file_name):
        self.linked_from.append(md_file_name)

    def is_not_linked_to(self):
        return len(self.linked_from) == 0

    def is_not_written(self):
        return not self.exists

    def __str__(self):
        article_string = self.name + "("
        if self.exists:
            article_string += str(self.path)
        article_string += "):"
        article_string += str(self.md_links) + str(self.linked_from)
        return article_string


# The ArticleExaminer class is the meat of this program. It tracks what the
# current working directory is and automatically loads the file lists when
# the directory changes. It also keeps a dictionary of filenames to Articles
# the main data for each markdown file,
class ArticleExaminer:
    def __init__(self, parent_path=None):
        self.directory_path = parent_path
        self.full_file_list = []
        self.md_file_list = []
        self.articles = {}
        self.set_directory_path(self.directory_path)
        self.md_link_regular_expression = re.compile(r"\]\s?\([^\)]*\)")
        self.inside_of_code_block = False

    def set_directory_path(self, path):
        if path:
            if check_valid_directory_at(path):
                self.directory_path = pathlib.Path(path)
                self.full_file_list = []
                for file in self.directory_path.iterdir():
                    self.full_file_list.append(file.name)
                self.md_file_list = list(filter(check_text_is_md_file_name, self.full_file_list))
                self.articles = {}
                for md_file in self.md_file_list:
                    self.articles[md_file] = Article(md_file, self.directory_path, exists=True)

    def add_link_between_articles(self, source_name, destination_name):
        if destination_name not in self.articles:
            self.articles[destination_name] = Article(destination_name, self.directory_path)
        self.articles[source_name].add_md_link_to(destination_name)
        self.articles[destination_name].add_md_link_from(source_name)

    # get_list_of_markdown_files_in(path): returns  set of filenames in the directory
    def get_list_of_md_files_in(self, path=None):
        self.set_directory_path(path)
        return self.md_file_list

    def print_file_line(self, text_line, file_name):
        print(file_name + ": " + text_line)

    # print_files(file_list, directory_path)
    def print_files_in(self, parent_path=None):
        self.set_directory_path(parent_path)
        self.run_on_file_lines_in(self.print_file_line, self.md_file_list)

    def run_on_file_list(self, function_given_article, file_list):
        for file_name in file_list:
            article = self.articles[file_name]
            function_given_article(article)

    def run_on_md_files_in(self, function_given_article, parent_path=None):
        self.set_directory_path(parent_path)
        self.run_on_file_list(function_given_article, self.md_file_list)

    def run_on_file_lines_in(self, function_given_text_line_and_file_name, parent_path=None):
        self.set_directory_path(parent_path)

        # This inner function allows better argument routing
        def file_to_line_socket(article):
            with open(article.path, "r", encoding="utf-8") as text_file:
                for text_line in text_file:
                    function_given_text_line_and_file_name(text_line, article.name)

        self.run_on_md_files_in(file_to_line_socket)

    # get_markdown_links(line_of_text, file_name)
    def get_md_links_in_text(self, line_of_text, file_name):
        if "```" in line_of_text:
            self.inside_of_code_block = not self.inside_of_code_block
        if not self.inside_of_code_block:
            matches = self.md_link_regular_expression.findall(line_of_text)
            for match in matches:
                link = match.split("(")[1][:-1]
                if check_text_is_local_md_file_name(link):
                    dbg(file_name + ": " + link)
                    self.add_link_between_articles(file_name, link)

    def summarize_md_issues_in(self, parent_path=None):
        self.set_directory_path(parent_path)
        self.run_on_file_lines_in(self.get_md_links_in_text)
        missing_articles = []
        floating_articles = []
        for article in self.articles:
            if self.articles[article].is_not_linked_to():
                floating_articles.append(article)
            if self.articles[article].is_not_written:
                missing_articles.append(article)
        print("Floating Articles: ")
        for article_name in floating_articles:
            print("- " + article_name)
        print("Missing Articles: ")
        for article_name in missing_articles:
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


# check_valid_directory_at(path): Verifies a directory at the path; returns boolean
def check_valid_directory_at(path):
    return pathlib.Path(path).is_dir()


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
if DEBUG:
    article_examiner.print_articles()

# Use sys.argv to check command line args. If we don't have an argument, assume the local directory.
