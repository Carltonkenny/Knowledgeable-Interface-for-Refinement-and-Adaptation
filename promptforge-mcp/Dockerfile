# promptforge-mcp/Dockerfile
# ─────────────────────────────────────────────
# Production Dockerfile for PromptForge MCP Cloud
# ─────────────────────────────────────────────

# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install all dependencies (including dev for tsc)
RUN npm install

# Copy source
COPY src/ ./src/

# Build TypeScript to JS
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy production dependencies only
COPY package*.json ./
RUN npm install --omit=dev

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Environment defaults
ENV PORT=3000
ENV MCP_TRANSPORT=sse

# Expose the SSE port
EXPOSE 3000

# Start the SSE server
CMD ["node", "dist/index.js"]
