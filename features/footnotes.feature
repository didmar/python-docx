Feature: Footnotes
  In order to add references to a document
  As a developer using python-docx
  I want to be able to add and read footnotes in a document

  Scenario: Get footnote text
    Given a document having a footnote
    When I get the footnote text
    Then the footnote text matches the content

  Scenario: Set footnote text
    Given a document having a footnote
    When I set the footnote text to "Updated footnote"
    Then the footnote text matches "Updated footnote"

  Scenario: Access footnote paragraph
    Given a document having a footnote
    When I access the footnote paragraph
    Then I get a footnote paragraph object 

  Scenario: Add footnote to paragraph
    Given a document having a paragraph
    When I add a footnote with text "New footnote"
    Then the paragraph has a footnote
    And the footnote text matches "New footnote"