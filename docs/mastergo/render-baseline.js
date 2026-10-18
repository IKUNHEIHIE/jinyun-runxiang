
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const px = v => typeof v==='number'?v+'px':v;
function paint(ref, styles){return styles[ref]?.value??[]}
function nodeHtml(n,styles,parentFlex=false,root=false){
 const l=n.layoutStyle??{},css={position:parentFlex?'relative':'absolute',width:px(l.width),height:px(l.height)};
 if(!parentFlex){css.left=px(root?0:(l.relativeX??0));css.top=px(root?0:(l.relativeY??0))}
 const values=paint(n.fill,styles),images=values.filter(x=>x?.url),colors=values.filter(x=>typeof x==='string');
 let bg=n._color??colors[0];
 if(n.type==='TEXT'){css.color=bg;bg=null;}
 if(bg){if(n.opacity!==undefined&&/^#[0-9A-Fa-f]{6}$/.test(bg)){const rgb=[1,3,5].map(i=>parseInt(bg.slice(i,i+2),16));bg='rgba('+rgb.join(',')+','+n.opacity+')'}css.background=bg;}
 if(images.length){css['background-image']=(colors.length?['linear-gradient('+colors[0]+','+colors[0]+')']:[]).concat(images.map(x=>'url("'+x.url+'")')).join(',');css['background-size']='cover';css['background-position']='center';if(n.opacity!==undefined&&!(n.children?.length))css.opacity=n.opacity;}
 if(n.borderRadius)css['border-radius']=n.borderRadius;
 if(n.strokeColor){css['border-color']=paint(n.strokeColor,styles).filter(x=>typeof x==='string')[0];css['border-width']=n.strokeWidth??'1px';css['border-style']='solid';}
 const effects=paint(n.effect,styles);for(const e of effects){const k=e.indexOf(':');if(k>0){const key=e.slice(0,k);const val=e.slice(k+1).replace(/;$/,'').trim();css[key]=css[key]?css[key]+','+val:val}}
 if(n.clipsContent||n.overflow==='hidden')css.overflow='hidden';
 const flex=n.flexContainerInfo;
 if(flex){css.display='flex';for(const [k,v] of Object.entries(flex)){const map={flexDirection:'flex-direction',justifyContent:'justify-content',alignItems:'align-items',gap:'gap',padding:'padding'};if(map[k])css[map[k]]=typeof v==='number'?px(v):v;}}
 let content='';
 if(n.type==='PATH'&&n.svgShortKey)content='@@SVG:'+n.svgShortKey+'@@';
 if(n.type==='TEXT'){
  const spans=n.text??[];const font=styles[spans[0]?.font]?.value??{};
  Object.assign(css,{'font-family':"'"+(font.family??'Noto Sans SC')+"',sans-serif",'font-size':px(font.size),'font-weight':font.weight??'400','line-height':font.lineHeight?px(Number(font.lineHeight)):undefined,'letter-spacing':font.letterSpacing==='auto'?'normal':font.letterSpacing,'text-align':n.textAlign??'left','white-space':n.textMode==='single-line'?'pre':'pre-wrap'});
  content=spans.map(t=>esc(t.text)).join('');
 }else content+=(n.children??[]).map(c=>nodeHtml(c,styles,!!flex)).join('');
 const style=Object.entries(css).filter(([,v])=>v!==undefined).map(([k,v])=>k+':'+v).join(';');
 return '<div data-node-id="'+esc(n.id)+'" data-name="'+esc(n.name)+'" style="'+esc(style)+'">'+content+'</div>';
}
function renderDesign(overview,sections){
 const styles={...(overview.rootMetadata?.styles??{})};for(const s of sections)Object.assign(styles,s.dsl.styles);
 let body='';
 for(const c of overview.splitContainers??[]){
 let css='position:absolute;left:'+c.x+'px;top:'+c.y+'px;width:'+c.width+'px;height:'+c.height+'px;';
 const vals=paint(c.fill,styles),img=vals.find(x=>x?.url);const bg=c.background??vals.find(x=>typeof x==='string');
 if(bg)css+='background:'+bg+';';
 if(img)css+='background-image:'+(bg?'linear-gradient('+bg+','+bg+'),':'')+'url('+img.url+');background-size:cover;';
 if(c.borderRadius)css+='border-radius:'+c.borderRadius+';';
 if(c.effect)css+=paint(c.effect,styles).join('');
 body+='<div data-node-id="'+c.id+'" style="'+esc(css)+'"></div>';
 }
 for(let i=0;i<sections.length;i++){const s=overview.sections[i];body+='<section data-section="'+i+'" style="position:absolute;left:'+s.x+'px;top:'+s.y+'px;width:'+s.width+'px;height:'+s.height+'px">'+sections[i].dsl.nodes.map(n=>nodeHtml(n,styles,false,true)).join('')+'</section>'}
 const root=Object.entries(overview.rootContainer).map(([k,v])=>k.replace(/[A-Z]/g,c=>'-'+c.toLowerCase())+':'+v).join(';');
 return '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(overview.rootMetadata.name)+'</title><style>*{box-sizing:border-box}html,body{margin:0}body{font-family:"Noto Sans SC",sans-serif}section{margin:0}</style></head><body><main data-design-root="'+esc(overview.rootMetadata.name)+'" style="'+esc(root)+'">'+body+'</main></body></html>';
}
;
export { renderDesign };

