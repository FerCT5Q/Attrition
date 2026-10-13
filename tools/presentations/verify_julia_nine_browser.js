async (page) => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.reload();
  await page.setViewportSize({ width: 1440, height: 810 });
  const active = () => page.evaluate(() => Number(document.querySelector('.nav-pill.pill-active').dataset.slide));
  const startsAtFirst = await active() === 0;
  const themes = ['theme-light-classic', 'theme-light-soft', 'theme-dark-royal', 'theme-dark-carbon'];
  const issues = [];
  for (const theme of themes) {
    await page.evaluate(t => document.querySelector('[data-theme="' + t + '"]').click(), theme);
    for (let i = 0; i < 9; i++) {
      await page.evaluate(n => document.querySelector('.nav-pill[data-slide="' + n + '"]').click(), i);
      await page.waitForTimeout(60);
      const bad = await page.evaluate(() => {
        const s = [...document.querySelectorAll('.slide-stage')].find(x => getComputedStyle(x).display !== 'none');
        const rect = s.getBoundingClientRect();
        return [...s.querySelectorAll('*')]
          .filter(e => e.getBoundingClientRect().width && !e.closest('[aria-hidden="true"]'))
          .map(e => ({ tag: e.tagName, cls: e.className, box: e.getBoundingClientRect(), text: e.textContent.slice(0, 60) }))
          .filter(e => e.box.bottom > rect.bottom + 2 || e.box.top < rect.top - 2 || e.box.right > rect.right + 2 || e.box.left < rect.left - 2)
          .map(e => ({ tag: e.tag, cls: e.cls, text: e.text }));
      });
      if (bad.length) issues.push({ theme, slide: i + 1, bad });
      await page.screenshot({ path: 'C:/Dev/Python/Attrition/output/preview/julia-nine-slides/' + theme + '-' + String(i + 1).padStart(2, '0') + '.png' });
    }
  }
  await page.keyboard.press('Home');
  const home = await active() === 0;
  await page.keyboard.press('ArrowRight');
  const forward = await active() === 1;
  await page.keyboard.press('ArrowLeft');
  const backward = await active() === 0;
  await page.keyboard.press('End');
  const end = await active() === 8;
  await page.reload();
  const persistence = await page.evaluate(() => document.body.classList.contains('theme-dark-carbon'));
  const reopen = await active() === 0;
  const noExternalResources = await page.evaluate(() => performance.getEntriesByType('resource').every(x => !x.name.startsWith('http') || x.name.startsWith(location.origin)));
  await page.evaluate(() => document.querySelector('[data-theme="theme-light-classic"]').click());
  return { screenshots: 36, viewport: '1440x810', issues, errors, startsAtFirst, home, forward, backward, end, persistence, reopen, noExternalResources };
}
