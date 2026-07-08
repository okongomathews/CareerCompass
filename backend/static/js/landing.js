/* ═══════════════════════════════════════════════════════════════════════════
   CareerCompass Kenya — Landing Page JS
   Vanilla JS, no dependencies. Nothing here makes a network request or
   stores anything — the check-in widget is purely client-side UI state,
   on purpose, consistent with the privacy claims made on this same page.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── Sticky nav shadow + mobile menu ─────────────────────────────────── */
  var nav = document.querySelector(".nav");
  var navToggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");

  function onScroll() {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    navLinks.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        navLinks.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ── Scroll-reveal ────────────────────────────────────────────────────── */
  var revealEls = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* ── Hero match-bar fill animation ───────────────────────────────────── */
  var heroBars = document.querySelectorAll(".hero-bar-fill");
  function fillHeroBars() {
    heroBars.forEach(function (bar) {
      bar.style.width = (bar.getAttribute("data-fill") || "0") + "%";
    });
  }
  if (heroBars.length) {
    if (reduceMotion) { fillHeroBars(); }
    else { window.requestAnimationFrame(function () { setTimeout(fillHeroBars, 250); }); }
  }

  /* ── Match-formula bar segments (single source of truth via data-*) ──── */
  document.querySelectorAll(".formula-bar").forEach(function (bar) {
    bar.querySelectorAll(".formula-seg").forEach(function (seg) {
      seg.style.width = (seg.getAttribute("data-pct") || "0") + "%";
    });
  });

  /* ── FAQ accordion ────────────────────────────────────────────────────── */
  document.querySelectorAll(".faq-q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") === "true";
      var panel = document.getElementById(btn.getAttribute("aria-controls"));
      btn.setAttribute("aria-expanded", String(!open));
      if (panel) panel.style.maxHeight = open ? "0px" : panel.scrollHeight + "px";
    });
  });

  /* ── Emotional check-in widget ────────────────────────────────────────
     Four cards represent four common emotional starting points. Selecting
     one reveals a short, specific reflection plus a single relevant next
     step. No selection is sent anywhere or persisted — closing or
     reloading the tab clears it completely. ────────────────────────────── */
  var checkinCards = document.querySelectorAll(".checkin-card");
  var checkinReplies = document.querySelectorAll(".checkin-reply");

  checkinCards.forEach(function (card) {
    card.addEventListener("click", function () {
      var key = card.getAttribute("data-checkin");

      checkinCards.forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      card.setAttribute("aria-pressed", "true");

      checkinReplies.forEach(function (reply) {
        var match = reply.getAttribute("data-checkin-reply") === key;
        reply.classList.toggle("is-active", match);
      });

      var activeReply = document.querySelector('.checkin-reply[data-checkin-reply="' + key + '"]');
      if (activeReply) {
        activeReply.setAttribute("tabindex", "-1");
        if (!reduceMotion) {
          window.requestAnimationFrame(function () {
            var rect = activeReply.getBoundingClientRect();
            var offset = window.scrollY + rect.top - 96;
            window.scrollTo({ top: offset, behavior: "smooth" });
          });
        }
        activeReply.focus({ preventScroll: true });
      }
    });
  });

})();
