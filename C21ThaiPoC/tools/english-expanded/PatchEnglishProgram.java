import java.io.*;
import java.security.*;
import java.util.*;
import oni.resource.KarSource;

/** Offline build only: patch a copied current program, then reopen and compare every entry. */
public final class PatchEnglishProgram {
    static byte[] read(File f) throws Exception {
        DataInputStream in=new DataInputStream(new FileInputStream(f));
        try {byte[] b=new byte[(int)f.length()];in.readFully(b);return b;}finally{in.close();}
    }
    static String hash(byte[] b) throws Exception {
        StringBuilder s=new StringBuilder();for(byte x:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format("%02X",x&255));return s.toString();
    }
    static Set<String> paths(KarSource s) {
        Set<String> result=new TreeSet<String>();for(Object p:s.getPathList())result.add(p.toString());return result;
    }
    public static void main(String[] args) throws Exception {
        BufferedReader r=new BufferedReader(new InputStreamReader(new FileInputStream(args[0]),"UTF-8"));
        String original=r.readLine(),candidate=r.readLine(),key=r.readLine(),manifest=r.readLine();r.close();
        if(new File(original).getCanonicalFile().equals(new File(candidate).getCanonicalFile()))throw new IOException("Original must stay read-only");
        if(!hash(read(new File(original))).equals("5C4026E3066507B85A63C7ED5F4328B107983876BC4EBD47E6ECDD78935F1EEF"))throw new IOException("Unsupported original program");
        if(!Arrays.equals(read(new File(original)),read(new File(candidate))))throw new IOException("Candidate must be fresh original copy");
        Map<String,byte[]> payloads=new TreeMap<String,byte[]>();
        Map<String,String> beforePins=new TreeMap<String,String>();
        r=new BufferedReader(new InputStreamReader(new FileInputStream(manifest),"UTF-8"));
        try {String line;while((line=r.readLine())!=null){String[] v=line.split("\t",-1);if(v.length!=4)throw new IOException("Manifest shape");
            String p=v[0];if(!p.endsWith(".class")||p.contains("..")||p.contains("\\")||p.contains(":"))throw new IOException("Invalid class path");
            if(v[1].equals("-")){if(!p.startsWith("/c21english/"))throw new IOException("Invalid new class scope");}
            else if(p.equals("/cosmic/stage/client/AbstractAreaClient.class")) {
                if(!v[1].equals("B670DDE7584C047808D4BBB0F152FF56918F93A13FE62A1DDDECB2E71021F093"))throw new IOException("Receive-side display pin mismatch");
            }
            else if(!p.startsWith("/cosmic/ui/"))throw new IOException("Invalid modified class scope");
            byte[] b=read(new File(v[3]));if(!hash(b).equals(v[2])||payloads.put(p,b)!=null)throw new IOException("Hash or duplicate");beforePins.put(p,v[1]);
        }}finally{r.close();}
        if(payloads.isEmpty())throw new IOException("Empty patch");
        KarSource a=new KarSource(new File(original),key),b=new KarSource(new File(candidate),key);
        Set<String> expected;
        try {
            expected=paths(a);
            for(String p:payloads.keySet()){
                if(beforePins.get(p).equals("-")){if(expected.contains(p))throw new IOException("New class exists");}
                else if(!expected.contains(p)||!hash(a.getContentBytes(p)).equals(beforePins.get(p)))throw new IOException("Source class pin mismatch");
            }
            for(String p:payloads.keySet()){b.createResource(p,payloads.get(p));expected.add(p);int i=p.lastIndexOf('/');while(i>0){expected.add(p.substring(0,i+1));i=p.lastIndexOf('/',i-1);}}
            b.save();
        }finally{a.close();b.close();}
        a=new KarSource(new File(original),key);b=new KarSource(new File(candidate),key);
        try{
            if(!expected.equals(paths(b)))throw new IOException("Unexpected archive paths");
            for(String p:expected)if(!p.endsWith("/")){byte[] want=payloads.containsKey(p)?payloads.get(p):a.getContentBytes(p);if(!Arrays.equals(want,b.getContentBytes(p)))throw new IOException("Unexpected member change "+p);}
            System.out.println("PASS program archive paths="+expected.size()+" approved class payloads="+payloads.size()+" all other decoded bytes unchanged");
        }finally{a.close();b.close();}
    }
}
