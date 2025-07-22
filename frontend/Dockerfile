# Node.js 18 als Basis
FROM node:18-alpine

# Arbeitsverzeichnis
WORKDIR /app

# Package.json und package-lock.json kopieren (für besseres Caching)
COPY package*.json ./

# Dependencies installieren (alle, nicht nur production - wegen Vite)
RUN npm ci

# App-Code kopieren
COPY . .

# Port freigeben
EXPOSE 3000

# Environment Variables (korrigierte Backend-URL)
ENV VITE_API_BASE_URL=http://localhost:8081/api

# Development Server starten
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]