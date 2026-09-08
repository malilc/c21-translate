"""Offline current-client build. No installed writes, game launch or network use."""
import argparse,ast,hashlib,json,pathlib,re,shutil,struct,subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--game-classes',type=pathlib.Path,required=True)
parser.add_argument('--out',type=pathlib.Path,required=True)
parser.add_argument('--prepare-only',action='store_true')
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
classes=args.game_classes;out=args.out
out.mkdir(parents=True,exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
decode=lambda s:re.sub(r'\\(\\|n|r|t|u001b)',lambda m:{'\\':'\\','n':'\n','r':'\r','t':'\t','u001b':'\x1b'}[m[1]],s)
legacy=(root/'tools/quest-pilot/build_payload.py').read_text(encoding='utf-8-sig')
tree=ast.parse(legacy)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='patch')
func=ast.get_source_segment(legacy,node).replace('c21thai/quest/QuestBridge','c21english/expanded/QuestBridge')
scope={'struct':struct,'hashlib':hashlib,'u2':lambda b,p:struct.unpack_from('>H',b,p)[0],'u4':lambda b,p:struct.unpack_from('>I',b,p)[0]}
exec(func,scope)
# Reuse original verified display getter scopes, excluding NPC overhead names.
exec(legacy[legacy.index("sentence='cosmic/"):legacy.index("npc='cosmic/")],scope)
spec=scope['spec'];approved=scope['approved'];counts=scope['expected_counts'];selected=scope['selected_by_class'];patch=scope['patch']
manifest=json.loads((root/'config/full-name-display-sites.json').read_text(encoding='utf-8-sig'))
allowed={'cosmic/robo/GeneralItemData','cosmic/robo/RoboParts','cosmic/robo/RoboPartsItem','cosmic/robo/GeneralItem','cosmic/robo/AttackData','cosmic/robo/AbstractItem','cosmic/robo/AbstractItemData','cosmic/robo/ColorStyle','cosmic/robo/CardData'}
for entry in manifest['Classes']:
    name=entry['Class'];sites=[s for s in entry['Sites'] if s['Owner'] in allowed]
    if not sites:continue
    assert sha((classes/(name+'.class')).read_bytes())==entry['SourceSha256']
    chosen=set()
    if name in spec:
        _,hits,_=patch(classes/(name+'.class'),spec[name])
        assert len(hits)==counts[name]
        chosen.update((h['method'],h['descriptor'],h['offset']) for h in hits)
    for site in sites:
        where=tuple(site[k] for k in ['Method','Descriptor','Offset']);assert where not in chosen;chosen.add(where)
        ref=tuple(site[k] for k in ['Owner','Name','ReturnDescriptor'])
        helper='getName' if site['Name']=='getName' else 'name'
        if site['Name']=='getName' and site['Owner'] in {'cosmic/robo/GeneralItem','cosmic/robo/RoboPartsItem','cosmic/robo/AbstractItem'}:helper='getItemName'
        spec.setdefault(name,{})[ref]=helper
    selected[name]=chosen;counts[name]=len(chosen);approved[name]=entry['SourceSha256']
assert 'cosmic/ui/RoboNameBalloon' not in spec
# MC display remains original, including previously known title/condition pairs.
effect_manifest=json.loads((root/'config/english-expanded/effect-display-sites.json').read_text(encoding='utf-8-sig'))
system_manifest=json.loads((root/'config/english-expanded/system-effect-display-sites.json').read_text(encoding='utf-8-sig'))
for entry in effect_manifest['Classes']+system_manifest['Classes']:
    name=entry['Class']
    assert sha((classes/(name+'.class')).read_bytes())==entry['SourceSha256']
    chosen=set(selected.get(name,()))
    if name in spec and name not in selected:
        _,hits,_=patch(classes/(name+'.class'),spec[name])
        chosen.update((h['method'],h['descriptor'],h['offset']) for h in hits)
    for site in entry['Sites']:
        where=tuple(site[k] for k in ['Method','Descriptor','Offset'])
        assert where not in chosen
        chosen.add(where)
        ref=tuple(site[k] for k in ['Owner','Name','ReturnDescriptor'])
        spec.setdefault(name,{})[ref]=site.get('Helper','itemMessage')
    selected[name]=chosen;counts[name]=len(chosen);approved[name]=entry['SourceSha256']

audit=[]
for name,fields in spec.items():
    assert sha((classes/(name+'.class')).read_bytes())==approved[name]
    data,hits,pin=patch(classes/(name+'.class'),fields,selected.get(name))
    assert len(hits)==counts[name]
    p=out/'classes'/(name+'.class');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    audit.append({'name':name,'sourceSha256':pin,'targetSha256':sha(data),'hits':hits})
(out/'patch-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print('PASS pinned display classes',len(audit),'sites',sum(len(a['hits']) for a in audit),'NPC overhead untouched')
if args.prepare_only:raise SystemExit(0)
catalogs=[root/'config/full-part-name-english.json',root/'config/full-item-name-english.json']
catalogs += [root/'config/english-expanded'/n for n in ['extra-ui.json','part-descriptions.json','item-descriptions.json','quests.json','quest-dialogue.json','quest-dialogue-continuation.json','robot-descriptions.json','choices.json','locations.json','story-a.json','story-b.json','story-c.json','effects.json']]
resolutions={e['source']:e for e in json.loads((root/'config/english-expanded/merge-resolutions.json').read_text(encoding='utf-8-sig'))}
mapping={};provenance={};conflicts=[];counts=[]
for catalog in catalogs:
    data=json.loads(catalog.read_text(encoding='utf-8-sig'));entries=data if isinstance(data,list) else data['Entries'];seen=set()
    for e in entries:
        if e.get('DisplayStatus','').startswith('catalog-only'):continue
        # Trap names belong only to the guarded system-message bridge.
        if catalog.name=='effects.json' and e.get('Table')=='traptable':continue
        source=decode(e['SourceEscaped']);target=decode(e['TargetEscaped'])
        assert sha(source.encode('utf-8'))==e['SourceUtf8Sha256'],catalog.name
        assert not re.search('[\u0e00-\u0e7f]',target),'Unexpected Thai in English target'
        assert re.findall('\x1b.',source)==re.findall('\x1b.',target),(catalog.name,'color controls')
        if source in resolutions:
            resolution=resolutions[source]
            assert target in resolution['acceptedAlternatives'],('Unreviewed conflict alternative',catalog.name,source,target)
            target=resolution['target']
        seen.add(source)
        if source in mapping and mapping[source]!=target:
            conflicts.append({'source':source,'kept':mapping[source],'candidate':target,'from':catalog.name,'previous':provenance[source]})
            continue
        mapping[source]=target;provenance[source]=catalog.name
    counts.append({'catalog':catalog.name,'uniqueSources':len(seen)})
(out/'merge-conflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2),encoding='utf-8')
if conflicts:raise RuntimeError('Conflicts need explicit review; see merge-conflicts.json')
generated=out/'generated/c21english/expanded';generated.mkdir(parents=True)
literal=lambda s:json.dumps(s,ensure_ascii=True).replace('\\u001b','\\033')
pairs=sorted(mapping.items());chunks=[]
for start in range(0,len(pairs),100):
    name='Catalog%03d'%(start//100);chunks.append(name)
    body='\n'.join('        map.put('+literal(s)+','+literal(t)+');' for s,t in pairs[start:start+100])
    (generated/(name+'.java')).write_text('package c21english.expanded;\nfinal class '+name+' { static void add(java.util.Map<String,String> map) {\n'+body+'\n} }\n',encoding='ascii')
(generated/'EnglishCatalog.java').write_text('package c21english.expanded;\nfinal class EnglishCatalog { static java.util.Map<String,String> create() {\njava.util.Map<String,String> m=new java.util.HashMap<String,String>();\n'+'\n'.join(n+'.add(m);' for n in chunks)+'\nreturn java.util.Collections.unmodifiableMap(m); } }\n',encoding='ascii')
(out/'catalog-audit.json').write_text(json.dumps({'mappings':len(mapping),'catalogs':counts,'catalogClasses':len(chunks)},indent=2),encoding='utf-8')
# Probe fixture is separate from shipped class data.
with (out/'expected-catalog.bin').open('wb') as f:
    f.write(struct.pack('>I',len(pairs)))
    for pair in pairs:
        for value in pair:
            b=value.encode('utf-8');f.write(struct.pack('>I',len(b)));f.write(b)
print('PASS exact English mappings',len(mapping),'generated catalog classes',len(chunks))
