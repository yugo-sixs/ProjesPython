import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QFileDialog
)
from fpdf import FPDF


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultrasonido - Versión Simplificada")
        self.setGeometry(100, 100, 600, 350)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        form_layout = QFormLayout()
        right_layout = QVBoxLayout()

        self.dosis_input = QDoubleSpinBox()
        self.dosis_input.setRange(0, 100)
        self.dosis_input.setValue(0)

        self.alto_input = QDoubleSpinBox()
        self.alto_input.setRange(0, 100.0)
        self.alto_input.setSingleStep(0.1)
        self.alto_input.setValue(0)

        self.ancho_input = QDoubleSpinBox()
        self.ancho_input.setRange(0, 100.0)
        self.ancho_input.setSingleStep(0.1)
        self.ancho_input.setValue(0)

        self.potencia_input = QDoubleSpinBox()
        self.potencia_input.setRange(0, 10.0)
        self.potencia_input.setSingleStep(0.1)
        self.potencia_input.setValue(0)

        self.porcentaje_input = QDoubleSpinBox()
        self.porcentaje_input.setRange(0, 100)
        self.porcentaje_input.setSingleStep(1.0)
        self.porcentaje_input.setValue(0)

        self.frecuencia_input = QComboBox()
        self.frecuencia_input.addItems(["1 MHz", "3 MHz"])

        form_layout.addRow("Dosis (J/cm²):", self.dosis_input)
        form_layout.addRow("Alto (cm):", self.alto_input)
        form_layout.addRow("Ancho (cm):", self.ancho_input)
        form_layout.addRow("Potencia (W):", self.potencia_input)
        form_layout.addRow("Porcentaje de trabajo (%):", self.porcentaje_input)
        form_layout.addRow("Frecuencia:", self.frecuencia_input)

        self.result_label = QLabel("Tiempo estimado: ")
        self.calc_button = QPushButton("Calcular")
        self.calc_button.clicked.connect(self.calcular_tiempo)

        self.clear_button = QPushButton("Limpiar campos")
        self.clear_button.clicked.connect(self.limpiar_campos)

        self.pdf_button = QPushButton("Exportar a PDF")
        self.pdf_button.clicked.connect(self.exportar_pdf)
        self.pdf_button.setEnabled(False)

        formula_label = QLabel(
            "<b>Fórmula:</b><br>"
            "Tiempo (min) = (Dosis × Superficie) / Potencia eficaz ÷ 60<br>"
            "Potencia eficaz = Potencia × (Porcentaje / 100)"
        )
        formula_label.setWordWrap(True)

        right_layout.addWidget(self.calc_button)
        right_layout.addWidget(self.clear_button)
        right_layout.addWidget(self.result_label)
        right_layout.addWidget(self.pdf_button)
        right_layout.addWidget(formula_label)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(right_layout)

        central_widget.setLayout(main_layout)
        self.tiempo_minutos = 0.0
        self.potencia_eficaz = 0.0
        self.superficie = 0.0

    def calcular_tiempo(self):
        dosis = self.dosis_input.value()
        alto = self.alto_input.value()
        ancho = self.ancho_input.value()
        self.superficie = alto * ancho
        potencia_total = self.potencia_input.value()
        porcentaje = self.porcentaje_input.value() / 100.0

        self.potencia_eficaz = potencia_total * porcentaje

        if self.potencia_eficaz == 0 or self.superficie == 0:
            self.result_label.setText("Error: verifique los valores de entrada.")
            self.pdf_button.setEnabled(False)
            return

        tiempo_segundos = (dosis * self.superficie) / self.potencia_eficaz
        self.tiempo_minutos = tiempo_segundos / 60.0

        self.result_label.setText(f"Tiempo estimado: {self.tiempo_minutos:.2f} minutos")
        self.pdf_button.setEnabled(True)

    def limpiar_campos(self):
        self.dosis_input.setValue(0)
        self.alto_input.setValue(0)
        self.ancho_input.setValue(0)
        self.potencia_input.setValue(0)
        self.porcentaje_input.setValue(0)
        self.result_label.setText("Tiempo estimado: ")
        self.pdf_button.setEnabled(False)

    def exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "dosificacion.pdf", "PDF Files (*.pdf)")
        if not path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Reporte de Dosificación de Ultrasonido", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Dosis: {self.dosis_input.value()} J/cm²", ln=True)
        pdf.cell(200, 10, txt=f"Alto: {self.alto_input.value()} cm", ln=True)
        pdf.cell(200, 10, txt=f"Ancho: {self.ancho_input.value()} cm", ln=True)
        pdf.cell(200, 10, txt=f"Superficie tratada: {self.superficie:.2f} cm²", ln=True)
        pdf.cell(200, 10, txt=f"Potencia total: {self.potencia_input.value()} W", ln=True)
        pdf.cell(200, 10, txt=f"Porcentaje trabajo: {self.porcentaje_input.value()}%", ln=True)
        pdf.cell(200, 10, txt=f"Frecuencia: {self.frecuencia_input.currentText()}", ln=True)
        pdf.cell(200, 10, txt=f"Potencia eficaz: {self.potencia_eficaz:.2f} W", ln=True)
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Tiempo estimado: {self.tiempo_minutos:.2f} minutos", ln=True)

        pdf.ln(10)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt="Tabla comparativa de frecuencia:", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.ln(5)
        pdf.cell(0, 10, txt="Frecuencia | Profundidad de penetración | Potencia recomendada", ln=True)
        pdf.cell(0, 10, txt="-------------------------------------------------------------", ln=True)
        pdf.cell(0, 10, txt="1 MHz      | 4-5 cm                   | Mayor (más profunda)", ln=True)
        pdf.cell(0, 10, txt="3 MHz      | 1-2 cm                   | Menor (más superficial)", ln=True)

        pdf.output(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
