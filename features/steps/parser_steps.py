import re

from behave import given, then, when

from jetpage.content.parser import parse


def _has_css_class(html: str, cls: str) -> bool:
    """Return True if `cls` appears as a word within any class="..." attribute."""
    pattern = rf'class="[^"]*\b{re.escape(cls)}\b[^"]*"'
    return bool(re.search(pattern, html))


@given('the markdown "{text}"')
def step_given_double_quoted(context, text):
    context.markdown = text


@given("the markdown '{text}'")
def step_given_single_quoted(context, text):
    context.markdown = text


@given("the markdown")
def step_given_block_markdown(context):
    context.markdown = context.text


@when("it is parsed")
def step_when_parsed(context):
    context.html = parse(context.markdown)


@then('the output contains "{expected}"')
def step_then_contains_double(context, expected):
    assert expected in context.html, f"Expected to find:\n  {expected!r}\n\nIn output:\n  {context.html!r}"


@then("the output contains '{expected}'")
def step_then_contains_single(context, expected):
    assert expected in context.html, f"Expected to find:\n  {expected!r}\n\nIn output:\n  {context.html!r}"


@then('the output contains tag "{tag}" with text "{text}"')
def step_then_tag_with_text(context, tag, text):
    pattern = rf"<{tag}[^>]*>.*?{re.escape(text)}.*?</{tag}>"
    assert re.search(pattern, context.html, re.DOTALL), (
        f"Expected <{tag}> containing {text!r}\n\nIn output:\n  {context.html!r}"
    )


@then('the output contains css class "{cls}"')
def step_then_has_css_class(context, cls):
    assert _has_css_class(context.html, cls), f"Expected CSS class {cls!r} in output:\n  {context.html!r}"
