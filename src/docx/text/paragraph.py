"""Paragraph-related proxy types."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Iterator, List, cast

from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml.text.run import CT_R
from docx.shared import StoryChild
from docx.styles.style import ParagraphStyle
from docx.text.comment import Comment
from docx.text.footnote import Footnote
from docx.text.hyperlink import Hyperlink
from docx.text.pagebreak import RenderedPageBreak
from docx.text.parfmt import ParagraphFormat
from docx.text.run import Run

if TYPE_CHECKING:
    import docx.types as t
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from docx.oxml.comments import CT_Com, CT_Comments
    from docx.oxml.footnotes import CT_Footnotes
    from docx.oxml.text.paragraph import CT_P
    from docx.styles.style import CharacterStyle


class Paragraph(StoryChild):
    """Proxy object wrapping a `<w:p>` element."""

    def __init__(self, p: CT_P, parent: t.ProvidesStoryPart):
        super(Paragraph, self).__init__(parent)
        self._p = self._element = p

    def add_run(self, text: str | None = None, style: str | CharacterStyle | None = None) -> Run:
        """Append run containing `text` and having character-style `style`.

        `text` can contain tab (``\\t``) characters, which are converted to the
        appropriate XML form for a tab. `text` can also include newline (``\\n``) or
        carriage return (``\\r``) characters, each of which is converted to a line
        break. When `text` is `None`, the new run is empty.
        """
        r = self._p.add_r()
        run = Run(r, self)
        if text:
            run.text = text
        if style:
            run.style = style
        return run

    def delete(self):
        """
        delete the content of the paragraph
        """
        self._p.getparent().remove(self._p)
        self._p = self._element = None

    def add_comment(
        self,
        text: str,
        author: str = "python-docx",
        initials: str = "pd",
        dtime: str | None = None,
        rangeStart: int = 0,
        rangeEnd: int = 0,
        comment_part_comments: CT_Comments | None = None,
    ) -> Comment:
        _comment_part_comments: CT_Comments = (
            comment_part_comments if comment_part_comments else self.part._comments_part.element  # pyright: ignore[reportPrivateUsage]
        )

        if dtime is None:
            dtime = str(datetime.now()).replace(" ", "T")

        comment: CT_Com = self._p.add_comm(
            author, initials, dtime, text, rangeStart, rangeEnd, _comment_part_comments
        )

        return Comment(comment, self.part)

    def add_footnote(self, text: str) -> Footnote:
        footnotes_part_footnotes: CT_Footnotes = self.part._footnotes_part.element  # pyright: ignore[reportPrivateUsage]
        footnote = self._p.add_fn(text, footnotes_part_footnotes)
        return Footnote(footnote, self.part)

    def merge_paragraph(self, otherParagraph: Paragraph):
        r_lst = otherParagraph.runs
        self.append_runs(r_lst)

    def append_runs(self, runs: List[Run]):
        self.add_run(" ")
        for run in runs:
            self._p.append(run._r)  # pyright: ignore[reportPrivateUsage]

    @property
    def alignment(self) -> WD_PARAGRAPH_ALIGNMENT | None:
        """A member of the :ref:`WdParagraphAlignment` enumeration specifying the
        justification setting for this paragraph.

        A value of |None| indicates the paragraph has no directly-applied alignment
        value and will inherit its alignment value from its style hierarchy. Assigning
        |None| to this property removes any directly-applied alignment value.
        """
        if self._p is None:
            raise ValueError("Paragraph is not initialized")

        return self._p.alignment

    @alignment.setter
    def alignment(self, value: WD_PARAGRAPH_ALIGNMENT):
        if self._p is None:
            raise ValueError("Paragraph is not initialized")

        self._p.alignment = value

    def clear(self):
        """Return this same paragraph after removing all its content.

        Paragraph-level formatting, such as style, is preserved.
        """
        if self._p is None:
            raise ValueError("Paragraph is not initialized")

        self._p.clear_content()
        return self

    @property
    def contains_page_break(self) -> bool:
        """`True` when one or more rendered page-breaks occur in this paragraph."""
        if self._p is None:
            raise ValueError("Paragraph is not initialized")

        return bool(self._p.lastRenderedPageBreaks)

    @property
    def hyperlinks(self) -> List[Hyperlink]:
        """A |Hyperlink| instance for each hyperlink in this paragraph."""
        if self._p is None:
            raise ValueError("Paragraph is not initialized")

        return [Hyperlink(hyperlink, self) for hyperlink in self._p.hyperlink_lst]

    def insert_paragraph_before(
        self, text: str | None = None, style: str | ParagraphStyle | None = None
    ) -> Paragraph:
        """Return a newly created paragraph, inserted directly before this paragraph.

        If `text` is supplied, the new paragraph contains that text in a single run. If
        `style` is provided, that style is assigned to the new paragraph.
        """
        paragraph = self._insert_paragraph_before()
        if text:
            paragraph.add_run(text)
        if style is not None:
            paragraph.style = style
        return paragraph

    def iter_inner_content(self) -> Iterator[Run | Hyperlink]:
        """Generate the runs and hyperlinks in this paragraph, in the order they appear.

        The content in a paragraph consists of both runs and hyperlinks. This method
        allows accessing each of those separately, in document order, for when the
        precise position of the hyperlink within the paragraph text is important. Note
        that a hyperlink itself contains runs.
        """
        if self._p is None:
            raise ValueError("Paragraph is not initialized")

        for r_or_hlink in self._p.inner_content_elements:
            yield (
                Run(r_or_hlink, self)
                if isinstance(r_or_hlink, CT_R)
                else Hyperlink(r_or_hlink, self)
            )

    @property
    def paragraph_format(self):
        """The |ParagraphFormat| object providing access to the formatting properties
        for this paragraph, such as line spacing and indentation."""
        if self._element is None:
            raise ValueError("Paragraph is not initialized")

        return ParagraphFormat(self._element)

    @property
    def rendered_page_breaks(self) -> List[RenderedPageBreak]:
        """All rendered page-breaks in this paragraph.

        Most often an empty list, sometimes contains one page-break, but can contain
        more than one is rare or contrived cases.
        """
        return [RenderedPageBreak(lrpb, self) for lrpb in self._p.lastRenderedPageBreaks]

    @property
    def runs(self) -> List[Run]:
        """Sequence of |Run| instances corresponding to the <w:r> elements in this
        paragraph."""
        return [Run(r, self) for r in self._p.r_lst]

    @property
    def all_runs(self) -> List[Run]:
        """Get all runs in the paragraph, including those nested within other elements."""
        return [Run(r, self) for r in self._p.xpath(".//w:r[not(ancestor::w:r)]")]

    @property
    def style(self) -> ParagraphStyle | None:
        """Read/Write.

        |_ParagraphStyle| object representing the style assigned to this paragraph. If
        no explicit style is assigned to this paragraph, its value is the default
        paragraph style for the document. A paragraph style name can be assigned in lieu
        of a paragraph style object. Assigning |None| removes any applied style, making
        its effective value the default paragraph style for the document.
        """
        style_id = self._p.style
        style = self.part.get_style(style_id, WD_STYLE_TYPE.PARAGRAPH)
        return cast(ParagraphStyle, style)

    @style.setter
    def style(self, style_or_name: str | ParagraphStyle | None):
        style_id = self.part.get_style_id(style_or_name, WD_STYLE_TYPE.PARAGRAPH)
        self._p.style = style_id

    @property
    def text(self) -> str:
        """The textual content of this paragraph.

        The text includes the visible-text portion of any hyperlinks in the paragraph.
        Tabs and line breaks in the XML are mapped to ``\\t`` and ``\\n`` characters
        respectively.

        Assigning text to this property causes all existing paragraph content to be
        replaced with a single run containing the assigned text. A ``\\t`` character in
        the text is mapped to a ``<w:tab/>`` element and each ``\\n`` or ``\\r``
        character is mapped to a line break. Paragraph-level formatting, such as style,
        is preserved. All run-level formatting, such as bold or italic, is removed.
        """
        return self._p.text

    @property
    def header_level(self) -> int | None:
        """
        input Paragraph Object
        output Paragraph level in case of header or returns None
        """
        if self.style is None or self.style.name is None:
            return None

        headerPattern = re.compile(r".*Heading (\d+)$")
        level = 0
        if headerPattern.match(self.style.name):
            level = int(self.style.name.lower().split("heading")[-1].strip())
        return level

    @property
    def NumId(self) -> int | None:
        """
        returns NumId val in case of paragraph has numbering
        else: return None
        """
        try:
            return self._p.pPr.numPr.numId.val
        except:
            return None

    @property
    def list_lvl(self) -> int | None:
        """
        returns ilvl val in case of paragraph has a numbering level
        else: return None
        """
        try:
            return self._p.pPr.numPr.ilvl.val
        except:
            return None

    @property
    def list_info(self) -> tuple[bool, int, int] | None:
        """
        returns tuple (has numbering info, numId value, ilvl value)
        """
        if self.NumId and self.list_lvl:
            return True, self.NumId, self.list_lvl
        else:
            return False, 0, 0

    @property
    def is_heading(self) -> bool:
        return bool(self.header_level)

    @property
    def full_text(self) -> str:
        return "".join([r.text for r in self.all_runs])

    @property
    def footnotes(self) -> List[Footnote]:
        footnote_ids = self._p.footnote_ids
        footnotes_part_footnotes: CT_Footnotes = self.part._footnotes_part.footnotes  # pyright: ignore[reportPrivateUsage]
        footnotes = []
        for footnote_id in footnote_ids:
            footnote = footnotes_part_footnotes.find(
                f"{qn('w:footnote')}[@{qn('w:id')}='{footnote_id}']"
            )
            if footnote is not None:
                footnotes.append(Footnote(footnote, self.part))

        return footnotes

    @property
    def footnote_ids(self) -> List[int] | None:
        return self._p.footnote_ids

    @property
    def comments(self) -> List[Comment]:
        runs_comments = [run.comments for run in self.runs]
        return [comment for comments in runs_comments for comment in comments]

    @property
    def comment_ids(self) -> List[int]:
        return [comment.id for comment in self.comments]

    @text.setter
    def text(self, text: str | None):
        self.clear()
        self.add_run(text)

    def _insert_paragraph_before(self) -> Paragraph:
        """Return a newly created paragraph, inserted directly before this paragraph."""
        p = self._p.add_p_before()
        return Paragraph(p, self._parent)
