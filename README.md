# Facebook Software Auto Poster v3 Album Mode

GitHub Actions par chalne wala Facebook Page auto poster. Har run mein `keywords.csv` se agla unposted software title leta hai, trusted source metadata dhoondta hai, optional AI se factual caption polish karta hai, Facebook par publish karta hai, aur duplicate prevention ke liye `posted_log.json` update karta hai.

## Album-style publishing

`FB_ALBUM_ID` set ho aur software image available ho to script image ko us Facebook Page album mein upload karti hai. Album ka public link is format mein log hota hai:

```text
https://www.facebook.com/media/set/?set=a.ALBUM_ID
```

Important: Current Facebook Graph API app ko naya Page album create karne ki permission nahi deta. Is liye album Facebook Page par pehle manually banana hoga. Script existing album mein photos automatically add karegi.

### Album ID kaise nikalein

1. Facebook Page par album manually create karein.
2. Browser mein album kholein.
3. URL mein `set=a.123456789...` ke baad wali numeric ID copy karein.
4. GitHub repository mein `FB_ALBUM_ID` secret create karein.
5. Secret value mein sirf numeric ID ya `a.NUMERIC_ID`, dono supported hain.

Image ya album ID unavailable ho to automatic fallback hota hai:

1. Existing album photo upload
2. Normal Page photo post
3. Normal Page feed/link post

## Post format

```text
{Software Title}

📥 Download Now:
{site link}

📦 Version: ...
🏢 Developer: ...
💻 Platform: ...
📄 License: ...
💾 File Size: ...
📅 Updated: ...

📝 About
...

✨ Key Features
• ...

#Hashtags
```

## Main files

- `auto_poster.py`: main runner
- `app/facebook.py`: album, photo and feed publishing
- `app/sources.py`: source search and metadata extraction
- `app/ai.py`: optional Groq/Gemini caption generator
- `app/keywords.py`: CSV reading and title normalization
- `.github/workflows/auto-post.yml`: schedule, secrets and log commit
- `keywords.csv`: `keyword,site_link,source_url`
- `posted_log.json`: post ID, photo ID, album ID, album URL and publish mode

## GitHub Secrets

Required:

- `FB_PAGE_ID`
- `FB_ACCESS_TOKEN`
- `FIXED_LINK`

Album mode:

- `FB_ALBUM_ID`

Optional:

- `AI_PROVIDER`: `groq`, `gemini`, or empty
- `AI_API_KEY`
- `AI_MODEL`
- `GRAPH_API_VERSION`

Real token files mein save na karein.

## Recommended keywords.csv

```csv
keyword,site_link,source_url
VLC Media Player 3.0.21,https://example.com/vlc,https://www.videolan.org/vlc/
7-Zip,https://example.com/7zip,https://www.7-zip.org/
Notepad++,https://example.com/notepad-plus-plus,
```

## First test

1. ZIP files GitHub repository mein upload karein.
2. Repository Settings → Actions → General mein **Read and write permissions** select karein.
3. Required secrets aur `FB_ALBUM_ID` add karein.
4. Actions → Auto Post to Facebook → Run workflow.
5. Pehle `dry_run` se preview check karein.
6. Normal run karein aur `posted_log.json` mein `facebook_album_url` check karein.

## Local dry run

```bash
python -m pip install -r requirements.txt
DRY_RUN=true FIXED_LINK=https://example.com FB_ALBUM_ID=123456789 python auto_poster.py
```

## Permissions

Facebook app/Page token ko Page content publish karne ki required permissions aur Page access chahiye. Token invalid, expired, wrong Page ka, ya album inaccessible ho to script warning ke baad normal photo/feed post par fallback karegi.
