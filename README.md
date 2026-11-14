# MiniPrint Linux (Cliente no oficial para impresoras térmicas MX06 / Cat Printer)

Aplicación de escritorio libre y de código abierto para **Linux (Ubuntu / Debian)** que permite imprimir imágenes en mini impresoras térmicas Bluetooth sin depender de aplicaciones móviles propietarias.

## Características
- **Conexión nativa:** Utiliza BlueZ y D-Bus directamente en Linux.
- **Control del cabezal:** Ajuste de temperatura/energía (1-10), contraste (1.0-3.0) y velocidad de avance del papel.
- **Vista previa:** Escala automáticamente cualquier imagen a 384 píxeles de ancho (200 DPI).

## Compatibilidad de Hardware
- **Probado y verificado al 100%:** Modelo **MX06**.
- **Otros modelos compatibles (no probados físicamente):** Series MX (MX05, MX08, MX10) y Cat Printers (GB01, GB02, GB03, GT01) que utilicen el protocolo térmico `0x51 0x78` / servicio GATT `AE01`.
- **No compatible:** Impresoras Phomemo, PeriPage o Niimbot.

## Aviso Legal
Este proyecto es software independiente desarrollado desde cero bajo licencia MIT con fines de interoperabilidad. No contiene código propietario ni está afiliado o respaldado por los fabricantes de Fun Print o WalkPrint.
