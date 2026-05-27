import com.fazecast.jSerialComm.SerialPort;
//import java.util.Scanner;
//import java.util.function.Consumer;

public class SerialManager {

    private SerialPort port;

    public interface SerialMessageListener {
        void onMessageReceived(String message);
    }
    
    private SerialMessageListener listener;

    public void setListener(SerialMessageListener listener) {
        this.listener = listener;
    }

    public void connect(String portName) {
        port = SerialPort.getCommPort(portName);
        port.setBaudRate(9600);
        boolean opened = port.openPort();
        if (opened) {
            System.out.println("Connected to " + portName);
        } else {
            System.out.println("Failed to connect.");
        }
    }

    public void sendCommand(String command) {
        if (port != null && port.isOpen()) {
            command += "\n";
            byte[] bytes = command.getBytes();
            port.writeBytes(bytes, bytes.length);
            System.out.println("Sent: " + command);
        } else {
            System.out.println("Port is not open.");
        }
    }


public void startListening() {
    new Thread(() -> {
        try {

            java.io.InputStream in = port.getInputStream();
            byte[] buffer = new byte[1024];
            while (true) {
                if (in.available() > 0) {
                    int len = in.read(buffer);
                    String message = new String(buffer, 0, len).trim();
                    
                    
                    System.out.println("Porttan Gelen Ham Veri: [" + message + "]");
                    
                    if (message.toUpperCase().contains("RESPONSE")) {
                        if (listener != null) listener.onMessageReceived("RESPONSE");
                    }
                }
                Thread.sleep(100);
            }
        } catch (Exception e) {
            System.out.println("Okuma hatası: " + e.getMessage());
        }
    }).start();
}

    public void disconnect() {
        if (port != null) {
            port.closePort();
            System.out.println("Disconnected.");
        }
    }
}