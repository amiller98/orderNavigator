# Order Navigator

A **Streamlit** app that takes tabular uploads (CSV / Excel) and helps you do **more** with them: orientation, health checks, and a clean table view. Roadmap: optional integration with your Inventory I/O app when you are ready.

## Run locally

```bash
cd orderNavigator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Requirements

- Python 3.10+

## GitHub (create and link)

One-time: `gh auth login` and complete the browser/device flow.

From this folder:

`gh repo create orderNavigator --public --source=. --remote=origin --push`

If the name is taken, pick another (for example `order-navigator`) and use that in the command.
