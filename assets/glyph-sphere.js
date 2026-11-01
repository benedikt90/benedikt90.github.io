// The homepage rotates continuously; research uses the same globe at a slower pace.
// Rasterize the glyphs once, then move their cached images at display refresh rate.
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const chars = '01/:{}<>[]=+#';
  const golden = Math.PI * (3 - Math.sqrt(5));
  const points = Array.from({ length: 2400 }, (_, index) => {
    const y = 1 - index / 2399 * 2;
    const r = Math.sqrt(1 - y * y);
    return { x: Math.cos(index * golden) * r, y, z: Math.sin(index * golden) * r, glyph: index % chars.length };
  });

  for (const canvas of document.querySelectorAll('.glyph-sphere')) {
    const context = canvas.getContext('2d');
    if (!context) continue;
    const continuous = ['continuous', 'slow'].includes(canvas.dataset.motion);
    const speed = canvas.dataset.motion === 'slow' ? 0.000008 : 0.00008;
    const toggle = document.getElementById(canvas.dataset.motionToggle);
    const atlas = document.createElement('canvas');
    const pen = atlas.getContext('2d');
    if (!pen) continue;
    let size = 0, cell = 0, atlasCell = 0;
    let frame = 0, previousTime = null, turn = 0;
    let visible = false, paused = false;

    function prepareGlyphs() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      const fontSize = size > 600 ? 12 : size > 300 ? 10 : 7;
      cell = fontSize + 4;
      atlasCell = Math.ceil(cell * dpr);
      atlas.width = atlasCell * chars.length;
      atlas.height = atlasCell;
      pen.font = `${fontSize * dpr}px ui-monospace, monospace`;
      pen.textAlign = 'center';
      pen.textBaseline = 'middle';
      pen.fillStyle = getComputedStyle(canvas).getPropertyValue('--glyph').trim();
      [...chars].forEach((char, index) => pen.fillText(char, (index + 0.5) * atlasCell, atlasCell / 2));
    }

    function draw() {
      if (!size) return;
      context.clearRect(0, 0, size, size);
      const angle = 0.45 + turn;
      const cos = Math.cos(angle), sin = Math.sin(angle);
      const stride = size < 250 ? 4 : size < 600 ? 2 : 1;
      for (let index = 0; index < points.length; index += stride) {
        const point = points[index];
        const x = point.x * cos + point.z * sin;
        const z = -point.x * sin + point.z * cos;
        const y = point.y * 0.97 - z * 0.24;
        const depth = z * 0.97 + point.y * 0.24;
        const perspective = 2.8 / (2.8 - depth);
        context.globalAlpha = depth > 0 ? 0.32 + depth * 0.55 : 0.08;
        context.drawImage(atlas, point.glyph * atlasCell, 0, atlasCell, atlasCell,
          size / 2 + x * size * 0.45 * perspective - cell / 2,
          size / 2 + y * size * 0.45 * perspective - cell / 2, cell, cell);
      }
      context.globalAlpha = 1;
    }

    function stop() {
      cancelAnimationFrame(frame);
      frame = 0;
      previousTime = null;
    }

    function animate(now) {
      frame = 0;
      if (!continuous || !visible || document.hidden || reduced.matches || paused) return;
      if (previousTime !== null) turn = (turn + Math.min(now - previousTime, 64) * speed) % (Math.PI * 2);
      previousTime = now;
      draw();
      frame = requestAnimationFrame(animate);
    }

    function resume() {
      if (!frame && continuous && visible && !document.hidden && !reduced.matches && !paused) {
        frame = requestAnimationFrame(animate);
      }
    }

    function updateControl() {
      if (!toggle) return;
      toggle.hidden = reduced.matches;
      toggle.textContent = paused ? 'Resume motion' : 'Pause motion';
      toggle.setAttribute('aria-pressed', String(paused));
    }
    toggle?.addEventListener('click', () => {
      paused = !paused;
      updateControl();
      if (paused) stop();
      else resume();
    });
    updateControl();

    new ResizeObserver(() => {
      size = canvas.getBoundingClientRect().width;
      const dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.round(size * dpr);
      canvas.height = Math.round(size * dpr);
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      prepareGlyphs();
      draw();
    }).observe(canvas);
    if (continuous) {
      new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        if (visible) resume();
        else stop();
      }).observe(canvas);
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) stop();
        else resume();
      });
      reduced.addEventListener('change', () => {
        stop();
        updateControl();
        resume();
      });
    }
    new MutationObserver(() => {
      prepareGlyphs();
      draw();
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  }
})();
