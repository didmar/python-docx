from __future__ import absolute_import, division, print_function, unicode_literals

import os
from typing import TYPE_CHECKING

from ..opc.constants import CONTENT_TYPE as CT
from ..opc.packuri import PackURI
from ..opc.part import XmlPart
from ..oxml import parse_xml

if TYPE_CHECKING:
    from docx.oxml.footnotes import CT_Footnotes
    from docx.package import Package


class FootnotesPart(XmlPart):
    """
    Definition of Footnotes Part
    """

    @classmethod
    def default(cls, package: "Package") -> "FootnotesPart":
        partname = PackURI("/word/footnotes.xml")
        content_type = CT.WML_FOOTNOTES
        element = parse_xml(cls._default_footnotes_xml())
        return cls(partname, content_type, element, package)

    @classmethod
    def _default_footnotes_xml(cls) -> bytes:
        path = os.path.join(os.path.split(__file__)[0], "..", "templates", "default-footnotes.xml")
        with open(path, "rb") as f:
            xml_bytes = f.read()
        return xml_bytes

    @property
    def footnotes(self) -> "CT_Footnotes":
        return self.element  # type: ignore
