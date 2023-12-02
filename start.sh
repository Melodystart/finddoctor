#!/bin/bash
python database.py &
python table.py &
python elastic.py &
python app.py