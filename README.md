# Facebook Software Auto Poster v2

GitHub Actions par chalne wala auto poster. Har run mein `keywords.csv` se agla unposted software title leta hai, trusted source metadata dhoondta hai, optional AI se factual caption ko polish karta hai, Facebook Page par post karta hai, aur duplicate prevention ke liye `posted_log.json` update karta hai.

## Post format

```text
{keyword}

📥 Download Now:
{FIXED_LINK ya row-specific site_link}

Version, developer, platform, license, file size aur description
Information source
Hashtags
```

`keyword` CSV mein jaisa clean title diya ho, post ke start mein wahi aata hai. Software data available ho to FileHippo, FileHorse, Uptodown, CNET Download, Softpedia, Softonic aur SourceForge se metadata liya jata hai. `source_url` column mein official page dene par usay pehli priority milti hai.

## Files

- `auto_poster.py`: main runner
- `app/sources.py`: source search and metadata extraction
- `app/ai.py`: optional Groq/Gemini caption generator
- `app/facebook.py`: Facebook Graph API publisher
- `app/keywords.py`: CSV reading and title normalization
- `.github/workflows/auto-post.yml`: schedule, secrets, logging and safe Git push
- `keywords.csv`: `keyword,site_link,source_url`

## GitHub Secrets

Repository → Settings → Secrets and variables → Actions:

Required:

- `FB_PAGE_ID`
- `FB_ACCESS_TOKEN`
- `FIXED_LINK`

Optional AI:

- `AI_PROVIDER`: `groq`, `gemini`, or leave empty
- `AI_API_KEY`
- `AI_MODEL`: optional. Defaults are built in.
- `GRAPH_API_VERSION`: optional, for example `v23.0`

Do not place real tokens inside files.

## Recommended keyword CSV

```csv
keyword,site_link,source_url
VLC Media Player 3.0.21,https://example.com/vlc,https://www.videolan.org/vlc/
7-Zip,https://example.com/7zip,https://www.7-zip.org/
Notepad++,https://example.com/notepad-plus-plus,
```

`site_link` blank ho to `FIXED_LINK` use hota hai. `source_url` blank ho to trusted-source search hoti hai.

## First test

1. Changes GitHub par upload karein.
2. Workflow permissions mein **Read and write permissions** select karein.
3. Actions → Auto Post to Facebook → Run workflow.
4. Pehle `dry_run` tick karke preview check karein.
5. Preview sahi ho to normal run karein.

## Local dry run

```bash
python -m pip install -r requirements.txt
DRY_RUN=true FIXED_LINK=https://example.com python auto_poster.py
```

Windows PowerShell:

```powershell
$env:DRY_RUN='true'
$env:FIXED_LINK='https://example.com'
python auto_poster.py
```

## Notes

- Source sites layout ya bot protection change karein to metadata unavailable ho sakta hai. Script fallback caption use karti hai aur workflow ko clear logs deti hai.
- Official `source_url` dena sabse reliable option hai.
- AI ko facts invent karne ki ijazat nahi di gayi. Missing fields post se omit hoti hain.
- GitHub workflow `contents: write`, bot identity, pull-rebase aur no-change checks use karta hai, is se common exit code 128 issues avoid hote hain.
- Publicly exposed Facebook tokens ko regenerate karke hi use karein.
