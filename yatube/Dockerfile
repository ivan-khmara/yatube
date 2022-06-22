FROM python:3.7-slim
WORKDIR /app
COPY ../requirements.txt /app/
RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt --no-cache-dir
COPY ../ /app/
RUN python3 manage.py migrate
# RUN python3 manage.py collectstatic --no-input
CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000"]
