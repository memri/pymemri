FROM python:3.7 as pymemri
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y libgl1-mesa-glx
WORKDIR /usr/src/pymemri

# In order to leverage docker caching, copy only the minimal
# information needed to install dependencies

COPY ./settings.ini ./settings.ini
COPY ./setup.py ./setup.py
RUN touch ./README.md

# Install dependencies

RUN python3 setup.py egg_info
RUN pip3 install -r pymemri.egg-info/requires.txt

# Copy the real project-s sources (docker caching is broken from here onwards)

COPY ./MANIFEST.in ./MANIFEST.in
COPY ./README.md ./README.md
COPY ./tools ./tools
COPY ./pymemri ./pymemri
COPY ./nbs ./nbs

# Build the final image

RUN pip3 install --editable .
CMD ["run_plugin"]

