import javax.swing.*;
import java.awt.*;
//import java.awt.geom.AffineTransform;
import java.util.ArrayList;
import java.util.List;

public class AudiogramPanel extends JPanel {

    // Verileri tutacak olan yardımcı sınıf
    public static class PointData {
        String frequency;
        int db;
        boolean isRight;

        public PointData(String frequency, int db, boolean isRight) {
            this.frequency = frequency;
            this.db = db;
            this.isRight = isRight;
        }
    }

    private List<PointData> points = new ArrayList<>();

    public void addPoint(String freq, int db, boolean isRight) {
        points.add(new PointData(freq, db, isRight));
        repaint(); // Paneli yenile
    }

    // Frekansın hangi sütuna denk geldiğini bulan garanti metod
    private int getFreqIndex(String freq) {
    if (freq == null) return 0;
    
    // Metnin içindeki rakam dışındaki her şeyi (Hz, boşluk vs.) siler
    String clean = freq.replaceAll("[^0-9]", "").trim();
    
    System.out.println("DEBUG: getFreqIndex temizlenmiş veri: " + clean);
    
    switch (clean) {
        case "250":  return 0;
        case "500":  return 1;
        case "1000": return 2;
        case "2000": return 3;
        case "4000": return 4;
        case "8000": return 5;
        default:     return 0; // Tanıyamazsa en başa çizer
    }
}

  @Override
protected void paintComponent(Graphics g) {
    super.paintComponent(g);
    Graphics2D g2 = (Graphics2D) g;
    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

    // HER ÇİZİMDE O ANKİ GÜNCEL BOYUTU AL
    double w = (double) getWidth();
    double h = (double) getHeight();
    double pad = 70.0;

    double usableW = w - (2.0 * pad);
    double usableH = h - (2.0 * pad);

    // 1. IZGARA ÇİZİMİ
    g2.setColor(Color.LIGHT_GRAY);
    for (int i = 0; i <= 12; i++) {
        int y = (int) (pad + (i * usableH / 12.0));
        g2.drawLine((int)pad, y, (int)(w - pad), y);
        g2.setColor(Color.BLACK);
        g2.drawString((i * 10) + "", (int)pad - 35, y + 5);
        g2.setColor(Color.LIGHT_GRAY);
    }

    String[] freqs = {"250", "500", "1000", "2000", "4000", "8000"};
    for (int i = 0; i < 6; i++) {
        int x = (int) (pad + (i * usableW / 5.0));
        g2.drawLine(x, (int)pad, x, (int)(h - pad));
        g2.setColor(Color.BLACK);
        g2.drawString(freqs[i], x - 15, (int)(h - pad) + 25);
        g2.setColor(Color.LIGHT_GRAY);
    }

    // 2. NOKTALARI ÇİZ (Burası Değişti!)
    g2.setStroke(new BasicStroke(3)); 
    for (PointData p : points) {
        // Frekans indeksini (0-5 arası) alıyoruz
        int fIdx = getFreqIndex(p.frequency); 
        
        // DİKKAT: Burada 'x' ve 'y' değişkenlerini LOCAL (yerel) olarak 
        // o anki usableW ve usableH'ye göre tekrar hesaplıyoruz!
        int targetX = (int) (pad + (fIdx * usableW / 5.0));
        int targetY = (int) (pad + (p.db * usableH / 120.0));

        if (p.isRight) {
            g2.setColor(Color.RED);
            g2.drawOval(targetX - 10, targetY - 10, 20, 20);
        } else {
            g2.setColor(Color.BLUE);
            g2.drawLine(targetX - 10, targetY - 10, targetX + 10, targetY + 10);
            g2.drawLine(targetX + 10, targetY - 10, targetX - 10, targetY + 10);
        }
    }
}
}
