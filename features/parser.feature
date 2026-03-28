Feature: Markdown parsing
  As a content author
  I want Markdown to be converted to HTML
  So that pages render correctly in the browser

  # --- Basic formatting ---

  Scenario: Headings render as HTML heading tags
    Given the markdown "# Hello World"
    When it is parsed
    Then the output contains tag "h1" with text "Hello World"

  Scenario: Bold text renders correctly
    Given the markdown "This is **bold** text"
    When it is parsed
    Then the output contains "<strong>bold</strong>"

  Scenario: Italic text renders correctly
    Given the markdown "This is *italic* text"
    When it is parsed
    Then the output contains "<em>italic</em>"

  Scenario: Unordered list renders as ul and li elements
    Given the markdown
      """
      - Item one
      - Item two
      - Item three
      """
    When it is parsed
    Then the output contains "<ul>"
    And the output contains "<li>Item one</li>"

  Scenario: Ordered list renders as ol and li elements
    Given the markdown
      """
      1. First
      2. Second
      """
    When it is parsed
    Then the output contains "<ol>"
    And the output contains "<li>First</li>"

  # --- Code blocks ---

  Scenario: Fenced code block renders as pre and code elements
    Given the markdown
      """
      ```python
      def hello():
          pass
      ```
      """
    When it is parsed
    Then the output contains "<pre>"
    And the output contains "<code"

  Scenario: Inline code renders as code element
    Given the markdown "Run `uv sync` to install"
    When it is parsed
    Then the output contains "<code>uv sync</code>"

  # --- Links ---

  Scenario: External links render as anchor tags
    Given the markdown "[Flet](https://flet.dev/)"
    When it is parsed
    Then the output contains '<a href="https://flet.dev/"'

  Scenario: Internal absolute links render as anchor tags
    Given the markdown "[Installation](/getting-started/installation)"
    When it is parsed
    Then the output contains '<a href="/getting-started/installation"'

  Scenario: Internal relative links render as anchor tags
    Given the markdown "[Configuration](../getting-started/configuration)"
    When it is parsed
    Then the output contains '<a href="../getting-started/configuration"'

  # --- Inline HTML ---

  Scenario: Inline HTML block is passed through unchanged
    Given the markdown
      """
      <div class="note">This is a note.</div>
      """
    When it is parsed
    Then the output contains '<div class="note">This is a note.</div>'

  Scenario: Inline HTML with attributes is passed through unchanged
    Given the markdown '<span style="color: red">red text</span>'
    When it is parsed
    Then the output contains '<span style="color: red">red text</span>'

  # --- Mixed content ---

  Scenario: A page with headings, paragraphs and a code block renders all elements
    Given the markdown
      """
      # My Page

      This is an intro paragraph.

      ```bash
      echo hello
      ```
      """
    When it is parsed
    Then the output contains tag "h1" with text "My Page"
    And the output contains "<p>This is an intro paragraph.</p>"
    And the output contains "<pre>"
