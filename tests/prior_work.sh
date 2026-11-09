# Shared test helper: write a checkable prior-work search and review into a finding folder.
# Usage: fill_prior_work <finding dir> [novelty]   (novelty: similar | nothing found | known)
fill_prior_work() {
  local d="$1" nov="${2:-similar}"
  cat > "$d/literature.md" <<LIT
# prior work

**Search date:** 2026-11-09

## Searches

| Query | Source | What I looked at |
|---|---|---|
| weather ice cream sales forecast | Google Scholar | first 20 results |
| temperature retail demand forecasting | arXiv | first 20 results |
| ice cream demand weather model | GitHub | first 10 repositories |

## Closest work found

| Work | Link | How it differs from the claim |
|---|---|---|
| Weather and retail demand (2019) | https://example.org/paper | uses observed weather, not the forecast of the day before |

## Assessment

The closest work uses the same idea on other data.

Novelty: $nov
LIT
  cat > "$d/review.md" <<REV
# review
No exploit found.

## Prior work re-check
Query: ice cream sales temperature
Source: Semantic Scholar
Missed: none

Verdict: ACCEPT
REV
}
