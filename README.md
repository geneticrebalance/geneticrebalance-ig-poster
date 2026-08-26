# Genetic Rebalance — Instagram Poster (GitHub Actions)

This runs `post_to_instagram.py` on GitHub's servers (which have full internet
access to Instagram's API), triggered manually whenever you want to publish
a post. It's free.

## One-time setup (~5 minutes)

1. **Create a new repo on GitHub**
   - Go to github.com → New repository
   - Name it something like `ig-poster`
   - Set it to **Private**
   - Don't add a README/gitignore (we already have files)

2. **Upload these files** to that repo (drag-and-drop on the GitHub web UI works fine, or use `git push` if you're comfortable with git):
   - `post_to_instagram.py`
   - `requirements.txt`
   - `.github/workflows/post-instagram.yml` (keep this exact folder path)

3. **Add your Instagram credentials as encrypted secrets** (never commit these as plain text):
   - In the repo: Settings → Secrets and variables → Actions → New repository secret
   - Add `IG_ACCESS_TOKEN` = your access token
   - Add `IG_ACCOUNT_ID` = `17841476266224612`

That's it — setup is done.

## Posting something

1. Go to the repo's **Actions** tab
2. Click **Post to Instagram** in the left sidebar
3. Click **Run workflow**
4. Fill in:
   - **image_urls**: one public image URL, or several separated by commas for a carousel (e.g. `https://.../slide1.png, https://.../slide2.png`)
   - **caption**: your caption text
5. Click the green **Run workflow** button
6. Watch it run under the Actions tab — green check = posted successfully, red X = click in to see the error message

## Important notes

- **Image URLs must be public** and reachable by Instagram's servers — this is separate from where you host the image. We'll sort out permanent image hosting next.
- Your access token is currently **short-lived (~1 hour, dev mode)**. If a run fails with an authentication error, you'll need a fresh token from the Meta developer dashboard — update the `IG_ACCESS_TOKEN` secret with the new value (same Settings → Secrets page, click the secret, click Update).
- Nothing here ever prints or logs your token — GitHub automatically masks secret values in the Actions log.
