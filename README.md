# Facebook Auto Poster

Ye tool aapke keyword list se automatically Facebook Page posts banata hai,
ek fixed template + fixed link ke sath, aur schedule par khud post karta rehta hai.

**Example:** agar template `{keyword} — Download Now ✓ {link}` hai aur link
`https://yourwebsite.com` hai, aur keyword "Product Name One" hai, to post banega:

```
Product Name One — Download Now ✓ https://yourwebsite.com
```

Har naya keyword ke sath sirf shuru ka word change hota hai, baaki text/link same rehta hai.

---

## Files

| File | Kaam |
|---|---|
| `auto_poster.py` | Main script — post banata aur Facebook par bhejta hai |
| `config.example.json` | Settings template (isko copy karke `config.json` banayen) |
| `keywords.csv` | Aapki keyword list (yahan apne product/software names daalein) |
| `posted_log.json` | Auto-generated — track karta hai kaunse keywords post ho chuke hain |
| `.github/workflows/auto-post.yml` | Automatic scheduling (GitHub Actions) |

---

## Setup — Step by Step

### 1. Keywords add karein
`keywords.csv` file kholein aur apne keywords ek per line daal dein:
```
keyword
Product Name One
Product Name Two
Product Name Three
```

### 2. Facebook Page Access Token banayein
1. https://developers.facebook.com par jayein aur login karein
2. **My Apps → Create App → "Other" → "Business"** select karein
3. App create hone ke baad, left menu se **Facebook Login for Business** ya
   **Graph API Explorer** tool open karein: https://developers.facebook.com/tools/explorer/
4. Graph API Explorer mein:
   - Apna App select karein
   - **"User or Page"** dropdown se apna Facebook Page select karein
   - Permissions mein ye add karein: `pages_manage_posts`, `pages_read_engagement`
   - **Generate Access Token** click karein
5. Ye token **temporary (1-2 hour)** hota hai. Long-term (60 din) token banane ke liye:
   - Token ko is URL mein daal kar exchange karein (apna APP_ID, APP_SECRET, SHORT_TOKEN daal kar):
   ```
   https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN
   ```
   - Better: Page ka **Never-expiring token** banane ke liye [Meta Business Suite → System User] use karein (permanent token, production ke liye recommended)
6. Page ID pata karne ke liye: apni Facebook Page → **About** section → "Page ID" wahan mil jayega

⚠️ Access token ko kabhi bhi public/GitHub public repo mein mat likhein — GitHub Secrets use karein (neeche step 4 mein bataya hai).

### 3. Local test (optional, pehle try karne ke liye)
```bash
pip install -r requirements.txt
cp config.example.json config.json
```
Ab `config.json` kholein aur apna `link`, `facebook_page_id`, `facebook_access_token` daal dein.

Phir run karein:
```bash
python auto_poster.py
```
Ye 1 post (config mein `posts_per_run` jitne) Facebook Page par bhej dega.

### 4. Automatic scheduling (GitHub Actions — free)
1. Ye poora folder GitHub par ek **private repository** mein upload karein
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**
   — ye 3 secrets add karein:
   - `FB_PAGE_ID` → aapka Facebook Page ID
   - `FB_ACCESS_TOKEN` → aapka access token
   - `FIXED_LINK` → aapki fixed link (jaise `https://yourwebsite.com`)
3. `.github/workflows/auto-post.yml` mein cron schedule edit kar sakte hain:
   - `0 */3 * * *` = har 3 ghante mein ek post
   - `0 9,14,19 * * *` = din mein 3 baar (9AM, 2PM, 7PM UTC)
4. Bas — ab ye har schedule par khud chalega aur agla keyword automatically post karega
5. Manually bhi chala sakte hain: repo → **Actions tab → Auto Post to Facebook → Run workflow**

---

## Customize karna
- **Template badalna:** `config.json` mein `template` field edit karein
- **Ek run mein zyada posts:** `posts_per_run` value badhayein (jaise 3)
- **Keywords dobara post karna:** `posted_log.json` delete/khali kar dein

---

## Important Notes
- Ye tool sirf **text posts** karta hai (image generate nahi karta) — jaisa aapne request kiya
- Facebook access tokens ki permissions/policies waqt ke sath change ho sakti hain — agar error aaye to token refresh karein
- Bulk/frequent auto-posting Facebook ki spam policies ke against na jaye iska khayal rakhein — realistic gap rakhein (2-3 ghante minimum recommended)
