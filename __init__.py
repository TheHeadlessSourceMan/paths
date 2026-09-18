"""
Tools for working with paths(urls)
"""

from .urlTyping import *

# exported goodies
from .httpMethod import *
from .search import *
from .pathLike import *
from ._uri import *
from ._url import *
from ._urn import *
from .loadAndSave import *
from .fileLocation import *
from .fileLocationSet import *
from .mimeType import *
from .errors import *
from .localFilenameUtils import *
from .httpUrl import *
from .filePath import *
from .urlMatch import *
from .urlFileFormat import *

# register common URL class types
URL.URL_PROTOCOL_OBJECT_TYPES['http']=HttpUrl # noqa: F405
URL.URL_PROTOCOL_OBJECT_TYPES['https']=HttpUrl # noqa: F405
URL.URL_PROTOCOL_OBJECT_TYPES['file']=FilePath # noqa: F405
