FROM node:24-alpine
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY edurag-p0.html /workspace/edurag-p0.html
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
