/* FARA stories: the map behind a scrolling story (pages are written by build_extra.py).
   window.FARA_STORY      = { steps:[map state per text card], zones:[polygons near the village, optional] }   (in the page)
   window.FARA_STORY_DATA = { towns, colors, dots:[[id,lat,lng,townIndex,status2017]], lines:[township borders] }  (/stories/data.js, shared and cached)
   A map state: { base:'dark'|'sat'|{rel,z18}, fit:'all'|'<township>'|['<township>',…], at:[lat,lng], zoom, dots:'town'|'st17'|'dim'|'none',
                  zones:true, lines:true, pin:true|[lat,lng], caption:'html', legend:'town'|'st17' }
   The map cannot be dragged: it only moves with the story, so scrolling always scrolls the page.
   Built to feel smooth: the text is on screen before any of this runs, the pictures for the next step are fetched
   ahead of time, and nothing is redrawn unless it changes. */
(function(){
  'use strict';
  var S = window.FARA_STORY, D = window.FARA_STORY_DATA || S, root = document.getElementById('story');
  if (!S || !D || !window.L || !root) return;
  var started = false, css = document.getElementById('lfcss');                 /* the map's own stylesheet loads without holding up the text */
  if (css && !css.sheet){ css.addEventListener('load', start); setTimeout(start, 2500); } else start();

  function start(){
    if (started) return; started = true;
    root.classList.add('js');
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var phone = function(){ return matchMedia('(max-width:760px)').matches; };
    var ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/';
    var WB = 'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/';
    var DARK = 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_';
    var ST = { d:'#FF3B5C', n:'#FFB020', z:'#8FA8C7', x:'#54708F' };
    var ST_NAME = { d:'Destroyed', n:'Destruction nearby', z:'None detected', x:'Not assessed' };
    var TILE = { maxZoom:20, keepBuffer:3, updateWhenZooming:false, updateWhenIdle:false };
    var opt = function(o){ var r = {}, k; for (k in TILE) r[k] = TILE[k]; for (k in o) r[k] = o[k]; return r; };

    var map = L.map('smap', { zoomControl:false, dragging:false, scrollWheelZoom:false, doubleClickZoom:false, boxZoom:false, keyboard:false,
      touchZoom:false, zoomSnap:.1, preferCanvas:true, attributionControl:true, fadeAnimation:true, zoomAnimation:true });
    map.attributionControl.setPrefix(false);

    /* ---- what is on the map ---- */
    var renderer = L.canvas({ padding:.3 });
    var dots = D.dots.map(function(d){ return { d:d, m:L.circleMarker([d[1], d[2]], { renderer:renderer, radius:2.4, weight:0, fillOpacity:.9, interactive:false }) }; });
    var dotGroup = L.layerGroup(dots.map(function(o){ return o.m; }));
    var ALL = L.latLngBounds(D.dots.map(function(d){ return [d[1], d[2]]; }));
    var TOWN = {};
    D.towns.forEach(function(t, i){ var pts = D.dots.filter(function(d){ return d[3] === i; }).map(function(d){ return [d[1], d[2]]; }); if (pts.length) TOWN[t] = L.latLngBounds(pts); });
    var lines = D.lines ? L.layerGroup([
      L.polyline(D.lines, { renderer:renderer, color:'#02050A', weight:4, opacity:.4, interactive:false }),
      L.polyline(D.lines, { renderer:renderer, color:'#FFFFFF', weight:1.4, opacity:.85, interactive:false }) ]) : null;
    var pin = L.circleMarker([0, 0], { radius:18, color:'#00E5FF', weight:2.5, fill:false, interactive:false });

    /* destroyed zones: the ones around this village come with the page; the full set is only fetched by a story that zooms out */
    var zonesNear = S.zones && S.zones.length ? L.polygon(S.zones, { interactive:false, attribution:'Destroyed zones: UNOSAT (CC BY-SA)' }) : null;
    var zonesAll = null, zonesWanted = false, zonesZoom = 12, zonesLoading = false;
    function zoneStyle(){ return zonesZoom >= 13.5 ? { color:'#FFD400', weight:2.2, opacity:.95, fill:false } : { color:'#FFD400', weight:1, opacity:.9, fillColor:'#FFD400', fillOpacity:.85, fill:true }; }
    function setZones(on, z){
      zonesWanted = !!on; zonesZoom = z;
      var close = z >= 13.5 && zonesNear;
      if (zonesNear){ if (on && close){ zonesNear.setStyle(zoneStyle()); if (!map.hasLayer(zonesNear)) zonesNear.addTo(map); } else map.removeLayer(zonesNear); }
      if (!on || close){ if (zonesAll) map.removeLayer(zonesAll); return; }
      if (zonesAll){ zonesAll.setStyle(zoneStyle()); if (!map.hasLayer(zonesAll)) zonesAll.addTo(map); return; }
      if (zonesLoading) return; zonesLoading = true;
      fetch('/unosat_2017_zones.geojson').then(function(r){ if (!r.ok) throw 0; return r.json(); }).then(function(g){
        zonesAll = L.geoJSON(g, { style:zoneStyle, interactive:false, attribution:'Destroyed zones: UNOSAT (CC BY-SA)' });
        if (zonesWanted && !(zonesZoom >= 13.5 && zonesNear)){ zonesAll.setStyle(zoneStyle()); zonesAll.addTo(map); }
      }).catch(function(){ zonesLoading = false; });
    }

    /* ---- base maps, cross-faded ---- */
    function urlOf(b){ return b === 'sat' ? ESRI + '{z}/{y}/{x}' : b && typeof b === 'object' ? WB + b.rel + '/{z}/{y}/{x}' : DARK + 'Base/MapServer/tile/{z}/{y}/{x}'; }
    function nativeOf(b){ return b === 'sat' ? 18 : b && typeof b === 'object' ? (b.z18 ? 18 : 17) : 16; }
    function make(b){
      if (b === 'sat') return [L.tileLayer(urlOf(b), opt({ maxNativeZoom:18, attribution:'Esri, Vantor, Earthstar Geographics' }))];
      if (b && typeof b === 'object') return [L.tileLayer(urlOf(b), opt({ maxNativeZoom:nativeOf(b), attribution:'Esri World Imagery Wayback' }))];
      return [L.tileLayer(urlOf(b), opt({ maxNativeZoom:16, attribution:'Esri, TomTom, Garmin, &copy; OpenStreetMap contributors' })),
              L.tileLayer(DARK + 'Reference/MapServer/tile/{z}/{y}/{x}', opt({ maxNativeZoom:16 }))];
    }
    var base = { key:null, layers:[] };
    function keyOf(b){ return b && typeof b === 'object' ? 'r' + b.rel : (b || 'dark'); }
    function setBase(b){
      var key = keyOf(b);
      if (key === base.key) return;
      var old = base.layers, neu = make(b);
      neu.forEach(function(l){ l.setOpacity(reduce ? 1 : 0); l.addTo(map); });
      if (!reduce) requestAnimationFrame(function(){ requestAnimationFrame(function(){ neu.forEach(function(l){ l.setOpacity(1); }); }); });
      setTimeout(function(){ old.forEach(function(l){ map.removeLayer(l); }); }, reduce ? 0 : 1100);
      base = { key:key, layers:neu };
    }

    /* ---- where the map looks: the part of the screen the text does not cover ---- */
    function free(){
      var w = innerWidth, h = innerHeight;
      return phone() ? { tl:[16, 64], br:[16, Math.round(h * .5)] } : { tl:[Math.min(Math.round(w * .44), 560), 70], br:[60, 80] };
    }
    function boundsOf(fit){
      if (!fit || fit === 'all') return ALL;
      if (typeof fit === 'string') return TOWN[fit] || ALL;
      if (typeof fit[0] === 'string'){ var b = null; fit.forEach(function(t){ if (TOWN[t]) b = b ? b.extend(TOWN[t]) : L.latLngBounds(TOWN[t].getSouthWest(), TOWN[t].getNorthEast()); }); return b || ALL; }
      return L.latLngBounds(fit);
    }
    /* centre and zoom a step asks for, without moving the map */
    function target(m){
      var p = free(), size = map.getSize(), z, c;
      if (m.at){
        z = m.zoom || 15;
        var cx = (p.tl[0] + size.x - p.br[0]) / 2, cy = (p.tl[1] + size.y - p.br[1]) / 2;
        c = map.unproject(map.project(m.at, z).subtract([cx - size.x / 2, cy - size.y / 2]), z);
      } else {
        var b = boundsOf(m.fit).pad(.04), pad = L.point(p.tl[0] + p.br[0], p.tl[1] + p.br[1]);
        z = map.getBoundsZoom(b, false, pad);
        var off = L.point(p.br[0] - p.tl[0], p.br[1] - p.tl[1]).divideBy(2);
        c = map.unproject(map.project(b.getCenter(), z).add(off), z);
      }
      return { c:c, z:z };
    }
    var view = '';
    function setView(m, instant){
      var t = target(m), key = t.c.lat.toFixed(5) + ',' + t.c.lng.toFixed(5) + ',' + t.z.toFixed(2);
      if (key !== view){
        view = key;
        if (instant || reduce) map.setView(t.c, t.z, { animate:false });
        else map.flyTo(t.c, t.z, { duration: phone() ? 1.25 : 1.7, easeLinearity:.2 });
      }
      return t.z;
    }
    var dotKey = '';
    function setDots(mode, z){
      if (mode === 'none'){ map.removeLayer(dotGroup); return; }
      var r = z >= 14 ? 6 : z >= 12 ? 4.2 : z >= 10.5 ? 3.2 : z >= 9.3 ? 2.5 : 1.9, key = mode + r;
      if (key !== dotKey){
        dotKey = key;
        dots.forEach(function(o){
          var s = o.d[4], col = mode === 'st17' ? ST[s] : mode === 'dim' ? '#C4D2E2' : (D.colors[o.d[3]] || '#8FA8C7');
          o.m.setStyle({ fillColor:col, radius: mode === 'st17' && s === 'd' ? r * 1.2 : r,
            fillOpacity: mode === 'dim' ? .55 : (mode === 'st17' && (s === 'z' || s === 'x')) ? .6 : .95 });
        });
      }
      if (!map.hasLayer(dotGroup)) dotGroup.addTo(map);
    }
    var legendEl = document.getElementById('slegend'), capEl = document.getElementById('scap'), legendKey = '';
    function setLegend(kind, zones){
      var key = (kind || '') + (zones ? 'z' : ''); if (key === legendKey) return; legendKey = key;
      var h = '';
      if (kind === 'town') h = D.towns.map(function(t, i){ return '<span><i style="background:' + D.colors[i] + ';color:' + D.colors[i] + '"></i>' + t + '</span>'; }).join('');
      else if (kind === 'st17') h = ['d', 'n', 'z', 'x'].map(function(k){ return '<span><i style="background:' + ST[k] + ';color:' + ST[k] + '"></i>' + ST_NAME[k] + '</span>'; }).join('');
      if (zones) h += '<span><i class="sq"></i>Destroyed zone · UNOSAT</span>';
      legendEl.innerHTML = h; legendEl.classList.toggle('show', !!h);
    }

    /* fetch the pictures of the step after this one while the reader is still reading, so the change is instant */
    var warmed = {};
    function warm(i){
      var m = S.steps[i]; if (!m || warmed[i]) return; warmed[i] = 1;
      var t = target(m), z = Math.min(nativeOf(m.base), Math.round(t.z)), size = map.getSize();
      var s = Math.pow(2, t.z - z), c = map.project(t.c, z), hw = size.x / 2 / s, hh = size.y / 2 / s;
      var url = urlOf(m.base), n = 0;
      for (var y = Math.floor((c.y - hh) / 256); y <= Math.floor((c.y + hh) / 256); y++)
        for (var x = Math.floor((c.x - hw) / 256); x <= Math.floor((c.x + hw) / 256); x++){
          if (++n > 40) return;
          new Image().src = url.replace('{z}', z).replace('{y}', y).replace('{x}', x);
        }
    }

    /* ---- one step ---- */
    var steps = [].slice.call(root.querySelectorAll('.step')), active = -1;
    function apply(i, instant){
      if (i === active && !instant) return;
      active = i;
      var m = S.steps[i] || {};
      setBase(m.base);
      var z = setView(m, instant);
      setDots(m.dots || 'town', z);
      if (lines){ if (m.lines){ if (!map.hasLayer(lines)) lines.addTo(map); } else map.removeLayer(lines); }
      setZones(m.zones, z);
      var at = m.pin === true ? m.at : m.pin;
      if (at){ pin.setLatLng(at); pin.setRadius(z >= 14 ? 18 : 9); if (!map.hasLayer(pin)) pin.addTo(map); } else map.removeLayer(pin);
      capEl.innerHTML = m.caption || ''; capEl.classList.toggle('show', !!m.caption);
      setLegend(m.legend, m.zones);
      steps.forEach(function(s, k){ s.classList.toggle('on', k === i); });
      setTimeout(function(){ if (active === i) warm(i + 1); }, instant ? 1200 : 700);
    }
    map.setView(ALL.getCenter(), 8, { animate:false });
    apply(0, true);

    /* the step whose card crosses the middle of the screen is the one on the map */
    if ('IntersectionObserver' in window){
      var io = new IntersectionObserver(function(es){
        es.forEach(function(e){ if (e.isIntersecting) apply(+e.target.dataset.i, false); });
      }, { rootMargin:'-50% 0px -50% 0px', threshold:0 });
      steps.forEach(function(s){ io.observe(s); });
    }
    var prog = document.createElement('div'); prog.className = 'sprog'; root.appendChild(prog);
    var ticking = false;
    addEventListener('scroll', function(){
      if (ticking) return; ticking = true;
      requestAnimationFrame(function(){
        ticking = false;
        var max = document.documentElement.scrollHeight - innerHeight;
        prog.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, scrollY / max) : 0) + ')';
        if (!('IntersectionObserver' in window)){
          var mid = innerHeight / 2, best = 0;
          steps.forEach(function(s, k){ if (s.getBoundingClientRect().top <= mid) best = k; });
          apply(best, false);
        }
      });
    }, { passive:true });
    var rt = 0, lastW = innerWidth;
    addEventListener('resize', function(){
      if (innerWidth === lastW && phone()) return;                   /* a phone's address bar sliding away is not a real resize */
      lastW = innerWidth;
      clearTimeout(rt); rt = setTimeout(function(){ map.invalidateSize(); view = ''; apply(Math.max(0, active), true); }, 180);
    });
  }
})();
