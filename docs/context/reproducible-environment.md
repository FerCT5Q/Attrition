# Reproducible local environment

Create the local Python 3.11 environment from the project root:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

The Redshift connection still reuses the secure Slides `.env`; do not copy credentials into this repository.
