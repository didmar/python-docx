"""
Custom element classes related to the comments part
"""

from typing import TYPE_CHECKING, List, Optional

from ..opc.constants import NAMESPACE
from ..text.paragraph import Paragraph
from ..text.run import Run
from . import OxmlElement
from .simpletypes import ST_DecimalNumber, ST_String
from .xmlchemy import BaseOxmlElement, RequiredAttribute, ZeroOrMore, ZeroOrOne

if TYPE_CHECKING:
    from docx.oxml.text.paragraph import CT_P


class CT_Com(BaseOxmlElement):
    """
    A ``<w:comment>`` element, a container for Comment properties
    """

    initials: str = RequiredAttribute("w:initials", ST_String)  # pyright: ignore[reportAssignmentType]
    _id: int = RequiredAttribute("w:id", ST_DecimalNumber)  # pyright: ignore[reportAssignmentType]
    date: str = RequiredAttribute("w:date", ST_String)  # pyright: ignore[reportAssignmentType]
    author: str = RequiredAttribute("w:author", ST_String)  # pyright: ignore[reportAssignmentType]

    p = ZeroOrOne("w:p", successors=("w:comment",))

    @classmethod
    def new(cls, initials: str, comm_id: int, date: str, author: str) -> "CT_Com":
        """
        Return a new ``<w:comment>`` element having _id of *comm_id* and having
        the passed params as meta data
        """
        comment = OxmlElement("w:comment")
        comment.initials = initials
        comment.date = date
        comment._id = comm_id
        comment.author = author
        return comment

    def _add_p(self, text: str) -> "CT_P":
        _p = OxmlElement("w:p")
        _r = _p.add_r()
        run = Run(_r, self)
        run.text = text
        self._insert_p(_p)
        return _p

    @property
    def meta(self) -> List[str]:
        return [self.author, self.initials, self.date]

    @property
    def paragraph(self) -> Paragraph:
        return Paragraph(self.p, self)


class CT_Comments(BaseOxmlElement):
    """
    A ``<w:comments>`` element, a container for Comments properties
    """

    comment = ZeroOrMore("w:comment", successors=("w:comments",))

    def add_comment(self, author: str, initials: str, date: str) -> CT_Com:
        _next_id = self._next_commentId
        comment: CT_Com = CT_Com.new(initials, _next_id, date, author)
        self.append(comment)
        print(self.xml)
        return comment

    @property
    def _next_commentId(self) -> int:
        ids = self.xpath("./w:comment/@w:id")
        _ids = [int(_str) for _str in ids]
        _ids.sort()
        if len(_ids) == 0:
            return 0
        return _ids[-1] + 1


class CT_CRS(BaseOxmlElement):
    """
    A ``<w:commentRangeStart>`` element
    """

    _id = RequiredAttribute("w:id", ST_DecimalNumber)

    @classmethod
    def new(cls, _id: int) -> "CT_CRS":
        commentRangeStart = OxmlElement("w:commentRangeStart")
        commentRangeStart._id = _id

        return commentRangeStart


class CT_CRE(BaseOxmlElement):
    """
    A ``w:commentRangeEnd`` element
    """

    _id = RequiredAttribute("w:id", ST_DecimalNumber)

    @classmethod
    def new(cls, _id: int) -> "CT_CRE":
        commentRangeEnd = OxmlElement("w:commentRangeEnd")
        commentRangeEnd._id = _id
        return commentRangeEnd


class CT_CRef(BaseOxmlElement):
    """
    w:commentReference
    """

    _id = RequiredAttribute("w:id", ST_DecimalNumber)

    @classmethod
    def new(cls, _id: int) -> "CT_CRef":
        commentReference = OxmlElement("w:commentReference")
        commentReference._id = _id
        return commentReference
