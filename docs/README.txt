The documentation build writes the planning site's generated HTML to
docs/html/, which git ignores; this directory holds the build's link
checker.

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

Check the sources alone, without a build (./be model-check runs this too):
  ./be docs-source-check

Build and open the full interactive planning site:
  ./be docs

Direct local-file fallback, once a build has written it:
  docs/html/index.html

The direct-file site is readable and uses relative URLs. Browser security
blocks local ES modules and fonts; use ./be docs for search, theme controls,
and the complete interactive site.

Set DOCS_BASE when publishing below a URL prefix, for example:
  DOCS_BASE=/beryllium/ npm run docs:build
