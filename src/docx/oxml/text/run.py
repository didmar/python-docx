"""Custom element classes related to text runs (CT_R)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterator, List

from docx.oxml import OxmlElement
from docx.oxml.drawing import CT_Drawing
from docx.oxml.ns import qn
from docx.oxml.simpletypes import ST_BrClear, ST_BrType, ST_String
from docx.oxml.text.pagebreak import CT_LastRenderedPageBreak
from docx.oxml.xmlchemy import (
    BaseOxmlElement,
    OptionalAttribute,
    RequiredAttribute,
    ZeroOrMore,
    ZeroOrOne,
)
from docx.shared import TextAccumulator

if TYPE_CHECKING:
    from docx.oxml.comments import CT_Com, CT_Comments
    from docx.oxml.footnotes import CT_FNR, CT_FootnoteRef
    from docx.oxml.shape import CT_Anchor, CT_Inline
    from docx.oxml.text.parfmt import CT_TabStop
    from docx.oxml.text.run import CT_RPr

# ------------------------------------------------------------------------------------
# Run-level elements


class CT_R(BaseOxmlElement):
    """`<w:r>` element, containing the properties and text for a run."""

    add_br: Callable[[], CT_Br]
    add_tab: Callable[[], CT_TabStop]
    get_or_add_rPr: Callable[[], CT_RPr]
    _add_drawing: Callable[[], CT_Drawing]
    _add_t: Callable[..., CT_Text]

    rPr: CT_RPr | None = ZeroOrOne("w:rPr")  # pyright: ignore[reportAssignmentType]
    # wrong
    ref = ZeroOrOne("w:commentRangeStart", successors=("w:r",))
    br = ZeroOrMore("w:br")
    cr = ZeroOrMore("w:cr")
    drawing = ZeroOrMore("w:drawing")
    t = ZeroOrMore("w:t")
    tab = ZeroOrMore("w:tab")

    def add_t(self, text: str) -> CT_Text:
        """Return a newly added `<w:t>` element containing `text`."""
        t = self._add_t(text=text)
        if len(text.strip()) < len(text):
            t.set(qn("xml:space"), "preserve")
        return t

    def add_drawing(self, inline_or_anchor: CT_Inline | CT_Anchor) -> CT_Drawing:
        """Return newly appended `CT_Drawing` (`w:drawing`) child element.

        The `w:drawing` element has `inline_or_anchor` as its child.
        """
        drawing = self._add_drawing()
        drawing.append(inline_or_anchor)
        return drawing

    def add_comment(
        self,
        author: str,
        initials: str,
        dtime: str,
        comment_text: str,
        comment_part_comments: CT_Comments,
    ) -> CT_Com:
        comment: CT_Com = comment_part_comments.add_comment(author, initials, dtime)
        _p = comment._add_p(comment_text)
        self.add_comment_reference(comment._id)
        self.link_comment(comment._id)

        return comment

    def link_comment(self, _id: int):
        rStart = OxmlElement("w:commentRangeStart")
        rStart._id = _id
        rEnd = OxmlElement("w:commentRangeEnd")
        rEnd._id = _id
        self.addprevious(rStart)
        self.addnext(rEnd)

    def add_comment_reference(self, _id: int) -> BaseOxmlElement:
        reference = OxmlElement("w:commentReference")
        reference._id = _id
        self.append(reference)
        return reference

    def add_footnote_reference(self, _id: int) -> "CT_FNR":
        rPr = self.get_or_add_rPr()
        rstyle = rPr.get_or_add_rStyle()
        rstyle.val = "FootnoteReference"
        reference = OxmlElement("w:footnoteReference")
        reference._id = _id
        self.append(reference)
        return reference

    def add_footnoteRef(self) -> "CT_FootnoteRef":
        ref = OxmlElement("w:footnoteRef")
        self.append(ref)

        return ref

    def footnote_style(self) -> "CT_R":
        rPr = self.get_or_add_rPr()
        rstyle = rPr.get_or_add_rStyle()
        rstyle.val = "FootnoteReference"

        self.add_footnoteRef()
        return self

    @property
    def footnote_id(self) -> int | None:
        _id = self.xpath("./w:footnoteReference/@w:id")
        if len(_id) > 1 or len(_id) == 0:
            return None
        else:
            return int(_id[0])

    def clear_content(self) -> None:
        """Remove all child elements except a `w:rPr` element if present."""
        # -- remove all run inner-content except a `w:rPr` when present. --
        for e in self.xpath("./*[not(self::w:rPr)]"):
            self.remove(e)

    @property
    def inner_content_items(self) -> List[str | CT_Drawing | CT_LastRenderedPageBreak]:
        """Text of run, possibly punctuated by `w:lastRenderedPageBreak` elements."""
        from docx.oxml.text.pagebreak import CT_LastRenderedPageBreak

        accum = TextAccumulator()

        def iter_items() -> Iterator[str | CT_Drawing | CT_LastRenderedPageBreak]:
            for e in self.xpath(
                "w:br"
                " | w:cr"
                " | w:drawing"
                " | w:lastRenderedPageBreak"
                " | w:noBreakHyphen"
                " | w:ptab"
                " | w:t"
                " | w:tab"
            ):
                if isinstance(e, (CT_Drawing, CT_LastRenderedPageBreak)):
                    yield from accum.pop()
                    yield e
                else:
                    accum.push(str(e))

            # -- don't forget the "tail" string --
            yield from accum.pop()

        return list(iter_items())

    @property
    def lastRenderedPageBreaks(self) -> List[CT_LastRenderedPageBreak]:
        """All `w:lastRenderedPageBreaks` descendants of this run."""
        return self.xpath("./w:lastRenderedPageBreak")

    def add_comment_reference(self, _id: int) -> BaseOxmlElement:
        reference = OxmlElement("w:commentReference")
        reference._id = _id
        self.append(reference)
        return reference

    @property
    def style(self) -> str | None:
        """String contained in `w:val` attribute of `w:rStyle` grandchild.

        |None| if that element is not present.
        """
        rPr = self.rPr
        if rPr is None:
            return None
        return rPr.style

    @style.setter
    def style(self, style: str | None):
        """Set character style of this `w:r` element to `style`.

        If `style` is None, remove the style element.
        """
        rPr = self.get_or_add_rPr()
        rPr.style = style

    @property
    def text(self) -> str:
        """The textual content of this run.

        Inner-content child elements like `w:tab` are translated to their text
        equivalent.
        """
        # TODO: insert '-' for qn('w:noBreakHyphen')?
        return "".join(
            str(e) for e in self.xpath("w:br | w:cr | w:noBreakHyphen | w:ptab | w:t | w:tab")
        )

    @text.setter
    def text(self, text: str):
        self.clear_content()
        _RunContentAppender.append_to_run_from_text(self, text)

    def _insert_rPr(self, rPr: CT_RPr) -> CT_RPr:
        self.insert(0, rPr)
        return rPr

    def add_fldChar(
        self, fldCharType: str, fldLock: bool = False, dirty: bool = False
    ) -> BaseOxmlElement | None:
        if fldCharType not in ("begin", "end", "separate"):
            return None

        fld_char = OxmlElement("w:fldChar")
        fld_char.set(qn("w:fldCharType"), fldCharType)
        if fldLock:
            fld_char.set(qn("w:fldLock"), "true")
        elif dirty:
            fld_char.set(qn("w:fldLock"), "true")
        self.append(fld_char)
        return fld_char

    @property
    def instr_text(self) -> BaseOxmlElement | None:
        for child in list(self):
            if child.tag.endswith("instrText"):
                return child
        return None

    @instr_text.setter
    def instr_text(self, instr_text_val: str):
        if self.instr_text is not None:
            self._remove_instr_text()

        instr_text = OxmlElement("w:instrText")
        instr_text.text = instr_text_val
        self.append(instr_text)

    def _remove_instr_text(self):
        for child in self.iterchildren("{*}instrText"):
            self.remove(child)


# ------------------------------------------------------------------------------------
# Run inner-content elements


class CT_Br(BaseOxmlElement):
    """`<w:br>` element, indicating a line, page, or column break in a run."""

    type: str | None = OptionalAttribute(  # pyright: ignore[reportAssignmentType]
        "w:type", ST_BrType, default="textWrapping"
    )
    clear: str | None = OptionalAttribute("w:clear", ST_BrClear)  # pyright: ignore

    def __str__(self) -> str:
        """Text equivalent of this element. Actual value depends on break type.

        A line break is translated as "\n". Column and page breaks produce the empty
        string ("").

        This allows the text of run inner-content to be accessed in a consistent way
        for all run inner-context text elements.
        """
        return "\n" if self.type == "textWrapping" else ""


class CT_Cr(BaseOxmlElement):
    """`<w:cr>` element, representing a carriage-return (0x0D) character within a run.

    In Word, this represents a "soft carriage-return" in the sense that it does not end
    the paragraph the way pressing Enter (aka. Return) on the keyboard does. Here the
    text equivalent is considered to be newline ("\n") since in plain-text that's the
    closest Python equivalent.

    NOTE: this complex-type name does not exist in the schema, where `w:tab` maps to
    `CT_Empty`. This name was added to give it distinguished behavior. CT_Empty is used
    for many elements.
    """

    def __str__(self) -> str:
        """Text equivalent of this element, a single newline ("\n")."""
        return "\n"


class CT_NoBreakHyphen(BaseOxmlElement):
    """`<w:noBreakHyphen>` element, a hyphen ineligible for a line-wrap position.

    This maps to a plain-text dash ("-").

    NOTE: this complex-type name does not exist in the schema, where `w:noBreakHyphen`
    maps to `CT_Empty`. This name was added to give it behavior distinguished from the
    many other elements represented in the schema by CT_Empty.
    """

    def __str__(self) -> str:
        """Text equivalent of this element, a single dash character ("-")."""
        return "-"


class CT_PTab(BaseOxmlElement):
    """`<w:ptab>` element, representing an absolute-position tab character within a run.

    This character advances the rendering position to the specified position regardless
    of any tab-stops, perhaps for layout of a table-of-contents (TOC) or similar.
    """

    def __str__(self) -> str:
        """Text equivalent of this element, a single tab ("\t") character.

        This allows the text of run inner-content to be accessed in a consistent way
        for all run inner-context text elements.
        """
        return "\t"


# -- CT_Tab functionality is provided by CT_TabStop which also uses `w:tab` tag. That
# -- element class provides the __str__() method for this empty element, unconditionally
# -- returning "\t".


class CT_Text(BaseOxmlElement):
    """`<w:t>` element, containing a sequence of characters within a run."""

    def __str__(self) -> str:
        """Text contained in this element, the empty string if it has no content.

        This property allows this run inner-content element to be queried for its text
        the same way as other run-content elements are. In particular, this never
        returns None, as etree._Element does when there is no content.
        """
        return self.text or ""


class CT_RPr(BaseOxmlElement):
    rStyle = ZeroOrOne("w:rStyle")


class CT_RStyle(BaseOxmlElement):
    val = RequiredAttribute("w:val", ST_String)


# ------------------------------------------------------------------------------------
# Utility


class _RunContentAppender:
    """Translates a Python string into run content elements appended in a `w:r` element.

    Contiguous sequences of regular characters are appended in a single `<w:t>` element.
    Each tab character ('\t') causes a `<w:tab/>` element to be appended. Likewise a
    newline or carriage return character ('\n', '\r') causes a `<w:cr>` element to be
    appended.
    """

    def __init__(self, r: CT_R):
        self._r = r
        self._bfr: List[str] = []

    @classmethod
    def append_to_run_from_text(cls, r: CT_R, text: str):
        """Append inner-content elements for `text` to `r` element."""
        appender = cls(r)
        appender.add_text(text)

    def add_text(self, text: str):
        """Append inner-content elements for `text` to the `w:r` element."""
        for char in text:
            self.add_char(char)
        self.flush()

    def add_char(self, char: str):
        """Process next character of input through finite state maching (FSM).

        There are two possible states, buffer pending and not pending, but those are
        hidden behind the `.flush()` method which must be called at the end of text to
        ensure any pending `<w:t>` element is written.
        """
        if char == "\t":
            self.flush()
            self._r.add_tab()
        elif char in "\r\n":
            self.flush()
            self._r.add_br()
        else:
            self._bfr.append(char)

    def flush(self):
        text = "".join(self._bfr)
        if text:
            self._r.add_t(text)
        self._bfr.clear()
