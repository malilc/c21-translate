import java.io.*;
import java.security.*;
import java.util.*;
import oni.resource.KarSource;

/** Source-anchored member updates for a fresh, copied resource archive. */
public final class PatchManualResources {
    private static String hash(byte[] bytes) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
        StringBuilder text = new StringBuilder();
        for (byte b : digest) text.append(String.format("%02x", b & 255));
        return text.toString();
    }
    private static byte[] read(File file) throws Exception {
        if (!file.isFile() || file.length() > 67108864) throw new IOException("Invalid payload file");
        byte[] bytes = new byte[(int) file.length()];
        DataInputStream input = new DataInputStream(new FileInputStream(file));
        try { input.readFully(bytes); } finally { input.close(); }
        return bytes;
    }
    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(args[0]), "UTF-8"));
        File root, archive, manifest;
        String password;
        try {
            root = new File(reader.readLine()).getCanonicalFile();
            archive = new File(reader.readLine()).getCanonicalFile();
            password = reader.readLine();
            manifest = new File(reader.readLine()).getCanonicalFile();
        } finally { reader.close(); }
        if (!archive.getParentFile().equals(root) ||
            !(archive.getName().equals("etc.kar") || archive.getName().equals("kwt.kar") || archive.getName().equals("image.kar"))) {
            throw new IOException("Archive scope mismatch");
        }
        KarSource source = new KarSource(archive, password);
        try {
            Map<String, byte[]> changes = new LinkedHashMap<String, byte[]>();
            reader = new BufferedReader(new InputStreamReader(new FileInputStream(manifest), "UTF-8"));
            try {
                String line;
                while ((line = reader.readLine()) != null) {
                    String[] row = line.split("\t", -1);
                    if (row.length != 4 || row[0].length() == 0) throw new IOException("Invalid patch row");
                    String target = null;
                    for (Object entry : source.getPathList()) {
                        String path = (String) entry;
                        if (path.equals(row[0]) || path.equals("/" + row[0])) {
                            if (target != null) throw new IOException("Ambiguous member: " + row[0]);
                            target = path;
                        }
                    }
                    if (target == null || changes.containsKey(target)) throw new IOException("Missing or duplicate member");
                    if (!hash(source.getContentBytes(target)).equalsIgnoreCase(row[1])) {
                        throw new IOException("Source member hash mismatch: " + row[0]);
                    }
                    byte[] payload = read(new File(row[3]));
                    if (!hash(payload).equalsIgnoreCase(row[2])) throw new IOException("Payload hash mismatch");
                    changes.put(target, payload);
                }
            } finally { reader.close(); }
            if (changes.isEmpty()) throw new IOException("Empty patch manifest");
            // Validate every source and payload before mutating the copied archive.
            for (Map.Entry<String, byte[]> entry : changes.entrySet()) source.createResource(entry.getKey(), entry.getValue());
            source.save();
            System.out.println("PASS copied archive source-anchored members replaced=" + changes.size());
        } finally { source.close(); }
    }
}
