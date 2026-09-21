# paths

[![Unit tests](https://github.com/TheHeadlessSourceMan/paths/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/TheHeadlessSourceMan/paths/actions/workflows/unit-tests.yml)
[![Pylint type checking](https://github.com/TheHeadlessSourceMan/paths/actions/workflows/pylint-type-checking.yml/badge.svg)](https://github.com/TheHeadlessSourceMan/paths/actions/workflows/pylint-type-checking.yml)
[![Coverage](https://img.shields.io/badge/coverage-30%25-red)](https://theheadlesssourceman.github.io/paths/coverage/)

This is primarily an abstract implementation of the concept of "a path", such as a/b/c wherein b is a child of a, and so on.
This is not only for file paths, but anything that can be represented as a path.

The interesting thing about that is you can operate upon any path using any query.
A query can be something like a glob, a regular expression, an xpath, and so on.

From that simple concept onward there are a number of very convenient features...

Obviously, the primary implementation of a path is a URL.
This automatically supports http:// https:// file:// ftp:// sftp:// urls, with other schemes easily added.

URL's can be dynamic, such that creating URL("file://c:/users/joe") will not create a URL object, but rather a FileURL object derived from it.

A note on FileURLs: These can take either file:// scheme strings or a regular old system path string.

All URL's are directly compatible with pathlib.Path objects.
This means you can easily do things like url.read_string() and url.write_string().

URL's will also duck-type as file-like objects, so that is also useful.
eg. PIL.Image(URL("http://someplace.org/img/schematic.png"))

Urls can be directly loaded/saved to .url files.

Url's also understand file locations and ranges.

This supports built-in URL groups with searching/filtering.

You can use polling to watch any URL for changes.