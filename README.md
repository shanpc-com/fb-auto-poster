# Facebook Auto Poster v5.3 SEO Photo Mode

Publishes exactly one verified Facebook Page photo post per scheduled run.

## What this version changes

- Uses a real public Page photo post, not a text-only feed fallback.
- Puts the software title on the first caption line.
- Publishes the image with `published=true`.
- Retrieves and verifies the Facebook `permalink_url` after publishing.
- Fails the workflow when Facebook accepts an upload but no public permalink can be verified.
- Saves the permalink in `posted_log.json` and prints it in Actions logs.
- Runs hourly at minute 17 UTC and publishes one post per run.

## Important Facebook limitation

A normal Page photo post does not have a separate editable HTML title or meta description. Facebook controls the final page markup. The first caption line is used as the visible title-like text. A `/media/set/?set=...` URL requires a real Facebook album and cannot be manufactured by the script when the Page has no album feature.

## GitHub Secrets

- `FB_PAGE_ID`
- `FB_ACCESS_TOKEN`
- `FIXED_LINK`

## Expected success log

```text
SUCCESS verified photo post: PAGE_ID_POST_ID
Facebook permalink: https://www.facebook.com/...
```

Google may index a public Facebook permalink, but indexing and the exact search title/snippet are controlled by Google and Facebook and are not guaranteed by this script.
