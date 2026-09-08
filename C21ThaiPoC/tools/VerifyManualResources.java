import java.io.*;
import java.security.*;
import java.util.*;
import oni.resource.KarSource;

/** Verify a copied archive against an explicit member/source/target hash manifest. */
public final class VerifyManualResources {
    private static String hash(byte[] bytes) throws Exception {
        StringBuilder result=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))result.append(String.format("%02X",b&255));
        return result.toString();
    }
    public static void main(String[] args) throws Exception {
        BufferedReader request=new BufferedReader(new InputStreamReader(new FileInputStream(args[0]),"UTF-8"));
        String before,after,key,manifest;
        try {before=request.readLine();after=request.readLine();key=request.readLine();manifest=request.readLine();}
        finally {request.close();}
        Map<String,String[]> expected=new HashMap<String,String[]>();
        BufferedReader rows=new BufferedReader(new InputStreamReader(new FileInputStream(manifest),"UTF-8"));
        try {
            String line;
            while((line=rows.readLine())!=null) {
                String[] row=line.split("\t",-1);
                if(row.length!=4 || expected.put(row[0],row)!=null)throw new IOException("Invalid or duplicate manifest row");
            }
        } finally {rows.close();}
        KarSource source=new KarSource(new File(before),key);
        KarSource target=new KarSource(new File(after),key);
        try {
            Set<String> paths=new TreeSet<String>(),targetPaths=new TreeSet<String>(),found=new HashSet<String>();
            for(Object path:source.getPathList())paths.add((String)path);
            for(Object path:target.getPathList())targetPaths.add((String)path);
            if(!paths.equals(targetPaths))throw new IOException("Archive member set changed");
            int changed=0;
            for(String path:paths) {
                if(path.endsWith("/"))continue;
                String name=path.startsWith("/")?path.substring(1):path;
                String a=hash(source.getContentBytes(path)),b=hash(target.getContentBytes(path));
                String[] row=expected.get(name);
                if(row==null) {
                    if(!a.equals(b))throw new IOException("Unexpected changed member "+name);
                } else {
                    if(!a.equalsIgnoreCase(row[1]) || !b.equalsIgnoreCase(row[2]))throw new IOException("Manifest hash mismatch "+name);
                    found.add(name);
                }
                if(!a.equals(b))changed++;
            }
            if(!found.equals(expected.keySet()))throw new IOException("Manifest member missing");
            System.out.println("PASS archive paths="+paths.size()+" expected members="+found.size()+" changed="+changed+" all other decoded member hashes preserved");
        } finally {source.close();target.close();}
    }
}
