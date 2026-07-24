# 0006. Plain-text prompt templates over Jinja2/structured formats

Date: 2026-07-24
Status: Accepted

## Context

Summaries are generated against a template that defines what to focus on. Options considered:
plain text/markdown prompt files, Jinja2 templates (allowing interpolation of metadata like title/
date/source), and structured YAML/JSON describing required sections, parsed into a prompt
programmatically.

## Decision

Templates are plain text/markdown files containing prompt instructions, combined directly with
the transcript text when calling the LLM. A generic default template ships with the tool; users
may pass `--template <path>` to supply their own.

## Consequences

- No templating engine dependency, no schema to define/validate/maintain.
- Templates are trivially human-editable and readable without documentation.
- No metadata interpolation (title/date/source) into the prompt in the MVP — if that's needed
  later, revisit Jinja2 rather than retrofitting string interpolation ad hoc.
