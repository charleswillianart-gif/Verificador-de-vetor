import sys
from pathlib import Path
from datetime import datetime
import pymupdf as fitz
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont, QIcon, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QFrame, QSplitter, QSlider, QScrollArea, QSplashScreen

NAVY = '#071426'
NAVY2 = '#142849'
BG = '#071426'
WHITE = '#0D1D34'
TEXT = '#EAF1FA'
MUTED = '#66758B'
VECTOR = '#36D17C'
RASTER = '#FF626D'
BORDER = '#2C445D'
BRAND_BLUE = '#2C445D'
LOGO_COLOR = '#2C445D'
APP_VERSION = '1.0.0'

def resource_path(relative_path):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return base / relative_path


class DropPreview(QLabel):
    """PDF preview that can be panned by click-and-drag."""
    def __init__(self, open_pdf_callback, parent=None):
        super().__init__('', parent)
        self.open_pdf_callback = open_pdf_callback
        self.document_loaded = False
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self._dragging = False
        self._drag_start = QPoint()
        self._scroll_start = (0, 0)
        self._scroll_area = None

    def set_scroll_area(self, area):
        self._scroll_area = area

    def set_document_loaded(self, loaded):
        self.document_loaded = loaded
        self.setCursor(Qt.OpenHandCursor if loaded else Qt.PointingHandCursor)
        if self._scroll_area is not None:
            self._scroll_area.setObjectName('previewScroll' if loaded else 'previewScrollEmpty')
            self._scroll_area.style().unpolish(self._scroll_area)
            self._scroll_area.style().polish(self._scroll_area)
            self._scroll_area.update()
        self.update()

    def paintEvent(self, event):
        if self.document_loaded:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center_x = self.width() // 2
        center_y = self.height() // 2
        # Usa a logo PDF fornecida pelo usuário, mantendo sua cor original.
        logo_path = resource_path('assets/logo_pdf.png')
        logo = QPixmap(str(logo_path))
        if not logo.isNull():
            logo_size = logo.scaled(76, 94, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_rect = QRect(center_x - logo_size.width() // 2, center_y - 78,
                              logo_size.width(), logo_size.height())
            painter.drawPixmap(logo_rect, logo_size)
        painter.setPen(QColor(LOGO_COLOR))
        painter.setFont(QFont('Arial', 14, QFont.DemiBold))
        painter.drawText(12, center_y + 35, self.width() - 24, 32, Qt.AlignCenter, 'clique aqui ou arraste seu PDF')
        painter.end()

    def mousePressEvent(self, event):
        if not self.document_loaded and event.button() == Qt.LeftButton:
            self.open_pdf_callback()
            event.accept()
            return
        if event.button() == Qt.LeftButton and self._scroll_area is not None:
            self._dragging = True
            self._drag_start = event.globalPosition().toPoint()
            hbar = self._scroll_area.horizontalScrollBar()
            vbar = self._scroll_area.verticalScrollBar()
            self._scroll_start = (hbar.value(), vbar.value())
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._scroll_area is not None:
            delta = event.globalPosition().toPoint() - self._drag_start
            hbar = self._scroll_area.horizontalScrollBar()
            vbar = self._scroll_area.verticalScrollBar()
            hbar.setValue(self._scroll_start[0] - delta.x())
            vbar.setValue(self._scroll_start[1] - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        # A roda controla o zoom apenas depois de carregar um documento.
        delta = event.angleDelta().y()
        if self.document_loaded and delta and self.open_pdf_callback:
            steps = max(1, abs(delta) // 120)
            window = self.window()
            slider = getattr(window, 'zoom_slider', None)
            if slider is not None:
                # Guarda o ponto sob o cursor para mantê-lo fixo durante a ampliação/redução.
                viewport = window.preview_scroll.viewport()
                cursor_in_viewport = viewport.mapFromGlobal(event.globalPosition().toPoint())
                old_size = self.size()
                window._zoom_anchor = (cursor_in_viewport, old_size)
                change = 10 * steps * (1 if delta > 0 else -1)
                slider.setValue(max(slider.minimum(), min(slider.maximum(), slider.value() + change)))
                event.accept()
                return
        super().wheelEvent(event)

    def dragEnterEvent(self, event):
        # Permite soltar um PDF apenas antes de carregar um documento.
        if not self.document_loaded and self.open_pdf_callback and any(url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf') for url in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.document_loaded:
            event.ignore()
            return
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.pdf'):
                self.open_pdf_callback(path)
                event.acceptProposedAction()
                return
        event.ignore()


class Verificador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Verificador de vetor - Cromotransfer')
        icon_path = resource_path('assets/logo_icone.ico')
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1240, 820)
        self.setMinimumSize(980, 660)
        self.setAcceptDrops(True)
        self.doc = None; self.pdf_path = None; self.page_index = 0
        self.analysis = []; self.report_text = ''
        central = QWidget(); central.setObjectName('central'); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(22, 20, 22, 20); root.setSpacing(14)
        header = QHBoxLayout(); titles = QVBoxLayout()
        title = QLabel('Verificador de vetor'); title.setObjectName('appTitle')
        sub = QLabel('Triagem visual de elementos vetoriais e imagens rasterizadas em PDFs'); sub.setObjectName('subtitle')
        titles.addWidget(title); titles.addWidget(sub); header.addLayout(titles, 1)
        brand_logo = QLabel(); brand_logo.setObjectName('brandLogo'); brand_logo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        brand_pix = QPixmap(str(resource_path('assets/logo_cromotransfer.png')))
        if not brand_pix.isNull(): brand_logo.setPixmap(brand_pix.scaled(390, 62, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand_logo.setMinimumWidth(250); header.addWidget(brand_logo, 0, Qt.AlignRight | Qt.AlignVCenter)
        root.addLayout(header)
        help_menu = self.menuBar().addMenu('Ajuda')
        about_action = QAction('Sobre o Verificador', self); about_action.triggered.connect(self.show_about); help_menu.addAction(about_action)
        filecard = QFrame(); filecard.setObjectName('card'); fl = QHBoxLayout(filecard); fl.setContentsMargins(16, 12, 16, 12)
        self.file_label = QLabel('Nenhum PDF selecionado'); self.file_label.setObjectName('fileLabel'); self.file_label.setWordWrap(True); fl.addWidget(self.file_label, 1)
        self.page_label = QLabel('Página —'); self.page_label.setObjectName('pageLabel'); fl.addWidget(self.page_label); root.addWidget(filecard)
        splitter = QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False); root.addWidget(splitter, 1)
        preview_card = QFrame(); preview_card.setObjectName('card'); pv = QVBoxLayout(preview_card); pv.setContentsMargins(14, 14, 14, 14); pv.setSpacing(12)
        row = QHBoxLayout(); st = QLabel('Pré-visualização'); st.setObjectName('sectionTitle'); row.addWidget(st); row.addStretch(1)
        self.prev_btn = QPushButton('← Anterior'); self.prev_btn.setObjectName('secondary'); self.prev_btn.clicked.connect(self.prev_page); self.prev_btn.setEnabled(False)
        self.next_btn = QPushButton('Próxima →'); self.next_btn.setObjectName('secondary'); self.next_btn.clicked.connect(self.next_page); self.next_btn.setEnabled(False)
        row.addWidget(self.prev_btn); row.addWidget(self.next_btn)
        self.zoom_out_btn = QPushButton('−'); self.zoom_out_btn.setObjectName('secondary'); self.zoom_out_btn.setFixedWidth(38)
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_slider.setValue(max(0, self.zoom_slider.value() - 10)))
        self.zoom_label = QLabel('Ajustar'); self.zoom_label.setObjectName('pageLabel')
        self.zoom_slider = QSlider(Qt.Horizontal); self.zoom_slider.setRange(0, 300); self.zoom_slider.setSingleStep(10); self.zoom_slider.setPageStep(25); self.zoom_slider.setValue(0); self.zoom_slider.setFixedWidth(170); self.zoom_slider.setToolTip('0% ajusta a página à área disponível; de 10% a 300% amplia ou reduz o documento')
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_in_btn = QPushButton('+'); self.zoom_in_btn.setObjectName('secondary'); self.zoom_in_btn.setFixedWidth(38)
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_slider.setValue(min(300, self.zoom_slider.value() + 10)))
        row.addWidget(self.zoom_out_btn); row.addWidget(self.zoom_label); row.addWidget(self.zoom_slider); row.addWidget(self.zoom_in_btn)
        pv.addLayout(row)
        self.preview = DropPreview(self.open_pdf, self); self.preview.setObjectName('preview'); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(440, 540); self.preview.setScaledContents(False); self.preview.setToolTip('Clique aqui ou arraste um PDF para carregar; após carregar, clique e arraste para navegar')
        self.preview_scroll = QScrollArea(); self.preview_scroll.setObjectName('previewScroll'); self.preview_scroll.setWidgetResizable(True); self.preview_scroll.setAlignment(Qt.AlignCenter); self.preview_scroll.setWidget(self.preview); self.preview_scroll.setMinimumSize(440, 540); self.preview.set_scroll_area(self.preview_scroll); self.preview.set_document_loaded(False); pv.addWidget(self.preview_scroll, 1)
        splitter.addWidget(preview_card)
        result_card = QFrame(); result_card.setObjectName('card'); rl = QVBoxLayout(result_card); rl.setContentsMargins(18, 16, 18, 16); rl.setSpacing(12)
        heading = QLabel('Resultado'); heading.setObjectName('sectionTitle'); rl.addWidget(heading)
        status = QFrame(); status.setObjectName('status'); sl = QVBoxLayout(status); sl.setContentsMargins(14, 13, 14, 13)
        cap = QLabel('RESUMO DA PÁGINA'); cap.setObjectName('eyebrow'); sl.addWidget(cap)
        self.summary = QLabel('Carregue um PDF para ver os elementos.'); self.summary.setObjectName('summary'); self.summary.setWordWrap(True); sl.addWidget(self.summary); rl.addWidget(status)
        self.vector_count = QLabel('Vetores / desenhos: —'); self.vector_count.setObjectName('vectorCount'); rl.addWidget(self.vector_count)
        self.raster_count = QLabel('Imagens rasterizadas: —'); self.raster_count.setObjectName('rasterCount'); rl.addWidget(self.raster_count)
        self.note = QLabel('Contornos aproximados: verde contínuo = desenhos/vetores; vermelho tracejado = imagens rasterizadas. A análise é uma triagem, não uma certificação de vetorização.'); self.note.setObjectName('note'); self.note.setWordWrap(True); rl.addWidget(self.note)
        rl.addStretch(1)
        action_col = QVBoxLayout()
        action_col.setSpacing(12)
        self.open_btn = QPushButton('＋  Abrir PDF'); self.open_btn.setObjectName('primary'); self.open_btn.setMinimumHeight(62); self.open_btn.setMinimumWidth(250); self.open_btn.clicked.connect(self.open_pdf); action_col.addWidget(self.open_btn)
        self.analyze_btn = QPushButton('Analisar PDF'); self.analyze_btn.setObjectName('primary'); self.analyze_btn.setMinimumHeight(62); self.analyze_btn.setMinimumWidth(250); self.analyze_btn.clicked.connect(self.analyze_pdf); self.analyze_btn.setEnabled(False); action_col.addWidget(self.analyze_btn)
        self.new_pdf_btn = QPushButton('Abrir um novo PDF'); self.new_pdf_btn.setObjectName('primary'); self.new_pdf_btn.setMinimumHeight(62); self.new_pdf_btn.setMinimumWidth(250); self.new_pdf_btn.clicked.connect(self.open_new_pdf); self.new_pdf_btn.setEnabled(False); action_col.addWidget(self.new_pdf_btn)
        rl.addLayout(action_col)
        result_card.setMinimumWidth(340); preview_card.setMinimumWidth(440)
        splitter.addWidget(result_card); splitter.setStretchFactor(0, 3); splitter.setStretchFactor(1, 2); splitter.setSizes([720, 460])
        footer = QHBoxLayout()
        signature = QLabel(f'Versão {APP_VERSION}  •  desenvolvido por Charles Willian')
        signature.setObjectName('signature')
        footer.addStretch(1)
        footer.addWidget(signature)
        root.addLayout(footer)
        self.setStyleSheet(f'''
            QMainWindow, QWidget#central {{ background: {BG}; color: {TEXT}; }}
            QMenuBar {{ background: {BG}; color: {TEXT}; border-bottom: 2px solid {BRAND_BLUE}; }}
            QMenuBar::item:selected, QMenu::item:selected {{ background: {BRAND_BLUE}; }}
            QMenu {{ background: {WHITE}; color: {TEXT}; border: 1px solid {BRAND_BLUE}; }}
            QLabel {{ font-size: 14px; color: {TEXT}; }}
            QLabel#appTitle {{ font-size: 27px; font-weight: 800; color: #6D8EAE; }}
            QLabel#subtitle {{ font-size: 15px; color: #A9B9D0; }}
            QFrame#card {{ background: {WHITE}; border: 1px solid {BORDER}; border-radius: 18px; }}
            QLabel#brandLogo {{ background: transparent; border: 0; }}
            QLabel#fileLabel {{ font-size: 15px; font-weight: 600; color: #F3F7FF; }}
            QLabel#pageLabel {{ font-size: 14px; font-weight: 700; color: {MUTED}; }}
            QLabel#sectionTitle {{ font-size: 19px; font-weight: 800; color: {BRAND_BLUE}; }}
            QLabel#preview {{ background: #09172B; border: 0; border-radius: 0; color: {MUTED}; font-size: 18px; }}
            QPushButton {{ border: 0; border-radius: 11px; padding: 10px 15px; font-size: 14px; font-weight: 700; }}
            QPushButton#primary {{ background: #1C4B80; color: white; padding: 16px 22px; font-size: 16px; }}
            QPushButton#primary:hover {{ background: #28619E; }}
            QPushButton#primary:disabled {{ background: #31435C; color: #91A0B5; }}
            QPushButton#secondary {{ background: #172C49; color: #EAF1FA; border: 1px solid {BORDER}; }}
            QPushButton:focus {{ border: 2px solid {BRAND_BLUE}; }}
            QPushButton#secondary:hover {{ background: #203B60; }}
            QPushButton#secondary:disabled {{ color: #72849D; background: #102039; }}
            QFrame#statusCard {{ background: #102541; border: 1px solid #2A4568; border-radius: 13px; }}
            QLabel#eyebrow {{ color: {MUTED}; font-size: 11px; font-weight: 800; letter-spacing: 1px; }}
            QLabel#pageSummary {{ color: #F3F7FF; font-size: 16px; font-weight: 700; }}
            QLabel#vectorCount {{ color: #36D17C; font-size: 21px; font-weight: 800; padding: 10px 0; }}
            QLabel#rasterCount {{ color: #FF626D; font-size: 21px; font-weight: 800; padding: 10px 0; }}
            QLabel#vectorLegend {{ color: #36D17C; font-weight: 700; font-size: 13px; }}
            QLabel#rasterLegend {{ color: #FF626D; font-weight: 700; font-size: 13px; }}
            QLabel#note {{ color: #A9B9D0; font-size: 12px; }}
            QLabel#signature {{ color: #A9B9D0; font-size: 14px; font-weight: 400; font-style: italic; padding: 4px 8px; }}
            QScrollArea#previewScroll {{ background: #09172B; border: 1px solid {BORDER}; border-radius: 12px; }}
            QScrollArea#previewScrollEmpty {{ background: #09172B; border: 0; border-radius: 0; }}
            QScrollArea#previewScroll QWidget {{ background: #09172B; }}
            QScrollBar:vertical {{ background: #102039; width: 18px; margin: 0; }}
            QScrollBar:horizontal {{ background: #102039; height: 24px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {BRAND_BLUE}; min-height: 36px; border-radius: 6px; margin: 2px; }}
            QScrollBar::handle:horizontal {{ background: {BRAND_BLUE}; min-width: 44px; border-radius: 6px; margin: 3px 2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; height: 0; }}
            QSlider::groove:horizontal {{ height: 5px; background: {BRAND_BLUE}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: #FFFFFF; border: 1px solid #D9E2EF; width: 14px; margin: -5px 0; border-radius: 7px; }}
            QSplitter::handle {{ background: transparent; width: 12px; }}
        ''')

    def show_about(self):
        QMessageBox.about(
            self,
            'Sobre o Verificador',
            f'<h3>Verificador de vetor - Cromotransfer</h3>'
            f'<p>Versão {APP_VERSION}</p>'
            '<p>Ferramenta de triagem visual de elementos vetoriais e imagens rasterizadas em PDFs.</p>'
            '<p>Os contornos e contagens são aproximados e não constituem certificação de vetorização.</p>'
            '<p>Desenvolvido por Charles Willian.</p>'
        )

    def dragEnterEvent(self, event):
        if self.doc is not None:
            event.ignore()
            return
        urls = event.mimeData().urls()
        if any(url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf') for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.doc is not None:
            event.ignore()
            return
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.pdf'):
                self.open_pdf(path)
                event.acceptProposedAction()
                return
        event.ignore()

    def open_pdf(self, path=None):
        # O arrastar e soltar é permitido apenas enquanto ainda não há documento aberto.
        if self.doc is not None:
            return
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'Abrir PDF', '', 'Arquivos PDF (*.pdf)')
        if not path: return
        self._load_pdf(path)

    def open_new_pdf(self):
        # Permite substituir o PDF atual por meio de um botão explícito.
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir um novo PDF', '', 'Arquivos PDF (*.pdf)')
        if path:
            self._load_pdf(path)

    def _load_pdf(self, path):
        try:
            new_doc = fitz.open(path)
            if not new_doc.page_count:
                new_doc.close()
                raise ValueError('O arquivo não contém páginas.')
            old_doc = self.doc
            self.doc = new_doc; self.pdf_path = Path(path); self.page_index = 0; self.analysis = []; self.report_text = ''
            if old_doc is not None:
                old_doc.close()
            self.zoom_slider.setValue(0)
            self.open_btn.setEnabled(False)
            self.open_btn.setText('PDF carregado')
            self.new_pdf_btn.setEnabled(True)
            self.preview.setAcceptDrops(False)
            self.preview.set_document_loaded(True)
            self.file_label.setText(f'{self.pdf_path.name}  •  {self.doc.page_count} página(s)')
            self.prev_btn.setEnabled(self.doc.page_count > 1); self.next_btn.setEnabled(self.doc.page_count > 1)
            self.analyze_btn.setEnabled(True)
            self.summary.setText('PDF carregado. Clique em “Analisar PDF”.'); self.vector_count.setText('Vetores / desenhos: —'); self.raster_count.setText('Imagens rasterizadas: —')
            self.render_page()
        except Exception as e: QMessageBox.critical(self, 'Não foi possível abrir o PDF', str(e))

    def analyze_pdf(self):
        if not self.doc: return
        self.analysis = []; report = ['VERIFICADOR DE VETOR - CROMOTRANSFER — RELATÓRIO DE TRIAGEM', f'Arquivo: {self.pdf_path.name}', f'Páginas: {self.doc.page_count}', '']
        for i in range(self.doc.page_count):
            page = self.doc.load_page(i); drawings = page.get_drawings()
            rects = [tuple(d['rect']) for d in drawings if d.get('rect') and not d['rect'].is_empty]
            try: images = [tuple(x['bbox']) for x in page.get_image_info(xrefs=True) if x.get('bbox')]
            except Exception: images = []
            self.analysis.append({'drawings': rects, 'images': images, 'vcount': len(drawings), 'rcount': len(images)})
            report.append(f'Página {i+1}: desenhos/vetores detectados={len(drawings)}; posições de imagens rasterizadas detectadas={len(images)}')
        report.extend(['', 'As caixas são aproximadas e a contagem de desenhos não certifica que toda a arte esteja vetorizada.', 'Conteúdo duvidoso deve ser conferido no software de arte-final apropriado.'])
        self.report_text = '\n'.join(report); self.render_page()

    def update_summary(self):
        if not self.analysis: return
        d = self.analysis[self.page_index]; v, r = d['vcount'], d['rcount']
        if v and r: msg = 'Conteúdo misto: vetores e imagens rasterizadas detectados'
        elif v: msg = 'Elementos vetoriais/desenhos detectados'
        elif r: msg = 'Imagens rasterizadas detectadas'
        else: msg = 'Nenhum elemento detectado nesta triagem'
        self.summary.setText(msg); self.vector_count.setText(f'Vetores / desenhos: {v}'); self.raster_count.setText(f'Imagens rasterizadas: {r}')
        self.page_label.setText(f'Página {self.page_index+1} de {self.doc.page_count}')

    def render_page(self):
        if not self.doc: return
        page = self.doc.load_page(self.page_index)
        # Renderizar novamente em alta resolução conforme o zoom evita ampliar apenas uma miniatura.
        zoom_value = self.zoom_slider.value()
        if zoom_value == 0:
            # 0% significa ajustar a página inteira à área visível, sem ampliação.
            viewport = self.preview_scroll.viewport().size()
            available_w = max(1, viewport.width() - 24)
            available_h = max(1, viewport.height() - 24)
            render_scale = min(available_w / page.rect.width, available_h / page.rect.height)
        else:
            # Mantém o comportamento visual anterior: 50% corresponde a escala 1:1.
            render_scale = zoom_value / 50.0
        pix = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale), alpha=False, annots=True)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy(); rendered = QPixmap.fromImage(img)
        if self.analysis:
            p = QPainter(rendered); p.setRenderHint(QPainter.Antialiasing); sx = rendered.width()/page.rect.width; sy = rendered.height()/page.rect.height; d = self.analysis[self.page_index]
            p.setPen(QPen(QColor(VECTOR), 6))
            for rect in d['drawings']:
                r = fitz.Rect(rect); p.drawRoundedRect(int(r.x0*sx), int(r.y0*sy), max(1,int(r.width*sx)), max(1,int(r.height*sy)), 4, 4)
            p.setPen(QPen(QColor(RASTER), 6, Qt.DashLine))
            for rect in d['images']:
                r = fitz.Rect(rect); p.drawRoundedRect(int(r.x0*sx), int(r.y0*sy), max(1,int(r.width*sx)), max(1,int(r.height*sy)), 4, 4)
            p.end()
        self.original_preview = rendered
        self.preview.setPixmap(rendered)
        self.preview.set_document_loaded(True)
        self.preview.setFixedSize(rendered.size())
        self.page_label.setText(f'Página {self.page_index+1} de {self.doc.page_count}')
        if self.analysis: self.update_summary()

    def on_zoom_changed(self, value):
        self.zoom_label.setText('Ajustar' if value == 0 else f'{value}%')
        if self.doc:
            hbar = self.preview_scroll.horizontalScrollBar()
            vbar = self.preview_scroll.verticalScrollBar()
            old_h, old_v = hbar.value(), vbar.value()
            anchor = getattr(self, '_zoom_anchor', None)
            old_size = anchor[1] if anchor else self.preview.size()
            old_max_h, old_max_v = max(1, hbar.maximum()), max(1, vbar.maximum())
            h_ratio, v_ratio = old_h / old_max_h, old_v / old_max_v
            self.render_page()
            if anchor:
                # Reposiciona a página para que o mesmo ponto do PDF continue sob o cursor.
                cursor_pos = anchor[0]
                ratio_x = self.preview.width() / max(1, old_size.width())
                ratio_y = self.preview.height() / max(1, old_size.height())
                hbar.setValue(round((old_h + cursor_pos.x()) * ratio_x - cursor_pos.x()))
                vbar.setValue(round((old_v + cursor_pos.y()) * ratio_y - cursor_pos.y()))
                self._zoom_anchor = None
            else:
                # Para botões/controle deslizante, preserva aproximadamente a região visível.
                hbar.setValue(int(h_ratio * hbar.maximum()))
                vbar.setValue(int(v_ratio * vbar.maximum()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Se estiver em 0%, reajusta a página inteira à área visível após redimensionar a janela.
        if self.doc is not None and hasattr(self, 'zoom_slider') and self.zoom_slider.value() == 0:
            self.render_page()
    def prev_page(self):
        if self.doc and self.page_index > 0: self.page_index -= 1; self.render_page()
    def next_page(self):
        if self.doc and self.page_index < self.doc.page_count-1: self.page_index += 1; self.render_page()
    def save_report(self):
        if not self.report_text: return
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar relatório', self.pdf_path.stem+'_triagem.txt', 'Texto (*.txt)')
        if not path: return
        try:
            Path(path).write_text(self.report_text + f'\nGerado em: {datetime.now():%d/%m/%Y %H:%M:%S}\n', encoding='utf-8')
            QMessageBox.information(self, 'Relatório salvo', 'O relatório foi salvo com sucesso.')
        except Exception as e: QMessageBox.critical(self, 'Erro ao salvar relatório', str(e))

def main():
    app = QApplication(sys.argv); app.setApplicationName('Verificador de vetor - Cromotransfer'); app.setApplicationVersion(APP_VERSION); app.setFont(QFont('Segoe UI', 11)); app.setStyle('Fusion')
    icon_path = resource_path('assets/logo_icone.ico')
    if icon_path.exists(): app.setWindowIcon(QIcon(str(icon_path)))
    splash_pix = QPixmap(str(resource_path('assets/logo_cromotransfer.png')))
    splash = None
    if not splash_pix.isNull():
        splash = QSplashScreen(splash_pix.scaled(480, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        splash.show(); app.processEvents()
    w = Verificador(); w.show()
    if splash is not None: splash.finish(w)
    sys.exit(app.exec())
if __name__ == '__main__': main()
