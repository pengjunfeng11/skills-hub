FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
# Replace mirror URLs in lockfile for broader build compatibility.
RUN sed -i 's#https://pypi.tuna.tsinghua.edu.cn/simple#https://pypi.org/simple#g; s#https://pypi.tuna.tsinghua.edu.cn/#https://files.pythonhosted.org/#g' uv.lock
RUN uv sync --no-dev --no-install-project

COPY . .

RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
