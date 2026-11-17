/* Datenschutz-Hinweis: nur funktionale Speicherung; Google Fonts werden erst nach Zustimmung geladen. */
(function(){
 var K="sg-consent",v=null;
 try{v=localStorage.getItem(K)}catch(e){}
 function fonts(){
  if(document.getElementById("sg-gf"))return;
  var l=document.createElement("link");l.id="sg-gf";l.rel="stylesheet";
  l.href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Archivo:wdth,wght@125,800&display=swap";
  document.head.appendChild(l);
 }
 function set(x){try{localStorage.setItem(K,x)}catch(e){}}
 function box(){
  var b=document.getElementById("sg-cb");if(b)b.remove();
  var d=document.createElement("div");d.id="sg-cb";d.setAttribute("role","dialog");d.setAttribute("aria-label","Datenschutz-Hinweis");
  d.innerHTML='<div class="cbi"><b>Datenschutz &amp; Cookies</b>'
   +'<p>Diese Seite nutzt <b>keine Tracking-, Analyse- oder Werbe-Cookies</b>. Im Speicher deines Browsers liegen nur funktionale Daten, etwa deine Auswahl und der Hell/Dunkel-Modus. Der Seitenbetreiber erhebt keine Daten über dich.</p>'
   +'<p>Optional: Die Schriften kommen von <b>Google Fonts</b>. Dabei wird deine IP-Adresse an Google übertragen. Ohne Zustimmung nutzt die Seite Standardschriften. Mehr dazu in der <a href="datenschutz.html">Datenschutzerklärung</a>.</p>'
   +'<div class="cbb"><button type="button" id="sg-cb-n">Nur notwendige</button><button type="button" id="sg-cb-y">Google-Schriften erlauben</button></div></div>';
  document.body.appendChild(d);
  document.getElementById("sg-cb-y").onclick=function(){set("fonts");d.remove();fonts()};
  document.getElementById("sg-cb-n").onclick=function(){var had=v==="fonts";set("min");v="min";d.remove();if(had)location.reload()};
 }
 var css=document.createElement("style");
 css.textContent='#sg-cb{position:fixed;left:0;right:0;bottom:0;z-index:99999;background:#fbf9f4;color:#1c1c1a;border-top:2px solid #1c1c1a;font:13px/1.55 system-ui,"Montserrat",sans-serif}'
  +'#sg-cb .cbi{max-width:980px;margin:0 auto;padding:16px clamp(16px,4vw,32px)}#sg-cb p{margin:6px 0;max-width:80ch}#sg-cb a{color:inherit}'
  +'#sg-cb .cbb{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}#sg-cb button{font:inherit;font-size:12px;letter-spacing:.12em;text-transform:uppercase;padding:11px 18px;border:1px solid #1c1c1a;background:transparent;color:#1c1c1a;cursor:pointer;border-radius:0}'
  +'#sg-cb button#sg-cb-y{background:#1c1c1a;color:#fbf9f4}'
  +'@media (prefers-color-scheme:dark){#sg-cb{background:#1b1b19;color:#efece4;border-top-color:#efece4}#sg-cb button{border-color:#efece4;color:#efece4}#sg-cb button#sg-cb-y{background:#efece4;color:#1b1b19}}';
 document.head.appendChild(css);
 if(v==="fonts")fonts();
 window.sgConsent=function(){box()};
 function ready(){if(!v)box()}
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",ready);else ready();
})();
