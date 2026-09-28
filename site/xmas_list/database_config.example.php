<?php

# Copy this file to database_config.php and replace the placeholder values.
# database_config.php is deliberately ignored by Git.
return array(
    'hostname' => 'localhost',
    'database' => 'xmas_list',
    'username' => 'xmas_list_user',
    'password' => 'replace-with-a-secure-password',

    # Generate with: openssl rand -hex 32
    'auth_cookie_secret' => 'replace-with-a-long-random-value',

    # Keys must exactly match names in the users table. Generate each hash from
    # the normalised (lower-case, letters-and-numbers-only) memorable phrase:
    # php -r "echo password_hash('normalisedphrase', PASSWORD_DEFAULT), PHP_EOL;"
    'auth_users' => array(
        'Example User' => array(
            'display_name' => 'Example User',
            'phrase_hash' => 'replace-with-a-password-hash',
            'alias' => false
        )
    )
);
