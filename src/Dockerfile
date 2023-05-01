FROM python:3.9.13

RUN mkdir usr/app

WORKDIR usr/app

COPY . .

RUN pip install -r requirements.txt

CMD python app.py