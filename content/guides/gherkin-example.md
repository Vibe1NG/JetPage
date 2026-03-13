# BDD with Gherkin

SiteGen's tests are written using **Behaviour-Driven Development (BDD)** with
the Gherkin syntax. Gherkin is a plain-English specification language that
doubles as executable test code via the [Behave](https://behave.readthedocs.io/)
framework.

## What Is Gherkin?

A Gherkin feature file describes software behaviour in terms of *scenarios*:
concrete examples of how the system should act. Each scenario is composed of
steps beginning with **Given**, **When**, or **Then** keywords.

This makes tests readable by non-programmers while remaining precise enough to
drive automation.

## Example Feature File

```gherkin
Feature: Navigation tree loading

  Background:
    Given a content directory with a valid _meta.json

  Scenario: Load top-level nav pages
    When the nav tree is loaded
    Then the node list contains a page node with slug "index"

  Scenario: Load a section with children
    Given the content directory has a "getting-started" section
    When the nav tree is loaded
    Then the nav tree contains a section node titled "Getting Started"
    And that section has child pages in the order defined by _meta.json

  Scenario: Missing section directory is handled gracefully
    Given no directory exists for the "missing-section" slug
    When the nav tree is loaded
    Then the "missing-section" section has an empty children list
```

## Python Step Definitions

```python
from pathlib import Path
import pytest
from behave import given, when, then
from sitegen.core.nav import load_nav_tree


@given("a content directory with a valid _meta.json")
def step_content_dir(context):
    context.content_dir = Path("content")


@when("the nav tree is loaded")
def step_load_nav(context):
    context.nav_tree = load_nav_tree(context.content_dir)


@then('the node list contains a page node with slug "index"')
def step_check_index(context):
    slugs = [n.slug for n in context.nav_tree.nodes]
    assert "index" in slugs, f"Expected 'index' in {slugs}"


@then('the nav tree contains a section node titled "Getting Started"')
def step_check_section(context):
    titles = [n.title for n in context.nav_tree.nodes if n.is_section]
    assert "Getting Started" in titles


@then("that section has child pages in the order defined by _meta.json")
def step_check_children(context):
    section = next(
        n for n in context.nav_tree.nodes
        if n.is_section and n.title == "Getting Started"
    )
    assert len(section.children) > 0, "Expected at least one child page"
```

## Running the Tests

```bash
poetry run behave features/
```

Behave discovers all `.feature` files under `features/`, matches each step to a
decorated function in `features/steps/`, and reports pass/fail for every
scenario.
