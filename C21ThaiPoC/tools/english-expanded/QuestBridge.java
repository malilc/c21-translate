package c21english.expanded;

import java.util.*;

/** Display-only lookup. Never writes fields on a game object. */
public final class QuestBridge {
    private static final Map<String,String> TEXT = EnglishCatalog.create();
    private static final int MAX_SOURCE_LENGTH = maxSourceLength();
    private static int maxSourceLength() {
        int max=0; for(String key:TEXT.keySet())max=Math.max(max,key.length()); return max;
    }
    public static void initialize() { TEXT.size(); }
    public static String translate(String s) {
        String t=TEXT.get(s); return t==null?c21english.pilot.AuraBridge.translate(s):t;
    }
    public static String npcName(String s) {
        return s; // NPC identities remain original.
    }
    private static Object field(Object o,String name) {
        if(o==null) throw new NullPointerException();
        try {return o.getClass().getField(name).get(o);}
        catch(Exception ex) {throw new IllegalStateException("Quest display field "+name,ex);}
    }
    public static String systemEffectMessage(Object o) {return SystemEffectBridge.systemEffectMessage(o);}
    public static String itemMessage(Object o) {return message(o);}
    public static String message(Object o) {return translate((String)field(o,"message"));}
    public static String name(Object o) {return translate((String)field(o,"name"));}
    public static String comment(Object o) {return translate((String)field(o,"comment"));}
    public static String info(Object o) {return translate((String)field(o,"info"));}
    public static String robocomment(Object o) {return translate((String)field(o,"robocomment"));}
    public static String robohelp(Object o) {return translate((String)field(o,"robohelp"));}
    public static String getComment(Object o) {
        return getter(o,"getComment");
    }
    public static String getName(Object o) {
        return getter(o,"getName");
    }
    // Called only by the pinned quest detail panel and its list renderer.
    public static String questRobo(Object o) {
        return npcName((String)invoke(o,"getRobo",new Class<?>[0],new Object[0]));
    }
    public static String questRoom(Object o) {return getter(o,"getRoom");}
    public static String questArea(Object o) {return getter(o,"getArea");}
    public static String questStory(Object o,int flag) {
        String source=(String)invoke(o,"getStory",new Class<?>[]{Integer.TYPE},new Object[]{Integer.valueOf(flag)});
        if(source==null)return null;
        String exact=TEXT.get(source);
        if(exact!=null)return exact;
        // The original getter joins complete local sentences with LF and prefixes
        // recorded choices with ->. Match complete segments, never substrings of
        // a line; longest match retains multiline sentences and their ESC colors.
        StringBuilder result=new StringBuilder();
        int start=0;
        while(start<source.length()) {
            if(source.startsWith("->",start)) {result.append("->");start+=2;}
            int matched=-1;
            String target=null;
            for(int end=source.indexOf('\n',start);;end=source.indexOf('\n',end+1)) {
                if(end<0)end=source.length();
                if(end-start>MAX_SOURCE_LENGTH)break;
                String candidate=TEXT.get(source.substring(start,end));
                if(candidate!=null) {matched=end;target=candidate;}
                if(end==source.length())break;
            }
            if(matched>=0) {result.append(target);start=matched;}
            else {
                int end=source.indexOf('\n',start);
                if(end<0)end=source.length();
                result.append(source.substring(start,end));start=end;
            }
            if(start<source.length() && source.charAt(start)=='\n') {result.append('\n');start++;}
        }
        return result.toString();
    }
    /** Only item display sites use this: robot/player names never parse suffixes. */
    public static String getItemName(Object o) {
        String s=getter(o,"getName");
        if(s==null)return null;
        int split=s.lastIndexOf(" +");
        if(split>0 && split+2<s.length()) {
            for(int i=split+2;i<s.length();i++)if(s.charAt(i)<'0'||s.charAt(i)>'9')return s;
            String target=TEXT.get(s.substring(0,split));
            if(target!=null)return target+s.substring(split);
        }
        return s;
    }
    private static String getter(Object o,String method) {
        return translate((String)invoke(o,method,new Class<?>[0],new Object[0]));
    }
    private static Object invoke(Object o,String method,Class<?>[] types,Object[] args) {
        if(o==null)throw new NullPointerException();
        try {return o.getClass().getMethod(method,types).invoke(o,args);}
        catch(java.lang.reflect.InvocationTargetException ex) {
            Throwable cause=ex.getCause();
            if(cause instanceof RuntimeException)throw (RuntimeException)cause;
            if(cause instanceof Error)throw (Error)cause;
            throw new IllegalStateException("Quest display getter",cause);
        }
        catch(Exception ex) {throw new IllegalStateException("Quest display getter",ex);}
    }
    public static String[] choices(Object o) {
        String[] values=(String[])field(o,"switchword"); if(values==null) return null;
        String[] result=values.clone();
        for(int i=0;i<result.length;i++) result[i]=translate(result[i]);
        return result;
    }
}
