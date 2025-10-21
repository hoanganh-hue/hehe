# Multi-stage build for BeEF Framework
FROM ruby:3.2-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies for build stage
FROM base as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Gemfile first for better caching
COPY Gemfile* ./

# Install Ruby dependencies
RUN bundle install --deployment --without development test

# Production stage
FROM base as production

# Create application user for security
RUN groupadd -r beefuser && useradd -r -g beefuser beefuser

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed gems from builder stage
COPY --from=builder /usr/local/bundle /usr/local/bundle

# Copy application code
COPY --chown=beefuser:beefuser . .

# Create logs directory
RUN mkdir -p /app/logs && chown -R beefuser:beefuser /app

# Switch to non-root user
USER beefuser

# Set environment variables
ENV BEEF_USER=beef \
    BEEF_PASSWORD=ZaloPay_BeEF_2025_Secure! \
    RACK_ENV=production \
    BEEF_DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/api/hooks || exit 1

# Expose port
EXPOSE 3000

# Start command
CMD ["ruby", "beef"]