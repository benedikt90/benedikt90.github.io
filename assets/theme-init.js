// Apply the saved preference before the stylesheet paints the page.
(() => {
  const root = document.documentElement;
  root.classList.add('js');
  let saved;
  try { saved = localStorage.getItem('bentr-theme'); } catch {}
  root.dataset.theme = saved === 'light' || saved === 'dark'
    ? saved
    : (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
})();
