import {Children, isValidElement, useState, type ReactNode} from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {Check, Copy} from 'lucide-react';

function textoDoNo(no: ReactNode): string {
  return Children.toArray(no).map(item => {
    if (typeof item === 'string' || typeof item === 'number') return String(item);
    return isValidElement<{children?: ReactNode}>(item) ? textoDoNo(item.props.children) : '';
  }).join('');
}

function Copiar({texto, rotulo = 'Copiar'}: {texto: string; rotulo?: string}) {
  const [estado, setEstado] = useState('');
  async function copiar() {
    try {
      await navigator.clipboard.writeText(texto);
      setEstado('Copiado');
    } catch {
      setEstado('Não foi possível copiar');
    }
  }
  return <button className="copy-button" type="button" onClick={()=>void copiar()} aria-label={estado || rotulo} title={estado || rotulo}>
    {estado === 'Copiado' ? <Check size={14}/> : <Copy size={14}/>}
    <span>{estado || rotulo}</span>
  </button>;
}

function BlocoCodigo({children}: {children: ReactNode}) {
  const elemento = Children.toArray(children).find(item => isValidElement(item));
  const classe = isValidElement<{className?: string}>(elemento) ? elemento.props.className : '';
  const linguagem = classe?.replace('language-', '') || 'Código';
  return <div className="code-card"><div className="code-header"><span>{linguagem}</span><Copiar texto={textoDoNo(children).replace(/\n$/, '')} rotulo="Copiar código"/></div><pre>{children}</pre></div>;
}

export default function Resposta({texto}: {texto: string}) {
  return <><div className="markdown-response"><Markdown remarkPlugins={[remarkGfm]} skipHtml components={{
    pre: ({children}) => <BlocoCodigo>{children}</BlocoCodigo>,
    table: ({children}) => <div className="table-scroll"><table>{children}</table></div>,
    a: ({children, href}) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
    img: ({alt}) => <span className="image-description">{alt || 'Imagem mencionada na resposta'}</span>,
  }}>{texto}</Markdown></div><div className="response-actions"><Copiar texto={texto} rotulo="Copiar resposta"/></div></>;
}
