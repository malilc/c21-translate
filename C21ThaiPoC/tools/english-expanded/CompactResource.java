import java.io.*;
import java.security.*;
import java.util.*;
import oni.resource.KarSource;

/** Offline only: compact labels and verify unchanged O/o/x member markers in pinned Final etc.kar. */
public final class CompactResource {
    private static final String FINAL_SHA = "1BBE1C1D64DB2EF3746523702181BC521DFB23C849BC84F6C7213E79C5043D09";

    static byte[] read(File file) throws Exception {
        if (!file.isFile() || file.length() > Integer.MAX_VALUE) throw new IOException("Invalid archive file");
        DataInputStream input = new DataInputStream(new FileInputStream(file));
        try {
            byte[] bytes = new byte[(int) file.length()];
            input.readFully(bytes);
            return bytes;
        } finally { input.close(); }
    }

    static String hash(byte[] bytes) throws Exception {
        StringBuilder result = new StringBuilder();
        for (byte value : MessageDigest.getInstance("SHA-256").digest(bytes)) {
            result.append(String.format("%02X", value & 255));
        }
        return result.toString();
    }

    static Set<String> paths(KarSource source) {
        Set<String> result = new TreeSet<String>();
        for (Object path : source.getPathList()) result.add(path.toString());
        return result;
    }

    // ISO-8859-1 is a reversible byte view, so CP932 bytes outside these ASCII
    // values, line endings, and whitespace are preserved without normalization.
    static byte[] compact(byte[] bytes) throws Exception {
        String text = new String(bytes, "ISO-8859-1");
        text = replaceOnce(text, "Additional Element Damage", "Extra Elem. DMG");
        text = replaceOnce(text, "Additional Element", "Extra Element");
        return text.getBytes("ISO-8859-1");
    }

    static String replaceOnce(String text, String before, String after) throws IOException {
        int at = text.indexOf(before);
        if (at < 0 || text.indexOf(before, at + before.length()) >= 0) {
            throw new IOException("Expected exactly one source label: " + before);
        }
        return text.substring(0, at) + after + text.substring(at + before.length());
    }

    static void verifyMarkers(byte[] bytes) throws Exception {
        String text = new String(bytes, "ISO-8859-1");
        String[] values = {"O", "o", "x"};
        for (int i = 0; i < values.length; i++) {
            String line = "msg.memberlist.fig" + (i + 1) + "=" + values[i] + "\r\n";
            replaceOnce(text, line, line); // Assert exactly one unchanged complete line.
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IOException("Usage: CompactResource request-file");
        BufferedReader input = new BufferedReader(new InputStreamReader(new FileInputStream(args[0]), "UTF-8"));
        String originalPath, candidatePath, key, expected;
        try {
            originalPath = input.readLine();
            candidatePath = input.readLine();
            key = input.readLine();
            expected = input.readLine();
            if (originalPath == null || candidatePath == null || key == null || key.length() == 0 || expected == null || input.readLine() != null) {
                throw new IOException("Expected four request lines");
            }
        } finally { input.close(); }
        File original = new File(originalPath).getCanonicalFile();
        File candidate = new File(candidatePath).getCanonicalFile();
        if (original.equals(candidate)) throw new IOException("Original must stay read-only");
        if (!FINAL_SHA.equalsIgnoreCase(expected) || !FINAL_SHA.equals(hash(read(original)))) {
            throw new IOException("Unsupported Final resource archive");
        }
        if (!Arrays.equals(read(original), read(candidate))) throw new IOException("Candidate must be a fresh original copy");

        Map<String, byte[]> baseline = new TreeMap<String, byte[]>();
        Set<String> originalPaths;
        String member = null;
        Map<String, byte[]> replacements = new TreeMap<String, byte[]>();
        KarSource source = new KarSource(original, key);
        try {
            originalPaths = paths(source);
            for (String path : originalPaths) {
                if (!path.endsWith("/")) baseline.put(path, source.getContentBytes(path));
                if (path.equals("kwtdic.conf") || path.endsWith("/kwtdic.conf")) {
                    if (member != null) throw new IOException("Ambiguous kwtdic.conf member");
                    member = path;
                }
            }
            if (member == null) throw new IOException("Missing kwtdic.conf member");
            replacements.put(member, compact(baseline.get(member)));
            if (!baseline.containsKey("/etc/dic.conf")) throw new IOException("Missing dic.conf");
            verifyMarkers(baseline.get("/etc/dic.conf"));
        } finally { source.close(); }

        KarSource target = new KarSource(candidate, key);
        try {
            if (!originalPaths.equals(paths(target))) throw new IOException("Candidate paths differ");
            for (String path : replacements.keySet()) target.createResource(path, replacements.get(path));
            target.save();
        } finally { target.close(); }
        if (!FINAL_SHA.equals(hash(read(original)))) throw new IOException("Original archive changed");
        target = new KarSource(candidate, key);
        try {
            if (!originalPaths.equals(paths(target))) throw new IOException("Unexpected archive paths");
            for (String path : baseline.keySet()) {
                byte[] want = replacements.containsKey(path) ? replacements.get(path) : baseline.get(path);
                if (!Arrays.equals(want, target.getContentBytes(path))) throw new IOException("Unexpected member bytes: " + path);
            }
            System.out.println("PASS compact labels=2 unchanged O/o/x markers=3 paths=" + originalPaths.size() + " all other decoded bytes unchanged; original SHA unchanged");
        } finally { target.close(); }
    }
}
