# Genetic Rebalance – Instagram poster

Publishes posts to **@geneticrebalance** on Instagram.

**To post or schedule a post, see [`posts/README.md`](posts/README.md).** In short: upload a folder with the images and a `caption.txt` into `posts/`, named with the date and time it should go live.

## Folders

| Folder | What's in it |
|---|---|
| `posts/` | Posts waiting to go out |
| `posted/` | Published posts, each with a `result.txt` linking to the live post |
| `failed/` | Posts that couldn't be published, each with an `error.txt` explaining why |
| `media/` | JPG copies the robot makes for Instagram to download. Don't edit |

## Settings (owner only)

Two secrets under **Settings → Secrets and variables → Actions**:

- `IG_ACCESS_TOKEN` – generated in the Meta developer dashboard (app *Genetic Rebalance Poster* → Use cases → Instagram → API setup with Instagram login → Generate token). **Expires after about 60 days**, so regenerate and paste it here when posts start failing with a token error.
- `IG_ACCOUNT_ID` – the number shown under *geneticrebalance* when generating the token.

## Manual posting

The **Post to Instagram** action (Actions tab → Run workflow) still works for posting from public image links.
