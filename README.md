# Facebook Auto Poster v8 — Search Visibility Engine

Production GitHub Actions auto-poster focused on clear, useful, non-duplicative Facebook content and reliable verified publishing.

## V8 improvements

- Deterministic rotating caption templates so posts do not all use one identical pattern.
- Automatic software category classification.
- Primary and secondary keyword logging for each post.
- Category-aware hashtags with duplication control.
- Engagement question/CTA rotation.
- Content quality score recorded in `posted_log.json`.
- Branded 1200×630 images with category badge.
- Existing album support inherited from v7 through `FB_ALBUM_ID`.
- Verified Page, published state, clean permalink, retry and status reporting.
- One post per hour at minute 17 by default.
- Lawful-content filter remains enabled.

## Required GitHub secrets

- `FB_PAGE_ID`
- `FB_ACCESS_TOKEN`
- `FIXED_LINK`

Optional:

- `FB_ALBUM_ID` — numeric ID of an existing Page album.

## Safe upgrade

Keep your existing `keywords.csv` and `posted_log.json`. Replace all other project files with the contents of this ZIP. Ensure this exact workflow path exists:

`.github/workflows/auto-post.yml`

## Important limitation

V8 improves content consistency, discoverability signals and click appeal, but it cannot guarantee Facebook Search ranking, organic reach, engagement, Google indexing, or a particular Facebook URL format. Those outcomes are controlled by Meta and user behavior.
