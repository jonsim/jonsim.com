/* given a comment block number (corresponding to the number of the post associated
   with the comments) toggles its display state */
function toggleCommentBlock (comment_number) {
    comment_block = document.getElementById('post_comments_' + comment_number)
    
    if (comment_block.style.display == 'none' || comment_block.style.display == '') {
        comment_block.style.display = 'block'
    } else {
        comment_block.style.display = 'none'
        shrinkAddComment(comment_number)
    }
}
   
/* given a comment block number (corresponding to the number of the post associated
    with the comments) expands the 'leave a comment' dialogue. also clears any
    template text that is in the field. */
function expandAddComment (comment_number) {
    comment_textarea = document.getElementById('post_comment_add_body_'   + comment_number)
    comment_footer   = document.getElementById('post_comment_add_footer_' + comment_number)
    
    comment_textarea.style.height = '4em'
    comment_footer.style.display  = 'block'
    
    if (comment_textarea.value == 'Leave a comment...') {
        comment_textarea.value = ''
        comment_textarea.style.color = '#000'
    }
}

/* given a comment block number (corresponding to the number of the post associated
    with the comments) shrinks the 'leave a comment' dialogue. also adds back any
    template text if nothing has been added (to avoid a blank, meaningless box).   */
function shrinkAddComment (comment_number) {
    comment_textarea = document.getElementById('post_comment_add_body_'   + comment_number)
    comment_footer   = document.getElementById('post_comment_add_footer_' + comment_number)
    
    comment_textarea.style.height = '2em'
    comment_footer.style.display  = 'none'
    
    if (comment_textarea.value == '') {
        comment_textarea.value = 'Leave a comment...'
        comment_textarea.style.color = '#555'
    }
}