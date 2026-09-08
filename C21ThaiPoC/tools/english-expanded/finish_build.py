"""Compile, verify and package an offline output of build_expanded.py."""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys,zipfile
p=argparse.ArgumentParser()
for n in ['work','game-classes','java','javac','original-program','key-file','final-resources-zip','output-zip']:p.add_argument('--'+n,type=pathlib.Path,required=True)
a=p.parse_args();w=a.work;root=pathlib.Path(__file__).resolve().parents[2];tool=root/'tools/english-expanded'
assert a.original_program.resolve()!= (w/'programs/c21.kar').resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def run(args,name):
    r=subprocess.run([str(v) for v in args],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (w/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    print(r.stdout.strip())
    if r.returncode:raise RuntimeError(name+' failed; see local log')
sources=list((w/'generated').rglob('*.java'))+[tool/'QuestBridge.java',root/'tools/english-pilot/AuraBridge.java',tool/'ExpandedProbe.java',tool/'PatchEnglishProgram.java',tool/'CompactResource.java',tool/'SystemEffectBridge.java',tool/'SystemEffectProbe.java']
run([sys.executable,'-X','utf8',tool/'audit_story.py'],'story-coverage')
argfile=w/'javac.args'
argfile.write_text('\n'.join('"'+str(x).replace('\\','/')+'"' for x in sources)+'\n',encoding='utf-8')
run([a.javac,'-encoding','UTF-8','-source','6','-target','6','-cp',a.game_classes,'-d',w/'classes','@'+str(argfile)],'compile')
audit=json.loads((w/'patch-audit.json').read_text());assert all(x['name']!='cosmic/ui/RoboNameBalloon' for x in audit)
(w/'class-names.txt').write_text('\n'.join(x['name'] for x in audit)+'\n',encoding='ascii')
run([a.java,'-Xverify:all','-Djava.awt.headless=true','-cp',str(w/'classes')+';'+str(a.game_classes),'ExpandedProbe',w/'expected-catalog.bin',w/'class-names.txt'],'probe')
run([a.java,'-Xverify:all','-Djava.awt.headless=true','-cp',str(w/'classes')+';'+str(a.game_classes),'SystemEffectProbe'],'system-effect-probe')
payload={('/'+x['name']+'.class'):(x['sourceSha256'],w/'classes'/(x['name']+'.class')) for x in audit}
for f in (w/'classes/c21english').rglob('*.class'):payload['/'+f.relative_to(w/'classes').as_posix()]=('-',f)
assert len(payload)>len(audit)
assert not any('Probe' in name for name in payload),'Test classes must never ship'
assert '/cosmic/ui/custom/MissionInfoListPanel$CellRenderer.class' not in payload
for entry in audit:
    if entry['name']=='cosmic/ui/custom/MissionSelectPanel':
        assert all(hit['method']=='getDropNameString' for hit in entry['hits']), 'MC title and summary must remain original'
assert not any('MissionBridge' in name for name in payload), 'MC helper must not ship'
manifest=w/'program-payload.tsv';manifest.write_text('\n'.join('\t'.join([n,before,sha(f),str(f)]) for n,(before,f) in sorted(payload.items()))+'\n',encoding='utf-8')
(w/'programs').mkdir();candidate=w/'programs/c21.kar';shutil.copy2(a.original_program,candidate)
key=a.key_file.read_text(encoding='utf-8-sig').strip();assert key and '\n' not in key
request=w/'program.private-request';request.write_text('\n'.join([str(a.original_program),str(candidate),key,str(manifest)])+'\n',encoding='utf-8')
run([a.java,'-Xmx512m','-cp',str(w/'classes')+';'+str(a.game_classes),'PatchEnglishProgram',request],'archive-verify')
catalog=json.loads((w/'catalog-audit.json').read_text())
readme='''C21 English Expanded Final — CyberStep 1.509.0
เปิดเกมตามปกติ ไม่ต้องใช้ BAT หรือ Java Agent

ติดตั้ง
1. ปิดเกมและตัวอัปเดต
2. สำรอง programs/c21.kar, resources/etc.kar และ resources/kwt.kar เดิมไว้ต่างหาก
   อย่าทับสำรองญี่ปุ่นเดิมด้วยไฟล์ม็อด หากลง AURA Pilot อยู่ ให้เก็บสำรองก่อนลง Pilot ไว้ด้วย
3. คัดลอกโฟลเดอร์ programs และ resources ใน ZIP เข้าโฟลเดอร์เกม
4. เปิดเกมตามปกติ ไม่ใช้ Start-C21ThaiFull*.bat

ขอบเขต
รวม UI อังกฤษ Final และขยายข้อความชิ้นส่วน ไอเทม เควสต์ บัฟกิลด์ และอัปเกรดที่มีในแค็ตตาล็อก
รวมบทสนทนาเนื้อเรื่องจากรายการ story-a, story-b และ story-c
ชื่อ MC และเงื่อนไขคงต้นฉบับ
สถานะสมาชิก: O พื้นที่เดียวกัน / o ออนไลน์ / x ออฟไลน์ (เหมือนแพ็กเดิม)
คงข้อความรูเล็ต Arena 10 แบบ และป้ายยศ/อัปเกรดที่ย่อไว้
เพิ่มชื่อเอฟเฟกต์/กับดัก 34 ชื่อ เฉพาะข้อความระบบรับผล/ฟื้นฟู/สนับสนุนที่ตรงรูปแบบ
บทนำ MC และข้อความระบบรูปแบบอื่นยังคงเดิม
ชื่อ NPC/ภาพต้นฉบับ/ชื่อที่ผู้เล่นตั้งคงเดิม ไม่เปลี่ยนข้อมูลตัวเลขหรือค่าชิ้นส่วน
ตัวอักษรที่เป็นคำใบ้หรือคำตอบของปริศนาคงเดิม เพื่อไม่ให้วิธีแก้ปริศนาเปลี่ยน
คำแปลเกิดเฉพาะตอนแสดงผล ข้อความที่ไม่มีในแค็ตตาล็อกยังเป็นญี่ปุ่น
เนื้อเรื่องและบทสนทนาทั้งเกมยังไม่ครบ แพ็กนี้ไม่ได้อ้างว่าแปลทุกข้อความ 100%
ไม่อ่านหรือแก้ cache และไม่เปลี่ยนมาโครหรือไฟล์บัญชี

การตรวจ
ผู้ใช้ยืนยันรุ่น 2 ใช้งานได้ แพ็ก Final ผ่านการตรวจออฟไลน์แล้ว แต่ยังรอลองหน้าจอจริง
ลองชี้ชิ้นส่วน/ไอเทม เปิดร้านค้า รายการเควสต์ และกล่องติดตามเควสต์

ถอน/อัปเดต
ปิดเกมแล้วคืนสามไฟล์จากสำรอง หากต้องการคง UI อังกฤษ ให้คืนเฉพาะ programs/c21.kar ต้นฉบับ
หลังเกมอัปเดต ห้ามทับโปรแกรมรุ่นใหม่ด้วยแพ็กนี้ ต้องสร้างให้ตรงรุ่นใหม่ก่อน
ไม่ต้องใช้ LE เพื่อแสดงอังกฤษ; แพ็กนี้ไม่ได้แก้ปัญหาพิมพ์ไทยใน LE
'''
files={'programs/c21.kar':candidate.read_bytes(),'README-TH.txt':b'\xef\xbb\xbf'+readme.encode('utf-8')}
final_expected=json.loads((root/'config/english-final/release.json').read_text())['files']
with zipfile.ZipFile(a.final_resources_zip) as z:
    for n in ['resources/etc.kar','resources/kwt.kar']:
        data=z.read(n);assert hashlib.sha256(data).hexdigest().lower()==final_expected[n].lower();files[n]=data
# Compact two labels and verify unchanged O/o/x member markers in an offline copy.
(w/'resources').mkdir()
original_etc=w/'final-etc.kar';original_etc.write_bytes(files['resources/etc.kar'])
compact_etc=w/'resources/etc.kar';shutil.copy2(original_etc,compact_etc)
compact_request=w/'compact.private-request'
compact_request.write_text('\n'.join([str(original_etc),str(compact_etc),key,final_expected['resources/etc.kar']])+'\n',encoding='utf-8')
run([a.java,'-Xmx512m','-cp',str(w/'classes')+';'+str(a.game_classes),'CompactResource',compact_request],'compact-resource')
files['resources/etc.kar']=compact_etc.read_bytes()
with zipfile.ZipFile(a.output_zip,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for n,data in files.items():z.writestr(n,data)
with zipfile.ZipFile(a.output_zip) as z:
    assert set(z.namelist())==set(files) and z.testzip() is None
    for n,data in files.items():assert z.read(n)==data
record={'release':'English Expanded Final','status':'offline PASS','storyCoverage':json.loads((w/'story-coverage.log').read_text(encoding='utf-8')),'catalog':catalog,'knownMcTitles':0,'knownMcConditions':0,'mcDisplay':'original titles and conditions; item drop names retain English','memberMarkers':'O/o/x; no added spacing','systemEffectNames':34,'patchedUiClasses':sum(x['name'].startswith('cosmic/ui/') for x in audit),'patchedDisplayClasses':len(audit),'displaySites':sum(len(x['hits']) for x in audit),'originalProgramSha256':sha(a.original_program),'files':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()},'zipSha256':sha(a.output_zip),'gameTest':'Final pending; v2 confirmed by user'}
pathlib.Path(str(a.output_zip)+'.validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('PASS verified ZIP '+str(a.output_zip))
