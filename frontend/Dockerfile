# Node.js 18 als Basis
FROM node:18-alpine

# Arbeitsverzeichnis
WORKDIR /app

# Package.json und package-lock.json kopieren (für besseres Caching)
COPY package*.json ./

# Dependencies installieren
RUN npm ci --only=production

# App-Code kopieren
COPY . .

# Vite dev server konfigurieren
# Alle Interfaces binden (nicht nur localhost)
EXPOSE 3000

# Environment Variables
ENV VITE_API_BASE_URL=http://localhost:8080/api

# Development Server starten
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]