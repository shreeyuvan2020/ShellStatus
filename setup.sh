PORT="$1"

kill -9 $(lsof -ti ":$PORT") 2>/dev/null

git pull

python3 -m venv .venv
source Shells/bin/activate
export
pip install -r requirements.txt

gunicorn -b ":$PORT" app:app

--log-syslog
