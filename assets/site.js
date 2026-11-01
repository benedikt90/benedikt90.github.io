(() => {
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const systemTheme = matchMedia('(prefers-color-scheme: light)');
  let manualTheme = false;
  try { manualTheme = ['light', 'dark'].includes(localStorage.getItem('bentr-theme')); } catch {}

  function updateThemeLabel() {
    if (!toggle) return;
    const label = `Switch to ${root.dataset.theme === 'light' ? 'dark' : 'light'} theme`;
    toggle.setAttribute('aria-label', label);
    toggle.title = label;
  }
  updateThemeLabel();
  toggle?.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    manualTheme = true;
    try { localStorage.setItem('bentr-theme', root.dataset.theme); } catch {}
    updateThemeLabel();
  });
  systemTheme.addEventListener('change', event => {
    if (manualTheme) return;
    root.dataset.theme = event.matches ? 'light' : 'dark';
    updateThemeLabel();
  });

  const contents = document.querySelector('.toc');
  const desktop = matchMedia('(min-width: 901px)');
  function setContentsLayout() { if (contents) contents.open = desktop.matches; }
  setContentsLayout();
  desktop.addEventListener('change', setContentsLayout);
  const contentsLinks = document.querySelectorAll('.toc a');
  if (contentsLinks.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        contentsLinks.forEach(link => {
          if (decodeURIComponent(link.hash.slice(1)) === entry.target.id) {
            link.setAttribute('aria-current', 'location');
          } else {
            link.removeAttribute('aria-current');
          }
        });
      }
    }, { rootMargin: '-5% 0px -75% 0px' });
    document.querySelectorAll('.article-body h2').forEach(heading => observer.observe(heading));
  }
  contentsLinks.forEach(link => link.addEventListener('click', () => {
    if (!desktop.matches) contents.open = false;
  }));

  document.querySelectorAll('.article-body pre').forEach(block => {
    block.tabIndex = 0;
    block.setAttribute('role', 'region');
    block.setAttribute('aria-label', 'Code example');
  });

  // Keep wide research tables scrollable without widening the reading column.
  document.querySelectorAll('.article-body table').forEach(table => {
    const wrapper = document.createElement('div');
    wrapper.className = 'table-scroll';
    wrapper.tabIndex = 0;
    wrapper.setAttribute('role', 'region');
    wrapper.setAttribute('aria-label', 'Research data table');
    table.before(wrapper);
    wrapper.append(table);
  });

  const lightbox = document.getElementById('lightbox');
  const preview = document.getElementById('lightbox-img');
  const close = document.getElementById('lightbox-close');
  if (!lightbox || !preview || !close) return;
  let trigger;
  document.querySelectorAll('.article-body figure img').forEach(image => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'image-zoom';
    button.setAttribute('aria-label', `Enlarge image: ${image.alt || 'Research figure'}`);
    image.before(button);
    button.append(image);
    button.addEventListener('click', () => {
      trigger = button;
      preview.src = image.currentSrc || image.src;
      preview.alt = image.alt;
      lightbox.showModal();
      document.body.style.overflow = 'hidden';
    });
  });
  close.addEventListener('click', () => lightbox.close());
  lightbox.addEventListener('click', event => {
    if (event.target !== lightbox) return;
    const rect = lightbox.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) lightbox.close();
  });
  lightbox.addEventListener('close', () => {
    document.body.style.overflow = '';
    preview.removeAttribute('src');
    trigger?.focus({ preventScroll: true });
  });
})();
