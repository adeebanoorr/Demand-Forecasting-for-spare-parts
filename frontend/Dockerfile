# Build Stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy and install dependencies
COPY package*.json ./
RUN npm install

# Copy application files
COPY . .

# Build args for Vite
ARG VITE_API_URL
ARG VITE_ANALYTICS_URL

# Set env during build for Vite
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ANALYTICS_URL=$VITE_ANALYTICS_URL

# Build the application
RUN npm run build

# Production Stage
FROM nginx:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build files from stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Default Nginx port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
