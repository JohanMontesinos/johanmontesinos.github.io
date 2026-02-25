# Site Features Setup Guide

Three features have been added to your site. Each requires a one-time account
setup to activate. Follow the steps below in order.

---

## 1. GitHub Pages Auto-Deploy (workflow already created)

**What it does:** Every `git push` to main automatically deploys your site.

**One-time setup:**

```
https://github.com/JohanMontesinos/johanmontesinos.github.io
→ Settings
→ Pages  (left sidebar)
→ Source: GitHub Actions   ← select this
→ Save
```

That's it. The workflow file `.github/workflows/deploy.yml` is already in
your repo. On your next push it will run automatically.

**Verify:** After pushing, go to:
```
https://github.com/JohanMontesinos/johanmontesinos.github.io/actions
→ "Deploy to GitHub Pages" should show green ✓
```

---

## 2. Giscus Comments (GitHub Discussions)

**What it does:** Real comments on your blog posts, powered by GitHub
Discussions. Readers log in with their GitHub account. Free, no backend,
no database — comments are stored as GitHub Discussions threads.

**One-time setup:**

### Step A — Enable GitHub Discussions on your repo
```
https://github.com/JohanMontesinos/johanmontesinos.github.io
→ Settings
→ Features section
→ Check: Discussions ✓
→ Save
```

### Step B — Install the Giscus GitHub App
```
https://github.com/apps/giscus
→ Install
→ Select: JohanMontesinos/johanmontesinos.github.io
→ Install
```

### Step C — Get your personal snippet
```
https://giscus.app

Fill in:
  Repository:   JohanMontesinos/johanmontesinos.github.io
  Page ↔ Discussion mapping: pathname
  Discussion category: General (or create a "Comments" category)
  Theme: light

→ The site generates a <script> tag for you.
→ Copy the data-repo-id and data-category-id values.
```

### Step D — Update the blog post
Open `post/microk8s-devops/blog-post-microk8s-devops.html` and find:

```html
data-repo-id="REPLACE_WITH_REPO_ID"
data-category-id="REPLACE_WITH_CATEGORY_ID"
```

Replace both values with what giscus.app gave you. Then push:

```bash
cd ~/johanmontesinos.github.io
git add post/microk8s-devops/blog-post-microk8s-devops.html
git commit -m "Activate Giscus comments"
git push origin main
```

Do the same for each new post you publish — paste the same script block
into the comments section of each post HTML file.

---

## 3. GoatCounter Analytics

**What it does:** Shows you how many visitors each page gets, which countries
they are from, which pages are most popular, and what links brought them.
Privacy-friendly — no cookies, no GDPR banner required. Free up to 100k
pageviews/month.

**One-time setup:**

### Step A — Create a free account
```
https://www.goatcounter.com
→ Sign up
→ Site code: johanmontesinos   (or any short name — becomes your URL)
→ Email + password
→ Create
```

Your dashboard will be at: `https://johanmontesinos.goatcounter.com`

### Step B — Update the tracking code in every HTML file
The snippet `YOUR_SITE_CODE` appears in every HTML file in your repo.
Replace it with the site code you chose (e.g. `johanmontesinos`):

```bash
# LAPTOP terminal — replace in all files at once
cd ~/johanmontesinos.github.io

# macOS (BSD sed requires '' after -i)
find . -name "*.html" -not -path "./.git/*" \
  -exec sed -i '' 's/YOUR_SITE_CODE/johanmontesinos/g' {} +

# Verify the replacement worked
grep -r "goatcounter.com" --include="*.html" | head -3
```

Then push:
```bash
git add .
git commit -m "Activate GoatCounter analytics"
git push origin main
```

### Step C — View your stats
```
https://johanmontesinos.goatcounter.com
→ Log in
→ Dashboard shows pageviews, referrers, countries in real time
```

---

## 4. Formspree Contact Form

**What it does:** The contact form on `contact.html` actually sends you an
email when someone submits it. Free tier: 50 submissions/month.

**One-time setup:**

### Step A — Create a free account
```
https://formspree.io
→ Get Started Free
→ Sign up with your GitHub or email
```

### Step B — Create a new form
```
→ New Form
→ Name: Blog Contact Form
→ Email: johan.montesinos@outlook.com  (where submissions go)
→ Create Form
→ Copy the Form ID  (looks like: xrgopqkz)
```

### Step C — Update contact.html
Open `contact.html` and find:

```html
action="https://formspree.io/f/YOUR_FORM_ID"
```

Replace `YOUR_FORM_ID` with your actual form ID:

```html
action="https://formspree.io/f/xrgopqkz"
```

Then push:
```bash
cd ~/johanmontesinos.github.io
git add contact.html
git commit -m "Activate Formspree contact form"
git push origin main
```

### Step D — Test it
Go to `https://johanmontesinos.github.io/contact.html`, fill in the form,
and submit. You should receive an email at your configured address within
a minute. Formspree also shows all submissions in its dashboard.

---

## Summary — Placeholders still to replace

| File | Placeholder | Replace with |
|---|---|---|
| `post/microk8s-devops/blog-post-microk8s-devops.html` | `REPLACE_WITH_REPO_ID` | from giscus.app |
| `post/microk8s-devops/blog-post-microk8s-devops.html` | `REPLACE_WITH_CATEGORY_ID` | from giscus.app |
| All `.html` files | `YOUR_SITE_CODE` | your GoatCounter site code |
| `contact.html` | `YOUR_FORM_ID` | from formspree.io |

---

## After all four are activated — daily workflow

```bash
cd ~/johanmontesinos.github.io

# Edit any file
nano post/microk8s-devops/blog-post-microk8s-devops.html

git add .
git commit -m "describe change"
git push origin main
# → GitHub Actions auto-deploys in ~30 seconds
# → Live at https://johanmontesinos.github.io
```
