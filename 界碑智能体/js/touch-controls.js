/**
 * 手机端触屏操作：左侧虚拟摇杆（移动）+ 右侧互动按钮。
 * 仅在粗指针/触屏设备激活；注入 window.__touchMove 供 PlayerController 读取，
 * 点击互动按钮时回调 window.__touchInteract（world.js 负责接线）。
 */
(function () {
  var coarse = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
  var touchable = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  if (!coarse && !touchable) return;

  window.__touchMove = { x: 0, y: 0, active: false, run: false };

  function init() {
    document.body.classList.add("touch-ui");
    var hint = document.querySelector(".controls-hint");
    if (hint) hint.textContent = "左侧摇杆移动 · 拖动屏幕转视角 · 点「互动」交流";

    var base = document.createElement("div");
    base.id = "touch-joystick";
    base.innerHTML = '<div id="touch-stick"></div>';
    document.body.appendChild(base);
    var stick = base.querySelector("#touch-stick");

    var act = document.createElement("button");
    act.id = "touch-interact";
    act.type = "button";
    act.textContent = "互动";
    document.body.appendChild(act);
    act.addEventListener("click", function () {
      if (typeof window.__touchInteract === "function") window.__touchInteract();
    });

    var pid = null, cx = 0, cy = 0;
    var RADIUS = 52;

    function setStick(dx, dy) {
      stick.style.transform = "translate(" + dx + "px, " + dy + "px)";
    }

    function move(e) {
      var dx = e.clientX - cx, dy = e.clientY - cy;
      var len = Math.hypot(dx, dy) || 1;
      var clamped = Math.min(len, RADIUS);
      dx = (dx / len) * clamped;
      dy = (dy / len) * clamped;
      setStick(dx, dy);
      var mag = Math.min(1, clamped / RADIUS);
      window.__touchMove = {
        x: dx / RADIUS,
        y: -dy / RADIUS,
        active: mag > 0.14,
        run: mag > 0.94,
      };
    }

    base.addEventListener("pointerdown", function (e) {
      pid = e.pointerId;
      base.setPointerCapture(pid);
      var r = base.getBoundingClientRect();
      cx = r.left + r.width / 2;
      cy = r.top + r.height / 2;
      move(e);
    });
    base.addEventListener("pointermove", function (e) {
      if (pid === e.pointerId) move(e);
    });
    base.addEventListener("pointerup", function (e) {
      if (pid !== e.pointerId) return;
      pid = null;
      window.__touchMove = { x: 0, y: 0, active: false, run: false };
      setStick(0, 0);
    });
    base.addEventListener("pointercancel", function (e) {
      if (pid !== e.pointerId) return;
      pid = null;
      window.__touchMove = { x: 0, y: 0, active: false, run: false };
      setStick(0, 0);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
