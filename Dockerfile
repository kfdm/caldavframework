FROM python:3.10-alpine
LABEL maintainer=kungfudiscomonkey@gmail.com

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV APP_DIR /usr/src/app
ENV STATIC_ROOT /var/cache/app

# Upgrade Pip
RUN pip install --no-cache-dir -U pip

# Install Postgres Support
RUN set -ex \
    && apk add --no-cache postgresql-dev \
    && apk add --no-cache --virtual build-deps build-base \
    && pip install --no-cache-dir psycopg2-binary \
    && apk del build-deps

# Finish installing app
WORKDIR ${APP_DIR}
ADD caldav_framework ${APP_DIR}/caldav_framework
COPY docker ${APP_DIR}/docker
COPY setup.* ${APP_DIR}/
RUN set -ex && pip install --no-cache-dir -r ${APP_DIR}/docker/requirements.txt -e .[standalone]
RUN todo-server collectstatic --noinput

USER nobody
EXPOSE 8000

ENTRYPOINT [ "/sbin/tini", "--" ]
CMD ["gunicorn", "caldav_framework.standalone.wsgi:application", "-b", "0.0.0.0:8000"]
