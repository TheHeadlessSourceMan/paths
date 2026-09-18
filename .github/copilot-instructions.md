## Purpose
The purpose of this project is to have a general-purpose URL system that can handle various URL formats, including file URLs, UNC paths, and standard web URLs, with support for relative paths, fragments, and query parameters.
* IMPORTANT: there is a lot of existing code that relies upon this library so any changes to the api should be justified, considered carefully, and reviewed thoroughly to avoid breaking existing functionality.

## Design
 * The idea is you can create a url object by saying something like URL('http://example.com') or URL('file:///path/to/file').
 * This employs automatic morphology such that attempting to create URL('file:///path/to/file') will actually create a FileURL object instead.
 * This supports adding new URL schemes and custom URL handling logic.
 * This url object can always be read from, and can be written to only if it is a url protocol + server configuration allows it.
 * URL objects can be used as drop-in replacements for pathlib.Path objects.
  * This also includes more getter-friendly methods for instance pathlib.Path contains .exists() method, but this is more logically a property. Yet it is implemented to return something with a __call__() dunder to maintain compatability with Path.
 * The reason this library is called "paths" is because it intends to base everything on an abstract path object that can represent any number of things. This way an abstract query object can operate over any path. Queries could be anything such as globs, reguar expressions, or custom matching functions... even something like xpath queries would be forseeable.
 * This supports urls with row,column information in the fragment, following the RFC 5147 standard.
 * This supports groups of URLs, allowing for batch operations and collective management of related URL objects.
 * This originally relied upon urllib menthods but more and more they have been found to be lacking.  The general philosophy now is to do the parsing ourselves instead of relying on urllib.
 * The design philosophy for this project relies upon lazy-loading and caching to optimize performance and minimize unnecessary computations.

## TODO
 * There seems to be some confusion in the code whether to parse urls into individual components immediately or to defer parsing until necessary. This needs to be determined which is the most efficient and stick with it rather than having inconsistent parsing strategies throughout the codebase.
 * Features of this code have been stedily growing, and there may be duplicate implementations or overlapping functionality that need to be reviewed and consolidated.
 * Testing is severely lacking and needs to be expanded to cover all edge cases and ensure the reliability of the URL system.
 * The URL object is getting too monolithic and should be separated into base classes that contain certain related aspects of its functionality.  This has been done a little bit, but it has not been achieved very well.  A refactor is probably in order.

## Scope
This project aims to provide a consistent and reliable way to work with URLs across different platforms and use cases, ensuring proper handling of edge cases and adherence to relevant standards.

## Instructions
Follow the coding conventions and guidelines outlined in this project when working with URL-related functionality. Ensure that all URL manipulations are performed using the provided URL system to maintain consistency and reliability.

## References
For more information on URL formats and standards, refer to:
- [RFC 3986: Uniform Resource Identifier (URI): Generic Syntax](https://datatracker.ietf.org/doc/html/rfc3986)
- [RFC 5147: The "lines" and "chars" URI Fragment Identifiers](https://datatracker.ietf.org/doc/html/rfc5147)
- [File URL Format](https://www.cyanwerks.com/formats/file-format-url.html)
- [UNC Path Format](https://en.wikipedia.org/wiki/Path_(computing)#Universal_Naming_Convention)
- [Windows Absolute Path Format](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)
- [URL File Format](https://www.cyanwerks.com/formats/file-format-url.html)