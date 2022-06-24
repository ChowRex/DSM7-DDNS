FROM python:3.9-alpine
MAINTAINER Rex Chow <879582094@qq.com>

ENV TZ='Asia/Shanghai'
ENV TIME_OUT=20
ENV LOG_LEVEL='info'
ENV CF_ZONE='example.com'

COPY app /app
WORKDIR /app
EXPOSE 80

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r /app/requirements.txt && \
    rm -rf ~/.cache/pip
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 80 --log-level $LOG_LEVEL"]

