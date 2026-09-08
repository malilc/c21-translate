package c21english.pilot;
import cosmic.robo.RoboParts;
import java.util.regex.*;

/** Pilot: translates only complete AURA charge-time lines for display. */
public final class AuraBridge {
    private static final Pattern SECONDS = Pattern.compile("AURAチャージ時間が([0-9]{1,3})秒短縮される");
    public static String getComment(Object object) {
        return translate(((RoboParts)object).getComment());
    }
    public static String translate(String source) {
        if (source == null) return null;
        String[] lines = source.split("\n", -1);
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < lines.length; i++) {
            if (i > 0) result.append('\n');
            String line = lines[i];
            boolean cr = line.endsWith("\r");
            String text = cr ? line.substring(0, line.length()-1) : line;
            Matcher match = SECONDS.matcher(text);
            if (match.matches()) result.append("AURA charge time -").append(match.group(1)).append("s");
            else if (text.equals("AURAチャージ時間が短縮されます")) result.append("Reduces AURA charge time");
            else result.append(text);
            if (cr) result.append('\r');
        }
        return result.toString();
    }
}
