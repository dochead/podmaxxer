# 0005. `trafilatura` for article text extraction

Date: 2026-07-24
Status: Accepted

## Context

The MVP accepts text articles (HTML) as a content kind, in addition to audio/video. Extracting
clean article text from arbitrary HTML (stripping navigation, ads, boilerplate) was considered
either via a purpose-built extraction library (`trafilatura`) or via `BeautifulSoup` plus hand-
rolled heuristics.

## Decision

Use `trafilatura` for HTML-to-article-text extraction.

## Consequences

- Avoids maintaining bespoke boilerplate-stripping heuristics, which are a well-known long tail of
  edge cases across real-world sites.
- Adds one dependency purpose-built for this exact problem, widely regarded as a strong extractor.
- If article extraction quality issues arise on specific sites, they're `trafilatura` upstream
  issues/config rather than this project's own heuristics to debug.
