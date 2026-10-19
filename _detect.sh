#!/usr/bin/env bash
echo '--- node ---'; command -v node && node --version
echo '--- npx ---'; command -v npx
echo '--- mmdc ---'; command -v mmdc
echo '--- dot ---'; command -v dot
echo '--- python3 ---'; command -v python3
echo '--- chromium ---'; command -v chromium || command -v chromium-browser || command -v google-chrome
echo '--- venv libs ---'
cd /home/thais/estudos/langchain && source .venv/bin/activate
python - <<'PY'
import importlib.util as u
for m in ("diagrams", "matplotlib", "graphviz", "PIL"):
    print(m, bool(u.find_spec(m)))
PY
