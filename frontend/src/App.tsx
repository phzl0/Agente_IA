import {useEffect, useRef, useState, type FormEvent} from 'react';
import {ArrowUp, BookOpen, Check, ChevronRight, CircleHelp, FileText, Folder, LoaderCircle, MessageSquare, Plus, Radio, Search, Settings, LogOut, Workflow, X} from 'lucide-react';
import Resposta from './Resposta';

type Fonte={fonte:string;linha_inicio:number;linha_fim:number;texto:string};
type Evento={ferramenta:string;argumentos:Record<string,unknown>;resultado:unknown};
type Mensagem={role:'user'|'model';text:string};
type Resultado={conversa_id:string;resposta:string;eventos:Evento[];fontes:Fonte[]};
const sugestoes=[{icone:Search,titulo:'Explore os documentos',texto:'Consulte os documentos: quanto XP uma missão diária concede?'},{icone:Folder,titulo:'Conheça o projeto',texto:'Liste os arquivos da pasta principal do projeto.'},{icone:CircleHelp,titulo:'Entenda as regras',texto:'Consulte os documentos: como funcionam as temporadas?'}];
export default function App(){
 const [mensagens,setMensagens]=useState<Mensagem[]>([]),[entrada,setEntrada]=useState(''),[ocupado,setOcupado]=useState(false),[erro,setErro]=useState('');
 const [eventos,setEventos]=useState<Evento[]>([]),[fontes,setFontes]=useState<Fonte[]>([]),[aba,setAba]=useState<'atividade'|'fontes'>('atividade'),[painelAberto,setPainelAberto]=useState(false);
 const [status,setStatus]=useState<{configurado:boolean;modelo:string}|null>(null),[ajuda,setAjuda]=useState(false);
 const [conta,setConta]=useState<{configurada:boolean;autenticado:boolean;nome:string;usuario?:string}|null>(null),[senha,setSenha]=useState(''),[nome,setNome]=useState('Paulo'),[authErro,setAuthErro]=useState(''),[authOcupado,setAuthOcupado]=useState(false);
 const [conversas,setConversas]=useState<{id:string;titulo:string}[]>([]),[conversaId,setConversaId]=useState<string|null>(null),[perfilAberto,setPerfilAberto]=useState(false),[senhaAtual,setSenhaAtual]=useState(''),[novaSenha,setNovaSenha]=useState(''),[avisoPerfil,setAvisoPerfil]=useState(''),[historicoAberto,setHistoricoAberto]=useState(false);
 async function requisitar(url:string,opcoes:RequestInit={}){const r=await fetch(url,opcoes);const d=await r.json();if(r.status===401)setConta({configurada:true,autenticado:false,nome:''});if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Não foi possível concluir.');return d}
 async function atualizarLista(){setConversas(await requisitar('/api/conversas'))}
 useEffect(()=>{fetch('/api/conta').then(r=>r.json()).then(d=>{setConta(d);if(d.nome)setNome(d.nome)}).catch(()=>setAuthErro('Backend indisponível. Inicie o Python na porta 8005.'))},[]);
 useEffect(()=>{if(conta?.autenticado)void atualizarLista().catch(()=>setErro('Não foi possível carregar as conversas.'))},[conta?.autenticado]);
 const [modoConta, setModoConta] = useState<'entrar' | 'cadastro' | null>(null);
 const [usuario, setUsuario] = useState('');
 const cadastrando = modoConta === 'cadastro' || (modoConta === null && conta?.configurada === false);

 async function autenticar(e: FormEvent) {
  e.preventDefault();
  setAuthOcupado(true);
  setAuthErro('');
  try {
   await requisitar(cadastrando ? '/api/conta/configurar' : '/api/conta/entrar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({nome: usuario.trim(), senha}),
   });
   window.location.reload();
  } catch (erro) {
   setAuthErro(erro instanceof Error ? erro.message : 'Não foi possível acessar a conta.');
  } finally {
   setAuthOcupado(false);
  }
 }

 function alternarModoConta() {
  setModoConta(cadastrando ? 'entrar' : 'cadastro');
  setSenha('');
  setAuthErro('');
 }

 async function abrirConversa(id:string){if(ocupado)return;try{const d=await requisitar('/api/conversas/'+id);setHistoricoAberto(false);setConversaId(id);setMensagens(d.mensagens);setEventos(d.eventos);setFontes(d.fontes);setErro('');setEntrada('')}catch(e){setErro(e instanceof Error?e.message:'Falha ao abrir conversa.')}}
 async function salvarPerfil(e:FormEvent){e.preventDefault();setAuthOcupado(true);setAvisoPerfil('');try{const d=await requisitar('/api/perfil',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome,senha_atual:senhaAtual,nova_senha:novaSenha})});setConta({configurada:true,autenticado:true,nome:d.nome,usuario:d.usuario});setSenhaAtual('');setNovaSenha('');setAvisoPerfil('Configurações salvas.')}catch(e){setAvisoPerfil(e instanceof Error?e.message:'Falha ao salvar.')}finally{setAuthOcupado(false)}}
 async function sair() {
  await requisitar('/api/conta/sair', {method: 'POST'});
  window.location.reload();
 }
 const fim=useRef<HTMLDivElement>(null);
 useEffect(()=>{const controle=new AbortController();fetch('/api/status',{signal:controle.signal}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(setStatus).catch(()=>{});return()=>controle.abort()},[]);
 useEffect(()=>{fim.current?.scrollIntoView({behavior:'smooth'})},[mensagens,ocupado]);
 async function enviar(texto=entrada){
  if(!texto.trim()||ocupado)return;
  const historico=mensagens;setEntrada('');setErro('');setOcupado(true);setEventos([]);setFontes([]);setMensagens([...historico,{role:'user',text:texto}]);
  try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensagem:texto,conversa_id:conversaId}),signal:AbortSignal.timeout(95000)});const dados=await r.json();if(r.status===401)setConta({configurada:true,autenticado:false,nome:''});if(!r.ok)throw Error(typeof dados.detail==='string'?dados.detail:'Não foi possível processar a mensagem.');const resultado=dados as Resultado;setMensagens([...historico,{role:'user',text:texto},{role:'model',text:resultado.resposta}]);setEventos(resultado.eventos);setFontes(resultado.fontes);setConversaId(resultado.conversa_id);void atualizarLista().catch(()=>setErro("Resposta salva, mas a lista de conversas não foi atualizada."))}catch(e){setMensagens(historico);setEntrada(texto);setErro(e instanceof Error?e.message:'Falha na conexão.')}finally{setOcupado(false)}
 }
 function nova(){if(ocupado)return;setConversaId(null);setMensagens([]);setEventos([]);setFontes([]);setErro('');setEntrada('')}
 function submeter(e:FormEvent){e.preventDefault();void enviar()}
 if (!conta?.autenticado) return (
  <div className="auth-page">
   <div className="auth-art"><img src="/robo.svg" alt="Robô triste, mascote do agente"/><span className="eyebrow">SEU NOVO COPILOTO DIGITAL</span><h1>Um pouco triste.<br/>Muito inteligente<span>.</span></h1><p>Suas ideias, documentos e conversas.<br/>Um universo de possibilidades.</p><div className="digital-lines">NEURAL SYSTEM / LOCAL WORKSPACE / ONLINE</div></div>
   <form className="auth-card" onSubmit={autenticar}>
    <img src="/robo.svg" alt=""/>
    <h2>{cadastrando ? 'Criar conta local' : 'Entrar na sua conta'}</h2>
    <p>{cadastrando ? 'Escolha um usuário e uma senha. Cada conta tem suas próprias conversas.' : 'Se você já tinha uma conta, use o nome do seu perfil anterior como usuário.'}</p>
    <label>
     Usuário
     <input autoComplete="username" value={usuario} onChange={e => setUsuario(e.target.value)} required maxLength={60}/>
    </label>
    <label>
     Senha
     <input type="password" autoComplete={cadastrando ? 'new-password' : 'current-password'} value={senha}
      onChange={e => setSenha(e.target.value)} required minLength={8} maxLength={128}/>
    </label>
    {authErro && <p role="alert" className="error">{authErro}</p>}
    <button className="primary" disabled={!conta || authOcupado}>
     {authOcupado ? 'Aguarde…' : cadastrando ? 'Criar conta' : 'Entrar'} <ChevronRight size={17}/>
    </button>
    <button type="button" className="logout" onClick={alternarModoConta} disabled={!conta || authOcupado}>
     {cadastrando ? 'Já tenho uma conta' : 'Cadastrar nova conta'}
    </button>
   </form>
  </div>
 );
 return <div className="app">
  <aside className="sidebar"><a className="brand" href="/" aria-label="Agente IA, início"><img className="brand-robot" src="/robo.svg" alt="Robô triste"/>agente<span className="brand-ai">.ia</span></a><span className="workspace-label">SEU WORKSPACE</span><button className="new-chat" onClick={nova} disabled={ocupado}><Plus size={17}/> Nova conversa <span>＋</span></button><nav aria-label="Navegação"><button className="nav-item selected" onClick={()=>setAjuda(false)}><MessageSquare size={18}/> Assistente <span className="small-dot"/></button><button className="nav-item" onClick={()=>{setAba('fontes');setPainelAberto(true);setAjuda(false)}}><BookOpen size={18}/> Fontes consultadas <span className="count">{fontes.length}</span></button><button className="nav-item" onClick={()=>setAjuda(!ajuda)}><Workflow size={18}/> Como funciona</button></nav><div className="saved-chats"><span className="workspace-label">CONVERSAS SALVAS</span>{conversas.length?conversas.map(c=><button disabled={ocupado} className={c.id===conversaId?'current':''} key={c.id} onClick={()=>void abrirConversa(c.id)}><MessageSquare size={14}/><span>{c.titulo}</span></button>):<p>Suas conversas aparecerão aqui.</p>}</div><div className="sidebar-bottom"><div className="local-badge"><span className="status-dot"/> Ambiente local</div><p>Seu conhecimento.<br/>Uma conversa de distância.</p><button className="profile" onClick={()=>{setNome(conta.nome);setPerfilAberto(true);setAvisoPerfil('')}}><span>{conta.nome.slice(0,2).toUpperCase()}</span><div>{conta.nome}<small>Perfil e configurações</small></div><Settings size={16}/></button></div></aside>
  <main className="main"><header><div><strong>Agente IA</strong><span className="model-label">Gemini</span><button className="mobile-settings" onClick={()=>setHistoricoAberto(true)} aria-label="Abrir conversas salvas"><MessageSquare size={16}/></button><button className="mobile-settings" onClick={nova} disabled={ocupado} aria-label="Nova conversa"><Plus size={16}/></button><button className="mobile-settings" onClick={()=>setPerfilAberto(true)} aria-label="Abrir perfil"><Settings size={16}/></button></div><div className="header-actions"><button className="context-toggle" onClick={()=>setPainelAberto(!painelAberto)} aria-expanded={painelAberto}><BookOpen size={16}/> Contexto {fontes.length ? <span>{fontes.length}</span> : null}</button><span className="connection"><span className={status?.configurado?'status-dot':'status-dot muted'}/>{status?.configurado?'API configurada':status?'Configure sua API':'Backend indisponível'}</span></div></header>
   <div className="main-body"><section className="chat-area" aria-label="Conversa">
   {ajuda?<div className="help"><button onClick={()=>setAjuda(false)} aria-label="Fechar explicação"><X size={18}/></button><h2>Como funciona</h2><p>Você pergunta. O Gemini identifica se precisa de uma ferramenta. O cliente MCP conecta ao servidor local, que consulta os arquivos ou busca trechos nos documentos.</p><p>Os trechos encontrados voltam ao Gemini para compor a resposta. Isso é RAG: recuperar informação antes de gerar o texto.</p><div className="flow">Chat → API Python → Gemini → MCP → RAG</div><p>A chave fica no backend. Conversas e perfil são salvos no banco local. Perguntas gerais usam o conhecimento do modelo; consultas aos documentos usam RAG. As atividades aparecem ao concluir.</p></div>:null}
   <div className="conversation" role="log" aria-label="Mensagens" aria-live="polite">{mensagens.length===0?<div className="welcome"><img className="welcome-robot" src="/robo.svg" alt=""/><h1>Como posso ajudar?</h1><p>Pergunte, explore uma ideia ou consulte seus documentos.</p><div className="suggestions">{sugestoes.map(({icone:Icon,titulo,texto})=><button key={titulo} disabled={ocupado} onClick={()=>void enviar(texto)}><Icon size={16}/><strong>{titulo}</strong></button>)}</div></div>:mensagens.map((m,i)=><article key={i} className={`message ${m.role}`}><span className="avatar">{m.role==='model'?<img src="/robo.svg" alt=""/>:conta.nome.slice(0,2).toUpperCase()}</span><div><strong>{m.role==='model'?'Agente IA':'Você'}</strong>{m.role==='model'?<Resposta texto={m.text}/>:<p>{m.text}</p>}</div></article>)}{ocupado?<div className="thinking" role="status"><LoaderCircle size={17} className="spin"/> Consultando o agente e suas ferramentas…</div>:null}<div ref={fim}/></div>
   <div className="composer-wrap">{erro?<p className="error" role="alert">{erro}</p>:null}<form className="composer" onSubmit={submeter}><label className="sr-only" htmlFor="message">Sua mensagem</label><textarea id="message" maxLength={2000} value={entrada} onChange={e=>setEntrada(e.target.value)} placeholder="Pergunte alguma coisa…" disabled={ocupado} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void enviar()}}}/><div className="composer-bottom"><span>{status?.modelo??'Gemini'} </span><button type="submit" disabled={ocupado||!entrada.trim()} aria-label="Enviar mensagem">{ocupado?<LoaderCircle size={18} className="spin"/>:<ArrowUp size={20}/>}</button></div></form><p className="disclaimer">Respostas geradas por IA. Confira as fontes. <span>Enter para enviar · Shift + Enter para nova linha</span></p></div></section>
   {painelAberto?<aside className="inspector" aria-label="Contexto da consulta"><div className="inspector-title"><Radio size={17}/><strong>Contexto da resposta</strong><button aria-label="Fechar contexto" onClick={()=>setPainelAberto(false)}><X size={17}/></button></div><p className="inspector-intro">Transparência em cada consulta.</p><div className="tabs"><button className={aba==='atividade'?'active':''} onClick={()=>setAba('atividade')}>Atividade <span>{eventos.length}</span></button><button className={aba==='fontes'?'active':''} onClick={()=>setAba('fontes')}>Fontes <span>{fontes.length}</span></button></div><div className="inspector-content">{aba==='atividade'?(eventos.length?eventos.map((e,i)=><div className="event" key={i}><span className="event-check"><Check size={14}/></span><strong>{e.ferramenta}</strong><small>Executada via MCP</small><details><summary>Ver pedido e resultado</summary><pre>{JSON.stringify(e,null,2)}</pre></details></div>):<div className="empty-panel"><Workflow size={27}/><h3>{ocupado?'Consulta em andamento':'Tudo começa com uma pergunta'}</h3><p>{ocupado?'As ferramentas utilizadas aparecerão aqui ao concluir.':'As chamadas de ferramentas aparecem aqui depois de cada resposta.'}</p></div>):(fontes.length?fontes.map((f,i)=><details className="source" key={i} open><summary><FileText size={16}/>{f.fonte}</summary><small>Linhas {f.linha_inicio}–{f.linha_fim}</small><p>{f.texto}</p></details>):<div className="empty-panel"><BookOpen size={27}/><h3>Nenhuma fonte nesta consulta</h3><p>Pergunte sobre os documentos para ver os trechos recuperados pelo RAG.</p></div>)}</div><div className="pipeline"><span className="eyebrow">COMO AS PEÇAS SE CONECTAM</span><div><span>Interface</span><ChevronRight size={12}/><span>MCP</span><ChevronRight size={12}/><span>RAG</span></div><p>O modelo responde.<br/>Seus documentos dão o contexto.</p></div></aside>:null}</div>
  </main>{historicoAberto?<div className="modal-backdrop"><section className="profile-modal" role="dialog" aria-modal="true" aria-label="Conversas salvas"><button className="modal-close" onClick={()=>setHistoricoAberto(false)} aria-label="Fechar conversas"><X size={18}/></button><h2>Suas conversas</h2><div className="saved-chats mobile-chats">{conversas.map(c=><button key={c.id} disabled={ocupado} onClick={()=>void abrirConversa(c.id)}><MessageSquare size={14}/><span>{c.titulo}</span></button>)}{!conversas.length?<p>Nenhuma conversa salva ainda.</p>:null}</div></section></div>:null}{perfilAberto?<div className="modal-backdrop"><section className="profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button className="modal-close" aria-label="Fechar configurações" onClick={()=>setPerfilAberto(false)}><X size={18}/></button><img src="/robo.svg" alt=""/><h2 id="profile-title">Seu perfil</h2><p>Usuário de acesso: {conta.usuario}</p><form onSubmit={salvarPerfil}><label>Nome<input value={nome} onChange={e=>setNome(e.target.value)} required maxLength={60}/></label><h3>Alterar senha</h3><label>Senha atual<input type="password" autoComplete="current-password" value={senhaAtual} onChange={e=>setSenhaAtual(e.target.value)}/></label><label>Nova senha<input type="password" autoComplete="new-password" value={novaSenha} onChange={e=>setNovaSenha(e.target.value)} minLength={8} maxLength={128}/></label><small>Deixe os campos de senha vazios para alterar somente o nome.</small>{avisoPerfil?<p role="status">{avisoPerfil}</p>:null}<button className="primary" disabled={authOcupado}>Salvar configurações</button></form><button className="logout" onClick={()=>void sair().then(()=>setPerfilAberto(false)).catch(()=>setAvisoPerfil('Não foi possível sair.'))}><LogOut size={15}/> Sair da conta</button></section></div>:null}</div>
}
