<?php

function dbLoadConfig() {
    static $config = null;
    if ($config !== null) {
        return $config;
    }

    $config_path = __DIR__ . '/database_config.php';
    if (!is_file($config_path)) {
        throw new RuntimeException(
            'Missing Christmas list database configuration. Copy ' .
            'database_config.example.php to database_config.php and fill in the values.'
        );
    }

    $config = require $config_path;
    if (!is_array($config)) {
        throw new RuntimeException('Christmas list configuration must return an array.');
    }

    return $config;
}

function dbConnect() {
    $config = dbLoadConfig();
    $required_keys = array('hostname', 'database', 'username', 'password');
    foreach ($required_keys as $key) {
        if (!isset($config[$key]) || $config[$key] === '') {
            throw new RuntimeException('Missing database configuration value: ' . $key);
        }
    }

    # Connect
    $dsn = 'mysql:host=' . $config['hostname'] . ';dbname=' . $config['database'];
    $db_handle = new PDO($dsn, $config['username'], $config['password']);
    $db_handle->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    return $db_handle;
}

function dbGetUser($db_handle, $user_id) {
    $statement = $db_handle->prepare('SELECT user_id, name FROM users WHERE user_id = :user_id');
    $statement->execute(array(':user_id' => $user_id));
    $user = $statement->fetch(PDO::FETCH_ASSOC);
    return $user === false ? null : $user;
}

function dbGetUsers($db_handle) {
    $statement = $db_handle->prepare('SELECT user_id, name FROM users ORDER BY name ASC');
    $statement->execute();
    return $statement->fetchAll(PDO::FETCH_ASSOC);
}

function dbDisconnect($db_handle) {
    # Nothing to do in a PDO implementation
}

function dbValidateUser($db_handle, $user_name) {
    # Check if user exists.
    $get_statement = $db_handle->prepare('SELECT user_id FROM users WHERE name = :user_name');
    $get_statement->execute(array(':user_name' => $user_name));
    $user_row = $get_statement->fetch(PDO::FETCH_ASSOC);

    if (isset($user_row) and $user_row != null and count($user_row) > 0) {
        # User exists.
        return (int) $user_row['user_id'];
    } else {
        # User does not exist.
        return -1;
    }
}

function dbGetAllUsersItems($db_handle) {
    $users_statement = $db_handle->prepare("SELECT users.user_id, users.name FROM users ORDER BY users.name ASC");
    $users_statement->execute();
    $users_rows = $users_statement->fetchAll(PDO::FETCH_ASSOC);

    // TODO: Optimise - we only need 1 query, not n+1...
    for ($i = 0; $i < count($users_rows); $i++)
    {
        $items_statement = $db_handle->prepare("SELECT items.item_id, items.description, items.bought, items.buyer_id FROM items WHERE items.requester_id = :user_id ORDER BY items.item_id ASC");
        $items_statement->execute(array(':user_id' => $users_rows[$i]['user_id']));
        $users_rows[$i]['items'] = $items_statement->fetchAll(PDO::FETCH_ASSOC);
    }
    return $users_rows;
}

function dbAddItem($db_handle, $user_id, $item_description) {
    $statement = $db_handle->prepare("INSERT INTO items (requester_id, description) VALUES (:user_id, :description)");
    $statement->execute(array(':user_id' => $user_id, ':description' => $item_description));
}

function dbDeleteItem($db_handle, $user_id, $item_id) {
    $statement = $db_handle->prepare("DELETE FROM items WHERE item_id = :item_id AND requester_id = :user_id");
    $statement->execute(array(':item_id' => $item_id, ':user_id' => $user_id));
}

function dbEditItem($db_handle, $user_id, $item_id, $item_description) {
    $statement = $db_handle->prepare("UPDATE items SET description = :description WHERE item_id = :item_id AND requester_id = :user_id");
    $statement->execute(array(':item_id' => $item_id, ':user_id' => $user_id, ':description' => $item_description));
}

function dbMarkBought($db_handle, $user_id, $item_id) {
    $statement = $db_handle->prepare("UPDATE items SET bought = 1, buyer_id = :buyer_id WHERE item_id = :item_id AND requester_id != :buyer_id AND bought = 0");
    $statement->execute(array(':item_id' => $item_id, ':buyer_id' => $user_id));
}

function dbMarkUnbought($db_handle, $user_id, $item_id) {
    $statement = $db_handle->prepare("UPDATE items SET bought = 0, buyer_id = NULL WHERE item_id = :item_id AND buyer_id = :buyer_id");
    $statement->execute(array(':item_id' => $item_id, ':buyer_id' => $user_id));
}

?>
