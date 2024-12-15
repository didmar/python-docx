from typing import TYPE_CHECKING

from ..shared import Parented

if TYPE_CHECKING:
    from docx.oxml.comments import CT_Comments
    from docx.text.paragraph import Paragraph


class Comment(Parented):
    """[summary]
    :param Parented: [description]
    :type Parented: [type]
    """

    def __init__(self, com: "CT_Comments", parent: Parented):
        super(Comment, self).__init__(parent)
        self._com = self._element = self.element = com

    @property
    def id(self) -> int:
        return self._com._id

    @property
    def paragraph(self) -> "Paragraph":
        return self.element.paragraph

    @property
    def text(self) -> str:
        return self.element.paragraph.text

    @text.setter
    def text(self, text: str):
        self.element.paragraph.text = text

    @property
    def author(self) -> str:
        return self.element.author

    @author.setter
    def author(self, author: str):
        self.element.author = author

    @property
    def initials(self) -> str:
        return self.element.initials

    @initials.setter
    def initials(self, initials: str):
        self.element.initials = initials

    @property
    def date(self) -> str:
        return self.element.date

    @date.setter
    def date(self, date: str):
        self.element.date = date
