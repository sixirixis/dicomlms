#!/bin/bash
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
find /var/www/html -type d -exec chmod 755 {} \;
find /var/www/html -type f -exec chmod 644 {} \;

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
