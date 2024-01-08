AI Scope
========

A Datascope project that is geared towards using AI and specifically Large Language Models (LLM).


Prerequisites
-------------

This project runs on ``Python 3.12`` and uses ``poetry``, ``Docker`` and ``Docker Compose V2`` for 
running and maintaining dependencies.
Make sure they are installed on your system before starting.


Installation
------------

Install Python packages with:

```
poetry install
```

Make sure that your ``/etc/hosts`` file or equivalent contains the following:

```
127.0.0.1	postgres
127.0.0.1   redis
```

Next you can run Postgres and Redis services using:

```
docker compose -f docker-compose.yml up
```

If you want to run the Uvicorn and Celery containers of this project, besides the Postgres and Redis services, 
you can instead simply run:

```
docker compose up
```

However you might find it easier to run the Django development server and Celery worker outside of containers.
You can do so with the regular commands from the ``aiscope`` directory. 
