"""Build only offline pilot resources; no installed-game writes or execution."""
import hashlib, json, pathlib, re, struct, sys

catalog, classes, out = map(pathlib.Path, sys.argv[1:4])
out.mkdir(parents=True, exist_ok=True)
u2 = lambda b, p: struct.unpack_from('>H', b, p)[0]
u4 = lambda b, p: struct.unpack_from('>I', b, p)[0]
def decode(s):
    return re.sub(r'\\(\\|n|r|t|u001b)', lambda m: {'\\':'\\','n':'\n','r':'\r','t':'\t','u001b':'\x1b'}[m[1]], s)

mapping = {}
for e in json.loads(catalog.read_text(encoding='utf-8-sig'))['Entries']:
    source, target = decode(e['SourceEscaped']), decode(e['TargetEscaped'])
    assert hashlib.sha256(source.encode()).hexdigest().upper() == e['SourceUtf8Sha256']
    assert source not in mapping or mapping[source] == target, 'ambiguous translation'
    mapping[source] = target
with (out/'quest-text.bin').open('wb') as f:
    f.write(struct.pack('>I',len(mapping)))
    for pair in sorted(mapping.items()):
        for value in pair:
            data=value.encode('utf-8'); f.write(struct.pack('>I',len(data))); f.write(data)

npc_catalog=pathlib.Path(__file__).resolve().parents[2]/'config/full-npc-name-english.json'
npc_names={}
for e in json.loads(npc_catalog.read_text(encoding='utf-8'))['Entries']:
    source,target=decode(e['SourceEscaped']),decode(e['TargetEscaped'])
    assert hashlib.sha256(source.encode()).hexdigest().upper()==e['SourceUtf8Sha256']
    assert source not in npc_names or npc_names[source]==target, 'Ambiguous NPC name'
    assert not re.search('[\u0e00-\u0e7f\u3040-\u30ff\u3400-\u9fff]',target)
    npc_names[source]=target
with (out/'npc-names.bin').open('wb') as f:
    f.write(struct.pack('>I',len(npc_names)))
    for pair in sorted(npc_names.items()):
        for value in pair:
            data=value.encode('utf-8');f.write(struct.pack('>I',len(data)));f.write(data)

def patch(path, fields, selected_sites=None):
    original=path.read_bytes(); b=bytearray(original)
    assert b[:4] == b'\xca\xfe\xba\xbe'
    count=u2(b,8); cp=[None]*count; p=10; i=1
    while i<count:
        tag=b[p]; p+=1
        if tag==1:
            n=u2(b,p); p+=2; cp[i]=(tag,bytes(b[p:p+n]).decode('utf-8',errors='replace')); p+=n
        elif tag in (7,8,16): cp[i]=(tag,u2(b,p)); p+=2
        elif tag in (9,10,11,12,18): cp[i]=(tag,u2(b,p),u2(b,p+2)); p+=4
        elif tag in (3,4): p+=4
        elif tag in (5,6): p+=8; i+=1
        elif tag==15: p+=3
        else: raise ValueError(('constant tag',tag))
        i+=1
    end=p; extra=bytearray(); nextidx=count
    def add(data):
        nonlocal nextidx
        idx=nextidx; nextidx+=1; extra.extend(data); return idx
    def utf(s):
        raw=s.encode(); return add(b'\x01'+struct.pack('>H',len(raw))+raw)
    bridge=add(b'\x07'+struct.pack('>H',utf('c21thai/quest/QuestBridge')))
    replacements={}
    for idx,item in enumerate(cp):
        if not item or item[0] not in (9,10): continue
        owner=cp[cp[item[1]][1]][1]; nt=cp[item[2]]
        name,desc=cp[nt[1]][1],cp[nt[2]][1]
        if (owner,name,desc) not in fields: continue
        method=fields[(owner,name,desc)]
        if item[0]==10: assert desc.startswith('()') or (owner,name,desc)==('cosmic/sys/QuestData$QuestTalkData','getStory','(I)Ljava/lang/String;'), 'Only verified display getters'
        return_desc=desc[2:] if item[0]==10 else desc
        helper_desc='(Ljava/lang/Object;I)Ljava/lang/String;' if desc=='(I)Ljava/lang/String;' else '(Ljava/lang/Object;)'+return_desc
        ni=utf(method); di=utf(helper_desc)
        nti=add(b'\x0c'+struct.pack('>HH',ni,di))
        replacements[idx]=(0xb6 if item[0]==10 else 0xb4,add(b'\x0a'+struct.pack('>HH',bridge,nti)))
    assert replacements, 'no requested fields'
    p=end+6; n=u2(b,p); p+=2+2*n
    hits=[]
    def attributes(pos,scan=False,method='',descriptor=''):
        n=u2(b,pos); pos+=2
        for _ in range(n):
            name=cp[u2(b,pos)][1]; size=u4(b,pos+2); start=pos+6
            if scan and name=='Code':
                length=u4(b,start+4); base=start+8; code=b[base:base+length]; off=0
                while off<length:
                    op=code[off]; width=1
                    if op in (0xaa,0xab):
                        q=(off+4)&~3
                        if op==0xaa:
                            lo,hi=struct.unpack_from('>ii',code,q+4); width=q+12+4*(hi-lo+1)-off
                        else: width=q+8+8*u4(code,q+4)-off
                    elif op==0xc4: width=6 if code[off+1]==0x84 else 4
                    elif op in (0xb9,0xba,0xc8,0xc9): width=5
                    elif op==0xc5: width=4
                    elif op in (0x11,0x13,0x14,0x84,0xbb,0xbd,0xc0,0xc1) or 0x99<=op<=0xa8 or 0xb2<=op<=0xb8 or op in (0xc6,0xc7): width=3
                    elif op in (0x10,0x12,0xa9,0xbc) or 0x15<=op<=0x19 or 0x36<=op<=0x3a: width=2
                    if op in (0xb4,0xb6) and u2(code,off+1) in replacements and method!='imagePanelSetting':
                        site=(method,descriptor,off)
                        if selected_sites is not None and site not in selected_sites:
                            off+=width
                            continue
                        expected_op,replacement=replacements[u2(code,off+1)]
                        assert op==expected_op
                        b[base+off:base+off+3]=b'\xb8'+struct.pack('>H',replacement)
                        hits.append({'method':method,'descriptor':descriptor,'offset':off})
                    assert width>0 and off+width<=length
                    off+=width
            pos=start+size
        return pos
    for is_method in (False,True):
        n=u2(b,p); p+=2
        for _ in range(n):
            method=cp[u2(b,p+2)][1]; descriptor=cp[u2(b,p+4)][1]; p+=6; p=attributes(p,is_method,method,descriptor)
    assert hits
    if selected_sites is not None:
        assert {(h['method'],h['descriptor'],h['offset']) for h in hits} == selected_sites, 'Missing or duplicate approved site'
    result=bytes(b[:8])+struct.pack('>H',nextidx)+bytes(b[10:end])+bytes(extra)+bytes(b[end:])
    return result,hits,hashlib.sha256(original).hexdigest().upper()

sentence='cosmic/sys/TalkData$TalkSentenceData'
story='cosmic/sys/QuestData$QuestStoryData'
spec={
 'cosmic/ui/TalkPanel':{(sentence,'message','Ljava/lang/String;'):'message',(sentence,'switchword','[Ljava/lang/String;'):'choices'},
 'cosmic/ui/root/QuestStoryPanel':{
  (story,'name','Ljava/lang/String;'):'name',
  ('cosmic/sys/QuestData$QuestTalkData','getRobo','()Ljava/lang/String;'):'questRobo',
  ('cosmic/sys/QuestData$QuestTalkData','getRoom','()Ljava/lang/String;'):'questRoom',
  ('cosmic/sys/QuestData$QuestTalkData','getArea','()Ljava/lang/String;'):'questArea',
  ('cosmic/sys/QuestData$QuestTalkData','getStory','(I)Ljava/lang/String;'):'questStory'},
 'cosmic/ui/root/QuestStoryPanel$StoryListCellRenderer':{
  (story,'name','Ljava/lang/String;'):'name',
  ('cosmic/sys/QuestData$QuestTalkData','getRobo','()Ljava/lang/String;'):'questRobo',
  ('cosmic/sys/QuestData$QuestTalkData','getRoom','()Ljava/lang/String;'):'questRoom',
  ('cosmic/sys/QuestData$QuestTalkData','getArea','()Ljava/lang/String;'):'questArea'},
 'cosmic/ui/custom/GuildGaragePanel':{
  ('cosmic/setting/GuildBoost','name','Ljava/lang/String;'):'name',
  ('cosmic/setting/GuildBoost','comment','Ljava/lang/String;'):'comment',
  ('cosmic/setting/GuildBoost','getName','()Ljava/lang/String;'):'name'},
 'cosmic/ui/custom/PartsUpgradePanel':{
  ('cosmic/robo/UpgradeRecipeData','name','Ljava/lang/String;'):'name',
  ('cosmic/robo/UpgradeRecipeData','comment','Ljava/lang/String;'):'comment'},
 'cosmic/ui/help/RoboPartsComment':{
  ('cosmic/robo/UpgradeRecipeData','name','Ljava/lang/String;'):'name',
  ('cosmic/sys/RaidPartsData','info','Ljava/lang/String;'):'info',
  ('cosmic/robo/RoboParts','getComment','()Ljava/lang/String;'):'getComment'},
 'cosmic/ui/root/StatusBigPanel':{
  ('cosmic/setting/PlayerRank','getName','()Ljava/lang/String;'):'name',
  ('cosmic/robo/UserRoboData','getComment','()Ljava/lang/String;'):'getComment'},
 'cosmic/ui/root/StatusSmallPanel':{('cosmic/setting/PlayerRank','getName','()Ljava/lang/String;'):'name'},
 'cosmic/ui/custom/DepartItemBuyPanel':{('cosmic/robo/GeneralItemData','comment','Ljava/lang/String;'):'comment'},
 'cosmic/ui/custom/ItemBuySellPanel':{('cosmic/robo/GeneralItemData','comment','Ljava/lang/String;'):'comment'},
 'cosmic/ui/custom/GachaPanel$PrizeCellRenderer':{
  ('cosmic/robo/GeneralItemData','comment','Ljava/lang/String;'):'comment',
  ('cosmic/robo/RoboParts','comment','Ljava/lang/String;'):'comment',
  ('cosmic/sys/GachaData$RoboPrize','robocomment','Ljava/lang/String;'):'robocomment',
  ('cosmic/sys/GachaData$RoboPrize','robohelp','Ljava/lang/String;'):'robohelp'},
 'cosmic/ui/custom/GachaPanel$PrizeInfoCellRender':{
  ('cosmic/robo/GeneralItemData','comment','Ljava/lang/String;'):'comment',
  ('cosmic/robo/RoboParts','comment','Ljava/lang/String;'):'comment'},
 'cosmic/ui/help/ItemComment':{('cosmic/robo/GeneralItemData','comment','Ljava/lang/String;'):'comment'},
 'cosmic/ui/custom/AbstractRoboPanel':{('cosmic/robo/UserRoboData','getComment','()Ljava/lang/String;'):'getComment'},
 'cosmic/ui/custom/RoboMake2Panel':{('cosmic/robo/UserRoboData','getComment','()Ljava/lang/String;'):'getComment'},
 'cosmic/ui/custom/RoboMake3Panel':{('cosmic/robo/UserRoboData','getComment','()Ljava/lang/String;'):'getComment'},
 'cosmic/ui/custom/RoboPaint2Panel':{('cosmic/robo/UserRoboData','getComment','()Ljava/lang/String;'):'getComment'},
}
audit=[]; pins=[]
approved={
 'cosmic/ui/TalkPanel':'201F29A0B2B84A131FA88A56424BFFCEAEBA54B0AAC6F5D8B763B237B8AA5C2C',
 'cosmic/ui/root/QuestStoryPanel':'7AA28C4297207D98DC5159FBAC8277ED09E103C21B879DC2BCCBE554FBC47172',
 'cosmic/ui/root/QuestStoryPanel$StoryListCellRenderer':'B7CD9CE9B1166EA2F856DC04A243B451E2721E8980329E326CE41B9CC78EB884',
 'cosmic/ui/custom/GuildGaragePanel':'33696BFB0F45567A0EBEC0359150AF9A1E26F88E53D0F0AD21D6A27DB1E380AC',
 'cosmic/ui/custom/PartsUpgradePanel':'EF31B2A3D200F48434477A1383954088432D7C7F5046684F44B3DC717817636C',
 'cosmic/ui/help/RoboPartsComment':'3E1974C335D8E280482E048856DFBD58292796C50AFD059E7B840868041CEC18',
 'cosmic/ui/root/StatusBigPanel':'70F6D85F571984E006DDC34CFAE05081AD69C51CE37EE850B44E1E67BCD02CFC',
 'cosmic/ui/root/StatusSmallPanel':'050B88D21F243F064D20B9C3BECF87352104D2C0FC0A73A768D3FF74E23A211B',
 'cosmic/ui/custom/DepartItemBuyPanel':'DE8A4C1F3D785513E7BC2867B374672058EB18E449085A77BE70DBC1FCACC7D5',
 'cosmic/ui/custom/ItemBuySellPanel':'4C6720A32ED5CA576B5D9008D00DF6F93028F7F675A2768F375846D9D04AA7EB',
 'cosmic/ui/custom/GachaPanel$PrizeCellRenderer':'CEE0B64B01061602BF613F86D2AFADB59275579E3B0360624D6A4BD3F4A0DEDA',
 'cosmic/ui/custom/GachaPanel$PrizeInfoCellRender':'56661827482B099DCB3DF28AE1C4900F09F3CDD975A80F8F6150AAD1685D291B',
 'cosmic/ui/help/ItemComment':'8C4E7E0A3AACD1C559B1B968D1DE226FF7845583BBAF19AA77D4DD1B94B13C55',
 'cosmic/ui/custom/AbstractRoboPanel':'55986574529F1D83BC6A768A7B332366C225216CD5C04D7BB45852C53942E765',
 'cosmic/ui/custom/RoboMake2Panel':'8588142194FA54408ABE01D9E025986DEAD585084AEFAADE6B53CA6A1BF3B974',
 'cosmic/ui/custom/RoboMake3Panel':'68C72C93555E1E903FD4FE91CE985E6BD74FCB19644DB5A4C3E1D65B4DBC37FC',
 'cosmic/ui/custom/RoboPaint2Panel':'EC16A582CE51713B0B1A3821695DE6F0D8F82EE98CB0F722539D255A7A619C7B',
}
expected_counts=dict(zip(spec,(4,5,5,5,3,10,2,1,1,1,4,2,3,1,1,1,2)))
selected_by_class={}
# The tracked quest HUD has its own display reads, separate from the quest list.
hud='cosmic/ui/StagePanel$14'
spec[hud]={
 (story,'name','Ljava/lang/String;'):'name',
 ('cosmic/sys/QuestData$QuestTalkData','getRoom','()Ljava/lang/String;'):'questRoom',
 ('cosmic/sys/QuestData$QuestTalkData','getArea','()Ljava/lang/String;'):'questArea',
 ('cosmic/sys/QuestData$QuestTalkData','getRobo','()Ljava/lang/String;'):'questRobo'}
approved[hud]='736ADB1C34FADAD9C84AF7CE0D3596AB79C0233FE7B5877D75011EE238A5288F'
expected_counts[hud]=4
selected_by_class[hud]={('run','()V',offset) for offset in (40,60,75,95)}
npc='cosmic/ui/RoboNameBalloon'
spec[npc]={('cosmic/stage/SimpleRoboData','name','Ljava/lang/String;'):'npcOverheadName'}
approved[npc]='3FAEE47640AD5EA07DBA28304BBD825D00AEA07592B4E17F8F3D976BA26BFECF'
expected_counts[npc]=1
selected_by_class[npc]={('<init>','(Lcosmic/stage/view/RoboViewModel;)V',116)}
if len(sys.argv)>4:
    display_manifest=json.loads(pathlib.Path(sys.argv[4]).read_text(encoding='utf-8-sig'))
    for entry in display_manifest['Classes']:
        name=entry['Class']; source=classes/(name+'.class')
        assert hashlib.sha256(source.read_bytes()).hexdigest().upper()==entry['SourceSha256'], 'Unsupported name display class'
        selected=set()
        if name in spec:
            _,old_hits,_=patch(source,spec[name])
            assert len(old_hits)==expected_counts[name]
            selected.update((h['method'],h['descriptor'],h['offset']) for h in old_hits)
        for site in entry['Sites']:
            assert site['Owner'] not in ('cosmic/robo/UserRoboData','cosmic/stage/SimpleRoboData') and site['Name'] != 'getRoboName', 'Player-controlled robot names must remain untouched'
            key=(site['Method'],site['Descriptor'],site['Offset'])
            assert key not in selected, 'Duplicate display hook'
            selected.add(key)
            ref=tuple(site[k] for k in ('Owner','Name','ReturnDescriptor'))
            helper='getName' if site['Name']=='getName' else 'name'
            if site['Name']=='getName' and site['Owner'] in ('cosmic/robo/GeneralItem','cosmic/robo/RoboPartsItem','cosmic/robo/AbstractItem'):
                helper='getItemName'
            assert ref[1:] in (('name','Ljava/lang/String;'),('getName','()Ljava/lang/String;'))
            spec.setdefault(name,{})[ref]=helper
        selected_by_class[name]=selected
        expected_counts[name]=len(selected)
        if name in approved: assert approved[name]==entry['SourceSha256']
        approved[name]=entry['SourceSha256']
if len(sys.argv)>5:
    mc_manifest=json.loads(pathlib.Path(sys.argv[5]).read_text(encoding='utf-8-sig'))
    for entry in mc_manifest['Classes']:
        name=entry['Class']; source=classes/(name+'.class')
        assert hashlib.sha256(source.read_bytes()).hexdigest().upper()==entry['SourceSha256'], 'Unsupported MC display class'
        selected=selected_by_class.setdefault(name,set())
        for site in entry['Sites']:
            ref=tuple(site[k] for k in ('Owner','Name','ReturnDescriptor'))
            assert ref in (('cosmic/sys/MissionInfo','name','Ljava/lang/String;'),('cosmic/sys/MissionInfo','qualificationdesc','Ljava/lang/String;'))
            assert site['Helper']=={'name':'missionName','qualificationdesc':'missionConditions'}[site['Name']]
            key=(site['Method'],site['Descriptor'],site['Offset'])
            assert key not in selected, 'Duplicate MC display hook'
            selected.add(key)
            spec.setdefault(name,{})[ref]=site['Helper']
        expected_counts[name]=len(selected)
        if name in approved: assert approved[name]==entry['SourceSha256']
        approved[name]=entry['SourceSha256']
for name,fields in spec.items():
    assert hashlib.sha256((classes/(name+'.class')).read_bytes()).hexdigest().upper()==approved[name], 'Unsupported source class'
    data,hits,sourcehash=patch(classes/(name+'.class'),fields,selected_by_class.get(name))
    assert len(hits)==expected_counts[name],(name,len(hits),expected_counts[name])
    if name=='cosmic/ui/root/QuestStoryPanel':
        assert {(h['method'],h['descriptor'],h['offset']) for h in hits} == {
            ('setShowStory','(Lcosmic/robo/UserCommandoData;)V',offset)
            for offset in (117,134,153,166,186)}, 'Quest detail display scope changed'
    if name=='cosmic/ui/root/QuestStoryPanel$StoryListCellRenderer':
        assert {(h['method'],h['descriptor'],h['offset']) for h in hits} == {
            ('getListCellRendererFigure','(Lkotori/kwt/ListPanel;Ljava/lang/Object;II)Lkotori/kwt/Figure;',offset)
            for offset in (39,63,76,89,121)}, 'Quest list display scope changed'
    target=out/'patched'/(name+'.class'); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
    pins.append(name+'='+sourcehash)
    audit.append(dict(name=name,sourceSha256=sourcehash,targetSha256=hashlib.sha256(data).hexdigest().upper(),hits=hits))
(out/'class-pins.properties').write_text('\n'.join(pins)+'\n',encoding='ascii')
(out/'patch-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('PASS: exact catalog mappings',len(mapping),'class patches',[(x['name'],len(x['hits'])) for x in audit])
