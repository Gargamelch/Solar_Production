# Hugging Face Spaces — Streamlit app
# https://huggingface.co/docs/hub/spaces-sdks-docker
FROM anaconda/miniconda:26.3.2


# Update system
RUN apt-get update -y 
RUN apt-get install nano unzip curl -y


# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && \
    python -c "import streamlit; print('streamlit ok')" && \
    which streamlit


# THIS IS SPECIFIC TO HUGGINFACE
# We create a new user named "user" with ID of 1000
RUN useradd -m -u 1000 user
USER user


# We set two environmnet variables 
# so that we can give ownership to all files in there afterwards
# we also add /home/user/.local/bin in the $PATH environment variable 
# PATH environment variable sets paths to look for installed binaries
# We update it so that Linux knows where to look for binaries if we were to install them with "user".
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH


# We set working directory to $HOME/app (<=> /home/user/app)
WORKDIR $HOME/app


# Copy all local files to /home/user/app with "user" as owner of these files
# Always use --chown=user when using HUGGINGFACE to avoid permission errors
COPY --chown=user . $HOME/app


CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
