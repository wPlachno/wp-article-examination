"""
article.py
Separated out of article-examination.py on 11/29/23

Summary: The Article class is used in the article-examination process
as a data container for each markdown file. The main program is designed
to search through a directory, find all the markdown files, then hold
each of the links written in the markdown files. We represent the markdown
files in our code as the Article class.
    As far as what information the article's contain, it includes the name
of the file, the file's path, whether we know the file exists, the last
modified timestamp, and then the link lists. The link lists are 3 different
lists: all_links, which contains every link written inside the markdown
file, md_links, a list of every link in the file that seems to point to a
local markdown file, as well as linked_from, a list of other files which
contain a link to this file.
    The Article class also has several methods, including get_non_md_links,
which parses the all_links list to find any links which seem to point at
local markdown files, add_link and remove_link, for all_links IO,
add_md_link_to and remove_md_link_to, for md_links IO, add_md_link_from and
remove_md_link_from, for linked_from IO, and finally, the predicates
is_not_linked_to and is_not_written, which determine whether the article
represents a floating article or a missing article.
"""
import pathlib


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
        self.has_existing_file = exists
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
        return not self.has_existing_file

    def __str__(self):
        """
        Compiles the article into a single string
        :return: A single string with no new lines:
            [article_name](article_path):
            [markdown_files_this_article_links_to]
            [markdown_files_that_link_to_this_article]
        """
        article_string = self.name + "("
        if self.has_existing_file:
            article_string += str(self.path)
        article_string += ")[" + str(self.last_modified) + "]:"
        article_string += str(self.md_links) + str(self.linked_from)
        return article_string
