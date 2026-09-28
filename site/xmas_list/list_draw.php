<?php

function formId($base, $id) {
    return $base . '[' . $id . ']';
}

function autoLink($text) {
    # Escape all text while turning absolute URLs into safe links. Keeping the
    # escaping here avoids running a URL regex over already-created HTML entities.
    $regex = '~\b(?:https?|ftps?)://[^\s<>"\']+~iu';
    preg_match_all($regex, $text, $matches, PREG_OFFSET_CAPTURE);

    $output = '';
    $offset = 0;
    foreach ($matches[0] as $match) {
        $url = $match[0];
        $url_offset = $match[1];
        $output .= htmlspecialchars(substr($text, $offset, $url_offset - $offset), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');

        # Do not absorb punctuation that ends a sentence containing the URL.
        $trailing = '';
        while ($url !== '' && preg_match('/[\.,;:!?\)\]\}]$/u', $url, $trailing_match)) {
            $trailing = $trailing_match[0] . $trailing;
            $url = substr($url, 0, -strlen($trailing_match[0]));
        }

        $escaped_url = htmlspecialchars($url, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        $output .= '<a href="'.$escaped_url.'" target="_blank" rel="noopener noreferrer">'.$escaped_url.'</a>';
        $output .= htmlspecialchars($trailing, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        $offset = $url_offset + strlen($match[0]);
    }

    $output .= htmlspecialchars(substr($text, $offset), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    return $output;
}

function drawDescription($item_id, $item_description, $is_this_user, $is_bought) {
    global $DESCRIPTION_BASE_ID;
    # Print the item description (optionally crossed through).
    $strike = (!$is_this_user && $is_bought);
    $output  = '<span class="listcontent" ';
    if ($strike) {
        $output .= 'title="Item is marked as bought by someone else" ';
    }
    $output .=   'id="'.formId($DESCRIPTION_BASE_ID, $item_id).'">';
    if ($strike) {
        $output .= '<strike>';
    }
    $output .= autoLink($item_description);
    if ($strike) {
        $output .= '</strike>';
    }
    $output .= '</span>';
    return $output;
}

function drawEditButton($item_id, $item_description) {
    global $EDIT_BASE_ID;
    # Keep user-provided text out of inline JavaScript. HTML attribute escaping
    # makes it safe to store in a data attribute; JavaScript reads it as data.
    $item_description = htmlspecialchars($item_description, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $output  = '<button type="button" ';
    $output .=   'title="Edit this entry" ';
    $output .=   'id="'  .formId($EDIT_BASE_ID . '_button', $item_id).'" ';
    $output .=   'name="'.formId($EDIT_BASE_ID . '_button', $item_id).'" ';
    $output .=   'data-description="'.$item_description.'" ';
    $output .=   'onclick="editItem(this, '.$item_id.')">';
    $output .= '<i class="fa fa-pencil fa-fw"></i>';
    $output .= '</button>';
    return $output;
}

function drawDeleteButton($item_id) {
    global $DELETE_BASE_ID;
    $output  = '<button type="submit" ';
    $output .=   'title="Delete this entry" ';
    $output .=   'id="'  .formId($DELETE_BASE_ID, $item_id).'" ';
    $output .=   'name="'.formId($DELETE_BASE_ID, $item_id).'" ';
    $output .=   'onclick="return window.confirm(\'Delete this item?\')">';
    $output .= '<i class="fa fa-trash fa-fw"></i>';
    $output .= '</button>';
    return $output;
}

function drawBoughtButton($item_id) {
    global $BOUGHT_BASE_ID;
    $output  = '<button type="submit" ';
    $output .=   'title="Mark this item as bought (not visible to requester)" ';
    $output .=   'id="'  .formId($BOUGHT_BASE_ID, $item_id).'" ';
    $output .=   'name="'.formId($BOUGHT_BASE_ID, $item_id).'">';
    $output .= '<i class="fa fa-shopping-cart fa-fw"></i>';
    $output .= '</button>';
    return $output;
}

function drawUnboughtButton($item_id) {
    global $UNBOUGHT_BASE_ID;
    $output  = '<button type="submit" ';
    $output .=   'title="Unmark this item as bought (not visible to requester)" ';
    $output .=   'id="'  .formId($UNBOUGHT_BASE_ID, $item_id).'" ';
    $output .=   'name="'.formId($UNBOUGHT_BASE_ID, $item_id).'">';
    $output .= '<i class="fa fa-unlock fa-fw"></i>';
    $output .= '</button>';
    return $output;
}

function drawAddButton() {
    global $ADD_BASE_ID;
    $output  = '<button type="button" ';
    $output .=   'id="'  .$ADD_BASE_ID.'_button" ';
    $output .=   'name="'.$ADD_BASE_ID.'_button" ';
    $output .=   'title="Add a new entry" ';
    $output .=   'onclick="addItem()">';
    $output .= '<i class="fa fa-plus fa-fw"></i>';
    $output .= '</button>';
    return $output;
}

?>
