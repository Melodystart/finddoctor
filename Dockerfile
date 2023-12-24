FROM python:3.10
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install -y wget
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable

EXPOSE 8080
EXPOSE 9200
COPY start.sh .
RUN chmod +x ./start.sh
CMD ["/bin/bash","-c","./start.sh"]