import math
import json
import os
import subprocess
import tempfile
import time
import traceback
import sys
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
import pymupdf as fitz
from PySide6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont, QIcon, QAction, QPainterPath, QPolygonF
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QFrame, QSplitter, QSlider, QScrollArea, QSplashScreen, QDialog, QSizePolicy, QGraphicsDropShadowEffect

NAVY = '#071426'
NAVY2 = '#142849'
BG = '#071426'
WHITE = '#0D1D34'
TEXT = '#EAF1FA'
MUTED = '#66758B'
VECTOR = '#00F58A'
RASTER = '#FF315B'
EMBEDDED = '#FFD900'
BORDER = '#2C445D'
BRAND_BLUE = '#2C445D'
LOGO_COLOR = '#2C445D'
APP_VERSION = '1.1.31'

def resource_path(relative_path):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return base / relative_path



def eye_icon(visible):
    """Ícone de olho desenhado em Qt, sem dependência de fontes externas."""
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor('#D7E8FA'), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    outline = QPainterPath()
    outline.moveTo(2, 12)
    outline.cubicTo(7, 4, 17, 4, 22, 12)
    outline.cubicTo(17, 20, 7, 20, 2, 12)
    painter.drawPath(outline)
    painter.setBrush(QColor('#D7E8FA'))
    painter.drawEllipse(QRectF(9, 9, 6, 6))
    if not visible:
        painter.setPen(QPen(QColor('#142849'), 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(3, 21, 21, 3)
        painter.setPen(QPen(QColor('#FFB4BA'), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(3, 21, 21, 3)
    painter.end()
    return QIcon(pix)


class GuidanceIllustration(QWidget):
    """Ilustração vetorial independente de fontes e arquivos externos."""
    def __init__(self, positive, parent=None):
        super().__init__(parent)
        self.positive = positive
        self.setMinimumSize(145, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        scale = min(self.width() / 200, self.height() / 190)
        painter.scale(scale, scale)
        color = QColor('#83C522' if self.positive else '#D58A57')
        dark = QColor('#203A2D' if self.positive else '#3A2518')
        painter.setPen(QPen(color, 2))
        painter.setBrush(dark)
        painter.drawEllipse(QRectF(-86, -55, 125, 125))
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QRectF(-58, -18, 9, 20))
        painter.drawEllipse(QRectF(-13, -18, 9, 20))
        painter.setPen(QPen(color, 6, Qt.SolidLine, Qt.RoundCap))
        smile = QPainterPath()
        if self.positive:
            smile.moveTo(-59, 19)
            smile.cubicTo(-43, 62, -2, 63, 19, 18)
        else:
            smile.moveTo(-59, 55)
            smile.cubicTo(-43, 14, -2, 13, 19, 55)
        painter.drawPath(smile)
        # Símbolo lateral: mão estilizada, positiva ou negativa.
        painter.save()
        painter.translate(43, 14)
        if not self.positive:
            painter.scale(1, -1)
        painter.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundJoin))
        painter.setBrush(dark)
        hand = QPainterPath()
        hand.moveTo(-8, 36)
        hand.cubicTo(3, 24, 14, 8, 20, -14)
        hand.cubicTo(24, -36, 40, -53, 49, -47)
        hand.cubicTo(61, -38, 48, -11, 48, 7)
        hand.lineTo(70, 7)
        hand.cubicTo(85, 7, 89, 24, 78, 33)
        hand.cubicTo(84, 44, 74, 53, 67, 55)
        hand.cubicTo(70, 68, 57, 73, 43, 73)
        hand.lineTo(13, 73)
        hand.cubicTo(1, 73, -12, 58, -8, 36)
        hand.closeSubpath()
        painter.drawPath(hand)
        painter.restore()
        painter.end()


class GuidanceDialog(QDialog):
    """Dialogo colorido com arte integral exportada diretamente do arquivo AI."""
    def __init__(self, positive, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Resultado da análise')
        self.setModal(True)
        self.setFixedSize(570, 350)
        accent = '#83C522' if positive else '#B7774F'
        dark = '#142A20' if positive else '#291B13'
        self._neon_color = QColor(accent)
        self.setStyleSheet(f'QDialog {{ background-color: {dark}; }}')

        art = QLabel(self)
        art.setGeometry(18, 8, 534, 300 if positive else 268)
        art.setAlignment(Qt.AlignCenter)
        art.setStyleSheet('background: transparent; border: none;')
        path = resource_path('assets/card_sucesso.png' if positive else 'assets/card_aviso.png')
        pix = QPixmap(str(path))
        if not pix.isNull():
            # KeepAspectRatio: nunca corta nenhuma parte da arte original.
            art.setPixmap(pix.scaled(art.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # Brilho aplicado ao contorno de TODA a arte, inclusive o balão.
            art_glow = QGraphicsDropShadowEffect(art)
            art_glow.setBlurRadius(25)
            art_glow.setOffset(0, 0)
            art_color = QColor(accent)
            art_color.setAlpha(135)
            art_glow.setColor(art_color)
            art.setGraphicsEffect(art_glow)
        if not positive:
            # A carinha é desenhada separadamente, 16% maior, sem ampliar o texto.
            # O PNG da carinha possui máscara alfa circular, sem o retângulo residual da exportação.
            face_path = resource_path('assets/card_rosto_laranja.png')
            face_pix = QPixmap(str(face_path))
            if not face_pix.isNull():
                face = QLabel(self)
                face.setGeometry(351, 128, 191, 191)
                face.setAlignment(Qt.AlignCenter)
                face.setStyleSheet('background: transparent; border: none;')
                face.setPixmap(face_pix.scaled(face.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                face_glow = QGraphicsDropShadowEffect(face)
                face_glow.setBlurRadius(24)
                face_glow.setOffset(0, 0)
                face_color = QColor(accent)
                face_color.setAlpha(165)
                face_glow.setColor(face_color)
                face.setGraphicsEffect(face_glow)
                face.raise_()

        # Sombra sólida deslocada, como no botão original do Illustrator.
        button_back = QLabel(self)
        button_back.setGeometry(54, 274, 158, 48)
        button_back.setStyleSheet(f'background-color: {accent}; border-radius: 23px;')
        button_back.lower()
        close_btn = QPushButton('FECHAR', self)
        close_btn.setGeometry(46, 266, 158, 48)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""QPushButton {{ background-color: {dark}; color: {accent};
            border: 1px solid {accent}; border-radius: 23px;
            font-size: 19px; font-weight: 700; padding: 0; }}
            QPushButton:hover {{ background-color: {'#254734' if positive else '#42291B'}; }}""")
        shadow = QGraphicsDropShadowEffect(close_btn)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 0)
        glow = QColor(accent)
        glow.setAlpha(210)
        shadow.setColor(glow)
        close_btn.setGraphicsEffect(shadow)
        close_btn.raise_()
        close_btn.clicked.connect(self.accept)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for inset, alpha, width in [(2, 24, 5), (4, 45, 4), (6, 85, 2), (7, 220, 1.5)]:
            color = QColor(self._neon_color)
            color.setAlpha(alpha)
            painter.setPen(QPen(color, width))
            painter.setBrush(Qt.NoBrush)
            rect = QRectF(inset + width / 2, inset + width / 2,
                          self.width() - 2 * inset - width,
                          self.height() - 2 * inset - width)
            painter.drawRoundedRect(rect, 9, 9)
        painter.end()


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
            self.window().paint_pdf_tiles(self, event)
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
        painter.drawText(12, center_y + 35, self.width() - 24, 32, Qt.AlignCenter, 'clique aqui ou arraste seu PDF para análise')
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
        self.show_indicators = True
        self._tile_cache = OrderedDict()
        self._tile_size = 256
        self._render_scale = 1.0
        self._fit_scale = 1.0
        # Agrupa eventos de zoom consecutivos antes de solicitar novos blocos PDF.
        self._zoom_timer = QTimer(self)
        self._zoom_timer.setSingleShot(True)
        self._zoom_timer.setInterval(85)
        self._zoom_timer.timeout.connect(self._apply_pending_zoom)
        self._pending_anchor = None
        central = QWidget(); central.setObjectName('central'); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(22, 20, 22, 20); root.setSpacing(14)
        header = QHBoxLayout(); titles = QVBoxLayout()
        title = QLabel('Verificador de vetor'); title.setObjectName('appTitle')
        sub = QLabel('Triagem visual de elementos vetoriais e imagens rasterizadas em PDFs'); sub.setObjectName('subtitle')
        # A linha nasce imediatamente após o texto 'vetor', na mesma altura do título.
        # O espaço restante é absorvido pela própria linha, sem empurrá-la para a direita.
        title_row = QHBoxLayout(); title_row.setSpacing(9)
        title_row.addWidget(title, 0, Qt.AlignVCenter)
        header_line = QFrame(); header_line.setObjectName('headerLine')
        header_line.setFixedHeight(3)
        title_row.addWidget(header_line, 1, Qt.AlignVCenter)
        titles.addLayout(title_row); titles.addWidget(sub); header.addLayout(titles, 1)
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
        self.indicators_btn = QPushButton()
        self.indicators_btn.setObjectName('secondary')
        self.indicators_btn.setFixedSize(36, 36)
        self.indicators_btn.setIcon(eye_icon(True))
        self.indicators_btn.setIconSize(QRect(0, 0, 24, 24).size())
        self.indicators_btn.setToolTip('Ocultar indicadores')
        self.indicators_btn.clicked.connect(self.toggle_indicators)
        self.zoom_out_btn = QPushButton('−'); self.zoom_out_btn.setObjectName('secondary'); self.zoom_out_btn.setFixedWidth(38)
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_slider.setValue(max(0, self.zoom_slider.value() - 10)))
        self.zoom_label = QLabel('Ajustar'); self.zoom_label.setObjectName('pageLabel')
        self.zoom_slider = QSlider(Qt.Horizontal); self.zoom_slider.setRange(0, 1000); self.zoom_slider.setSingleStep(10); self.zoom_slider.setPageStep(25); self.zoom_slider.setValue(0); self.zoom_slider.setFixedWidth(170); self.zoom_slider.setToolTip('0% ajusta a página à área disponível; até 1000% de ampliação adicional a partir do tamanho ajustado')
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_in_btn = QPushButton('+'); self.zoom_in_btn.setObjectName('secondary'); self.zoom_in_btn.setFixedWidth(38)
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_slider.setValue(min(1000, self.zoom_slider.value() + 10)))
        row.addWidget(self.zoom_out_btn); row.addWidget(self.zoom_label); row.addWidget(self.zoom_slider); row.addWidget(self.zoom_in_btn)
        pv.addLayout(row)
        self.preview = DropPreview(self.open_pdf, self); self.preview.setObjectName('preview'); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(440, 540); self.preview.setScaledContents(False); self.preview.setToolTip('Clique aqui ou arraste um PDF para carregar; após carregar, clique e arraste para navegar')
        self.preview_scroll = QScrollArea(); self.preview_scroll.setObjectName('previewScroll'); self.preview_scroll.setWidgetResizable(True); self.preview_scroll.setAlignment(Qt.AlignCenter); self.preview_scroll.setWidget(self.preview); self.preview_scroll.setMinimumSize(440, 540); self.preview.set_scroll_area(self.preview_scroll); self.preview.set_document_loaded(False); pv.addWidget(self.preview_scroll, 1)
        # Controle discreto no canto inferior esquerdo do painel de pré-visualização.
        # Fora da área rolável: permanece visível mesmo com zoom ou rolagem.
        indicators_row = QHBoxLayout()
        indicators_row.setContentsMargins(0, 0, 0, 0)
        indicators_row.addWidget(self.indicators_btn, 0, Qt.AlignLeft)
        indicators_row.addStretch(1)
        pv.addLayout(indicators_row)
        splitter.addWidget(preview_card)
        # Painel rolável: em janelas baixas, os botões mantêm espaço e não se sobrepõem.
        result_scroll = QScrollArea(); result_scroll.setObjectName('resultScroll')
        result_scroll.setWidgetResizable(True); result_scroll.setFrameShape(QFrame.NoFrame)
        result_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        result_card = QFrame(); result_card.setObjectName('resultInner')
        rl = QVBoxLayout(result_card); rl.setContentsMargins(18, 16, 18, 16); rl.setSpacing(12)
        result_scroll.setWidget(result_card)
        heading = QLabel('Resultado'); heading.setObjectName('sectionTitle'); rl.addWidget(heading)
        status = QFrame(); status.setObjectName('status'); sl = QVBoxLayout(status); sl.setContentsMargins(14, 13, 14, 13)
        cap = QLabel('RESUMO DA PÁGINA'); cap.setObjectName('eyebrow'); sl.addWidget(cap)
        self.summary = QLabel('Carregue um PDF para ver os elementos.'); self.summary.setObjectName('summary'); self.summary.setWordWrap(True); sl.addWidget(self.summary); rl.addWidget(status)
        self.vector_count = QLabel('Vetores / desenhos: —'); self.vector_count.setObjectName('vectorCount'); rl.addWidget(self.vector_count)
        self.embedded_count = QLabel('Imagens incorporadas/ máscara de recorte: —'); self.embedded_count.setObjectName('embeddedCount'); self.embedded_count.setWordWrap(True); rl.addWidget(self.embedded_count)
        self.raster_count = QLabel('Imagens rasterizadas/PNG: —'); self.raster_count.setObjectName('rasterCount'); rl.addWidget(self.raster_count)
        self.note = QLabel('Contornos aproximados: verde = vetores; amarelo = imagens incorporadas ou possíveis máscaras; vermelho = imagens rasterizadas. A classificação é uma triagem, não uma certificação.'); self.note.setObjectName('note'); self.note.setWordWrap(True); rl.addWidget(self.note)
        # Card de orientação baseado na referência do Illustrator. Só aparece após análise.
        self.guidance_card = QFrame(); self.guidance_card.setObjectName('guidanceCard')
        guidance_layout = QHBoxLayout(self.guidance_card)
        guidance_layout.setContentsMargins(16, 15, 14, 15); guidance_layout.setSpacing(12)
        self.guidance_message = QLabel(); self.guidance_message.setObjectName('guidanceMessage')
        self.guidance_message.setWordWrap(True)
        guidance_layout.addWidget(self.guidance_message, 1)
        self.guidance_icon = QLabel(); self.guidance_icon.setObjectName('guidanceIcon')
        self.guidance_icon.setAlignment(Qt.AlignCenter)
        self.guidance_icon.setFixedSize(48, 48)
        guidance_layout.addWidget(self.guidance_icon, 0, Qt.AlignVCenter)
        self.guidance_card.hide()
        rl.addWidget(self.guidance_card)
        rl.addStretch(1)
        action_col = QVBoxLayout()
        action_col.setSpacing(10)
        self.open_btn = QPushButton('＋  Abrir PDF'); self.open_btn.setObjectName('primary'); self.open_btn.setMinimumHeight(48); self.open_btn.setMinimumWidth(250); self.open_btn.clicked.connect(self.open_pdf); action_col.addWidget(self.open_btn)
        self.analyze_btn = QPushButton('Analisar PDF'); self.analyze_btn.setObjectName('primary'); self.analyze_btn.setMinimumHeight(48); self.analyze_btn.setMinimumWidth(250); self.analyze_btn.clicked.connect(self.analyze_pdf); self.analyze_btn.setEnabled(False); action_col.addWidget(self.analyze_btn)
        self.new_pdf_btn = QPushButton('Abrir um novo PDF'); self.new_pdf_btn.setObjectName('primary'); self.new_pdf_btn.setMinimumHeight(48); self.new_pdf_btn.setMinimumWidth(250); self.new_pdf_btn.clicked.connect(self.open_new_pdf); self.new_pdf_btn.setEnabled(False); action_col.addWidget(self.new_pdf_btn)
        self.clear_btn = QPushButton('Limpar seleção'); self.clear_btn.setObjectName('primary'); self.clear_btn.setMinimumHeight(48); self.clear_btn.setMinimumWidth(250); self.clear_btn.clicked.connect(self.clear_selection); self.clear_btn.setEnabled(False); action_col.addWidget(self.clear_btn)
        rl.addLayout(action_col)
        result_scroll.setMinimumWidth(310); preview_card.setMinimumWidth(440)
        splitter.addWidget(result_scroll); splitter.setStretchFactor(0, 3); splitter.setStretchFactor(1, 2); splitter.setSizes([720, 460])
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
            QFrame#headerLine {{ background: {BRAND_BLUE}; border: 0; }}
            QFrame#guidanceCard {{ background: #173528; border: 2px solid #78C343; border-radius: 16px; }}
            QLabel#guidanceMessage {{ background: transparent; color: #85D64B; font-size: 15px; font-weight: 700; }}
            QLabel#guidanceIcon {{ background: #173528; color: #85D64B; border: 2px solid #85D64B; border-radius: 24px; font-size: 26px; font-weight: 800; }}
            QScrollArea#resultScroll {{ background: {WHITE}; border: 1px solid {BORDER}; border-radius: 18px; }}
            QFrame#resultInner {{ background: {WHITE}; border: 0; }}
            QLabel#brandLogo {{ background: transparent; border: 0; }}
            QLabel#fileLabel {{ font-size: 15px; font-weight: 600; color: #F3F7FF; }}
            QLabel#pageLabel {{ font-size: 14px; font-weight: 700; color: {MUTED}; }}
            QLabel#sectionTitle {{ font-size: 19px; font-weight: 800; color: {BRAND_BLUE}; }}
            QLabel#preview {{ background: #09172B; border: 0; border-radius: 0; color: {MUTED}; font-size: 18px; }}
            QPushButton {{ border: 0; border-radius: 11px; padding: 10px 15px; font-size: 14px; font-weight: 700; }}
            QPushButton#primary {{ background: #1C4B80; color: white; padding: 10px 14px; font-size: 16px; }}
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
            QLabel#embeddedCount {{ color: #F5C84C; font-size: 19px; font-weight: 800; padding: 6px 0; }}
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
        """Substituição segura: não descarta o documento atual antes de abrir o novo."""
        new_doc = None
        try:
            new_doc = fitz.open(path)
            if not new_doc.page_count:
                raise ValueError('O arquivo não contém páginas.')
            # Validar o primeiro conteúdo antes de trocar o documento em uso.
            new_doc.load_page(0)
        except Exception as exc:
            if new_doc is not None:
                new_doc.close()
            QMessageBox.critical(self, 'Não foi possível abrir o PDF', str(exc))
            return

        self._zoom_timer.stop()
        self._pending_anchor = None
        self._zoom_anchor = None
        # Evita eventos de pintura pendentes durante a troca do documento.
        self.preview.setUpdatesEnabled(False)
        old_doc = self.doc
        try:
            self.doc = new_doc
            self.pdf_path = Path(path)
            self.page_index = 0
            self.analysis = []
            self.report_text = ''
            self._tile_cache.clear()
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(0)
            self.zoom_slider.blockSignals(False)
            self.zoom_label.setText('Ajustar')
            self.open_btn.setEnabled(False)
            self.open_btn.setText('PDF carregado')
            self.new_pdf_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.preview.setAcceptDrops(False)
            self.preview.set_document_loaded(True)
            self.file_label.setText(f'{self.pdf_path.name}  •  {self.doc.page_count} página(s)')
            self.prev_btn.setEnabled(self.doc.page_count > 1)
            self.next_btn.setEnabled(self.doc.page_count > 1)
            self.analyze_btn.setEnabled(True)
            self.guidance_card.hide()
            self.summary.setText('PDF carregado. Clique em “Analisar PDF”.')
            self.vector_count.setText('Vetores / desenhos: —')
            self.embedded_count.setText('Imagens incorporadas/ máscara de recorte: —')
            self.raster_count.setText('Imagens rasterizadas/PNG: —')
            self._fit_scale = 0.0
            self.render_page()
        except Exception as exc:
            self.doc = old_doc
            new_doc.close()
            QMessageBox.critical(self, 'Erro ao carregar PDF', str(exc))
            return
        finally:
            self.preview.setUpdatesEnabled(True)
            self.preview.update()
        if old_doc is not None and old_doc is not new_doc:
            # A renderização é concluída antes de sair de _load_pdf; não manter
            # documentos antigos vivos durante a análise seguinte.
            old_doc.close()

    def clear_selection(self):
        """Retorna ao estado inicial, descartando documento, contornos e cache."""
        self._zoom_timer.stop()
        self._pending_anchor = None
        self._zoom_anchor = None
        if self.doc is not None:
            self.doc.close()
        self.doc = None
        self.pdf_path = None
        self.page_index = 0
        self.analysis = []
        self.report_text = ''
        self._tile_cache.clear()
        self._fit_scale = 0.0
        self._render_scale = 1.0
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(0)
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText('Ajustar')
        self.file_label.setText('Nenhum PDF selecionado')
        self.page_label.setText('Página —')
        self.guidance_card.hide()
        self.summary.setText('Carregue um PDF para ver os elementos.')
        self.vector_count.setText('Vetores / desenhos: —')
        self.embedded_count.setText('Imagens incorporadas/ máscara de recorte: —')
        self.raster_count.setText('Imagens rasterizadas/PNG: —')
        self.open_btn.setText('＋  Abrir PDF')
        self.open_btn.setEnabled(True)
        self.analyze_btn.setEnabled(False)
        self.new_pdf_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.preview.setFixedSize(max(440, self.preview_scroll.viewport().width()),
                                  max(540, self.preview_scroll.viewport().height()))
        self.preview.setAcceptDrops(True)
        self.preview.set_document_loaded(False)
        self.preview.update()

    def analyze_pdf(self):
        if not self.doc or not self.pdf_path:
            return
        self.analysis = []
        self.analyze_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        log_path = Path.home() / 'Verificador_Cromotransfer_diagnostico.log'
        try:
            # Each analysis runs in a fresh OS process. A crash in MuPDF/Qt
            # cannot terminate the main application or corrupt the next run.
            with tempfile.TemporaryDirectory(prefix='cromo_analise_') as tmp:
                result_path = Path(tmp) / 'resultado.json'
                if getattr(sys, 'frozen', False):
                    command = [sys.executable, '--analyze-worker', str(self.pdf_path), str(result_path)]
                else:
                    command = [sys.executable, str(Path(__file__).resolve()),
                               '--analyze-worker', str(self.pdf_path), str(result_path)]
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                completed = subprocess.run(command, capture_output=True, text=True,
                                           timeout=180, creationflags=flags)
                if completed.returncode != 0 or not result_path.exists():
                    raise RuntimeError(f'Processo de análise encerrou com código {completed.returncode}. '
                                       f'{completed.stderr[-1200:]}')
                result = json.loads(result_path.read_text(encoding='utf-8'))
                if 'error' in result:
                    raise RuntimeError(result['error'])
                if len(result['analysis']) != self.doc.page_count:
                    raise RuntimeError('A quantidade de páginas analisadas não corresponde ao PDF aberto.')
                self.analysis = result['analysis']
                self.report_text = result['report_text']
            self.update_summary()
            self.update_guidance_card()
            self.preview.update()
            QApplication.restoreOverrideCursor()
            try:
                GuidanceDialog(self.analysis[self.page_index]['vcount'] > 0, self).exec()
            finally:
                QApplication.setOverrideCursor(Qt.WaitCursor)
        except Exception as exc:
            self.analysis = []
            self.report_text = ''
            self.summary.setText('Não foi possível concluir a análise deste PDF.')
            with log_path.open('a', encoding='utf-8') as log:
                log.write(f'\n{datetime.now().isoformat()} | {self.pdf_path} | {type(exc).__name__}: {exc}\n')
                log.write(traceback.format_exc() + '\n')
            QMessageBox.critical(self, 'Erro na análise do PDF',
                                 f'{type(exc).__name__}: {exc}\n\n'
                                 f'Diagnóstico salvo em: {log_path}')
        finally:
            QApplication.restoreOverrideCursor()
            self.analyze_btn.setEnabled(self.doc is not None)

    def update_guidance_card(self):
        """Orienta o comercial pelo resultado da página atualmente exibida."""
        found_vectors = bool(self.analysis and self.page_index < len(self.analysis) and
                             self.analysis[self.page_index]['vcount'] > 0)
        if found_vectors:
            self.guidance_message.setText('Ótimo, foram encontrados vetores, veja se estão de acordo com a arte solicitada e envie para o arte finalista!')
            self.guidance_icon.setText('✓')
            bg, border, foreground = '#173528', '#78C343', '#85D64B'
        else:
            self.guidance_message.setText('Não foram encontrados vetores, apenas artes em PNG ou rasterizadas, entre em contato com o cliente!')
            self.guidance_icon.setText('!')
            bg, border, foreground = '#36210F', '#BB7950', '#D58A57'
        self.guidance_card.setStyleSheet(
            f'QFrame#guidanceCard {{ background: {bg}; border: 2px solid {border}; border-radius: 16px; }}'
            f'QLabel#guidanceMessage {{ background: transparent; color: {foreground}; font-size: 15px; font-weight: 700; }}'
            f'QLabel#guidanceIcon {{ background: {bg}; color: {foreground}; border: 2px solid {foreground}; border-radius: 24px; font-size: 26px; font-weight: 800; }}'
        )
        self.guidance_card.hide()

    def update_summary(self):
        if not self.analysis:
            return
        d = self.analysis[self.page_index]
        v, e, r = d['vcount'], d['ecount'], d['rcount']
        if sum(bool(x) for x in (v, e, r)) > 1:
            msg = 'Conteúdo misto: diferentes tipos de elementos detectados'
        elif v:
            msg = 'Elementos vetoriais/desenhos detectados'
        elif e:
            msg = 'Imagens incorporadas detectadas'
        elif r:
            msg = 'Imagens rasterizadas detectadas'
        else:
            msg = 'Nenhum elemento detectado nesta triagem'
        self.summary.setText(msg)
        self.vector_count.setText(f'Vetores / desenhos: {v}')
        self.embedded_count.setText(f'Imagens incorporadas/ máscara de recorte: {e}')
        self.raster_count.setText(f'Imagens rasterizadas/PNG: {r}')
        self.page_label.setText(f'Página {self.page_index+1} de {self.doc.page_count}')
        self.update_guidance_card()

    def render_page(self):
        """Resize the virtual page only; actual PDF pixels are rendered in visible tiles."""
        if not self.doc:
            return
        page = self.doc.load_page(self.page_index)
        zoom_value = self.zoom_slider.value()
        # 0% = tamanho inicial ajustado. Cada incremento amplia a partir
        # desse tamanho, sem saltar para uma escala absoluta menor.
        viewport = self.preview_scroll.viewport().size()
        available_w = max(1, viewport.width() - 24)
        available_h = max(1, viewport.height() - 24)
        if zoom_value == 0 or self._fit_scale <= 0:
            self._fit_scale = min(available_w / page.rect.width, available_h / page.rect.height)
        render_scale = self._fit_scale * (1.0 + zoom_value / 100.0)
        self._render_scale = max(0.01, render_scale)
        # Cache limitado por escala: renderiza somente o que estiver visível.
        # Conserva blocos de escalas anteriores durante o zoom para reduzir
        # recálculos em movimentos de ida e volta; LRU limita a memória.
        width = max(1, round(page.rect.width * self._render_scale))
        height = max(1, round(page.rect.height * self._render_scale))
        self.preview.setFixedSize(width, height)
        self.preview.update()
        self.page_label.setText(f'Página {self.page_index+1} de {self.doc.page_count}')
        if self.analysis:
            self.update_summary()

    def toggle_indicators(self):
        """Alterna somente a exibição dos contornos, sem alterar os resultados."""
        self.show_indicators = not self.show_indicators
        self.indicators_btn.setIcon(eye_icon(self.show_indicators))
        self.indicators_btn.setToolTip('Ocultar indicadores' if self.show_indicators else 'Mostrar indicadores')
        self.preview.update()

    def paint_pdf_tiles(self, widget, event):
        """Render only visible 512px tiles and reuse them during panning.

        This avoids multi-megapixel full-page rasterization at 200-300% zoom.
        """
        if not self.doc:
            return
        painter = QPainter(widget)
        painter.fillRect(event.rect(), QColor('#FFFFFF'))
        scale = self._render_scale
        page = self.doc.load_page(self.page_index)
        tile_size = self._tile_size
        visible = event.rect().intersected(widget.rect())
        if visible.isEmpty():
            painter.end()
            return
        left, right = visible.left() // tile_size, visible.right() // tile_size
        top, bottom = visible.top() // tile_size, visible.bottom() // tile_size
        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                key = (self.page_index, round(scale, 6), tx, ty)
                pixmap = self._tile_cache.get(key)
                if pixmap is None:
                    x0, y0 = tx * tile_size, ty * tile_size
                    x1 = min(widget.width(), x0 + tile_size)
                    y1 = min(widget.height(), y0 + tile_size)
                    clip = fitz.Rect(x0 / scale, y0 / scale, x1 / scale, y1 / scale) & page.rect
                    if clip.is_empty:
                        continue
                    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip,
                                          alpha=False, annots=True)
                    qimage = QImage(pix.samples, pix.width, pix.height, pix.stride,
                                    QImage.Format_RGB888).copy()
                    pixmap = (QPixmap.fromImage(qimage), pix.x, pix.y)
                    self._tile_cache[key] = pixmap
                    # Bound memory: at most 24 tiles, ~19 MB for RGB pixels.
                    while len(self._tile_cache) > 48:
                        self._tile_cache.popitem(last=False)
                else:
                    self._tile_cache.move_to_end(key)
                painter.drawPixmap(pixmap[1], pixmap[2], pixmap[0])
        if self.show_indicators and self.analysis and self.page_index < len(self.analysis):
            d = self.analysis[self.page_index]
            painter.setRenderHint(QPainter.Antialiasing)
            # Margem visual constante em pixels, independente do zoom.
            # Os contornos ficam fora da arte para evitar confusão com cores similares.
            indicator_margin_px = 5.0
            def draw_indicators(rectangles, color, style):
                pen = QPen(QColor(color), 2, style)
                pen.setCosmetic(True)  # Espessura de 2 px em qualquer zoom.
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                for rect in rectangles:
                    r = fitz.Rect(rect)
                    if r.is_empty or r.is_infinite:
                        continue
                    qr = QRectF(r.x0 * scale, r.y0 * scale,
                                max(1.0, r.width * scale), max(1.0, r.height * scale))
                    qr.adjust(-indicator_margin_px, -indicator_margin_px,
                              indicator_margin_px, indicator_margin_px)
                    if qr.intersects(QRectF(visible)):
                        painter.drawRoundedRect(qr, 4, 4)
            draw_indicators(d['drawings'], VECTOR, Qt.SolidLine)
            draw_indicators(d['embedded'], EMBEDDED, Qt.DashDotLine)
            draw_indicators(d['images'], RASTER, Qt.DashLine)
        painter.end()

    def on_zoom_changed(self, value):
        self.zoom_label.setText('Ajustar' if value == 0 else f'{value}%')
        if not self.doc:
            return
        # Debounce: scroll rápido ou arraste do slider não dispara dezenas de
        # renderizações síncronas que congelam a interface em 700%-1000%.
        anchor = getattr(self, '_zoom_anchor', None)
        if anchor is not None:
            self._pending_anchor = anchor
            self._zoom_anchor = None
        self._zoom_timer.start()

    def _apply_pending_zoom(self):
        if not self.doc:
            return
        hbar = self.preview_scroll.horizontalScrollBar()
        vbar = self.preview_scroll.verticalScrollBar()
        old_h, old_v = hbar.value(), vbar.value()
        anchor = self._pending_anchor
        self._pending_anchor = None
        old_size = self.preview.size()
        old_max_h, old_max_v = max(1, hbar.maximum()), max(1, vbar.maximum())
        h_ratio, v_ratio = old_h / old_max_h, old_v / old_max_v
        self.render_page()
        if anchor:
            cursor_pos = anchor[0]
            ratio_x = self.preview.width() / max(1, old_size.width())
            ratio_y = self.preview.height() / max(1, old_size.height())
            hbar.setValue(round((old_h + cursor_pos.x()) * ratio_x - cursor_pos.x()))
            vbar.setValue(round((old_v + cursor_pos.y()) * ratio_y - cursor_pos.y()))
        else:
            hbar.setValue(int(h_ratio * hbar.maximum()))
            vbar.setValue(int(v_ratio * vbar.maximum()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Se estiver em 0%, reajusta a página inteira à área visível após redimensionar a janela.
        if self.doc is not None and hasattr(self, 'zoom_slider') and self.zoom_slider.value() == 0:
            self._fit_scale = 0.0
            self.render_page()
    def _change_page(self, step):
        if not self.doc or not (0 <= self.page_index + step < self.doc.page_count):
            return
        self._zoom_timer.stop()
        self._pending_anchor = None
        self.page_index += step
        self._fit_scale = 0.0
        self.render_page()
        # A mensagem considera exclusivamente a página atual.
        # Antes de analisar, navegar não exibe qualquer resultado.
        if self.analysis and self.page_index < len(self.analysis):
            GuidanceDialog(self.analysis[self.page_index]['vcount'] > 0, self).exec()

    def prev_page(self):
        self._change_page(-1)

    def next_page(self):
        self._change_page(1)
    def save_report(self):
        if not self.report_text: return
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar relatório', self.pdf_path.stem+'_triagem.txt', 'Texto (*.txt)')
        if not path: return
        try:
            Path(path).write_text(self.report_text + f'\nGerado em: {datetime.now():%d/%m/%Y %H:%M:%S}\n', encoding='utf-8')
            QMessageBox.information(self, 'Relatório salvo', 'O relatório foi salvo com sucesso.')
        except Exception as e: QMessageBox.critical(self, 'Erro ao salvar relatório', str(e))

def analyze_document_isolated(pdf_path):
    """Executed in a dedicated subprocess; native PDF failures cannot kill the GUI."""
    doc = fitz.open(str(pdf_path))
    analysis = []
    try:
        report = ['VERIFICADOR DE VETOR - CROMOTRANSFER — RELATÓRIO DE TRIAGEM',
                  f'Arquivo: {pdf_path.name}', f'Páginas: {doc.page_count}', '']
        for i in range(doc.page_count):
            page = doc.load_page(i)
            drawings = page.get_drawings()
            # Caminhos PDF podem ser auxiliares, repetidos ou ficar encobertos.
            # Para preenchimentos pequenos de cor clara, verifica se ao menos
            # alguns pixels da cor do preenchimento sobrevivem na página final.
            # Não aplicar esse teste a texto escuro, traços ou gradientes.
            rendered = None
            rendered_pixels = None
            rendered_scale = 1.0
            seen_paths = set()
            visible_drawings = []
            for d in drawings:
                r = d.get('rect')
                if not r or r.is_empty:
                    continue
                clipped = fitz.Rect(r) & page.rect
                if clipped.is_empty or clipped.width < 0.5 or clipped.height < 0.5:
                    continue
                fill = d.get('fill')
                color = d.get('color')
                key = (tuple(round(v, 2) for v in clipped), d.get('type'),
                       tuple(round(v, 3) for v in fill) if fill else None,
                       tuple(round(v, 3) for v in color) if color else None)
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                # Formas pequenas com preenchimento colorido, mas totalmente
                # ocultas no resultado renderizado, não devem ganhar contorno.
                if (fill and d.get('type') == 'f' and min(fill) > 0.18
                        and clipped.get_area() < page.rect.get_area() * 0.025):
                    if rendered is None:
                        # Limita a imagem auxiliar a ~4 milhões de pixels,
                        # evitando picos de memória em PDFs de grande formato.
                        area = max(1.0, page.rect.width * page.rect.height)
                        rendered_scale = min(1.5, math.sqrt(4_000_000 / area))
                        rendered = page.get_pixmap(
                            matrix=fitz.Matrix(rendered_scale, rendered_scale),
                            alpha=False)
                        # samples cria uma cópia completa a cada acesso.
                        # samples_mv mantém uma visão sem copiar o bitmap.
                        rendered_pixels = rendered.samples_mv
                    target = tuple(round(v * 255) for v in fill)
                    matched = False
                    for gy in range(1, 16):
                        for gx in range(1, 16):
                            px = min(rendered.width - 1, max(0, int((clipped.x0 + clipped.width * gx / 16) * rendered_scale)))
                            py = min(rendered.height - 1, max(0, int((clipped.y0 + clipped.height * gy / 16) * rendered_scale)))
                            offset = (py * rendered.width + px) * rendered.n
                            rgb = rendered_pixels[offset:offset + 3]
                            if len(rgb) == 3 and max(abs(rgb[k] - target[k]) for k in range(3)) <= 28:
                                matched = True
                                break
                        if matched:
                            break
                    if not matched:
                        continue
                visible_drawings.append(tuple(clipped))
            rendered_pixels = None
            rendered = None
            rects = visible_drawings
            embedded, raster = [], []
            try:
                # O tipo de operação gráfica é mais confiável que xref:
                # fill-shade representa sombreamento/gradiente, não um PNG.
                # fill-image representa uma imagem de pixels, inclusive PNGs
                # incorporados como XObject. O xref não define a categoria.
                ops = page.get_bboxlog()
                infos = page.get_image_info(xrefs=True)
                shade_infos = [it for it in infos if not it.get('xref')]
                raster_infos = [it for it in infos if it.get('xref')]
                def valid_rect(bbox):
                    if not bbox or len(bbox) != 4:
                        return None
                    vals = tuple(float(v) for v in bbox)
                    if not all(math.isfinite(v) and abs(v) < 1_000_000 for v in vals):
                        return None
                    r = fitz.Rect(vals) & page.rect
                    if r.is_empty or r.width < 0.5 or r.height < 0.5:
                        return None
                    return tuple(round(float(v), 3) for v in r)
                # Os retângulos de fill-shade podem ser infinitos na API.
                # Para esses casos, usamos as posições visíveis reportadas
                # pelo extrator de imagens; nunca desenhamos bboxes infinitas.
                shade_positions = [valid_rect(it.get('bbox')) for it in shade_infos]
                shade_positions = [r for r in shade_positions if r]
                # Evita duplicar a mesma região várias vezes por operações
                # internas do Illustrator.
                embedded = list(dict.fromkeys(shade_positions))
                raster_positions = [valid_rect(it.get('bbox')) for it in raster_infos]
                raster = list(dict.fromkeys(r for r in raster_positions if r))
                # Outras imagens rasterizadas podem não ter xref. A lista
                # bboxlog permite detectar fill-image mesmo nesses casos.
                for kind, bbox in ops:
                    if kind == 'fill-image':
                        r = valid_rect(bbox)
                        if r and r not in raster:
                            raster.append(r)
                # Nunca colocar uma imagem rasterizada em amarelo apenas
                # porque está incorporada ao PDF.
                embedded = [r for r in embedded if r not in raster]
                # PDFs exportados pelo Illustrator podem usar gradientes / padrões
                # dentro de um caminho de recorte sem criar imagem XObject.
                # Nesses casos, get_image_info retorna bbox vazia e get_bboxlog
                # retorna limites infinitos. A geometria útil está nos clips.
                if any(kind == 'fill-shade' for kind, _ in ops):
                    clip_candidates = []
                    for path in page.get_drawings(extended=True):
                        if path.get('type') != 'clip':
                            continue
                        scissor = path.get('scissor')
                        if scissor is None:
                            continue
                        candidate = valid_rect(tuple(scissor))
                        if candidate is None:
                            continue
                        rect = fitz.Rect(candidate)
                        # Desconsiderar clips de página inteira e micro-recortes
                        # de detalhes internos; manter a máscara principal.
                        fraction = rect.get_area() / max(page.rect.get_area(), 1)
                        if not 0.003 <= fraction <= 0.85:
                            continue
                        clip_candidates.append((path.get('level', 999), candidate))
                    # Os clips de menor nível geralmente representam o objeto
                    # externo, evitando dezenas de caixas sobre a mesma arte.
                    if clip_candidates:
                        min_level = min(level for level, _ in clip_candidates)
                        main_clips = [r for level, r in clip_candidates
                                      if level == min_level]
                        for r in dict.fromkeys(main_clips):
                            if r not in embedded and r not in raster:
                                embedded.append(r)
            except Exception as exc:
                report.append(f'AVISO página {i+1}: falha ao inspecionar gráficos: {type(exc).__name__}: {exc}')
                print(f'[Verificador] Falha ao inspecionar gráficos da página {i+1}: {exc}')
            analysis.append({'drawings': rects, 'embedded': embedded,
                                  'images': raster, 'vcount': len(rects),
                                  'ecount': len(embedded), 'rcount': len(raster)})
            report.append(f'Página {i+1}: vetores/desenhos={len(rects)}; '
                          f'áreas de sombreamento/possível máscara={len(embedded)}; '
                          f'imagens rasterizadas={len(raster)}')
        report.extend(['', 'ATENÇÃO: classificação heurística, não certificação.',
                       'Amarelo = sombreamentos/gradientes, possíveis efeitos associados a recortes.',
                       'Vermelho = operações de imagem de pixels (raster).',
                       'A detecção de sombreamento não comprova máscara de recorte.',
                       'Ocorrências repetidas na mesma posição são agrupadas.'])
        return analysis, '\n'.join(report)
    finally:
        doc.close()

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
def worker_main():
    pdf_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    try:
        analysis, report_text = analyze_document_isolated(pdf_path)
        output_path.write_text(json.dumps({'analysis': analysis, 'report_text': report_text},
                                          ensure_ascii=False), encoding='utf-8')
    except Exception as exc:
        output_path.write_text(json.dumps({'error': f'{type(exc).__name__}: {exc}'}), encoding='utf-8')
        raise

if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == '--analyze-worker':
        worker_main()
    else:
        main()
