FROM python:3.6-alpine3.7

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

LABEL com.epam.legion.model.id="demo-abc-model" \
      com.epam.legion.model.version="1.3" \
      com.epam.legion.container_type="model"

ENTRYPOINT ["python"]
CMD ["app.py"]