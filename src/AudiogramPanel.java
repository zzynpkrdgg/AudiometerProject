import javax.swing.*;
import java.awt.*;
//import java.awt.geom.AffineTransform;
import java.util.ArrayList;
import java.util.List;

public class AudiogramPanel extends JPanel {


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


    private int getFreqIndex(String freq) {
    if (freq == null) return 0;
    

    String clean = freq.replaceAll("[^0-9]", "").trim();
    
    System.out.println("DEBUG: getFreqIndex temizlenmiş veri: " + clean);
    
    switch (clean) {
        case "250":  return 0;
        case "500":  return 1;
        case "1000": return 2;
        case "2000": return 3;
        case "4000": return 4;
        case "8000": return 5;
        default:     return 0;
    }
}

  @Override
protected void paintComponent(Graphics g) {
    super.paintComponent(g);
    Graphics2D g2 = (Graphics2D) g;
    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);


    double w = (double) getWidth();
    double h = (double) getHeight();
    double pad = 70.0;

    double usableW = w - (2.0 * pad);
    double usableH = h - (2.0 * pad);


    g2.setColor(Color.BLACK);
    g2.setFont(new Font("Arial", Font.BOLD, 12));


    String xLabel = "Frequency (Hz)";
    int xLabelWidth = g2.getFontMetrics().stringWidth(xLabel);
    g2.drawString(xLabel, (int)(pad + (usableW / 2.0) - (xLabelWidth / 2.0)), (int)(h - pad + 55));

    java.awt.geom.AffineTransform oldTransform = g2.getTransform();
    g2.translate(pad - 50, (int)(pad + (usableH / 2.0)));
    g2.rotate(-Math.PI / 2); // 90 derece sola döndür
    String yLabel = "Intensity (dB)";
    int yLabelWidth = g2.getFontMetrics().stringWidth(yLabel);
    g2.drawString(yLabel, -yLabelWidth / 2, 0);
    g2.setTransform(oldTransform);


    g2.setColor(Color.LIGHT_GRAY);
    int totalSteps = (80 - 30) / 5;
    
    for (int i = 0; i <= totalSteps; i++) {
        int y = (int) ((h - pad) - (i * usableH / (double)totalSteps));
        g2.drawLine((int)pad, y, (int)(w - pad), y);
        
        g2.setColor(Color.BLACK);
        int currentLabelDb = 30 + (i * 5); 
        g2.drawString(currentLabelDb + "", (int)pad - 30, y + 5);
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

    g2.setStroke(new BasicStroke(3)); 
    for (PointData p : points) {
        int fIdx = getFreqIndex(p.frequency); 
        
        int targetX = (int) (pad + (fIdx * usableW / 5.0));
        

        int targetY = (int) ((h - pad) - ((p.db - 30) * usableH / 50.0));

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
