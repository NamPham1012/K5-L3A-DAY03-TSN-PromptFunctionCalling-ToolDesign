---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia (MediaWiki API, no key)
requires_env: []
inputs: [query, lang, max_results]
outputs: [items]
side_effect: false
---
# wiki

Searches Wikipedia and returns matching articles with a plain-text summary of
each (title, url, source, summary). Use it for stable background knowledge:
definitions, people, organizations, concepts, history. Not for current news
(use `lookup` with `topic=news`) or a specific URL (use `fetch`).

`lang` is a Wikipedia language code: `en` (default) or `vi`.
