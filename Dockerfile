FROM python:3

WORKDIR /usr/src/app

# Do not spam yt-dl.org servers

RUN mkdir -p /persist/bin
RUN wget https://yt-dl.org/downloads/latest/youtube-dl -O /persist/bin/youtube-dl
RUN chmod a+x /persist/bin/youtube-dl
# VOLUME /persist

ENV PATH="/persist/bin:${PATH}"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
