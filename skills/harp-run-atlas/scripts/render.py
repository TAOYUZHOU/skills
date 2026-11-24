"""Render annotated HARP runs as a self-contained, offline HTML atlas."""
import argparse
import json
from pathlib import Path


def validate_graph(nodes, parents):
    seen = set()
    visiting = set()

    def visit(key):
        if key in visiting:
            raise ValueError(f"Cycle through {key}")
        if key not in nodes:
            raise ValueError(f"Unknown or out-of-scope parent {key}")
        if key not in seen:
            visiting.add(key)
            for parent in parents(nodes[key]):
                visit(parent)
            visiting.remove(key)
            seen.add(key)

    for key in nodes:
        visit(key)


def index(rows, fields):
    result = {}
    if not isinstance(rows, list):
        raise ValueError("Expected a list of nodes")
    for row in rows:
        if not isinstance(row, dict) or any(not isinstance(row.get(f), str) for f in fields):
            raise ValueError(f"Expected string fields {fields}")
        key = row["id"]
        if not key.strip() or key in result:
            raise ValueError(f"Empty or repeated ID: {key}")
        result[key] = row
    return result


def validate(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError("Expected a nonempty case list")
    for case in cases:
        if any(not isinstance(case.get(f), str) for f in ("title", "summary", "source")):
            raise ValueError("Missing case title, summary or source")
        plans = index(case["plans"], ("id", "title", "summary"))
        known = set(plans)
        if not plans:
            raise ValueError("Expected plans")
        for plan in plans.values():
            deps = plan["depends_on"]
            if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps) or len(set(deps)) != len(deps):
                raise ValueError("Expected distinct dependency IDs")
            attempts = index(plan["attempts"], ("id", "parent", "title", "summary", "status", "evidence"))
            if known.intersection(attempts):
                raise ValueError("Ambiguous node identity")
            known.update(attempts)
            validate_graph(attempts, lambda a: [a["parent"]] if a["parent"] else [])
        validate_graph(plans, lambda p: p["depends_on"])


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HARP · Agent 运行图谱</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f5f1;color:#173c37;font:16px/1.65 system-ui,sans-serif}main{max-width:1420px;margin:auto;padding:30px clamp(12px,4vw,56px)}h1{margin:0;font-size:clamp(28px,4vw,46px)}h2{margin:4px 0}select,button{font:inherit;color:inherit;padding:5px;max-width:100%}article,aside{border-radius:12px;background:white;padding:18px;min-width:0}.layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,1fr);gap:12px}.viewport{overflow:auto;max-height:73vh;background:#181523;border-radius:8px}.map{position:relative;color:white}.map svg{position:absolute;inset:0;pointer-events:none}.map button{position:absolute;background:#393348;color:#e9e3f1;border:1px solid #766086;border-radius:7px;width:160px;height:52px;font-size:13px;overflow:hidden;line-height:1.25}.map button:hover,.map button:focus-visible{outline:3px solid #faf0ff}.map button.selected{border:3px solid white}.map button.up{border-color:#72dbff}.map button.down{border-color:#ffbd72}.map button.local{border-color:#d498fb}.map .muted{opacity:.45}path{fill:none;stroke-width:2}details{border-top:1px solid #cbd8d3;padding:8px 0}summary{cursor:pointer;font-weight:600}aside p,details p{white-space:pre-wrap;overflow-wrap:anywhere}small{color:#536960;overflow-wrap:anywhere}.legend{font-size:14px}aside{scroll-margin:12px}button.jump{font-size:13px;margin:2px}@media(max-width:850px){.layout{grid-template-columns:1fr}}.snapshot{position:absolute;left:20px;color:#d8caea;font:600 15px/1.5 system-ui;letter-spacing:.03em}</style>
<main><h1>HARP 运行图谱</h1><label>工作区 <select id="chooser"></select></label><h2 id="title"></h2><p id="summary"></p><p><small id="source"></small></p><div class="layout"><article><h2>计划与策略尝试</h2><p class="legend">从左向右读取。蓝线来自直接前置计划，橙线指向直接下游；虚线连到本计划的根尝试，紫线连接父子尝试。</p><button type="button" id="scaleMode">原尺寸</button> <span id="scaleLabel"></span><div class="viewport" id="viewport"><div id="extent" style="position:relative;overflow:hidden"><div class="map" id="map" style="transform-origin:top left"></div></div></div><a href="#detail">查看所选节点 ↓</a></article><aside id="detail"></aside></div></main>
<script type="application/json" id="data">DATA_HERE</script><script>
const cases=JSON.parse(document.getElementById('data').textContent), by=id=>document.getElementById(id);
function add(parent,tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;parent.append(e);return e}
function svg(tag,attrs,parent){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e}
cases.forEach((c,i)=>add(by('chooser'),'option',c.title).value=i);
let scene, overview=true;
function scaleMap(){
 if(!scene)return;
 const viewport=by('viewport'),map=by('map'),w=map.offsetWidth,h=map.offsetHeight;
 const ratio=overview?Math.min(1,viewport.clientWidth/w,window.innerHeight*.72/h):1;
 map.style.transform='scale('+ratio+')';by('extent').style.width=Math.ceil(w*ratio)+'px';by('extent').style.height=Math.ceil(h*ratio)+'px';
 by('scaleMode').textContent=overview?'原尺寸':'显示全图';by('scaleLabel').textContent=(overview?'全图':'原尺寸')+' · '+Math.round(ratio*100)+'%';
}
function locate(b){
 const v=by('viewport'),a=b.getBoundingClientRect(),r=v.getBoundingClientRect();
 if(a.left<r.left||a.right>r.left+v.clientWidth)v.scrollLeft+=(a.left+a.right-r.left*2-v.clientWidth)/2;
 if(a.top<r.top||a.bottom>r.top+v.clientHeight)v.scrollTop+=(a.top+a.bottom-r.top*2-v.clientHeight)/2;
}
by('scaleMode').onclick=()=>{overview=!overview;scaleMap();const b=by('map').querySelector('.selected');if(b)locate(b)};
window.addEventListener('resize',scaleMap);
function draw(){
 const c=cases[Number(by('chooser').value)],map=by('map');map.replaceChildren();
 for(const f of ['title','summary','source'])by(f).textContent=c[f];
 const plans=new Map(c.plans.map(p=>[p.id,p])),nodes=new Map(),edges=[],depths=new Map();
 function depth(p){if(!depths.has(p.id))depths.set(p.id,Math.max(-1,...p.depends_on.map(k=>depth(plans.get(k))))+1);return depths.get(p.id)}
 const maxDepth=Math.max(...c.plans.map(depth));let row=0,width=0;
 let lastSnapshot;
 const layer=svg('svg',{},map);
 function node(obj,owner,col,r){const x=20+col*196,y=20+r*69,b=add(map,'button',obj.title);b.style.left=x+'px';b.style.top=y+'px';b.title=obj.title;b.onclick=()=>select(obj.id);nodes.set(obj.id,{obj,owner,x,y,b});width=Math.max(width,x+180)}
 for(const p of c.plans){
  if(p.snapshot && p.snapshot!==lastSnapshot){
   const group=add(map,'strong',p.snapshot);group.className='snapshot';
   group.style.top=(row*69+10)+'px';row+=.5;lastSnapshot=p.snapshot;
  }
  const aMap=new Map(p.attempts.map(a=>[a.id,a])),levels=new Map();
  function tier(a){if(!levels.has(a.id))levels.set(a.id,a.parent?tier(aMap.get(a.parent))+1:0);return levels.get(a.id)}
  const counts=new Map();node(p,p,depth(p),row);
  for(const a of p.attempts){const d=tier(a),i=counts.get(d)||0;counts.set(d,i+1);node(a,p,maxDepth+1+d,row+i);edges.push({from:a.parent||p.id,to:a.id,type:a.parent?'tree':'root'})}
  for(const from of p.depends_on)edges.push({from,to:p.id,type:'dag'});
  row+=Math.max(1,...counts.values());
 }
 const height=row*69+20;Object.assign(map.style,{height:height+'px',width:width+'px'});layer.setAttribute('width',width);layer.setAttribute('height',height);
 for(const edge of edges){const a=nodes.get(edge.from),b=nodes.get(edge.to),x=a.x+160,y=a.y+26,u=b.x,v=b.y+26,m=(x+u)/2;
  edge.line=svg('path',{d:'M '+x+' '+y+' C '+m+' '+y+' '+m+' '+v+' '+u+' '+v,'stroke-dasharray':edge.type==='root'?'4 4':'none'},layer)}
 scene={plans,nodes,edges};overview=true;scaleMap();select(c.plans[0].id)
}
function select(id){
 const {plans,nodes,edges}=scene,{obj,owner}=nodes.get(id),up=owner.depends_on,down=Array.from(plans.values()).filter(p=>p.depends_on.includes(owner.id)).map(p=>p.id);
 for(const [key,n] of nodes){n.b.className=[key===id?'selected':'',up.includes(key)?'up':down.includes(key)?'down':n.owner===owner?'local':'muted'].join(' ');n.b.setAttribute('aria-pressed',key===id)}
 for(const e of edges){const color=e.type==='dag'?(e.to===owner.id?'#72dbff':e.from===owner.id?'#ffbd72':'#6b626e'):nodes.get(e.to).owner===owner?'#d498fb':'#6b626e';e.line.setAttribute('stroke',color)}
 locate(nodes.get(id).b);
 const box=by('detail');box.replaceChildren();add(box,'h2',obj.title);add(box,'small',obj.id);add(box,'p',obj.summary);
 function links(title,ids){if(ids.length){add(box,'strong',title);const group=add(box,'div');for(const key of ids){const b=add(group,'button',nodes.get(key).obj.title);b.className='jump';b.onclick=()=>select(key)}}}
 if(obj===owner){links('直接依赖',up);links('直接下游',down)}else{links('所属计划',[owner.id]);if(obj.parent)links('父尝试',[obj.parent])}
 add(box,'h3','策略尝试 · '+owner.attempts.length);
 for(const a of owner.attempts){const d=add(box,'details');d.open=a.id===id;add(d,'summary',a.title+' · '+a.status);add(d,'p',a.summary);const ev=add(d,'details');add(ev,'summary','原记录与证据');add(ev,'small',a.id);add(ev,'p',a.evidence)}
}
by('chooser').onchange=draw;draw()
</script></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cases = json.loads(args.input.read_text(encoding="utf-8"))
    validate(cases)
    payload = json.dumps(cases, ensure_ascii=False).replace("<", "\\u003c")
    args.output.write_text(PAGE.replace("DATA_HERE", payload), encoding="utf-8")


if __name__ == "__main__":
    main()
