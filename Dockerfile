FROM python:3.12-slim
SHELL ["/bin/bash", "-c"]
ARG UID=1000
ARG GID=1000

RUN apt-get update && apt-get install -y less vim git build-essential gettext libpq-dev

# Create the app environment
RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/static
RUN mkdir -p /usr/src/datagrowth
WORKDIR /usr/src/app

# Adding an app user to prevent container access as root
# Most options speak for itself.
# The -r options make it a system user and group.
# The -m option forces a home folder (which Python tools rely upon rather heavily)
# We also add default Python user path to PATH so installed binaries get found
RUN groupadd -r app -g $GID && useradd app -u $UID -r -m -g app
ENV PATH="/home/app/.local/bin:${PATH}"
ENV PYTHONPATH="/usr/src/app"
# Give access to app user
RUN chown -R app:app /usr/src/app
RUN chown -R app:app /usr/src/static
RUN chown -R app:app /usr/src/datagrowth

# Become app user to prevent attacks during install (possibly from hijacked PyPi packages)
USER app:app

# Python dependencies
RUN pip install --no-cache-dir --user poetry
COPY pyproject.toml /usr/src/app/
COPY poetry.lock /usr/src/app/
RUN poetry export --format requirements.txt --output requirements.txt --without-hashes
RUN pip install --user -r requirements.txt

# Copy application
COPY aiscope /usr/src/app

# We're serving static files through Whitenoise
# See: http://whitenoise.evans.io/en/stable/index.html#
# If you doubt this decision then read the "infrequently asked question" section for details
# Here we gather static files that get served through Uvicorn if they don't exist
RUN python manage.py collectstatic --noinput

# Entrypoint sets our environment correctly
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# The default command is to start a Uvicorn server (NodeJS based Python server)
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080",  "aiscope.asgi:application"]

# EXPOSE port 8080 to allow communication to/from server
EXPOSE 8080
