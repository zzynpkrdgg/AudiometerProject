import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;

public class PythonConnector {


    public static String sendToPython(String frequency, int db, String ear) {

        String jsonPayload = String.format("{\"frekans\": \"%s\", \"db\": %d, \"kulak\": \"%s\"}", frequency, db, ear);

        try (Socket socket = new Socket("localhost", 5050);
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {


            out.println(jsonPayload);
            

            return in.readLine(); 

        } catch (Exception e) {
            System.err.println("Python sunucusuna bağlanılamadı. Python kodunun çalıştığından emin ol.");
            return "{\"error\": \"Bağlantı Hatası\"}";
        }
    }
}