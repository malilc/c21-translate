import c21english.expanded.SystemEffectBridge;

import cosmic.stage.event.CosmicChatEvent;
import java.lang.reflect.Field;

/** Offline fixtures only: no client, server or network initialization. */
public final class SystemEffectProbe {
    private static int checks;
    private static final String NAME = "\u5f15\u529b";
    private static final String NEGATIVE = "[" + NAME + "] \u306e\u52b9\u679c\u3092\u53d7\u3051\u305f\uFF01";
    private static final String HEAL = "[" + NAME + " 12 \uFF05] \u306e\u52b9\u679c\u304c\u639b\u304b\u308a\u307e\u3057\u305f";
    private static void expect(int type, String input, String expected) {
        check(CosmicChatEvent.createSystemChatEvent(type, input), expected);
    }
    private static void check(CosmicChatEvent event, String expected) {
        String message = event.message, username = event.username, uid = event.uidstr;
        int source = event.getSource(), range = event.range, type = event.type;
        int target = event.target, emotion = event.emotion;
        String result = SystemEffectBridge.systemEffectMessage(event);
        if (expected == null ? result != null : !expected.equals(result))
            throw new AssertionError("Unexpected display translation in case " + checks);
        if (message != event.message || username != event.username || uid != event.uidstr
            || source != event.getSource() || range != event.range || type != event.type
            || target != event.target || emotion != event.emotion)
            throw new AssertionError("Event was modified");
        if (expected == message && result != message)
            throw new AssertionError("Unchanged event must return original string");
        checks++;
    }
    public static void main(String[] args) throws Exception {
        expect(8, NEGATIVE, "Affected by [Attraction]!");
        expect(8, "Affected by [" + NAME + "]!", "Affected by [Attraction]!");
        expect(4, HEAL, "The effect of [Attraction 12 %] was applied");
        expect(4, "The effect of [" + NAME + " 12 %] was applied", "The effect of [Attraction 12 %] was applied");
        String owner = "Player [" + NAME + "] / \u30d6\u30ed\u30c3\u30b5\u30e0\nSecond line";
        String suffix = " [" + NAME + " -12 \uFF05] \u304c\u639b\u304b\u308a\u307e\u3057\u305f";
        expect(4, owner + " \u304b\u3089\u306e\u30b5\u30dd\u30fc\u30c8\u52b9\u679c" + suffix,
            "Support effect from " + owner + " [Attraction -12 %] was applied");
        expect(4, "Support effect from " + owner + " [" + NAME + " -12 %] was applied",
            "Support effect from " + owner + " [Attraction -12 %] was applied");
        for (String amount : new String[] {"0", "-1", "2147483647", "-2147483648"})
            expect(4, "The effect of [" + NAME + " " + amount + " %] was applied",
                "The effect of [Attraction " + amount + " %] was applied");
        for (String amount : new String[] {"01", "+1", "-0", "1.0", "1e2", "2147483648", "-2147483649", "", " 1", "1\n2"}) {
            String input = "The effect of [" + NAME + " " + amount + " %] was applied";
            expect(4, input, input);
        }
        for (String input : new String[] {NEGATIVE + "\n", NEGATIVE + "\r\n", NEGATIVE + "junk", "prefix" + NEGATIVE,
                HEAL + "\n", "Affected by [" + NAME + "]!\n", "Support effect from Player [" + NAME + " 12 %] was applied\n",
                "Affected by [Unknown]!", "The effect of [Unknown 12 %] was applied", NAME,
                NAME + "\uFF01\u3000suffix", NAME + "! suffix", "Someone said: " + NEGATIVE, ""}) {
            expect(8, input, input);
            expect(4, input, input);
        }
        expect(4, NEGATIVE, NEGATIVE);
        expect(8, HEAL, HEAL);
        expect(4, null, null);
        for (int type : new int[] {0, 1, 2, 3, 5, 6, 7, 9, 10}) expect(type, NEGATIVE, NEGATIVE);
        CosmicChatEvent ranged = CosmicChatEvent.createSystemChatEvent(8, NEGATIVE);
        ranged.range = 1; check(ranged, NEGATIVE);
        CosmicChatEvent player = new CosmicChatEvent() { public int getSource() { return 123; } };
        player.type = 8; player.range = 0; player.message = NEGATIVE; check(player, NEGATIVE);
        // Exercise every exact name and every accepted form, including overlapping name prefixes.
        Field field = SystemEffectBridge.class.getDeclaredField("NAMES"); field.setAccessible(true);
        String[][] names = (String[][])field.get(null);
        if (names.length != 34) throw new AssertionError("Expected 34 reviewed names");
        for (String[] pair : names) {
            String name = pair[0], target = pair[1];
            expect(8, "[" + name + "] \u306e\u52b9\u679c\u3092\u53d7\u3051\u305f\uFF01", "Affected by [" + target + "]!");
            expect(8, "Affected by [" + name + "]!", "Affected by [" + target + "]!");
            expect(4, "[" + name + " 3 \uFF05] \u306e\u52b9\u679c\u304c\u639b\u304b\u308a\u307e\u3057\u305f", "The effect of [" + target + " 3 %] was applied");
            expect(4, "The effect of [" + name + " 3 %] was applied", "The effect of [" + target + " 3 %] was applied");
            expect(4, "P \u304b\u3089\u306e\u30b5\u30dd\u30fc\u30c8\u52b9\u679c [" + name + " 3 \uFF05] \u304c\u639b\u304b\u308a\u307e\u3057\u305f", "Support effect from P [" + target + " 3 %] was applied");
            expect(4, "Support effect from P [" + name + " 3 %] was applied", "Support effect from P [" + target + " 3 %] was applied");
        }
        System.out.println("PASS " + checks + " system-effect display cases; 34 names; exact JP/EN forms; event unchanged; player chat and trapstart untouched");
    }
}
