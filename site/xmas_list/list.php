<?php

    $ADD_BASE_ID        = 'add';
    $DELETE_BASE_ID     = 'delete';
    $EDIT_BASE_ID       = 'edit';
    $BOUGHT_BASE_ID     = 'bought';
    $UNBOUGHT_BASE_ID   = 'unbought';
    $DESCRIPTION_BASE_ID= 'description';

    include 'database_access.php';
    include 'list_draw.php';

    $AUTH_COOKIE = 'xmas_list_auth';
    $AUTH_COOKIE_LIFETIME = 60 * 60 * 24 * 365;

    # Disable page caching.
    header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
    header("Cache-Control: post-check=0, pre-check=0", false);
    header("Pragma: no-cache");
    header("Expires: Sun, 01 Jan 2014 00:00:00 GMT");

    function redirectToList() {
        header('Location: list.php', true, 303);
        exit;
    }

    function authCookiePath() {
        return rtrim(str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'])), '/') . '/';
    }

    function setAuthCookie($name, $value, $expires) {
        setcookie($name, $value, array(
            'expires' => $expires,
            'path' => authCookiePath(),
            'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
            'httponly' => true,
            'samesite' => 'Lax'
        ));
    }

    function normalisePhrase($phrase) {
        return preg_replace('/[^a-z0-9]/', '', strtolower($phrase));
    }

    function createAuthCookie($user_id, $expires, $secret) {
        $payload = $user_id . '|' . $expires;
        return $payload . '|' . hash_hmac('sha256', $payload, $secret);
    }

    function readAuthCookie($cookie, $secret) {
        $parts = explode('|', $cookie);
        if (count($parts) !== 3 || !ctype_digit($parts[0]) || !ctype_digit($parts[1])) {
            return null;
        }

        $payload = $parts[0] . '|' . $parts[1];
        $expected_signature = hash_hmac('sha256', $payload, $secret);
        if ((int) $parts[1] < time() || !hash_equals($expected_signature, $parts[2])) {
            return null;
        }

        return (int) $parts[0];
    }

    # Handle the database interface.
    $config = dbLoadConfig();
    if (empty($config['auth_cookie_secret']) || empty($config['auth_users']) || !is_array($config['auth_users'])) {
        throw new RuntimeException('Missing or incomplete Christmas list authentication configuration.');
    }
    $db_handle = dbConnect();

    if (isset($_POST['logout'])) {
        setAuthCookie($AUTH_COOKIE, '', time() - 3600);
        redirectToList();
    }

    $this_user = null;
    if (isset($_COOKIE[$AUTH_COOKIE])) {
        $cookie_user_id = readAuthCookie($_COOKIE[$AUTH_COOKIE], $config['auth_cookie_secret']);
        if ($cookie_user_id !== null) {
            $cookie_user = dbGetUser($db_handle, $cookie_user_id);
            if ($cookie_user !== null && isset($config['auth_users'][$cookie_user['name']])) {
                $this_user = $cookie_user;
            }
        }
    }

    $login_error = null;
    if ($this_user === null && isset($_POST['login'])) {
        $login_user_id = filter_input(INPUT_POST, 'user_id', FILTER_VALIDATE_INT);
        $login_user = ($login_user_id === false || $login_user_id === null)
            ? null
            : dbGetUser($db_handle, $login_user_id);
        $phrase = (isset($_POST['phrase']) && is_string($_POST['phrase']))
            ? normalisePhrase($_POST['phrase'])
            : '';

        if ($login_user !== null && isset($config['auth_users'][$login_user['name']])) {
            $auth_user = $config['auth_users'][$login_user['name']];
            if (isset($auth_user['phrase_hash']) && password_verify($phrase, $auth_user['phrase_hash'])) {
                $expires = time() + $AUTH_COOKIE_LIFETIME;
                setAuthCookie(
                    $AUTH_COOKIE,
                    createAuthCookie($login_user_id, $expires, $config['auth_cookie_secret']),
                    $expires
                );
                redirectToList();
            }
        }

        $login_error = 'That name and memorable phrase do not match. Please try again.';
    }

    $show_login = ($this_user === null);
    $is_alias_user = false;
    if (!$show_login) {
        $this_user_id = (int) $this_user['user_id'];
        $this_user_name = $this_user['name'];
        $auth_user = $config['auth_users'][$this_user_name];
        $is_alias_user = !empty($auth_user['alias']);
    }

    # Handle POST requests.
    # Handle adds
    if (!$show_login && isset($_POST[$ADD_BASE_ID])) {
        $item_description = $_POST[$ADD_BASE_ID];
        if ($item_description != null and !empty($item_description)) {
            dbAddItem($db_handle, $this_user_id, $item_description);
        }
    }
    # Handle deletes
    if (!$show_login && isset($_POST[$DELETE_BASE_ID])) {
        foreach ($_POST[$DELETE_BASE_ID] as $item_id=>$item_data) {
            dbDeleteItem($db_handle, $this_user_id, $item_id);
        }
    }
    # Handle edits
    if (!$show_login && isset($_POST[$EDIT_BASE_ID])) {
        foreach ($_POST[$EDIT_BASE_ID] as $item_id=>$item_data) {
            dbEditItem($db_handle, $this_user_id, $item_id, $item_data);
        }
    }
    # Handle boughts
    if (!$show_login && isset($_POST[$BOUGHT_BASE_ID])) {
        foreach ($_POST[$BOUGHT_BASE_ID] as $item_id=>$item_data) {
            dbMarkBought($db_handle, $this_user_id, $item_id);
        }
    }
    # Handle unboughts
    if (!$show_login && isset($_POST[$UNBOUGHT_BASE_ID])) {
        foreach ($_POST[$UNBOUGHT_BASE_ID] as $item_id=>$item_data) {
            dbMarkUnbought($db_handle, $this_user_id, $item_id);
        }
    }

    if ($show_login) {
        $login_users = array_filter(dbGetUsers($db_handle), function ($user) use ($config) {
            return isset($config['auth_users'][$user['name']]);
        });
    } else {
        # Now the database is up to date, get all list items.
        $users_items = dbGetAllUsersItems($db_handle);
    }

?>
<!doctype html>
<html lang="en">

<head>
  <meta name="robots" content="noindex, nofollow" />
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>jonsim | xmas list</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap"
    rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Lekton:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap"
    rel="stylesheet">
  <link rel="stylesheet" type="text/css" href="../style.css">
  <link rel="stylesheet" type="text/css" href="list_style.css">
  <script src="https://use.fontawesome.com/141f2d0518.js"></script>
  <script>
    function editItem(item_id, item_description) {
      var descId   = <?php echo '"' . formId($DESCRIPTION_BASE_ID,    '" + item_id + "') . '"'; ?>;
      var editId   = <?php echo '"' . formId($EDIT_BASE_ID,           '" + item_id + "') . '"'; ?>;
      var buttonId = <?php echo '"' . formId($EDIT_BASE_ID.'_button', '" + item_id + "') . '"'; ?>;
      var desc = document.getElementById(descId);

      if (desc) {
        // Not in edit mode - create new edit field.
        var field = document.createElement("input");
        field.type = "text";
        field.className = "listeditor";
        field.id =   editId;
        field.name = editId;
        field.value = item_description;
        desc.parentNode.replaceChild(field, desc);
        // Update edit button.
        var button = document.getElementById(buttonId);
        button.innerHTML = '<i class="fa fa-arrow-right fa-fw"></i>';
        // Finally give the new field focus.
        field.focus();
      } else {
        // Already in edit mode, just submit the form as requested.
        document.getElementById("list_form").submit();
      }
    }

    function addItem() {
      var addId    = <?php echo '"' . $ADD_BASE_ID . '"'; ?>;
      var buttonId = <?php echo '"' . $ADD_BASE_ID . '_button"'; ?>;
      var field = document.getElementById(addId);

      if (field) {
        // Already in add mode, just submit the form as requested.
        document.getElementById("list_form").submit();
      } else {
        // Not in add mode - create add field.
        var button = document.getElementById(buttonId);
        field = document.createElement("input");
        field.type = "text";
        field.className = "listeditor";
        field.id   = addId;
        field.name = addId;
        button.parentNode.insertBefore(field, button);
        // Update add button.
        button.innerHTML = '<i class="fa fa-arrow-right fa-fw"></i>';
        // Finally give the new field focus.
        field.focus();
      }
    }
  </script>
</head>

<body>
  <header>
    <div class="wrap nav">
      <a class="brand" href="../index.html">jonsim</a>
      <nav>
        <a href="../code/index.html">code</a>
        <a href="../design/index.html">design</a>
        <a href="../woodwork/index.html">woodwork</a>
        <a href="../blog/index.html">blog</a>
        <a href="../recipes/index.html">recipes</a>
      </nav>
    </div>
  </header>
  <main class="wrap">
    <section class="list-hero">
      <div class="list-hero-header">
        <h1>Simmonds Christmas List <span>2026</span></h1>
      </div>
    </section>
    <div class="hero-rule"></div>

    <section id="list">
      <div class="list-body">

    <?php
        if ($show_login) {
            echo '<div class="login-card">';
            echo '<h2>Open the Christmas list</h2>';
            echo '<p>Choose your name and enter your memorable phrase. Capitalisation, spaces and punctuation do not matter.</p>';
            if ($login_error !== null) {
                echo '<p class="login-error" role="alert">'.htmlspecialchars($login_error, ENT_QUOTES, 'UTF-8').'</p>';
            }
            echo '<form class="login-form" method="POST" action="list.php">';
            echo '<label for="user_id">Your name</label>';
            echo '<select id="user_id" name="user_id" required>';
            echo '<option value="" selected disabled>Select your name&hellip;</option>';
            foreach ($login_users as $user) {
                $auth_user = $config['auth_users'][$user['name']];
                $display_name = isset($auth_user['display_name']) ? $auth_user['display_name'] : $user['name'];
                $selected = (isset($_POST['user_id']) && (int) $_POST['user_id'] === (int) $user['user_id']) ? ' selected' : '';
                echo '<option value="'.(int) $user['user_id'].'"'.$selected.'>'.htmlspecialchars($display_name, ENT_QUOTES, 'UTF-8').'</option>';
            }
            echo '</select>';
            echo '<label for="phrase">Memorable phrase</label>';
            echo '<input id="phrase" name="phrase" type="text" autocomplete="off" autocapitalize="none" spellcheck="false" required>';
            echo '<button class="login-submit" type="submit" name="login">Show the list</button>';
            echo '</form>';
            echo '</div>';
        } else {
            $display_name = isset($auth_user['display_name']) ? $auth_user['display_name'] : $this_user_name;
            echo '<div class="current-identity">';
            echo '<span>Viewing as <strong>'.htmlspecialchars($display_name, ENT_QUOTES, 'UTF-8').'</strong></span>';
            echo '<form method="POST" action="list.php"><button class="logout-button" type="submit" name="logout">Not you?</button></form>';
            echo '</div>';

            echo '<form id="list_form" method="POST" action="list.php">';

            # Add a hidden default button. This prevents accidentally performing
            # random actions when pressing CR on some browsers which interpret CR as
            # a submission of the first element.
            echo '<button id="form_default" type="submit" value="default action"></button>';

            foreach ($users_items as $user) {
                $is_this_user = ((int) $user['user_id'] === $this_user_id);

                echo '<h1>'.htmlspecialchars($user['name'], ENT_QUOTES, 'UTF-8').'</h1>';
                echo '<ul>';
                foreach ($user['items'] as $item) {
                    $item_id = $item['item_id'];
                    $is_bought = (strcmp($item['bought'], "1") == 0) && !$is_alias_user;
                    $buyer_is_this_user = (((int) $item['buyer_id']) == $this_user_id);
                    echo '<li>';
                    echo drawDescription($item_id, $item['description'], $is_this_user, $is_bought);
                    # Print the controls.
                    if ($is_this_user) {
                        # If this is the current user - print edit and delete.
                        echo drawEditButton($item_id, $item['description']);
                        echo drawDeleteButton($item_id);
                    } else if (!$is_alias_user) {
                        # Otherwise add the bought button if unbought, or un-buy if
                        # bought and bought by the current user.
                        if (!$is_bought) {
                            echo drawBoughtButton($item_id);
                        } else if ($buyer_is_this_user) {
                            echo drawUnboughtButton($item_id);
                        }
                    }
                    echo '</li>';
                }
                # If current user, allow them to add to the list.
                if ($is_this_user) {
                    echo '<li>';
                    echo drawAddButton();
                    echo '</li>';
                }
                echo '</ul>';
            }
            echo '</form>';
        }
    ?>

      </div>
    </section>

  </main>
  <footer>
    <div class="wrap">© Jonathan Simmonds</div>
  </footer>
</body>
