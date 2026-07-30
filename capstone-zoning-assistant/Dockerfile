FROM python:3.12-slim

RUN pip install --no-cache-dir pipenv

WORKDIR /app

# If you've committed Pipfile.lock (recommended: run `pipenv lock` once),
# switch to: COPY Pipfile Pipfile.lock ./ && pipenv install --deploy --ignore-pipfile --system
COPY Pipfile ./
RUN pipenv install --system --skip-lock

COPY data/zoning.csv data/parcels.csv data/
COPY zoning_assistant zoning_assistant
COPY app.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
