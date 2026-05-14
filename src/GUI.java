import javax.swing.*;
import java.awt.*;

public class GUI {

    Timer heartbeatTimer;
    JFrame frame;
    JPanel mainPanel;
    JPanel leftPanel;
    AudiogramPanel graphPanel;
    JTextArea logArea;
    JButton startButton;
    JButton stopButton;
    JComboBox<String> frequencyBox;
    JSlider intensitySlider;
    JRadioButton rightEarButton;
    JRadioButton leftEarButton;
    SerialManager serialManager;

    public GUI() {
        // 1. ÖNCE ARAYÜZÜ ÇİZ (Hata olsa bile programı görelim)
        createWindow();
        createComponents();
        addComponents();
        addEvents();
        frame.setVisible(true);

        // 2. SONRA BAĞLANTIYI YAP
        try {
            logArea.append("Sistem başlatılıyor...\n");
            
            serialManager = new SerialManager();
            serialManager.setListener(this::handleSerialMessage);
            serialManager.connect("COM3"); 
            serialManager.startListening();
            
            logArea.append("Bağlantı başarılı! Teste başlayabilirsiniz.\n");
        } catch (Throwable e) { // Her türlü hatayı yakala
            logArea.append("HATA: COM3 portuna bağlanırken bir sorun oluştu!\n");
            logArea.append("Detay: " + e.getMessage() + "\n");
        }
    }

    private void createWindow() {
        frame = new JFrame("Audiometer System");
        frame.setSize(1200, 700);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setLocationRelativeTo(null);
        mainPanel = new JPanel(new BorderLayout());
        frame.add(mainPanel);
    }

    private void createComponents() {
        leftPanel = new JPanel();
        leftPanel.setBorder(BorderFactory.createEmptyBorder(30, 20, 30, 20));
        leftPanel.setPreferredSize(new Dimension(250, 700));
        leftPanel.setLayout(new GridLayout(12, 1, 10, 10));

        startButton = new JButton("Start Test");
        stopButton = new JButton("Stop Test");

        String[] frequencies = {"250 Hz", "500 Hz", "1000 Hz", "2000 Hz", "4000 Hz", "8000 Hz"};
        frequencyBox = new JComboBox<>(frequencies);

        intensitySlider = new JSlider(0, 120, 40);
        intensitySlider.setMajorTickSpacing(10);
        intensitySlider.setPaintTicks(true);
        intensitySlider.setPaintLabels(true);

        rightEarButton = new JRadioButton("Sağ Kulak (Right)", true);
        leftEarButton = new JRadioButton("Sol Kulak (Left)");
        ButtonGroup earGroup = new ButtonGroup();
        earGroup.add(rightEarButton);
        earGroup.add(leftEarButton);

        graphPanel = new AudiogramPanel();
        logArea = new JTextArea();
        logArea.setEditable(false);
    }

    private void addComponents() {
        leftPanel.add(startButton);
        leftPanel.add(stopButton);
        
        leftPanel.add(new JLabel("Kulak Seçimi:"));
        leftPanel.add(rightEarButton);
        leftPanel.add(leftEarButton);

        leftPanel.add(new JLabel("Frequency"));
        leftPanel.add(frequencyBox);
        leftPanel.add(new JLabel("Intensity (dB)"));
        leftPanel.add(intensitySlider);

        mainPanel.add(leftPanel, BorderLayout.WEST);
        mainPanel.add(graphPanel, BorderLayout.CENTER);
        mainPanel.add(new JScrollPane(logArea), BorderLayout.SOUTH);
    }

    private void addEvents() {
startButton.addActionListener(e -> {
    // Varsa eski zamanlayıcıyı durdur
    if (heartbeatTimer != null && heartbeatTimer.isRunning()) {
        heartbeatTimer.stop();
    }

    // HER 1 SANİYEDE BİR ÇALIŞACAK DÖNGÜ
    heartbeatTimer = new javax.swing.Timer(1000, event -> {
        if (serialManager != null) {
            // 1. Mevcut dB değerini Slider'dan al
            int currentDb = intensitySlider.getValue();
            
            // 2. Eğer dB 0'dan büyükse 1 azalt ve Slider'ı güncelle
            if (currentDb > 0) {
                int newDb = currentDb - 1;
                intensitySlider.setValue(newDb); // Slider otomatik kayar
                
                // 3. Güncel bilgileri al ve donanıma gönder
                String f = (String) frequencyBox.getSelectedItem();
                String ear = rightEarButton.isSelected() ? "RIGHT" : "LEFT";
                String command = "FREQ:" + f + ";DB:" + newDb + ";EAR:" + ear;
                
                serialManager.sendCommand(command);
            } else {
                // dB 0'a ulaştıysa durdur
                heartbeatTimer.stop();
                logArea.append(">> Test Bitti: Minimum şiddete ulaşıldı.\n");
            }
        }
    });

    heartbeatTimer.start();
    logArea.append(">> Otomatik Test Başlatıldı (Saniyede -1 dB).\n");
});
    stopButton.addActionListener(e -> {
    if (heartbeatTimer != null) heartbeatTimer.stop();
    logArea.append("Test ve Sinyal Durduruldu.\n");
});
}

// private void sendCurrentStatus() {
//     if (serialManager != null) {
//         String f = (String) frequencyBox.getSelectedItem();
//         int d = intensitySlider.getValue();
//         String e = rightEarButton.isSelected() ? "RIGHT" : "LEFT";
        
//         String cmd = "FREQ:" + f + ";DB:" + d + ";EAR:" + e;
//         serialManager.sendCommand(cmd);
//         // Debug için terminale yazdırabilirsin:
//         // System.out.println("Heartbeat gönderildi: " + cmd);
//     }
// }
    private void handleSerialMessage(String message) {
    SwingUtilities.invokeLater(() -> {
        if (message.contains("RESPONSE")) {
            // 1. HEMEN ZAMANLAYICIYI DURDUR (Veri akışı ve dB düşüşü kesilsin)
            if (heartbeatTimer != null && heartbeatTimer.isRunning()) {
                heartbeatTimer.stop();
                logArea.append(">> RESPONSE ALINDI: Test durduruldu.\n");
            }

            // 2. Mevcut değerleri al
            String currentFreq = (String) frequencyBox.getSelectedItem();
            int currentDb = intensitySlider.getValue();
            boolean isRight = rightEarButton.isSelected();
            String earStr = isRight ? "RIGHT" : "LEFT";

            // 3. Grafiğe noktayı bas
            graphPanel.addPoint(currentFreq, currentDb, isRight);
            
            // 4. Python'a gönder (Analiz için)
            String pythonCevabi = PythonConnector.sendToPython(currentFreq, currentDb, earStr);
            logArea.append(">> Algoritma Analizi: " + pythonCevabi + "\n");

            try {
                // dB GÜNCELLEME (Eğer Python yeni_db gönderdiyse)
                if (pythonCevabi.contains("yeni_db")) {
                    int yeniDb = extractInt(pythonCevabi, "yeni_db");
                    intensitySlider.setValue(yeniDb);
                    
                    // FREKANS GÜNCELLEME (Eğer Python yeni_frekans gönderdiyse)
                    if (pythonCevabi.contains("yeni_frekans")) {
                        int yeniFreq = extractInt(pythonCevabi, "yeni_frekans");
                        frequencyBox.setSelectedItem(yeniFreq + " Hz");
                    }

                    // 3. Yeni değerleri al ve donanıma (Arduino) "Yeni sesi çal" emrini gönder
                    String guncelFreq = (String) frequencyBox.getSelectedItem();
                    int guncelDb = intensitySlider.getValue();
                    String guncelKomut = "FREQ:" + guncelFreq + ";DB:" + guncelDb + ";EAR:" + earStr;
                    
                    serialManager.sendCommand(guncelKomut);
                    logArea.append(">> OTOMATİK AYAR: " + guncelFreq + " ve " + guncelDb + " dB gönderildi.\n");
                }
            } catch (Exception e) {
                System.out.println("JSON Ayrıştırma Hatası: " + e.getMessage());
            }
        }
    });
}

// BU YARDIMCI METODU GUI CLASS'ININ EN ALTINA EKLE (Hata almamak için)
private int extractInt(String json, String key) {
    // JSON içinden belirttiğimiz anahtarın (key) yanındaki sayıyı çekip alır
    String[] parts = json.split("\"" + key + "\":");
    String val = parts[1].split("[,}]")[0].replaceAll("[^0-9]", "").trim();
    return Integer.parseInt(val);
}
}