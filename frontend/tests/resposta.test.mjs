import assert from 'node:assert/strict';
import {mkdtemp, rm} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

const pasta = await mkdtemp(join(process.cwd(), '.teste-render-'));
try {
  const arquivo = join(pasta, 'Resposta.mjs');
  await build({entryPoints:['src/Resposta.tsx'],outfile:arquivo,bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic'});
  const {default:Resposta} = await import(pathToFileURL(arquivo).href);
  const html = renderToStaticMarkup(React.createElement(Resposta,{texto:'**Importante**\n\n- Primeiro\n- Segundo\n\n> **Atenção**\n> Um card.\n\n| A | B |\n| --- | --- |\n| Um | Dois |\n\n```python\nprint("!@$$#")\n```\n\n<script>alert(1)</script>\n\n[link](javascript:alert(1))'}));
  assert.ok(html.includes('<strong>Importante</strong>'));
  assert.ok(html.includes('<ul>'));
  assert.ok(html.includes('<blockquote>'));
  assert.ok(html.includes('<table>'));
  assert.ok(html.includes('Copiar código'));
  assert.ok(html.includes('!@$$#'), 'Símbolos válidos em código devem ser preservados');
  assert.ok(!html.includes('<script>'));
  assert.ok(!html.includes('href="javascript:'));
  assert.ok(!html.includes('**Importante**'));
  console.log('OK: Markdown, cards, tabelas, código e conteúdo inseguro.');
} finally {
  await rm(pasta,{recursive:true,force:true});
}
