// classes
function Gallery(parent_element)
{
    this.parent_element = parent_element;
    this.image          = parent_element.getElementsByTagName('img')[0];
    this.sources        = parent_element.getElementsByTagName('li');
    this.caption        = getElementsByClass(parent_element, 'image_caption')[0];
    this.next_button    = getElementsByClass(parent_element, 'image_arrow_right')[0];
    this.prev_button    = getElementsByClass(parent_element, 'image_arrow_left')[0];
    this.position       = 0;
    
    this.parent_element.onmouseover = function(){getGalleryFromWrapper(this).show_controls()};
    //this.parent_element.addEventListener('mouseout', makeMouseOutFn(this.parent_element), true);
    addEvent('mouseout', this.parent_element, makeMouseOutFn(this.parent_element), true);
    this.next_button.onclick = function(){getGalleryFromWrapper(this.parentNode).next_pos()};
    this.prev_button.onclick = function(){getGalleryFromWrapper(this.parentNode).prev_pos()};
    this.update();
    //this.hide_controls();
    this.preload_sources();
}
Gallery.prototype.update = function()
{
    this.image.src = this.sources[this.position].innerHTML;
    this.caption.innerHTML = "Image " + (this.position+1) + " of " + this.sources.length;
}
Gallery.prototype.next_pos = function()
{
    this.position++;
    if (this.position >= this.sources.length)
    {
        this.position = 0;
    }
    this.update();
}
Gallery.prototype.prev_pos = function()
{
    this.position--;
    if (this.position < 0)
    {
        this.position = this.sources.length-1;
    }
    this.update();
}
Gallery.prototype.show_controls = function()
{
    this.next_button.style.display = "block";
    this.prev_button.style.display = "block";
    this.caption.style.display     = "block";
}
Gallery.prototype.hide_controls = function()
{
    this.next_button.style.display = "none";
    this.prev_button.style.display = "none";
    this.caption.style.display     = "none";
}
Gallery.prototype.preload_sources = function()
{
    var images = new Array();
    for (var i = 0; i < this.sources.length; i++)
    {
        images[i] = new Image();
        images[i].src = this.sources[i].innerHTML;
    }
}


// globals
var galleries = new Array();


// functions
function loadGalleries ()
{
    gallery_wrappers = getElementsByClass(document.body, 'image_wrapper');
    for (var gid = 0; gid < gallery_wrappers.length; gid++)
    {
        galleries[gid] = new Gallery(gallery_wrappers[gid]);
    }
}

function getGalleryFromWrapper (wrapper)
{
    for (var gid = 0; gid < galleries.length; gid++)
    {
        if (galleries[gid].parent_element == wrapper)
        {
            return galleries[gid];
        }
    }
    return null;
}


// event weird stuff
function makeMouseOutFn(elem)
{
    var list = traverseChildren(elem);
    return function onMouseOut(event)
    {
        var e = event.toElement || event.relatedTarget;
        if (!!~list.indexOf(e))
        {
            return;
        }
        
        // handle mouse event here!
        getGalleryFromWrapper(this).hide_controls();
    };
}
function traverseChildren(elem)
{
    var children = [];
    var q = [];
    q.push(elem);
    while (q.length>0)
    {
        var elem = q.pop();
        children.push(elem);
        pushAll(elem.children);
    }
        function pushAll(elemArray){
            for(var i=0;i<elemArray.length;i++)
            {
                q.push(elemArray[i]);
            }
            
        }
        return children;
}

// ie compatability
function getElementsByClass (node, classname)
{
    if (document.getElementsByClassName)
    {
        return node.getElementsByClassName(classname);
    }
    else
    {
        var a = [];
        var re = new RegExp('(^| )'+classname+'( |$)');
        var els = node.getElementsByTagName("*");
        for(var i=0,j=els.length; i<j; i++)
            if(re.test(els[i].className))a.push(els[i]);
        return a;
    }
}
function addEvent (evnt, elem, func, capture)
{
    if (elem.addEventListener)  // W3C DOM
    {
        elem.addEventListener(evnt, func, capture);
    }
    else if (elem.attachEvent)  // IE DOM
    {
        elem.attachEvent("on"+evnt, func);
    }
    else                        // give up
    {
      elem[evnt] = func;
    }
}