# Create Moodle Dockerfile with medical imaging plugins
moodle_dockerfile = """FROM php:8.2-apache-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    libpng-dev \\
    libjpeg-dev \\
    libfreetype6-dev \\
    libzip-dev \\
    libicu-dev \\
    libxml2-dev \\
    libpq-dev \\
    libreoffice \\
    ghostscript \\
    curl \\
    unzip \\
    git \\
    cron \\
    supervisor \\
    && rm -rf /var/lib/apt/lists/*

# Configure PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \\
    && docker-php-ext-install -j$(nproc) \\
    gd \\
    intl \\
    pdo_pgsql \\
    pgsql \\
    zip \\
    opcache \\
    exif \\
    soap \\
    xmlrpc

# Install additional PHP extensions for medical imaging
RUN pecl install redis \\
    && docker-php-ext-enable redis

# Configure Apache
RUN a2enmod rewrite ssl headers \\
    && a2dissite 000-default \\
    && rm -rf /var/www/html/*

# Set up Moodle directory structure
RUN mkdir -p /var/www/html/moodledata \\
    && chown -R www-data:www-data /var/www/html \\
    && chmod -R 755 /var/www/html

# Download and install Moodle
ARG MOODLE_VERSION=MOODLE_405_STABLE
RUN git clone --depth=1 --branch=$MOODLE_VERSION https://github.com/moodle/moodle.git /var/www/html \\
    && chown -R www-data:www-data /var/www/html \\
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
RUN chmod 0644 /etc/cron.d/moodle-cron \\
    && crontab /etc/cron.d/moodle-cron

# Copy startup script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost/ || exit 1

# Start services
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
"""

# Create Apache configuration for Moodle
apache_config = """<VirtualHost *:80>
    ServerName medicallms.local
    DocumentRoot /var/www/html
    
    # Redirect HTTP to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName medicallms.local
    DocumentRoot /var/www/html
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/fullchain.pem
    SSLCertificateKeyFile /etc/ssl/private/privkey.pem
    
    # Security headers for HIPAA compliance
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; media-src 'self' https:; object-src 'none'; frame-src 'self'"
    
    # Directory configuration
    <Directory /var/www/html>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        
        # PHP configuration
        php_value upload_max_filesize 512M
        php_value post_max_size 512M
        php_value max_execution_time 300
        php_value memory_limit 512M
    </Directory>
    
    # Protect sensitive files
    <FilesMatch "\\.(env|ini|conf|log)$">
        Require all denied
    </FilesMatch>
    
    # Enable compression
    LoadModule deflate_module modules/mod_deflate.so
    <Location />
        SetOutputFilter DEFLATE
        SetEnvIfNoCase Request_URI \\
            \\.(?:gif|jpe?g|png|ico|zip|gz|bz2)$ no-gzip dont-vary
        SetEnvIfNoCase Request_URI \\
            \\.(?:exe|t?gz|zip|bz2|sit|rar)$ no-gzip dont-vary
    </Location>
    
    # Logging
    ErrorLog /var/log/apache2/error.log
    CustomLog /var/log/apache2/access.log combined
    LogLevel warn
</VirtualHost>
"""

# Create PHP configuration optimized for medical imaging
php_config = """[PHP]
; Basic settings
upload_max_filesize = 512M
post_max_size = 512M
max_execution_time = 300
max_input_time = 300
memory_limit = 512M
max_input_vars = 5000

; Session settings for security
session.cookie_secure = 1
session.cookie_httponly = 1
session.use_strict_mode = 1
session.cookie_samesite = "Strict"

; File upload settings
file_uploads = On
upload_tmp_dir = /tmp

; Error reporting
display_errors = Off
log_errors = On
error_log = /var/log/php/error.log

; Opcache settings for performance
opcache.enable = 1
opcache.enable_cli = 1
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 10000
opcache.revalidate_freq = 0
opcache.validate_timestamps = 1

; Security settings
expose_php = Off
allow_url_fopen = Off
allow_url_include = Off

; DICOM file handling
; Allow handling of large DICOM files
max_file_uploads = 100

; Medical imaging specific settings
; Enable large file processing for pathology slides
post_max_size = 2G
upload_max_filesize = 2G
max_execution_time = 600
memory_limit = 1G
"""

# Create Docker entrypoint script
entrypoint_script = """#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h ${MOODLE_DATABASE_HOST} -p 5432 -U ${MOODLE_DATABASE_USER}; do
    sleep 2
done

echo "Database is ready!"

# Create Moodle data directory if it doesn't exist
if [ ! -d "/var/www/html/moodledata" ]; then
    mkdir -p /var/www/html/moodledata
    chown -R www-data:www-data /var/www/html/moodledata
    chmod -R 755 /var/www/html/moodledata
fi

# Create config.php if it doesn't exist
if [ ! -f "/var/www/html/config.php" ]; then
    cat > /var/www/html/config.php << EOF
<?php
unset(\$CFG);
global \$CFG;
\$CFG = new stdClass();

\$CFG->dbtype    = '${MOODLE_DATABASE_TYPE}';
\$CFG->dblibrary = 'native';
\$CFG->dbhost    = '${MOODLE_DATABASE_HOST}';
\$CFG->dbname    = '${MOODLE_DATABASE_NAME}';
\$CFG->dbuser    = '${MOODLE_DATABASE_USER}';
\$CFG->dbpass    = '${MOODLE_DATABASE_PASSWORD}';
\$CFG->prefix    = 'mdl_';
\$CFG->dboptions = array (
  'dbpersist' => 0,
  'dbport' => 5432,
  'dbsocket' => '',
  'dbcollation' => 'utf8_unicode_ci',
);

\$CFG->wwwroot   = '${SSL_PROXY:+https://}${SSL_PROXY:-http://}medicallms.local';
\$CFG->dataroot  = '/var/www/html/moodledata';
\$CFG->admin     = 'admin';
\$CFG->directorypermissions = 0755;

// Performance settings
\$CFG->cachedir = '/var/www/html/moodledata/cache';
\$CFG->tempdir = '/var/www/html/moodledata/temp';
\$CFG->localcachedir = '/var/www/html/moodledata/localcache';

// Security settings for HIPAA compliance
\$CFG->cookiesecure = true;
\$CFG->cookiehttponly = true;
\$CFG->cookiesamesite = 'Strict';
\$CFG->loginhttps = true;
\$CFG->logoutredirect = true;

// Medical imaging specific settings
\$CFG->maxbytes = 2147483648; // 2GB max file size
\$CFG->orthanc_url = '${ORTHANC_URL}';
\$CFG->orthanc_user = 'moodle';
\$CFG->orthanc_password = '${ORTHANC_PASSWORD}';

// Enable debugging in development
if (getenv('NODE_ENV') !== 'production') {
    \$CFG->debug = 32767;
    \$CFG->debugdisplay = 1;
}

require_once(__DIR__ . '/lib/setup.php');
EOF

    chown www-data:www-data /var/www/html/config.php
    chmod 644 /var/www/html/config.php
fi

# Set proper permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {} \\;
find /var/www/html -type f -exec chmod 644 {} \\;

# Install/update Moodle if needed
if [ ! -f "/var/www/html/moodledata/.installed" ]; then
    echo "Installing Moodle..."
    sudo -u www-data php /var/www/html/admin/cli/install_database.php --agree-license --fullname="${MOODLE_SITE_NAME}" --shortname="${MOODLE_SITE_SHORT_NAME}" --adminuser="${MOODLE_ADMIN_USER}" --adminpass="${MOODLE_ADMIN_PASSWORD}" --adminemail="${MOODLE_ADMIN_EMAIL}"
    
    # Install medical imaging plugins
    echo "Installing medical imaging plugins..."
    sudo -u www-data php /var/www/html/admin/cli/upgrade.php --non-interactive
    
    # Mark as installed
    touch /var/www/html/moodledata/.installed
fi

# Start cron service
service cron start

# Execute the main command
exec "$@"
"""

# Create supervisor configuration
supervisor_config = """[supervisord]
nodaemon=true
user=root

[program:apache2]
command=/usr/sbin/apache2ctl -D FOREGROUND
stdout_logfile=/var/log/supervisor/apache2.log
stderr_logfile=/var/log/supervisor/apache2_error.log
autorestart=true

[program:cron]
command=/usr/sbin/cron -f
stdout_logfile=/var/log/supervisor/cron.log
stderr_logfile=/var/log/supervisor/cron_error.log
autorestart=true
"""

# Create Moodle cron configuration
cron_config = """# Moodle cron job for maintenance tasks
*/5 * * * * www-data /usr/bin/php /var/www/html/admin/cli/cron.php > /dev/null 2>&1

# Medical imaging specific tasks
0 2 * * * www-data /usr/bin/php /var/www/html/mod/medical_imaging/cli/cleanup.php > /dev/null 2>&1
0 3 * * * www-data /usr/bin/php /var/www/html/mod/medical_imaging/cli/audit.php > /dev/null 2>&1
"""

# Write all Moodle configuration files
os.makedirs("medical-imaging-lms/docker/moodle", exist_ok=True)

with open("medical-imaging-lms/docker/moodle/Dockerfile", "w") as f:
    f.write(moodle_dockerfile)

with open("medical-imaging-lms/docker/moodle/apache-moodle.conf", "w") as f:
    f.write(apache_config)

with open("medical-imaging-lms/docker/moodle/php-moodle.ini", "w") as f:
    f.write(php_config)

with open("medical-imaging-lms/docker/moodle/docker-entrypoint.sh", "w") as f:
    f.write(entrypoint_script)

with open("medical-imaging-lms/docker/moodle/supervisord.conf", "w") as f:
    f.write(supervisor_config)

with open("medical-imaging-lms/docker/moodle/moodle-cron", "w") as f:
    f.write(cron_config)

print("✅ Created Moodle Docker configuration")
print("📁 Files created:")
print("- docker/moodle/Dockerfile")
print("- docker/moodle/apache-moodle.conf")
print("- docker/moodle/php-moodle.ini")
print("- docker/moodle/docker-entrypoint.sh")
print("- docker/moodle/supervisord.conf")
print("- docker/moodle/moodle-cron")