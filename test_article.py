"""
test_article.py
Written by Will Plachno on 12/1/23

This pytest test suite executes unit tests on the functionality provided by article.py, including:
Article.__init__
Article.add_link
Article.remove_link
Article.get_non_md_links
Article.add_md_link_to
Article.remove_md_link_to
Article.add_md_link_from
Article.remove_md_link_from
Article.is_not_linked_to
Article.is_not_written
Article.__str__
"""
from article import Article
from wcutil import tail_matches_token

class TestArticle:
    file_name = "test.md"
    file_path = "C:\\Users\\test\\test.md"
    parent_path = "C:/Users/test/"
    links = ("test1.md", "test2.txt", "test3.md")
    md = ("test1.md", "test2.md", "test3.md")
    art_string = ( "test.md()[0]:['test2.md', 'test3.md']['test1.md']",
                   "test.md(C:\\Users\\test\\test.md)[0]:['test2.md', 'test3.md']['test1.md']")

    def test_init(self):
        art = Article(self.file_name, self.parent_path)
        assert art.name == self.file_name
        assert str(art.path) == self.file_path
        assert art.last_modified == 0
        assert not art.has_existing_file
        assert len(art.all_links) == 0
        assert len(art.md_links) == 0
        assert len(art.linked_from) == 0
        art2 = Article(self.file_name, self.parent_path, True)
        assert art2.has_existing_file

    def test_add_link(self):
        art = Article(self.file_name, self.parent_path)
        assert art.add_link(self.links[0])
        assert len(art.all_links) == 1
        assert art.add_link(self.links[1])
        assert len(art.all_links) == 2
        assert not art.add_link(self.links[0])
        assert len(art.all_links) == 2

    def test_remove_link(self):
        art = Article(self.file_name, self.parent_path)
        art.add_link(self.links[0])
        assert not art.remove_link(self.links[1]), "Don't remove nonexisting"
        assert len(art.all_links) == 1
        assert art.remove_link(self.links[0])
        assert len(art.all_links) == 0

    def test_get_non_md_links(self):
        art = Article(self.file_name, self.parent_path)
        for link in self.links:
            art.add_link(link)
            if tail_matches_token(link, ".md"):
                art.add_md_link_to(link)
        non_links = art.get_non_md_links()
        assert len(non_links) == 1, "We should only be getting the non-md links."
        assert non_links[0] == self.links[1]

    def test_add_md_link_to(self):
        art = Article(self.file_name, self.parent_path)
        assert art.add_md_link_to(self.md[0]), "True if link is a new add"
        assert len(art.md_links) == 1
        assert not art.add_md_link_to(self.md[0]), "Don't add duplicates"
        assert len(art.md_links) == 1

    def test_remove_md_link_to(self):
        art = Article(self.file_name, self.parent_path)
        art.add_md_link_to(self.md[0])
        art.add_md_link_to(self.md[1])
        assert len(art.md_links) == 2
        art.remove_md_link_to(self.md[0])
        assert len(art.md_links) == 1

    def test_add_md_link_from(self):
        art = Article(self.file_name, self.parent_path)
        art.add_md_link_from(self.md[0])
        assert len(art.linked_from) == 1
        art.add_md_link_from(self.md[0])
        assert len(art.linked_from) == 1, "Duplicates should not be added"

    def test_remove_md_link_from(self):
        art = Article(self.file_name, self.parent_path)
        # Prepopulate with two links
        art.add_md_link_from(self.md[0])
        art.add_md_link_from(self.md[1])
        assert len(art.linked_from) == 2, "Making sure we prepopulated"
        assert not art.remove_md_link_from(self.md[0]), "Return val= whether the article should be deleted."
        assert len(art.linked_from) == 1, "Validate removal"
        assert art.remove_md_link_from(self.md[1]), "This should send the signal to delete."
        # Now we pretend the file exists
        art.has_existing_file = True
        art.add_md_link_from(self.md[0])
        assert not art.remove_md_link_from(self.md[0]), "We believe the article exists"

    def test_is_not_linked_to(self):
        art = Article(self.file_name, self.parent_path)
        assert art.is_not_linked_to()
        art.add_md_link_from(self.md[0])
        assert not art.is_not_linked_to()

    def test_is_not_written(self):
        art = Article(self.file_name, self.parent_path)
        assert art.is_not_written()
        art.has_existing_file = True
        assert not art.is_not_written()

    def test_str(self):
        art = Article(self.file_name, self.parent_path)
        art.add_link(self.links[0])
        art.add_link(self.links[1])
        art.add_link(self.links[2])
        art.add_md_link_to(self.md[1])
        art.add_md_link_to(self.md[2])
        art.add_md_link_from(self.md[0])
        assert str(art) == self.art_string[0]
        art.has_existing_file = True
        assert str(art) == self.art_string[1]


