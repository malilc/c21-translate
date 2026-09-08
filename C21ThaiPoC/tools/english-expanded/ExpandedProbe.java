import java.io.*;
import java.util.*;
import c21english.expanded.QuestBridge;

/** Exercises display behavior independently of game startup and account data. */
public final class ExpandedProbe {
    public static final class Data {
        public String name,comment,info,robocomment,robohelp,message;
        public String[] switchword;
        public int calls;
        public String getComment(){calls++;return comment;}
        public String getName(){calls++;return name;}
        public String getRobo(){calls++;return name;}
        public String getStory(int flag){calls++;return comment;}
    }
    public static final class Broken {public String getComment(){throw new IllegalArgumentException("original");}}
    static void equal(Object expected,Object actual){if(expected==null?actual!=null:!expected.equals(actual))throw new AssertionError("Unexpected result");}
    static String read(DataInputStream in)throws Exception{int n=in.readInt();byte[] b=new byte[n];in.readFully(b);return new String(b,"UTF-8");}
    public static void main(String[] args)throws Exception {
        Map<String,String> expected=new HashMap<String,String>();
        DataInputStream in=new DataInputStream(new FileInputStream(args[0]));
        int count=in.readInt();for(int i=0;i<count;i++)expected.put(read(in),read(in));in.close();
        for(String source:expected.keySet())equal(expected.get(source),QuestBridge.translate(source));
        equal(null,QuestBridge.translate(null));equal("unchanged [id:999999]",QuestBridge.translate("unchanged [id:999999]"));
        String source="AURAチャージ時間が5秒短縮される";
        Data d=new Data();d.comment=source;d.name="特殊任務兵";
        String translated=QuestBridge.translate(source);
        if(source.equals(translated))throw new AssertionError("AURA coverage missing");
        equal(translated,QuestBridge.getComment(d));equal(source,d.comment);equal(Integer.valueOf(1),Integer.valueOf(d.calls));
        equal(d.name,QuestBridge.questRobo(d));equal(d.name,QuestBridge.npcName(d.name));
        equal(Integer.valueOf(2),Integer.valueOf(d.calls));
        d.comment="->"+source+"\nunknown sentence\n";
        equal("->"+translated+"\nunknown sentence\n",QuestBridge.questStory(d,0));
        equal(Integer.valueOf(3),Integer.valueOf(d.calls));
        // Regression: the screenshot showed the title translated but all of these
        // complete quest-history sentences untranslated in Expanded 1.
        String[] story={
            "（あ、か、かっこいい…）\nあ、あの…天使軍の方ですか？",
            "わたくし…もう一度天使軍に入りたくて\n六度悪魔軍を抜けて\n来たのですが…まだ天使軍に\n参加できてなくて…",
            "もしあなたが天使軍の方でしたら\n少しだけお願いがあるのですが…\nよろしいでしょうか…？"
        };
        StringBuilder history=new StringBuilder(),englishHistory=new StringBuilder();
        for(String sentence:story) {
            if(!expected.containsKey(sentence)||sentence.equals(expected.get(sentence)))
                throw new AssertionError("Anniversary quest dialogue missing");
            history.append(sentence).append('\n');
            englishHistory.append(expected.get(sentence)).append('\n');
        }
        history.append("->unknown choice\n");englishHistory.append("->unknown choice\n");
        d.comment=history.toString();
        equal(englishHistory.toString(),QuestBridge.questStory(d,0));
        equal(history.toString(),d.comment);
        d.message="%sの全員が\n無敵になった！";
        equal("Everyone on %s\nis invincible!",QuestBridge.itemMessage(d));
        equal("%sの全員が\n無敵になった！",d.message);
        equal("Everyone on TEAM_123\nis invincible!",kotori.util.KotoriUtil.format(QuestBridge.itemMessage(d),new String[]{"TEAM_123"}));
        d.message=null;equal(null,QuestBridge.itemMessage(d));
        String item="リペアパック250";if(!expected.containsKey(item))throw new AssertionError("Item catalog absent");
        d.name=item+" +12";equal(expected.get(item)+" +12",QuestBridge.getItemName(d));equal(item+" +12",d.name);
        d.switchword=new String[]{source,null,"unchanged"};String[] copy=QuestBridge.choices(d);
        equal(translated,copy[0]);equal(null,copy[1]);equal("unchanged",copy[2]);equal(source,d.switchword[0]);if(copy==d.switchword)throw new AssertionError("Mutated choices");
        boolean ok=false;try{QuestBridge.getComment(null);}catch(NullPointerException ex){ok=true;}if(!ok)throw new AssertionError("Null receiver changed");
        ok=false;try{QuestBridge.getComment(new Broken());}catch(IllegalArgumentException ex){ok="original".equals(ex.getMessage());}if(!ok)throw new AssertionError("Getter exception changed");
        BufferedReader r=new BufferedReader(new FileReader(args[1]));String name;int classes=0;
        while((name=r.readLine())!=null){Class<?> c=Class.forName(name.replace('/','.'),false,ExpandedProbe.class.getClassLoader());if(name.equals("cosmic/ui/StagePanel"))c.getDeclaredConstructors();else c.getDeclaredMethods();classes++;}r.close();
        System.out.println("PASS catalog entries="+count+" patched classes="+classes+" verified; getter-once, original fields, NPC identity, history arrows, suffixes, choices, null and exceptions preserved");
    }
}
