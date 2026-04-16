# Materials Science Explorer

A starter Streamlit app for exploring a browser-based materials science mind map.

## What this version does
- Search topics from the sidebar
- Filter by top-level branch
- Click into child branches
- See notes for the selected topic
- Browse a JSON-backed knowledge tree

## Repo layout
- `app.py` — main Streamlit app
- `data/materials_map.json` — the knowledge tree
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — optional theme settings

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. Log into Streamlit Community Cloud.
3. Choose the repository, branch, and `app.py`.
4. Deploy.

## Good next upgrades
- true node-link graph view
- markdown pages or database-backed notes
- topic cards with journals, software, and papers
- curriculum mode vs research mode
- export selected subtree
