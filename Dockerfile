FROM python:3.10
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 8080
CMD python database.py & python table.py & python elastic.py & python app.py
