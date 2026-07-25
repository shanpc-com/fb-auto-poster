# Facebook Auto Poster v7 — Album-Aware Publishing

V7 keeps the verified Graph API publishing flow from v6 and adds optional uploads to an **existing Facebook Page album**.

## What v7 adds

- Optional `FB_ALBUM_ID` support.
- Verifies that the album exists and belongs to the configured Page when Facebook returns owner data.
- Uploads through `/{album-id}/photos` when album mode is enabled.
- Saves both the individual photo/post permalink and the album URL.
- Album URL format: `https://www.facebook.com/media/set/?set=a.ALBUM_ID`.
- Automatic fallback to a normal Page photo if album upload fails.
- Set `ALBUM_FALLBACK_TO_PAGE=false` to make album upload mandatory.
- Preserves v6 Page verification, read-back verification, clean permalinks, retries, logs, generated image fallback, hourly workflow, tests, and duplicate protection.

## Important limitation

V7 can upload into an **existing album**. It does not create a separate new album for every keyword. Every photo uploaded to the same album shares the same `/media/set/?set=a...` album URL, while each photo still receives its own individual Facebook permalink.

## GitHub Secrets

Required:

- `FB_PAGE_ID`
- `FB_ACCESS_TOKEN`
- `FIXED_LINK`

Optional:

- `FB_ALBUM_ID` — numeric ID of an existing Page album.

If `FB_ALBUM_ID` is absent, v7 publishes a verified normal Page photo exactly like v6.

## How to find the album ID

Open the album on Facebook. A URL such as:

`https://www.facebook.com/media/set/?set=a.122114030823387405`

contains this album ID:

`122114030823387405`

Add only the numeric value to the GitHub secret `FB_ALBUM_ID`.

## Recommended repository update

Keep your existing `keywords.csv` and `posted_log.json`. Replace the remaining old project files with this v7 package. Your existing repository secrets remain safe.

## Publishing records

Each successful item in `posted_log.json` includes:

- `facebook_permalink`
- `facebook_album_id`
- `facebook_album_url`
- `publish_mode`
- verification status and timestamps

## Schedule

The workflow runs once per hour at minute 17 and publishes one eligible item per run.
