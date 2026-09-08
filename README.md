# C21 English Expanded

แพ็กแปลภาษาอังกฤษสำหรับ **C21 CyberStep client 1.509.0** ติดตั้งโดยคัดลอกไฟล์ แล้วเปิดเกมตามปกติ ไม่ต้องใช้ BAT หรือตัวเปิดแปลภาษา

## ดาวน์โหลด

**[ดาวน์โหลด English Expanded Final](https://github.com/malilc/c21-translate/releases/tag/english-expanded-final-1.509.0)**

ในหัวข้อ **Assets** เลือก `C21-English-Expanded-CyberStep-1.509.0-Final.zip` ซึ่งเป็นแพ็กพร้อมติดตั้ง ส่วน `Source code (zip)` และ `Source code (tar.gz)` เป็นซอร์สสำหรับพัฒนา

ถ้า repository เป็น Private ผู้ดาวน์โหลดต้องลงชื่อเข้าใช้ GitHub และได้รับสิทธิ์เข้าถึง repository นี้

## วิธีติดตั้ง

1. ตรวจว่าใช้ **CyberStep client 1.509.0** แพ็กนี้ยังไม่ได้ยืนยันกับ Steam client หรือเกมรุ่นอื่น
2. ปิดเกมและตัวอัปเดต
3. สำรองไฟล์เดิมทั้งสามไว้ในโฟลเดอร์อื่น โดยเก็บสำรองญี่ปุ่นต้นฉบับไว้ด้วย
4. แตก ZIP แล้วคัดลอกโฟลเดอร์ `programs` และ `resources` ไปยังโฟลเดอร์เกม ให้ตรงโครงสร้างด้านล่าง จากนั้นยืนยันการทับไฟล์
5. เปิดเกมตามปกติ ไม่ต้องใช้ `Start-C21ThaiFull*.bat` หรือ Java Agent

```text
C21/
├── programs/
│   └── c21.kar
└── resources/
    ├── etc.kar
    └── kwt.kar
```

ไม่ต้องใช้ Locale Emulator เพื่อแสดงอังกฤษ แพ็กนี้ไม่ได้แก้ปัญหาการพิมพ์ไทยเมื่อเปิดผ่าน Locale Emulator

## สิ่งที่แปล

- เมนู UI และค่าสถานะ ใช้คำอังกฤษสั้นให้เหมาะกับพื้นที่
- ชื่อและคำอธิบายชิ้นส่วน ไอเทม หุ่น รวมถึงข้อความ AURA ที่รองรับ
- ชื่อเควสต์ คำอธิบาย บทสนทนา และสถานที่ที่มีในแค็ตตาล็อก
- ข้อความรูเล็ต Arena 10 แบบ และชื่อเอฟเฟกต์/กับดัก 34 ชื่อ เฉพาะข้อความระบบที่ตรงรูปแบบที่รองรับ

มีแผนที่คำแปลรวม **33,348 รายการ** คำแปลบางส่วนทำงานตอนแสดงผลผ่านโปรแกรมใน `c21.kar` จึงต้องติดตั้งครบสามไฟล์

## ขอบเขตที่คงต้นฉบับ

- ชื่อ NPC และชื่อที่ผู้เล่นตั้ง
- ชื่อและเงื่อนไข MC รวมถึงบทนำ MC ที่ยังไม่รองรับ
- ข้อความฝังในภาพและข้อมูล cache
- ข้อความที่ไม่มีคำแปลหรือไม่ตรงรูปแบบที่รองรับ และคำใบ้ปริศนาบางรายการ

**Final คือแพ็กที่เลือกใช้ล่าสุด ไม่ได้หมายความว่าแปลทั้งเกมครบ 100%**

เครื่องหมายรายชื่อเพื่อน/กิลด์ใช้แบบเดิม:

| เครื่องหมาย | ความหมาย |
| --- | --- |
| `O` | อยู่พื้นที่เดียวกัน |
| `o` | ออนไลน์ |
| `x` | ออฟไลน์ |

## ถอนการติดตั้งและอัปเดตเกม

ปิดเกมแล้วคืนไฟล์ทั้งสามจากสำรอง หากเกมอัปเดต **อย่าทับไฟล์รุ่นใหม่ด้วยแพ็ก 1.509.0** ต้องใช้แพ็กที่สร้างสำหรับเกมรุ่นนั้น

## สถานะการตรวจสอบ

ผ่านการตรวจออฟไลน์ของคำแปล 33,348 รายการ การโหลดคลาสที่แก้ไข 46 คลาส กรณีทดสอบข้อความเอฟเฟกต์ 266 กรณี และโครงสร้าง/เนื้อหา archive กับ ZIP ผู้ใช้ยืนยันว่าแพ็กรุ่น 2 ใช้งานได้ แต่การตรวจหน้าจอจริงของแพ็ก Final ยังรอทดสอบ

SHA-256 ของ ZIP Final:

```text
56C41ACEF0E1E122EC1DFDC5D99BE6606952FABB87ED0D7D88DAE079650F5A48
```

พบปัญหาให้แจ้งใน [Issues](https://github.com/malilc/c21-translate/issues) พร้อมรุ่นเกม ชื่อแพ็ก หน้าจอที่พบ และภาพที่ปิดข้อมูลบัญชีแล้ว

## สำหรับผู้พัฒนา

ซอร์สเครื่องมืออยู่ใน `C21ThaiPoC/tools/english-expanded/` แค็ตตาล็อกและข้อมูลรุ่นอยู่ใน `C21ThaiPoC/config/english-expanded/` ดู [ขอบเขต Final](C21ThaiPoC/docs/english-expanded-final.md) เพิ่มเติม การสร้างแพ็กต้องมีไฟล์เกมต้นฉบับที่ตรงค่าแฮชและสภาพแวดล้อม Java ที่รองรับ ไม่ได้รวมไฟล์เกมหรือกุญแจ archive ไว้ใน Git

## English quick start

Download the **Final ZIP under Release Assets**, back up the three KAR files, then copy `programs/` and `resources/` into your **CyberStep 1.509.0** game folder while the game and updater are closed. Launch normally; no BAT is required. This is a partial English translation. NPC names, MC titles/conditions, image text and cache remain unchanged. Do not apply this package to a newer client version.
