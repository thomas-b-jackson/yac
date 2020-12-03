FROM nginx:{{yac-ref:nginx-label}}

COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./default.conf /etc/nginx/conf.d/default.conf

RUN useradd -u 10001 -g www-data mynginx

RUN touch /var/run/nginx.pid && \
  chown -R mynginx:www-data /var/run/nginx.pid && \
  chown -R mynginx:www-data /var/cache/nginx

USER mynginx

VOLUME /var/www