#!/bin/bash
# Run the gunicorn service

# Make sure we're in the right virtual env and location
source /home/paul/.virtualenvs/live/bin/activate
source /home/paul/.virtualenvs/live/bin/postactivate

cd /home/paul/live

exec gunicorn -c /home/paul/live/_site_setup/gunicorn.conf.py logicalc.wsgi:application
