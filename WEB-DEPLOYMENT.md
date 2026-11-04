# BCT Tuition Calculator 5.4 Web Deployment

## What changed

- Synchronized `pyproject.toml` project version to `5.4.0`.
- Added `.github/workflows/deploy-web.yml`.
- Kept the existing Android APK and unsigned iOS IPA workflows unchanged.

## GitHub Pages setup (one-time)

1. Open the repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment → Source**, select **GitHub Actions**.
4. Commit and push these changes to the `main` branch.
5. Open **Actions → Build and Deploy Web App** and monitor the run.

The workflow builds a static Flet web app and deploys it to GitHub Pages
whenever a commit is pushed to `main`. Pull requests build the app but do
not publish it. A manual run is also available from the Actions tab.

## Expected website address

`https://disudaryl.github.io/bct-tuition-calculator/`

GitHub Pages must be enabled and the first deployment must succeed before
the address becomes available.

## iPhone Home Screen

Once the site is live, open it in Safari on the iPhone, tap **Share**,
choose **Add to Home Screen**, then confirm **Add**.

## Notes

- This is the web/PWA deployment, not a signed native iOS IPA.
- The static Flet app runs Python in the browser using Pyodide. The first
  load can take longer while the runtime and app assets are downloaded.
- The source code is delivered to the browser in a static deployment.
- The existing iOS and Android workflows were intentionally preserved.
