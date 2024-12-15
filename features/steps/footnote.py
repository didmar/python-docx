from behave import given, when, then
from docx import Document
from docx.text.paragraph import Paragraph

from helpers import test_docx


@given("a document having a footnote")
def given_document_having_footnote(context):
    context.document = Document(test_docx("having-footnotes"))
    context.footnote = context.document.paragraphs[0].footnotes[0]


@when("I get the footnote text")
def when_get_footnote_text(context):
    context.footnote_text = context.footnote.text


@then("the footnote text matches the content")
def then_text_matches_content(context):
    assert context.footnote_text == "Footnote text"


@when('I set the footnote text to "{text}"')
def when_set_footnote_text(context, text: str):
    context.footnote.text = text


@then('the footnote text matches "{text}"')
def then_footnote_text_matches(context, text: str):
    assert context.footnote.text == text, f"Footnote text: '{context.footnote.text}'"


@when("I access the footnote paragraph")
def when_access_footnote_paragraph(context):
    context.paragraph = context.footnote.paragraph


@then("I get a footnote paragraph object")
def then_get_footnote_paragraph_object(context):
    assert isinstance(context.paragraph, Paragraph)


# ----- Add footnote -----
@when('I add a footnote with text "{text}"')
def when_add_footnote_with_text(context, text: str):
    context.footnote = context.paragraph.add_footnote(text)


@then("the paragraph has a footnote")
def then_paragraph_has_footnote(context):
    assert len(context.paragraph.footnotes) > 0
