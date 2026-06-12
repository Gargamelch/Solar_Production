# This Dockerfile is for running a local container
# Use the other Dockerfile to deploy in Hugging Face
FROM anaconda/miniconda:26.3.2

RUN apt-get update -y && apt-get install -y nano unzip curl

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
