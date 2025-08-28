import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox, QFileDialog
)
from fpdf import FPDF


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora de Dosificación de Ultrasonido")
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.dosis_input = QDoubleSpinBox()
        self.dosis_input.setRange(1, 100)
        self.dosis_input.setValue(35)

        self.superficie_input = QDoubleSpinBox()
        self.superficie_input.setRange(1, 1000)

        self.intensidad_input = QDoubleSpinBox()
        self.intensidad_input.setRange(0.1, 5.0)
        self.intensidad_input.setSingleStep(0.1)

        self.area_cabezal_input = QDoubleSpinBox()
        self.area_cabezal_input.setRange(0.1, 20.0)
        self.area_cabezal_input.setSingleStep(0.1)

        self.ciclo_input = QSpinBox()
        self.ciclo_input.setRange(1, 100)

        self.frecuencia_input = QComboBox()
        self.frecuencia_input.addItems(["1 MHz", "3 MHz"])

        form_layout.addRow("Dosis (J/cm²):", self.dosis_input)
        form_layout.addRow("Superficie tratada (cm²):", self.superficie_input)
        form_layout.addRow("Intensidad (W/cm²):", self.intensidad_input)
        form_layout.addRow("Área cabezal (cm²):", self.area_cabezal_input)
        form_layout.addRow("Ciclo de trabajo (%):", self.ciclo_input)
        form_layout.addRow("Frecuencia:", self.frecuencia_input)

        layout.addLayout(form_layout)

        self.result_label = QLabel("Tiempo estimado: ")
        self.calc_button = QPushButton("Calcular")
        self.calc_button.clicked.connect(self.calcular_dosificacion)

        self.pdf_button = QPushButton("Exportar a PDF")
        self.pdf_button.clicked.connect(self.exportar_pdf)
        self.pdf_button.setEnabled(False)

        layout.addWidget(self.calc_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.pdf_button)

        central_widget.setLayout(layout)
        self.tiempo_minutos = 0.0
        self.potencia_eficaz = 0.0

    def calcular_dosificacion(self):
        dosis = self.dosis_input.value()
        superficie = self.superficie_input.value()
        intensidad = self.intensidad_input.value()
        area_cabezal = self.area_cabezal_input.value()
        ciclo = self.ciclo_input.value() / 100.0

        self.potencia_eficaz = intensidad * area_cabezal * ciclo

        if self.potencia_eficaz == 0:
            self.result_label.setText("Error: potencia eficaz no puede ser 0.")
            self.pdf_button.setEnabled(False)
            return

        tiempo_segundos = (dosis * superficie) / self.potencia_eficaz
        self.tiempo_minutos = tiempo_segundos / 60.0
        self.result_label.setText(f"Tiempo estimado: {self.tiempo_minutos:.2f} minutos")
        self.pdf_button.setEnabled(True)

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
        pdf.cell(200, 10, txt=f"Superficie tratada: {self.superficie_input.value()} cm²", ln=True)
        pdf.cell(200, 10, txt=f"Intensidad: {self.intensidad_input.value()} W/cm²", ln=True)
        pdf.cell(200, 10, txt=f"Área del cabezal: {self.area_cabezal_input.value()} cm²", ln=True)
        pdf.cell(200, 10, txt=f"Ciclo de trabajo: {self.ciclo_input.value()}%", ln=True)
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
    from fpdf import FPDF
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
