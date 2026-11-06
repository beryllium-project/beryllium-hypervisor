This directory contains the generated HTML documentation.

Source of truth:
  planning/*.md

Do not edit files under docs/html directly.

Planning diagram source:
  planning/diagrams/*.dot

Generated diagram assets:
  planning/public/diagrams/*.svg

The documentation build regenerates diagrams before VitePress.

Build and validate:
  npm ci
  ./be docs-check

Build and open the full interactive planning site:
  ./be docs

Direct local-file fallback:
  docs/html/index.html

The direct-file site is readable and uses relative URLs. Browser security
blocks local ES modules and fonts; use ./be docs for search, theme controls,
and the complete interactive site.

Set DOCS_BASE when publishing below a URL prefix, for example:
  DOCS_BASE=/beryllium/ npm run docs:build

Helium has a separate standalone generated site:
  pathfinder/docs/html/index.html

Its source and validation commands are:
  pathfinder/docs/*.md
  ./be helium docs-check
