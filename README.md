# wp-article-examination

The Article Examination Project, or AEP, is designed to look through a directory filled with Markdown links, referred to as a Markdown Library, and find the files that are not linked to, referred to as Floating links, as well as the links within files that point to a file that does not exist, or Missing links. These are great for seeing where your knowledge base can be expanded, reorganized, or rewritten.

It was written by Will Plachno from scratch with an MIT License. You can find the [developer's notes here](https://wplachno.github.io/wjpPersWiki/#!project-article-exam.md). 

## Setup

This setup assumes that you have a single-directory Markdown library, as required by MDWiki (and maybe vimwiki?). To run the script, you should have PYthone 3.10.5 or newer. 

## Using the Script

The centerpoint of aep is article-examination.py, so you just need to replace `[DIRECTORY_PATH]` with the path to your markdown library.
```
py article-examination.py [DIRECTORY_PATH]
```
You can also include paths to other Markdown libraries in the same call, or use one of the command line flags to modify its usage.

### Command Line Flags

These command line flags are all-caps, no-space identifiers you can add to the script call to modify its usage.

#### VERBOSE

```
py article-examination.py /wiki/ VERBOSE
```

This flag will print any log messages to the console as they happen. Note that log messages include whenever a new link is found, or an existing link is removed. 

#### DEBUG

```
py article-examination.py /wiki/ DEBUG
```

Using the DEBUG flag runs aep in debug mode, with several data dumps included, but most obviously is the dump of the article data at the end of running the script. Inside the script, Articles are the objects we use to represent our collected data regarding an individual Markdown file. Debug mode ends the script by printing to the console each articles name, path, last_modified, and link information.

#### HISTORY

```
py article-examination.py /wiki/ HISTORY
```

The HISTORY flag prints the entire log history of the Markdown Library. If it is the only flag used, then the script will print the logs, then terminate before doing any other logic. 

#### ALLLINKS

```
py article-examination.py /wiki/ ALLLINKS
```

Instead of only printing the floating and missing links, including the ALLLINKS flag will precede those lists with a full print of all links pointing to local Markdown files. 

#### NONMD

```
py article-examination.py /wiki/ NONMD
```

Internally, aep tracks all links, not just the local markdown links. Including the NONMD links on its own will not seem to have any effect, but using it in combination with ALLLINKS will print non-Markdown links in those prints as well. 

#### NOCACHE

```
py article-examination.py /wiki/ NOCACHE
```

If you use aep without this flag, it will add a file to the directory, `aep-control.pickle`. The pickle file is the serialized state of the folders aep. This includes its log history, its articles, and the link structures. Using the pickle file allows us to track changes over time. Using NOCACHE will require the script to not access an existing pickle file, nor create a new one. 