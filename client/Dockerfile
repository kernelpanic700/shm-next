# Client Panel Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
ARG NEXT_PUBLIC_ADMIN_URL=http://localhost:3002
ARG NEXT_PUBLIC_ENABLE_REGISTRATION=false
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_ADMIN_URL=${NEXT_PUBLIC_ADMIN_URL}
ENV NEXT_PUBLIC_ENABLE_REGISTRATION=${NEXT_PUBLIC_ENABLE_REGISTRATION}

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev for build)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine AS runtime

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm install --legacy-peer-deps --omit=dev

# Copy built application
COPY --from=builder /app/.next ./.next
# Copy public directory if it exists in builder
COPY --from=builder /app/public* ./public
# Copy source files needed at runtime
COPY --from=builder /app/*.js ./
COPY --from=builder /app/*.config.js ./
COPY --from=builder /app/*.config.ts ./
COPY --from=builder /app/tsconfig.json ./
# Copy node_modules (next binary is needed at runtime)
COPY --from=builder /app/node_modules ./node_modules

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=production
ENV PORT=3000
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
ARG NEXT_PUBLIC_ADMIN_URL=http://localhost:3002
ARG NEXT_PUBLIC_ENABLE_REGISTRATION=false
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_ADMIN_URL=${NEXT_PUBLIC_ADMIN_URL}
ENV NEXT_PUBLIC_ENABLE_REGISTRATION=${NEXT_PUBLIC_ENABLE_REGISTRATION}

# Start the application
CMD ["npm", "start"]
