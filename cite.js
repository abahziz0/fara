/* FARA: copy buttons for the citations on village pages and the methods page.
   The citations themselves are in the page (written by build_edition.py), so they can be read and copied without this script. */
(function(){
  function copy(text, btn){
    var done = function(ok){
      btn.textContent = ok ? 'Copied' : 'Select the text and copy it';
      setTimeout(function(){ btn.textContent = 'Copy'; }, 2200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ done(true); }, function(){ done(fallback(text)); });
    } else done(fallback(text));
  }
  function fallback(text){
    var t = document.createElement('textarea');
    t.value = text; t.setAttribute('readonly', ''); t.style.cssText = 'position:fixed;left:-999px;top:0';
    document.body.appendChild(t); t.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) {}
    t.remove();
    return ok;
  }
  document.querySelectorAll('.citefmt').forEach(function(box){
    var pre = box.querySelector('pre'), h = box.querySelector('h3');
    if (!pre || !h) return;
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'citecopy'; b.textContent = 'Copy';
    b.setAttribute('aria-label', h.textContent === 'Citation' ? 'Copy the citation' : 'Copy the ' + h.textContent + ' citation');
    b.addEventListener('click', function(){ copy(pre.textContent, b); });
    h.appendChild(b);
  });
  /* a link to #cite opens the page at the citation; make sure it is the first thing seen */
  if (location.hash === '#cite'){ var c = document.getElementById('cite'); if (c) c.scrollIntoView(); }
})();
