# Deploying the Crop Condition Streamlit App

This folder contains the Streamlit app entrypoint `app/crop_condition_app.py` for the Crop Suitability Analysis prototype. The instructions below prepare the folder for an easy deployment to Streamlit Community Cloud (recommended) or an alternative host.

1) What I added
- `requirements.txt` — lists the Python dependencies (minimal: `streamlit`).

2) Recommended (easy, free): Streamlit Community Cloud
- Create a GitHub repo and push the `Crop Suitability Analysis` folder.
- In Streamlit Cloud, connect your GitHub account, choose the repo, set the app path to:

  `Crop Suitability Analysis/app/crop_condition_app.py`

- Deploy — Streamlit will build using `requirements.txt` and provide a public `share.streamlit.io` URL.

3) Commands to prepare and push (run locally from the project root)

```bash
# initialize a new repo (if you don't already have one)
cd "Crop Suitability Analysis"
git init
git add .
git commit -m "Add crop suitability Streamlit app and requirements"

# Create a GitHub repo (use GitHub UI or CLI), then push
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

4) Streamlit Cloud settings
- Repository: your GitHub repo
- Branch: `main` (or whichever branch you pushed)
- File path: `Crop Suitability Analysis/app/crop_condition_app.py`
- Python requirements: Streamlit Cloud automatically installs from `requirements.txt`.

5) Alternatives
- Render: https://render.com/docs/deploy-streamlit
- Railway / PythonAnywhere — use if you need more control or background processes.

6) Notes and constraints
- I did not move or modify your existing app files; changes are limited to this folder.
- I cannot push to your GitHub on your behalf (no credentials). If you want, I can produce the exact `git` commands or a GitHub actions file to auto-deploy after push.

7) Next steps I can do for you
- Create a `.github/workflows/deploy.yml` GitHub Actions file to auto-deploy to Streamlit or Render after push.
- Walk you through connecting Streamlit Cloud step-by-step and retrieving the public URL.

If you want me to create the GitHub Actions file or help push, tell me which option you prefer.
