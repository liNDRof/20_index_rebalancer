(function () {
  var form = document.getElementById('lang-form');
  var select = document.getElementById('lang-select');
  if (!form || !select) return;

  // Ensure <html lang> reflects current selection
  try {
    document.documentElement.setAttribute('lang', select.value);
  } catch (_) {}

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function postSetLanguage(lang) {
    var url = form.getAttribute('action') || '/i18n/setlang/';
    var next = (form.querySelector('input[name="next"]') || {}).value || window.location.pathname;
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: new URLSearchParams({ language: lang, next: next }).toString(),
      credentials: 'same-origin'
    });
  }

  select.addEventListener('change', function () {
    // Build URL-prefixed path: /<lang>/<rest>
    try {
      var lang = select.value;
      var path = window.location.pathname;
      // strip existing /en or /uk prefix
      var parts = path.replace(/^\/+/, '').split('/');
      if (parts.length && (parts[0] === 'en' || parts[0] === 'uk')) {
        parts.shift();
      }
      var newPath = '/' + lang + '/' + parts.join('/');
      if (newPath.endsWith('//')) newPath = newPath.slice(0, -1);
      // Persist cookie via set_language and then navigate
      postSetLanguage(lang).finally(function () {
        window.location.assign(newPath);
      });
    } catch (_) {
      form.submit();
    }
  });
})();


