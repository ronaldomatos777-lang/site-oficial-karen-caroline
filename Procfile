web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60 --graceful-timeout 30 --keep-alive 5 --preload --access-logfile - --error-logfile - --capture-output
