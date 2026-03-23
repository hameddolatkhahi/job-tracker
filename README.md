# jobs.ac.uk Daily Tracker

Automatically scrapes [jobs.ac.uk](https://www.jobs.ac.uk) every morning for your keywords and displays results on a GitHub Pages website.

---

## Setup (takes ~5 minutes)

### 1. Create a GitHub repository

1. Go to [github.com](https://github.com) and sign in (or create a free account)
2. Click **+** → **New repository**
3. Name it anything, e.g. `jobs-tracker`
4. Set it to **Public** (required for free GitHub Pages)
5. Click **Create repository**

### 2. Upload these files

Upload the full folder structure to your repo:

```
jobs-tracker/
├── .github/
│   └── workflows/
│       └── scrape.yml
├── docs/
│   └── index.html
├── scrape.py
└── README.md
```

The easiest way is to drag and drop all files via the GitHub web UI, or use Git:

```bash
git clone https://github.com/YOUR_USERNAME/jobs-tracker
# copy files in, then:
git add .
git commit -m "initial setup"
git push
```

### 3. Set your keywords

1. In your repo, go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Click **New repository variable**
3. Name: `KEYWORDS`
4. Value: comma-separated keywords, e.g.:  
   `technologist, research software engineer, data scientist, librarian`
5. Click **Save**

### 4. Enable GitHub Pages

1. In your repo, go to **Settings** → **Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: `main`, Folder: `/docs`
4. Click **Save**
5. GitHub will give you a URL like `https://YOUR_USERNAME.github.io/jobs-tracker`

### 5. Run the scraper for the first time

The action runs automatically at **07:00 UTC every day**, but to get results right now:

1. Go to **Actions** tab in your repo
2. Click **Daily Jobs Scraper** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Wait ~1 minute for it to finish
5. Visit your GitHub Pages URL — results will be there!

---

## Changing keywords later

Go to **Settings** → **Secrets and variables** → **Actions** → **Variables**, edit `KEYWORDS`, and the next daily run will use your new list.

## Schedule

The scraper runs at **07:00 UTC** (08:00 in winter, 09:00 BST in summer). To change the time, edit `.github/workflows/scrape.yml` and modify the cron line:

```yaml
- cron: "0 7 * * *"
#         ^ hour (UTC)
```

---

## How it works

1. **GitHub Actions** wakes up on schedule, runs `scrape.py`
2. `scrape.py` fetches jobs.ac.uk search results for each keyword and saves them to `docs/results.json`
3. The action commits `results.json` back to the repo
4. **GitHub Pages** serves `docs/index.html`, which reads `results.json` and renders the results

No servers. No costs. Fully automated.
