#!/bin/bash
python table.py &
python elastic.py &
python app.py