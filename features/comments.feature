Feature: Comments
  In order to add annotations to a document
  As a developer using python-docx
  I want to be able to add and read comments in a document

  Scenario: Add comment to paragraph's first run
    Given a document having a paragraph
    When I add a comment with text "New comment" to the paragraph's first run
    Then the comment text matches "New comment"
    
  Scenario: Add comment to paragraph
    Given a document having a paragraph
    When I add a comment with text "New comment"
    Then the paragraph has a comment
    And the comment text matches "New comment"

  Scenario: Get comment text
    Given a document having a comment
    When I get the comment text
    Then the text matches the comment content

  Scenario: Set comment text
    Given a document having a comment
    When I set the comment text to "Updated comment"
    Then the comment text matches "Updated comment"

  Scenario: Access comment paragraph
    Given a document having a comment
    When I access the comment paragraph
    Then I get a comment paragraph object 