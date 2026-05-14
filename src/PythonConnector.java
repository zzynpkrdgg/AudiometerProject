import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;

public class PythonConnector {

    // Python'a JSON formatında veri gönderir ve gelen cevabı okur
    public static String sendToPython(String frequency, int db, String ear) {
        // Gönderilecek JSON verisini oluştur (Manuel formatlama)
        String jsonPayload = String.format("{\"frekans\": \"%s\", \"db\": %d, \"kulak\": \"%s\"}", frequency, db, ear);

        try (Socket socket = new Socket("localhost", 5050);
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {

            // Veriyi Python'a ateşle
            out.println(jsonPayload);
            
            // Python'dan gelen algoritma sonucunu oku
            return in.readLine(); 

        } catch (Exception e) {
            System.err.println("Python sunucusuna bağlanılamadı. Python kodunun çalıştığından emin ol.");
            return "{\"error\": \"Bağlantı Hatası\"}";
        }
    }
}