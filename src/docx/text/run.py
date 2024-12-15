"""Run-related proxy objects for python-docx, Run in particular."""

from __future__ import annotations

from datetime import datetime
from typing import IO, TYPE_CHECKING, Iterator, List, cast

from docx.drawing import Drawing
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK
from docx.opc.packuri import PackURI
from docx.oxml.drawing import CT_Drawing
from docx.oxml.ns import qn
from docx.oxml.text.pagebreak import CT_LastRenderedPageBreak
from docx.shape import InlineShape
from docx.shared import StoryChild
from docx.styles.style import CharacterStyle
from docx.text.comment import Comment
from docx.text.font import Font
from docx.text.footnote import Footnote
from docx.text.pagebreak import RenderedPageBreak

if TYPE_CHECKING:
    import docx.types as t
    from docx.enum.text import WD_UNDERLINE
    from docx.opc.part import Part
    from docx.oxml.comments import CT_Com, CT_Comments, CT_CRef
    from docx.oxml.footnotes import CT_Footnotes
    from docx.oxml.text.run import CT_R, CT_Text
    from docx.parts.comments import CommentsPart
    from docx.parts.document import DocumentPart
    from docx.shared import Length


class Run(StoryChild):
    """Proxy object wrapping `<w:r>` element.

    Several of the properties on Run take a tri-state value, |True|, |False|, or |None|.
    |True| and |False| correspond to on and off respectively. |None| indicates the
    property is not specified directly on the run and its effective value is taken from
    the style hierarchy.
    """

    def __init__(self, r: CT_R, parent: t.ProvidesStoryPart):
        super().__init__(parent)
        self._r = self._element = self.element = r

    def add_break(self, break_type: WD_BREAK = WD_BREAK.LINE):
        """Add a break element of `break_type` to this run.

        `break_type` can take the values `WD_BREAK.LINE`, `WD_BREAK.PAGE`, and
        `WD_BREAK.COLUMN` where `WD_BREAK` is imported from `docx.enum.text`.
        `break_type` defaults to `WD_BREAK.LINE`.
        """
        type_, clear = {
            WD_BREAK.LINE: (None, None),
            WD_BREAK.PAGE: ("page", None),
            WD_BREAK.COLUMN: ("column", None),
            WD_BREAK.LINE_CLEAR_LEFT: ("textWrapping", "left"),
            WD_BREAK.LINE_CLEAR_RIGHT: ("textWrapping", "right"),
            WD_BREAK.LINE_CLEAR_ALL: ("textWrapping", "all"),
        }[break_type]
        br = self._r.add_br()
        if type_ is not None:
            br.type = type_
        if clear is not None:
            br.clear = clear

    def add_picture(
        self,
        image_path_or_stream: str | IO[bytes],
        width: int | Length | None = None,
        height: int | Length | None = None,
    ) -> InlineShape:
        """Return |InlineShape| containing image identified by `image_path_or_stream`.

        The picture is added to the end of this run.

        `image_path_or_stream` can be a path (a string) or a file-like object containing
        a binary image.

        If neither width nor height is specified, the picture appears at
        its native size. If only one is specified, it is used to compute a scaling
        factor that is then applied to the unspecified dimension, preserving the aspect
        ratio of the image. The native size of the picture is calculated using the dots-
        per-inch (dpi) value specified in the image file, defaulting to 72 dpi if no
        value is specified, as is often the case.
        """
        inline = self.part.new_pic_inline(image_path_or_stream, width, height)
        self._r.add_drawing(inline)
        return InlineShape(inline)

    def add_tab(self) -> None:
        """Add a ``<w:tab/>`` element at the end of the run, which Word interprets as a
        tab character."""
        self._r.add_tab()

    def add_text(self, text: str):
        """Returns a newly appended |_Text| object (corresponding to a new ``<w:t>``
        child element) to the run, containing `text`.

        Compare with the possibly more friendly approach of assigning text to the
        :attr:`Run.text` property.
        """
        t = self._r.add_t(text)
        return _Text(t)

    def add_comment(
        self,
        text: str,
        author: str = "python-docx",
        initials: str = "pd",
        dtime: datetime | None = None,
    ) -> Comment:
        document_part: DocumentPart = self.part
        comments_part: CommentsPart = document_part._comments_part  # pyright: ignore[reportPrivateUsage]
        comments_part_comments: CT_Comments = comments_part.comments

        if dtime is None:
            dtime = datetime.now()
        date = str(dtime).replace(" ", "T")

        comment: CT_Com = self._r.add_comment(author, initials, date, text, comments_part_comments)

        return Comment(comment, comments_part)

    @property
    def bold(self) -> bool | None:
        """Read/write tri-state value.

        When |True|, causes the text of the run to appear in bold face. When |False|,
        the text unconditionally appears non-bold. When |None| the bold setting for this
        run is inherited from the style hierarchy.
        """
        return self.font.bold

    @bold.setter
    def bold(self, value: bool | None):
        self.font.bold = value

    def clear(self):
        """Return reference to this run after removing all its content.

        All run formatting is preserved.
        """
        self._r.clear_content()
        return self

    @property
    def contains_page_break(self) -> bool:
        """`True` when one or more rendered page-breaks occur in this run.

        Note that "hard" page-breaks inserted by the author are not included. A hard
        page-break gives rise to a rendered page-break in the right position so if those
        were included that page-break would be "double-counted".

        It would be very rare for multiple rendered page-breaks to occur in a single
        run, but it is possible.
        """
        return bool(self._r.lastRenderedPageBreaks)

    @property
    def font(self) -> Font:
        """The |Font| object providing access to the character formatting properties for
        this run, such as font name and size."""
        return Font(self._element)

    @property
    def italic(self) -> bool | None:
        """Read/write tri-state value.

        When |True|, causes the text of the run to appear in italics. When |False|, the
        text unconditionally appears non-italic. When |None| the italic setting for this
        run is inherited from the style hierarchy.
        """
        return self.font.italic

    @italic.setter
    def italic(self, value: bool | None):
        self.font.italic = value

    def iter_inner_content(self) -> Iterator[str | Drawing | RenderedPageBreak]:
        """Generate the content-items in this run in the order they appear.

        NOTE: only content-types currently supported by `python-docx` are generated. In
        this version, that is text and rendered page-breaks. Drawing is included but
        currently only provides access to its XML element (CT_Drawing) on its
        `._drawing` attribute. `Drawing` attributes and methods may be expanded in
        future releases.

        There are a number of element-types that can appear inside a run, but most of
        those (w:br, w:cr, w:noBreakHyphen, w:t, w:tab) have a clear plain-text
        equivalent. Any contiguous range of such elements is generated as a single
        `str`. Rendered page-break and drawing elements are generated individually. Any
        other elements are ignored.
        """
        for item in self._r.inner_content_items:
            if isinstance(item, str):
                yield item
            elif isinstance(item, CT_LastRenderedPageBreak):
                yield RenderedPageBreak(item, self)
            elif isinstance(item, CT_Drawing):  # pyright: ignore[reportUnnecessaryIsInstance]
                yield Drawing(item, self)

    @property
    def style(self) -> CharacterStyle:
        """Read/write.

        A |CharacterStyle| object representing the character style applied to this run.
        The default character style for the document (often `Default Character Font`) is
        returned if the run has no directly-applied character style. Setting this
        property to |None| removes any directly-applied character style.
        """
        style_id = self._r.style
        return cast(CharacterStyle, self.part.get_style(style_id, WD_STYLE_TYPE.CHARACTER))

    @style.setter
    def style(self, style_or_name: str | CharacterStyle | None):
        style_id = self.part.get_style_id(style_or_name, WD_STYLE_TYPE.CHARACTER)
        self._r.style = style_id

    @property
    def text(self) -> str:
        """String formed by concatenating the text equivalent of each run.

        Each `<w:t>` element adds the text characters it contains. A `<w:tab/>` element
        adds a `\\t` character. A `<w:cr/>` or `<w:br>` element each add a `\\n`
        character. Note that a `<w:br>` element can indicate a page break or column
        break as well as a line break. Only line-break `<w:br>` elements translate to
        a `\\n` character. Others are ignored. All other content child elements, such as
        `<w:drawing>`, are ignored.

        Assigning text to this property has the reverse effect, translating each `\\t`
        character to a `<w:tab/>` element and each `\\n` or `\\r` character to a
        `<w:cr/>` element. Any existing run content is replaced. Run formatting is
        preserved.
        """
        return self._r.text

    @text.setter
    def text(self, text: str):
        self._r.text = text

    @property
    def underline(self) -> bool | WD_UNDERLINE | None:
        """The underline style for this |Run|.

        Value is one of |None|, |True|, |False|, or a member of :ref:`WdUnderline`.

        A value of |None| indicates the run has no directly-applied underline value and
        so will inherit the underline value of its containing paragraph. Assigning
        |None| to this property removes any directly-applied underline value.

        A value of |False| indicates a directly-applied setting of no underline,
        overriding any inherited value.

        A value of |True| indicates single underline.

        The values from :ref:`WdUnderline` are used to specify other outline styles such
        as double, wavy, and dotted.
        """
        return self.font.underline

    @underline.setter
    def underline(self, value: bool):
        self.font.underline = value

    @property
    def footnote(self) -> Footnote | None:
        _id = self._r.footnote_id

        if _id is not None:
            footnotes_part_footnotes: CT_Footnotes = (
                self._parent._parent.part._footnotes_part.element
            )
            footnote = footnotes_part_footnotes.get_footnote_by_id(_id)
            return Footnote(footnote, footnotes_part_footnotes)
        else:
            return None

    @property
    def is_hyperlink(self) -> bool:
        """
        checks if the run is nested inside a hyperlink element
        """
        return self.element.getparent().tag.split("}")[1] == "hyperlink"

    def get_hyperlink(self) -> tuple[str, bool]:
        """
        returns the text of the hyperlink of the run in case of the run has a hyperlink
        """
        document = self._parent._parent.document
        parent = self.element.getparent()
        link_text = ""
        if self.is_hyperlink:
            if parent.attrib.__contains__(qn("r:id")):
                rId = parent.get(qn("r:id"))
                link_text = document._part._rels[rId].target_ref
                return link_text, True
            elif parent.attrib.__contains__(qn("w:anchor")):
                link_text = parent.get(qn("w:anchor"))
                return link_text, False
            else:
                print("No Link in Hyperlink!")
                print(self.text)
                return "", False
        else:
            return "None"

    @property
    def comments(self) -> List[Comment]:
        """Return a list of Comment objects for comments referenced by this run."""
        comment_part_comments: CT_Comments = self._parent._parent.part._comments_part.element
        comment_refs: list[CT_CRef] = self._element.findall(qn("w:commentReference"))
        ids = [int(ref.get(qn("w:id"))) for ref in comment_refs]
        coms: list[CT_Com] = [com for com in comment_part_comments if com._id in ids]
        return [Comment(com, comment_part_comments) for com in coms]

    def add_ole_object_to_run(self, ole_object_path: str) -> str:
        """
        Add saved OLE Object in the disk to an run and retun the newly created relationship ID
        Note: OLE Objects must be stored in the disc as `.bin` file
        """
        reltype: str = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"
        )
        pack_path: str = "/word/embeddings/" + ole_object_path.split("\\")[-1]
        partname: PackURI = PackURI(pack_path)
        content_type: str = "application/vnd.openxmlformats-officedocument.oleObject"

        with open(ole_object_path, "rb") as f:
            blob = f.read()
        target_part: Part = Part(partname=partname, content_type=content_type, blob=blob)
        rel_id: str = self.part.rels._next_rId  # pyright: ignore[reportPrivateUsage]
        self.part.rels.add_relationship(reltype=reltype, target=target_part, rId=rel_id)
        return rel_id

    def add_fldChar(self, fldCharType: str, fldLock: bool = False, dirty: bool = False) -> str:
        fldChar = self._r.add_fldChar(fldCharType, fldLock, dirty)
        return fldChar

    @property
    def instr_text(self) -> str | None:
        return self._r.instr_text

    @instr_text.setter
    def instr_text(self, instr_text_val: str):
        self._r.instr_text = instr_text_val

    def remove_instr_text(self):
        if self.instr_text is None:
            return None
        else:
            self._r._remove_instr_text()  # pyright: ignore[reportPrivateUsage]


class _Text:
    """Proxy object wrapping `<w:t>` element."""

    def __init__(self, t_elm: CT_Text):
        super(_Text, self).__init__()
        self._t = t_elm
