from typing import TYPE_CHECKING

from ..shared import Parented

if TYPE_CHECKING:
    from docx.oxml.footnotes import CT_Footnote
    from docx.text.paragraph import Paragraph


class Footnote(Parented):
    """A footnote object representing a footnote in a document.

    :param Parented: Parent class providing document hierarchy functionality
    """

    def __init__(self, footnote: "CT_Footnote", parent: Parented):
        super(Footnote, self).__init__(parent)
        self._footnote = self._element = self.element = footnote

    @property
    def id(self) -> int:
        """The ID of the footnote."""
        return self._footnote._id

    @property
    def paragraph(self) -> "Paragraph":
        """The paragraph containing this footnote's content."""
        return self.element.paragraph

    @property
    def text(self) -> str:
        """The text content of this footnote."""
        return self.element.paragraph.text

    @text.setter
    def text(self, text: str):
        """Set the text content of this footnote."""
        self.element.paragraph.text = text
