FROM python:3.9.15-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /usr/src/pymemri

COPY . . 
RUN --mount=type=cache,target=/root/.cache \
    pip3 install .
CMD ["run_plugin", "--read_args_from_env", "True"]

