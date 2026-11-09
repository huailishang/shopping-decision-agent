import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;

/** P0.4: Java frontend -> offline Python candidate ingest; no browser automation, no network. */
public final class P04MarketplaceRegression {
    private static void check(boolean condition, String why) {
        if (!condition) throw new AssertionError(why);
    }
    private static Map<String,String> invoke(String python, String query, String links) throws Exception {
        List<String> command = new ArrayList<>();
        command.add(python);
        command.add("-m");
        command.add("shopping_decision.discovery_bridge");
        for (String value : List.of(query, links))
            command.add(Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8)));
        return DesktopBridgeClient.invoke(new ProcessBuilder(command), 10_000);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: P04MarketplaceRegression <python>");
        URI search = ShoppingDecisionDesktop.marketplaceSearchUri("冰箱 500L");
        check("search.jd.com".equals(search.getHost()), "search host must be official JD");
        check(search.toASCIIString().contains("%"), "search terms must be URL encoded");
        System.out.println("PASS official browser search URL");

        try {
            ShoppingDecisionDesktop.marketplaceSearchUri("请输入\n账号密码");
            throw new AssertionError("control chars unexpectedly allowed");
        } catch (IllegalArgumentException expected) {
            System.out.println("PASS malformed search query refused");
        }

        String links = "https://item.jd.com/100126724020.html\n"
                + "https://item.m.jd.com/100777000001.html\n"
                + "https://item.jd.com/100777000002.html";
        Map<String,String> good = invoke(args[0], "打印机", links);
        check("candidates_unverified".equals(good.get("status")), "candidate status incorrect");
        check(good.getOrDefault("summary", "").contains("商品线索：3条"), "3 items were not returned");
        check(good.getOrDefault("report_json", "").contains("\"verified_quote_count\": 0"),
              "incorrectly upgraded price");
        check(good.getOrDefault("report_json", "").contains("\"transactions_enabled\": false"),
              "transactions must stay disabled");
        System.out.println("PASS Java->Python subprocess 3 candidate URLs, zero quotes");

        Map<String,String> wrong = invoke(args[0], "冰箱", "https://item.jd.com.evil.net/100126724020.html");
        check("no_valid_candidates".equals(wrong.get("status")), "spoofed host must be rejected");
        System.out.println("PASS spoofed URL rejected");
        System.out.println("P04 Java marketplace regression: 4/4 PASS");
    }
}
