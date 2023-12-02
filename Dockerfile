FROM python:3.10
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 8080
EXPOSE 9200
COPY start.sh .
CMD ["/bin/bash","-c","./start.sh"]