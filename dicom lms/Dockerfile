FROM php:8.2-apache-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libzip-dev \
    libicu-dev \
    libxml2-dev \
    libpq-dev \
    libreoffice \
    ghostscript \
    curl \
    unzip \
    git \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Configure PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
    gd \
    intl \
    pdo_pgsql \
    pgsql \
    zip \
    opcache \
    exif \
    soap \
    xmlrpc

# Install additional PHP extensions for medical imaging
RUN pecl install redis \
    && docker-php-ext-enable redis

# Configure Apache
RUN a2enmod rewrite ssl headers \
    && a2dissite 000-default \
    && rm -rf /var/www/html/*

# Set up Moodle directory structure
RUN mkdir -p /var/www/html/moodledata \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

# Download and install Moodle
ARG MOODLE_VERSION=MOODLE_405_STABLE
RUN git clone --depth=1 --branch=$MOODLE_VERSION https://github.com/moodle/moodle.git /var/www/html \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

# Install Composer for plugin management
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy custom Apache configuration
COPY apache-moodle.conf /etc/apache2/sites-enabled/000-default.conf

# Copy PHP configuration optimized for medical imaging
COPY php-moodle.ini /usr/local/etc/php/conf.d/moodle.ini

# Copy DICOM viewer plugin
COPY dicom-viewer-plugin/ /var/www/html/mod/dicomviewer/

# Copy custom medical imaging activity plugin
COPY medical-imaging-plugin/ /var/www/html/mod/medical_imaging/

# Set up cron for Moodle maintenance
COPY moodle-cron /etc/cron.d/moodle-cron
RUN chmod 0644 /etc/cron.d/moodle-cron \
    && crontab /etc/cron.d/moodle-cron

# Copy startup script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start services
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
