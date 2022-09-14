FROM python:3.7 as pymemri
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y libgl1-mesa-glx
WORKDIR /usr/src/pymemri

# In order to leverage docker caching, copy only the minimal
# information needed to install dependencies

COPY ./setup.cfg ./setup.cfg
COPY ./setup.py ./setup.py
RUN touch ./README.md
COPY ./MANIFEST.in ./MANIFEST.in
COPY ./README.md ./README.md
COPY ./tools ./tools
COPY ./pymemri ./pymemri
COPY ./nbs ./nbs

# Build the final image

RUN pip3 install --editable .
# CMD ["python3", "tools/run_integrator.py"]
CMD ["run_plugin", "--read_args_from_env", "True"]

