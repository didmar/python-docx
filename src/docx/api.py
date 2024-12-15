"""Directly exposed API functions and classes, :func:`Document` for now.

Provides a syntactically more convenient API for interacting with the OpcPackage graph.
"""

from __future__ import annotations

import os
from typing import IO, TYPE_CHECKING, Any, Optional, Union, cast

from docx.opc.constants import CONTENT_TYPE as CT
from docx.package import Package

if TYPE_CHECKING:
    import docx.types as t
    from docx.document import Document as DocumentObject
    from docx.parts.document import DocumentPart
    from docx.section import Section
    from docx.table import Table
    from docx.text.paragraph import Paragraph


def Document(docx: str | IO[bytes] | None = None) -> DocumentObject:
    """Return a |Document| object loaded from `docx`, where `docx` can be either a path
    to a ``.docx`` file (a string) or a file-like object.

    If `docx` is missing or ``None``, the built-in default document "template" is
    loaded.
    """
    docx = _default_docx_path() if docx is None else docx
    document_part = cast("DocumentPart", Package.open(docx).main_document_part)
    if document_part.content_type != CT.WML_DOCUMENT_MAIN:
        tmpl = "file '%s' is not a Word file, content type is '%s'"
        raise ValueError(tmpl % (docx, document_part.content_type))
    return document_part.document


def _default_docx_path():
    """Return the path to the built-in default .docx package."""
    _thisdir = os.path.split(__file__)[0]
    return os.path.join(_thisdir, "templates", "default.docx")


def element(element: Any, part: t.ProvidesStoryPart) -> Optional[Union[Paragraph, Table, Section]]:
    if (
        isinstance(element, type)
        and element.__module__ == "docx.oxml.text.paragraph"
        and element.__name__ == "CT_P"
    ):
        from .text.paragraph import Paragraph

        return Paragraph(element, part)
    elif (
        isinstance(element, type)
        and element.__module__ == "docx.oxml.table"
        and element.__name__ == "CT_Tbl"
    ):
        from .table import Table

        return Table(element, part)
    elif (
        isinstance(element, type)
        and element.__module__ == "docx.oxml.section"
        and element.__name__ == "CT_SectPr"
    ):
        from .section import Section

        if not isinstance(part, DocumentPart):
            raise TypeError("part must be a DocumentPart for Section elements")

        return Section(element, part)
