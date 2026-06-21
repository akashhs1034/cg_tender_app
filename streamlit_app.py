"""Streamlit Cloud entry point.

Streamlit keeps the Python process warm between reruns, so first-party modules
imported by app.py (core, accounts, …) stay cached in sys.modules even after a
new deploy. That can surface freshly-added code as AttributeError (e.g.
core.profile_is_configured) until the container is fully recycled. We evict our
own modules here so every run re-imports the just-deployed source.
"""
import sys
import runpy

for _mod in ("core", "accounts", "evaluator", "bid_engine", "alerts"):
    sys.modules.pop(_mod, None)

runpy.run_path("app.py", run_name="__main__")
