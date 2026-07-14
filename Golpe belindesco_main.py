import asyncio
import cv2
import numpy as np
import sys
import os
from bleak import BleakScanner, BleakError

# Configuración de umbrales
UMBRAL_REFLEJO = 240       
VALOR_MITIGACION = 100     
RSSI_PROXIMIDAD = -60      

def verificar_permisos():
    """Verifica si el sistema requiere permisos de administrador para BLE."""
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        if os.geteuid() != 0:
            print("\n[!] ADVERTENCIA: En Linux/macOS podrías necesitar ejecutar como SUDO para escanear BLE.")
            print("Ejecuta: sudo python main.py\n")

async def escanear_ble_y_procesar_video():
    verificar_permisos()
    
    # Selección de backend de cámara automático para máxima compatibilidad
    backend = cv2.CAP_ANY
    if sys.platform.startswith('linux'):
        backend = cv2.CAP_V4L2  # Forzar Linux Video4Linux2 si falla el estándar
        
    cap = cv2.VideoCapture(0, backend)
    if not cap.isOpened():
        print("Error: No se detectó ninguna cámara de video disponible.")
        return

    print("=== DETECTOR BLE 2.0 + MITIGADOR DE REFLEJOS ===")
    print("Repositorio Universal - Presiona 'q' para salir.")

    try:
        while True:
            ble_cercano = False
            try:
                # Escaneo asíncrono optimizado multiplataforma
                dispositivos = await BleakScanner.discover(timeout=0.4)
                for d in dispositivos:
                    if d.rssi and d.rssi > RSSI_PROXIMIDAD:
                        ble_cercano = True
                        break
            except BleakError as be:
                # Si falla el Bluetooth por hardware o permisos, el video sigue funcionando
                pass

            ret, frame = cap.read()
            if not ret:
                break

            if ble_cercano:
                # Filtro matricial de reflejos usando OpenCV vectorial
                mascara_reflejo = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) >= UMBRAL_REFLEJO
                frame[mascara_reflejo] = np.clip(frame[mascara_reflejo] - VALOR_MITIGACION, 0, 255)
                
                cv2.putText(frame, "FILTRO BLE ACTIVO: REFLEJOS MITIGADOS", (15, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Escaneando BLE... Modo Normal", (15, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

            cv2.imshow("Detector BLE 2.0", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Solución para problemas de bucles asíncronos cerrados en Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(escanear_ble_y_procesar_video())
              
