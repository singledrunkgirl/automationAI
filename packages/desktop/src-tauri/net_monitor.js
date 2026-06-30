(function(){
var errors=window.__hwai_errs||[];
window.__hwai_errs=errors;
var _onerror=window.onerror;
window.onerror=function(m,s,l,c,e){
    var msg=(e&&e.message||m||"");
    errors.push("[JS] "+msg+" @"+(s||"?")+":"+l);
    if(_onerror)return _onerror.apply(this,arguments);
    return false;
};
window.addEventListener('unhandledrejection',function(ev){
    errors.push("[PROMISE] "+(ev.reason&&ev.reason.message||String(ev.reason)));
});
window.addEventListener('error',function(ev){
    if(ev instanceof ErrorEvent)return;
    var t=(ev.target&&ev.target.tagName)||'?';
    var u=(ev.target&&(ev.target.src||ev.target.href))||'';
    errors.push("[RES-ERR] "+t+" "+u);
},true);
var _ce=console.error;
console.error=function(){
    errors.push("[CONSOLE] "+Array.prototype.slice.call(arguments).join(' '));
    return _ce.apply(console,arguments);
};
var origF=window.fetch;
window.fetch=function(u,op){
    var s=typeof u==='string'?u:String(u.url||u);
    try{var p=new URL(s,''+window.location);errors.push("[FETCH] "+(op&&op.method||"GET")+" port="+p.port+" host="+p.hostname+" "+p.pathname.slice(0,30))}catch(e){}
    return origF.apply(this,arguments).then(function(r){
        errors.push("[FETCH-RES] "+r.status+" "+s.slice(0,30));
        return r;
    }).catch(function(e){
        errors.push("[FETCH-FAIL] "+(e.message||"")+" "+s.slice(0,40));
        throw e;
    });
};
var origX=window.XMLHttpRequest;
window.XMLHttpRequest=function(){
    var x=new origX(),m='',u='';
    var oo=x.open;x.open=function(a,b){m=a;u=String(b);return oo.apply(this,arguments)};
    x.addEventListener('load',function(){try{var p=new URL(u,''+window.location);errors.push("[XHR] port="+p.port+" host="+p.hostname)}catch(e){}});
    x.addEventListener('error',function(){errors.push("[XHR-FAIL] "+m+" "+u.slice(0,30))});
    return x;
};
document.title="ERR-CAP:"+errors.length;
})();
