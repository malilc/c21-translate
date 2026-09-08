package c21english.expanded;

import cosmic.stage.event.CosmicChatEvent;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Only the pinned receive-side chat display read calls this helper. */
public final class SystemEffectBridge {
    private SystemEffectBridge() {}
    // Exact 34 trap-name pairs from config/english-expanded/effects.json.
    private static final String[][] NAMES = {
        {"\u30b8\u30e3\u30f3\u30d7\u53f0", "Jump Pad"},
        {"\u30ab\u30bf\u30d1\u30eb\u30c8", "Catapult"},
        {"\u5f15\u529b", "Attraction"},
        {"\u5f15\u529b lv2", "Attraction lv2"},
        {"\u5f15\u529b lv3", "Attraction lv3"},
        {"\u30c7\u30a3\u30ac\u30a4\u30a2\u30b9\u7528\u7adc\u5dfb\u578b\u5f15\u529b", "Digaius Tornado Attraction"},
        {"\u6b7b\u795e\u5b50(\u4eee)\u7adc\u5dfb\u578b\u5f15\u529b", "Shinigamiko (Temp) Tornado Attraction"},
        {"\u6b7b\u795e\u5b50(\u4eee)\u30dc\u30b9\u7adc\u5dfb\u578b\u5f15\u529b", "Shinigamiko (Temp) Boss Tornado Attraction"},
        {"\u30d1\u30e9\u30bb\u30af\u30bf\u30fc\u30d5\u30c3\u30af", "Parasector Hook"},
        {"\u30d1\u30e9\u30bb\u30af\u30bf\u30fc\u30d5\u30c3\u30af(PvP)", "Parasector Hook (PvP)"},
        {"\u30d1\u30e9\u30bb\u30af\u30bf\u30fc\u30d5\u30c3\u30af\u30fb\u30df\u30cb", "Parasector Hook Mini"},
        {"\u30d1\u30e9\u30bb\u30af\u30bf\u30fc\u30d5\u30c3\u30af\u30fb\u30df\u30cb(PvP)", "Parasector Hook Mini (PvP)"},
        {"\u65a5\u529b", "Repulsion"},
        {"\u30bc\u30d5\u30a1\u30fc\u30d5\u30c3\u30afLv1", "Zephyr Hook Lv1"},
        {"\u30bc\u30d5\u30a1\u30fc\u30d5\u30c3\u30afLv2", "Zephyr Hook Lv2"},
        {"\u30bc\u30d5\u30a1\u30fc\u30d5\u30c3\u30afLv1(PvP)", "Zephyr Hook Lv1 (PvP)"},
        {"\u30bc\u30d5\u30a1\u30fc\u30d5\u30c3\u30afLv2(PvP)", "Zephyr Hook Lv2 (PvP)"},
        {"\u9ad8\u5ea6\u5236\u9650\u91cd\u529b", "Altitude Limit Gravity"},
        {"\u30a2\u30f3\u30ab\u30fc\u30b7\u30e7\u30c3\u30c8", "Anchor Shot"},
        {"\u3059\u3044\u3053\u307fLV1", "Suction LV1"},
        {"\u3059\u3044\u3053\u307fLV2", "Suction LV2"},
        {"\u3059\u3044\u3053\u307fLV3", "Suction LV3"},
        {"\u53e3\u306e\u4e2d\u3078GO", "Into the Mouth"},
        {"\u3059\u3044\u3053\u307f", "Suction"},
        {"\u58c1", "Wall"},
        {"\u30a6\u30a9\u30fc\u30bf\u30fc\u30c7\u30d0\u30d5\u30d5\u30a3\u30fc\u30eb\u30c9", "Water Debuff Field"},
        {"\u30a6\u30a9\u30fc\u30bf\u30fc\u30d0\u30d5\u30d5\u30a3\u30fc\u30eb\u30c9", "Water Buff Field"},
        {"HP\u56de\u5fa9", "HP Recovery"},
        {"\u30b7\u30e7\u30c3\u30af\u30d5\u30a3\u30fc\u30eb\u30c9", "Shock Field"},
        {"\u7121\u6575\u9663", "Invincibility Field"},
        {"\u30d0\u30a4\u30f3\u30c9\u30c7\u30d0\u30d5\u30d5\u30a3\u30fc\u30eb\u30c9", "Bind Debuff Field"},
        {"\u8d64\u30db\u30cd\u30c7\u30d0\u30d5\u30d5\u30a3\u30fc\u30eb\u30c9", "Red Bone Debuff Field"},
        {"\u9752\u30db\u30cd\u30c7\u30d0\u30d5\u30d5\u30a3\u30fc\u30eb\u30c9", "Blue Bone Debuff Field"},
        {"\u7d2b\u30db\u30cd\u30c7\u30d0\u30d5\u30d5\u30a3\u30fc\u30eb\u30c9", "Purple Bone Debuff Field"},
    };
    private static final String INTEGER = "(0|-[1-9][0-9]*|[1-9][0-9]*)";
    private static final Pattern[][] HEAL = new Pattern[NAMES.length][4];
    static {
        for (int i = 0; i < NAMES.length; i++) {
            String name = Pattern.quote(NAMES[i][0]);
            HEAL[i][0] = Pattern.compile("\\[" + name + " " + INTEGER + " \uFF05\\] \u306e\u52b9\u679c\u304c\u639b\u304b\u308a\u307e\u3057\u305f");
            HEAL[i][1] = Pattern.compile("The effect of \\[" + name + " " + INTEGER + " %\\] was applied");
            HEAL[i][2] = Pattern.compile("(.*) \u304b\u3089\u306e\u30b5\u30dd\u30fc\u30c8\u52b9\u679c \\[" + name + " " + INTEGER + " \uFF05\\] \u304c\u639b\u304b\u308a\u307e\u3057\u305f", Pattern.DOTALL);
            HEAL[i][3] = Pattern.compile("Support effect from (.*) \\[" + name + " " + INTEGER + " %\\] was applied", Pattern.DOTALL);
        }
    }
    public static String systemEffectMessage(Object object) {
        CosmicChatEvent event = (CosmicChatEvent)object;
        String text = event.message;
        if (text == null || event.getSource() != -1 || event.range != 0) return text;
        if (event.type != 4 && event.type != 8) return text;
        String result = null;
        for (int i = 0; i < NAMES.length; i++) {
            String name = NAMES[i][0], translated = NAMES[i][1];
            if (event.type == 8) {
                if (text.equals("[" + name + "] \u306e\u52b9\u679c\u3092\u53d7\u3051\u305f\uFF01") || text.equals("Affected by [" + name + "]!")) {
                    if (result != null) return text;
                    result = "Affected by [" + translated + "]!";
                }
            } else {
                for (int form = 0; form < 4; form++) {
                    Matcher match = HEAL[i][form].matcher(text);
                    if (!match.matches()) continue;
                    String amount = match.group(form < 2 ? 1 : 2);
                    if (!isCanonicalInt(amount)) continue;
                    if (result != null) return text;
                    result = form < 2 ? "The effect of [" + translated + " " + amount + " %] was applied"
                        : "Support effect from " + match.group(1) + " [" + translated + " " + amount + " %] was applied";
                }
            }
        }
        return result == null ? text : result;
    }
    private static boolean isCanonicalInt(String value) {
        try { return Integer.toString(Integer.parseInt(value)).equals(value); }
        catch (NumberFormatException exception) { return false; }
    }
}
