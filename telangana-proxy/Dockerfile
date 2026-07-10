# Minimal container for the Telangana rain proxy (Cloud Run / any container host).
FROM node:20-alpine
WORKDIR /app
COPY proxy.mjs .
ENV PORT=8080
EXPOSE 8080
CMD ["node", "proxy.mjs"]
