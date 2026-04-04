# Frontend Dockerfile - React + Vite
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server with host flag to allow container access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
