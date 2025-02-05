#!/bin/bash
gunicorn -w 4 -k sync -b 0.0.0.0:10000 app:app
