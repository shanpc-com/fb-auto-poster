# Facebook Auto Poster v5 Production Edition

Complete replacement project for GitHub Actions. It publishes **photo posts only**. There is no album mode and no text-only fallback.

## GitHub Secrets

Create these exact repository secrets:

- `FB_PAGE_ID`
- `FB_ACCESS_TOKEN`
- `FIXED_LINK`

## Install

1. Delete the old repository files.
2. Extract this ZIP.
3. Upload everything inside `fb-auto-poster-v5-production-edition` to the repository root, including `.github`.
4. Keep the repository default branch as `main`.
5. Add the three secrets above.
6. Open **Actions → Facebook Auto Poster v5 → Run workflow**.

## Expected successful log

```text
Processing: Example Software
Image found: https://...
SUCCESS photo posted: PAGE_ID_POST_ID
```

If no valid image is found, the workflow fails and nothing is posted.

## CSV format

The existing simple one-column `keywords.csv` works. Optional header format:

```csv
keyword,search_term,display_title,source_url,site_link
VLC Media Player,VLC Media Player,VLC Media Player,,
```

Providing a direct `source_url` is the most reliable way to obtain the correct image and metadata.

## Content rule

`LAWFUL_CONTENT_ONLY=true` skips titles containing crack, keygen, activator, patched, serial-key, or pre-activated terms. This is enabled in the workflow by default.

## Schedule

The included workflow runs every 6 hours and posts one item per run. Change `POSTS_PER_RUN` or the cron only after a successful manual test.
