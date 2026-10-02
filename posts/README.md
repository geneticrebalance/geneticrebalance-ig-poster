# How to post to Instagram

Each post is **one folder** inside this `posts` folder. When its time comes, it's published to **@geneticrebalance** automatically.

## 1. Prepare the folder on your computer

Name the folder with the **date and time** it should go live (UK time), then a short description:

```
2026-10-06 0900 testimonial
```

Put inside it:

- **The images** – JPG, PNG or WEBP. One image = a single post. 2 to 10 images = a carousel, in file-name order (name them `1.jpg`, `2.jpg`, … to control the order).
- **`caption.txt`** – a plain text file with the caption and hashtags (optional).

Image shapes Instagram accepts: square (1080×1080), portrait 4:5 (1080×1350), or landscape up to 1.91:1. Anything else is rejected with a note explaining why.

## 2. Upload it

1. Open this `posts` folder on GitHub.
2. Click **Add file → Upload files**.
3. **Drag the whole folder** from your computer onto the page.
4. Click **Commit changes**.

That's it. If the date and time have already passed, it posts within a minute or two. Otherwise it posts at the scheduled time (checked every 30 minutes, so allow up to half an hour).

## Good to know

- **Post straight away:** leave the date off the folder name, e.g. `new blog post`.
- **Not ready yet?** Keep it on your computer and only upload it once it's final. Anything uploaded here with a date in the past goes out straight away.
- **Date only:** `2026-10-06 testimonial` posts at 09:00 that day.
- **After posting** the folder moves to `posted`, with a `result.txt` containing the link to the live post.
- **If something goes wrong** the folder moves to `failed` with an `error.txt` explaining what to fix. GitHub also emails the account owner. Fix the problem and upload the corrected folder into `posts` again.
- **Change or cancel a scheduled post:** open its folder here and edit or delete the files before the posting time.
- This project is public, so anyone with the link can see scheduled posts before they go live. Never put private client information in here.
