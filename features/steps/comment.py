from behave import given, then, when

from docx import Document

from helpers import test_docx


# ----- Document having comment -----
@given("a document having a comment")
def given_document_having_comment(context):
    context.document = Document(test_docx("having-comments"))
    context.comment = context.document.paragraphs[2].comments[0]


# ----- Get comment text -----
@when("I get the comment text")
def when_get_comment_text(context):
    context.comment_text = context.comment.text


@then("the text matches the comment content")
def then_text_matches_content(context):
    assert context.comment_text == "Comment text"


# ----- Set comment text -----
@when('I set the comment text to "{text}"')
def when_set_comment_text(context, text):
    context.comment.text = text


@then('the comment text matches "{text}"')
def then_comment_text_matches(context, text):
    assert context.comment.text == text, f"Expected '{text}', got '{context.comment.text}'"


# ----- Access comment paragraph -----
@when("I access the comment paragraph")
def when_access_comment_paragraph(context):
    context.paragraph = context.comment.paragraph


@then("I get a comment paragraph object")
def then_get_comment_paragraph_object(context):
    from docx.text.paragraph import Paragraph

    assert isinstance(context.paragraph, Paragraph)


# ----- Add comment to paragraph -----
@when('I add a comment with text "{text}"')
def when_add_comment_with_text(context, text: str):
    context.comment = context.paragraph.add_comment(text)


@then("the comment text matches {text}")
def then_comment_text_matches(context, text: str):
    assert context.comment.text == text


@then("the paragraph has a comment")
def then_paragraph_has_comment(context):
    assert len(context.paragraph.comments) > 0


# ----- Add comment to run -----
@when('I add a comment with text "{text}" to the paragraph\'s first run')
def when_add_comment_to_run(context, text: str):
    context.comment = context.paragraph.runs[0].add_comment(text)


@then("the run has a comment")
def then_run_has_comment(context):
    assert len(context.run.comments) > 0
