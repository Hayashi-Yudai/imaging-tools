# Builder
FROM python:3.9.5 as builder

COPY requirements.txt .

RUN pip install -r requirements.txt

# Runner
FROM python:3.9.5 as runner

WORKDIR /app/

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

RUN apt update \
  && apt upgrade -y \
  && apt install -y ffmpeg imagemagick \
  && apt autoremove -y \
  && apt clean -y \
  && rm -rf /var/lib/apt/lists/*

CMD ["python", "make_gif.py"]
