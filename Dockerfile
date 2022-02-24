FROM pandoc/latex:2-alpine

ENV PYTHONUNBUFFERED=1

RUN apk add --update --no-cache python3
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools gunicorn

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip3 install --no-cache -r ./requirements.txt

COPY . .

EXPOSE 5000

ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "main:app"]
