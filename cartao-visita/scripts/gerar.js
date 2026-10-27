// Gera o PDF para a gráfica (com sangria) e as pré-visualizações PNG.
// Uso (a partir da pasta cartao-visita): node scripts/gerar.js
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const root = path.resolve(__dirname, '..');
  const url = 'file://' + path.join(root, 'cartao-visita-mavisky.html');
  const browser = await chromium.launch();

  // PDF: 2 páginas de 91 x 61 mm (85 x 55 mm + 3 mm de sangria)
  const pdfPage = await browser.newPage();
  await pdfPage.goto(url);
  await pdfPage.evaluate(() => document.fonts.ready);
  await pdfPage.pdf({
    path: path.join(root, 'cartao-visita-mavisky-grafica.pdf'),
    width: '91mm', height: '61mm', printBackground: true, preferCSSPageSize: true,
  });

  // PNG: cada face no formato final, alta resolução
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 4 });
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: '.sheet{zoom:1!important}.card{border-radius:0!important;box-shadow:none!important}' });
  const cards = await page.$$('.card');
  await cards[0].screenshot({ path: path.join(root, 'previews/frente.png') });
  await cards[1].screenshot({ path: path.join(root, 'previews/verso.png') });

  // Vista geral da página (como aparece no navegador)
  const overview = await browser.newPage({ viewport: { width: 1300, height: 640 }, deviceScaleFactor: 2 });
  await overview.goto(url);
  await overview.evaluate(() => document.fonts.ready);
  await overview.screenshot({ path: path.join(root, 'previews/vista-geral.png'), fullPage: true });

  await browser.close();
  console.log('ok');
})();
