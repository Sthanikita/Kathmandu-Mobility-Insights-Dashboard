# Streamlit Cloud entry point.
# The app is configured with "check.py" as its main module, but the real
# dashboard lives in app.py. This wrapper simply runs it.
import runpy

runpy.run_path("app.py", run_name="__main__")
