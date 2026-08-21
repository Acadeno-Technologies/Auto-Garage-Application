/* ==========================================================================
   KRISHNA AUTO CARE — APP.JS
   Dark mode, animated counters, scroll reveal, toasts, sidebar collapse.
   Additive only — does not touch existing inline scripts in base.html.
   ========================================================================== */
(function () {
  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Dark mode ---------- */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { window.localStorage.setItem('garage-theme', theme); } catch (e) {}
  }
  var savedTheme = 'light';
  try { savedTheme = window.localStorage.getItem('garage-theme') || 'light'; } catch (e) {}
  applyTheme(savedTheme);

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.theme-toggle-btn');
    if (!btn) return;
    var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(current);
  });

  /* ---------- Sidebar collapse (desktop) ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    var collapseBtn = document.querySelector('.sidebar-collapse-btn');
    var sidebar = document.querySelector('.sidebar');
    if (collapseBtn && sidebar) {
      var collapsed = false;
      try { collapsed = window.localStorage.getItem('garage-sidebar-collapsed') === 'true'; } catch (e) {}
      if (collapsed) sidebar.classList.add('collapsed');
      collapseBtn.addEventListener('click', function () {
        sidebar.classList.toggle('collapsed');
        try { window.localStorage.setItem('garage-sidebar-collapsed', sidebar.classList.contains('collapsed')); } catch (e) {}
      });
    }

    /* ---------- Animated stat counters ---------- */
    var counters = document.querySelectorAll('.stat-value, .metric-value-lg');
    if (!prefersReduced && counters.length) {
      var counterObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        });
      }, { threshold: 0.3 });
      counters.forEach(function (el) { counterObserver.observe(el); });
    }

    function animateCounter(el) {
      var raw = el.textContent.trim();
      var match = raw.match(/([\d,]+\.?\d*)/);
      if (!match) return;
      var prefix = raw.slice(0, match.index);
      var suffix = raw.slice(match.index + match[0].length);
      var target = parseFloat(match[0].replace(/,/g, ''));
      if (isNaN(target)) return;
      var decimals = (match[0].split('.')[1] || '').length;
      var duration = 900;
      var startTime = null;

      function step(ts) {
        if (!startTime) startTime = ts;
        var progress = Math.min((ts - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = target * eased;
        var formatted = current.toLocaleString('en-IN', {
          minimumFractionDigits: decimals, maximumFractionDigits: decimals
        });
        el.textContent = prefix + formatted + suffix;
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = raw;
      }
      requestAnimationFrame(step);
    }

    /* ---------- Scroll reveal ---------- */
    var revealEls = document.querySelectorAll('.reveal, .stagger');
    if (revealEls.length) {
      if (prefersReduced) {
        revealEls.forEach(function (el) { el.classList.add('in-view'); });
      } else {
        var revealObserver = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add('in-view');
              revealObserver.unobserve(entry.target);
            }
          });
        }, { threshold: 0.15 });
        revealEls.forEach(function (el) { revealObserver.observe(el); });
      }
    }

    /* ---------- Progress bar fill animation ---------- */
    document.querySelectorAll('.progress-fill[data-progress]').forEach(function (el) {
      var pct = el.getAttribute('data-progress');
      requestAnimationFrame(function () { el.style.width = pct + '%'; });
    });

    /* ---------- Auto-toast from Django messages ---------- */
    document.querySelectorAll('.messages-bar .alert').forEach(function (el, i) {
      var text = el.textContent.trim();
      var type = 'info';
      if (el.classList.contains('alert-success')) type = 'success';
      else if (el.classList.contains('alert-error')) type = 'error';
      else if (el.classList.contains('alert-warning')) type = 'warning';
      setTimeout(function () { window.showToast(text, type); }, 150 * i);
    });
  });

  /* ---------- Toast API ---------- */
  window.showToast = function (message, type) {
    var stack = document.getElementById('toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.id = 'toast-stack';
      document.body.appendChild(stack);
    }
    var toast = document.createElement('div');
    toast.className = 'toast ' + (type || 'info');
    toast.textContent = message;
    stack.appendChild(toast);
    setTimeout(function () {
      toast.classList.add('hide');
      setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
  };
})();
