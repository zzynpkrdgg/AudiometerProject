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

        createWindow();
        createComponents();
        addComponents();
        addEvents();
        frame.setVisible(true);

        try {
            logArea.append("Sistem başlatılıyor...\n");
            
            serialManager = new SerialManager();
            serialManager.setListener(this::handleSerialMessage);
            serialManager.connect("COM3"); 
            serialManager.startListening();
            
            logArea.append("Bağlantı başarılı! Teste başlayabilirsiniz.\n");
        } catch (Throwable e) {
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


        intensitySlider = new JSlider(30, 80, 30);
        intensitySlider.setMajorTickSpacing(5);
        intensitySlider.setSnapToTicks(true);
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
        if (heartbeatTimer != null && heartbeatTimer.isRunning()) {
            heartbeatTimer.stop();
        }


        if (serialManager != null) {
            String currentFreq = (String) frequencyBox.getSelectedItem();
            String cleanFreq = currentFreq.replaceAll("[^0-9]", "").trim(); 
            
            int initialDb = intensitySlider.getValue();
            int dbKademe = ((initialDb - 30) / 5) + 1;
            
            String command = cleanFreq + " " + dbKademe;
            
            serialManager.sendCommand(command);
            logArea.append(">> Test Başlatıldı. Başlangıç Şiddeti: " + initialDb + " dB (Kademe: " + dbKademe + ")\n");
        }

        heartbeatTimer = new javax.swing.Timer(2000, event -> {
            if (serialManager != null) {
                int currentDb = intensitySlider.getValue();
                
                if (currentDb < 80) {
                    int newDb = currentDb + 5;
                    intensitySlider.setValue(newDb);
                    
                    String currentFreq = (String) frequencyBox.getSelectedItem();
                    String cleanFreq = currentFreq.replaceAll("[^0-9]", "").trim();
                    
                    int dbKademe = ((newDb - 30) / 5) + 1;
                    String command = cleanFreq + " " + dbKademe;
                    
                    serialManager.sendCommand(command);
                    logArea.append("Otomatik Artış: " + newDb + " dB (Kademe: " + dbKademe + ") gönderildi.\n");
                } else {
                    heartbeatTimer.stop();
                    logArea.append(">> Test Bitti: Maksimum şiddete (80 dB) ulaşıldı.\n");
                }
            }
        });

        heartbeatTimer.start();
    });

    stopButton.addActionListener(e -> {
        if (heartbeatTimer != null && heartbeatTimer.isRunning()) {
            heartbeatTimer.stop();
        }
        logArea.append(">> Test kullanıcı tarafından durduruldu.\n");
    });
}

   private void handleSerialMessage(String message) {
    SwingUtilities.invokeLater(() -> {
        if (message.contains("RESPONSE")) {
            // 1. Zamanlayıcıyı hemen durdur
            if (heartbeatTimer != null && heartbeatTimer.isRunning()) {
                heartbeatTimer.stop();
                logArea.append(">> RESPONSE ALINDI: Test durduruldu.\n");
            }

            String currentFreq = (String) frequencyBox.getSelectedItem();
            int currentDb = intensitySlider.getValue();
            boolean isRight = rightEarButton.isSelected();
            String earStr = isRight ? "RIGHT" : "LEFT";


            graphPanel.addPoint(currentFreq, currentDb, isRight);
            
            String cleanFreqForPython = currentFreq.replaceAll("[^0-9]", "").trim();

            String pythonCevabi = PythonConnector.sendToPython(cleanFreqForPython, currentDb, earStr.toLowerCase());
            logArea.append(">> Algoritma Analizi: " + pythonCevabi + "\n");

            try {
                if (pythonCevabi.contains("next_db")) {
                    int yeniDb = extractInt(pythonCevabi, "next_db");
                    
                    if (yeniDb < 30) yeniDb = 30;
                    if (yeniDb > 80) yeniDb = 80;
                    
                    intensitySlider.setValue(yeniDb);
                    
                    if (pythonCevabi.contains("frequency")) {
                        int yeniFreq = extractInt(pythonCevabi, "frequency");
                        frequencyBox.setSelectedItem(yeniFreq + " Hz");
                    }

          
                    String guncelFreq = (String) frequencyBox.getSelectedItem();
                    String cleanGuncelFreq = guncelFreq.replaceAll("[^0-9]", "").trim();
                    int guncelDb = intensitySlider.getValue();
                    
                    int dbKademe = ((guncelDb - 30) / 5) + 1; 
                    String guncelKomut = cleanGuncelFreq + " " + dbKademe; 
                    
                    serialManager.sendCommand(guncelKomut);
                    logArea.append(">> OTOMATİK ALGORİTMA AYARI: " + guncelFreq + " ve Kademe " + dbKademe + " set edildi.\n");
                }
            } catch (Exception e) {
                System.out.println("JSON Ayrıştırma Hatası: " + e.getMessage());
            }
        }
    });
}


private int extractInt(String json, String key) {

    String[] parts = json.split("\"" + key + "\":");
    String val = parts[1].split("[,}]")[0].replaceAll("[^0-9]", "").trim();
    return Integer.parseInt(val);
}
}